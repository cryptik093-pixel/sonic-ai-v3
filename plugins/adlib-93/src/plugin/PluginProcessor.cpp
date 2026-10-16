#include "PluginProcessor.h"
#include "PluginEditor.h"
#include "dsp/Transitions.h"
#include "presets/FactoryBank.h"
#include "presets/PresetStore.h"
#include <algorithm>
#include <cmath>
#include <limits>

using namespace adlib93;
namespace {
juce::StringArray choices(Param p) {
    switch(p) {
        case Param::CharacterMode:return {"Clean","Soft","Hard","Asymmetric"};
        case Param::DelayDivision:return {"1/32","1/16","1/8","1/4","1/2","Bar"};
        case Param::DelayModifier:return {"Straight","Dotted","Triplet"};
        case Param::DelayThrowMode:return {"Continuous (+6 dB)","Throw only"};
        case Param::RoutingMode:return {"Insert","Send"};
        default:return {};
    }
}
juce::String displayValue(Param p,float value) {
    const auto& d=parameterDefinition(p);
    if(d.kind==ParameterKind::level)return value<=0?juce::String("-inf dB"):juce::String(levelToDb(value),1)+" dB";
    if(juce::String(d.unit)=="fraction")return juce::String(value*100,1)+" %";
    if(juce::String(d.unit)=="Hz"&&value>=1000)return juce::String(value/1000,2)+" kHz";
    return juce::String(value,value==std::floor(value)?0:2)+" "+d.unit;
}
float parseValue(Param p,const juce::String& text) {
    const auto& d=parameterDefinition(p);
    if(d.kind==ParameterKind::level)return text.containsIgnoreCase("inf")?0:levelFromDb(text.getFloatValue());
    auto value=text.getFloatValue();
    if(juce::String(d.unit)=="fraction")value*=.01f;
    if(juce::String(d.unit)=="Hz"&&text.containsIgnoreCase("k"))value*=1000;
    return std::isfinite(value)?std::clamp(value,d.min,d.max):d.initial;
}
float peakDb(float value) noexcept {return value>1.e-5f?std::max(-100.f,20.f*std::log10(value)):-100.f;}
bool sameSnapshot(const ParameterSnapshot& a,const ParameterSnapshot& b) noexcept {
    for(std::size_t i=0;i<parameterCount;++i)
        if(std::abs(a.values[i]-b.values[i])>std::max(1.e-6f,std::abs(b.values[i])*1.e-6f))return false;
    return true;
}
}

juce::AudioProcessorValueTreeState::ParameterLayout AdlibProcessor::makeParameters() {
    juce::AudioProcessorValueTreeState::ParameterLayout layout;
    for(std::size_t i=0;i<parameterCount;++i) {
        const auto p=static_cast<Param>(i);const auto& d=parameterDefinitions()[i];
        const juce::ParameterID id{d.id,1};
        if(d.kind==ParameterKind::boolean) {
            layout.add(std::make_unique<juce::AudioParameterBool>(id,d.name,d.initial>.5f));
        } else if(d.kind==ParameterKind::choice) {
            layout.add(std::make_unique<juce::AudioParameterChoice>(id,d.name,choices(p),static_cast<int>(d.initial)));
        } else {
            juce::NormalisableRange<float> range(d.min,d.max,
                [p](float,float,float value){return parameterFromNormalized(p,value);},
                [p](float,float,float value){return parameterToNormalized(p,value);},
                [p](float,float,float value){const auto& def=parameterDefinition(p);return std::isfinite(value)?std::clamp(value,def.min,def.max):def.initial;});
            layout.add(std::make_unique<juce::AudioParameterFloat>(id,d.name,range,d.initial,
                juce::AudioParameterFloatAttributes().withLabel(d.unit)
                .withStringFromValueFunction([p](float value,int){return displayValue(p,value);})
                .withValueFromStringFunction([p](const juce::String& text){return parseValue(p,text);})));
        }
    }
    return layout;
}

AdlibProcessor::AdlibProcessor()
    : AudioProcessor(BusesProperties().withInput("Vocal input",juce::AudioChannelSet::stereo(),true)
                                     .withOutput("Processed vocal",juce::AudioChannelSet::stereo(),true)),
      parameters(*this,nullptr,"ADLIB93Parameters",makeParameters()),processing(std::make_unique<Transitions>()) {
    static_assert(std::atomic<uint64_t>::is_always_lock_free&&std::atomic<bool>::is_always_lock_free);
    for(std::size_t i=0;i<parameterCount;++i) {
        raw[i]=parameters.getRawParameterValue(parameterDefinitions()[i].id);
        ranged[i]=parameters.getParameter(parameterDefinitions()[i].id);
        jassert(raw[i]&&ranged[i]);
    }
    setLatencySamples(0);
}
AdlibProcessor::~AdlibProcessor()=default;

bool AdlibProcessor::isBusesLayoutSupported(const BusesLayout& layout) const {
    if(layout.inputBuses.size()!=1||layout.outputBuses.size()!=1)return false;
    const auto in=layout.getMainInputChannelSet(),out=layout.getMainOutputChannelSet();
    return (in==juce::AudioChannelSet::mono()&&(out==juce::AudioChannelSet::mono()||out==juce::AudioChannelSet::stereo()))
        ||(in==juce::AudioChannelSet::stereo()&&out==juce::AudioChannelSet::stereo());
}
ParameterSnapshot AdlibProcessor::snapshot() const noexcept {
    ParameterSnapshot result;
    // Atomic physical values are safe on host/state/UI threads. Audio applies the
    // revision fence below; this inspection API does not spin on a writer.
    for(std::size_t i=0;i<parameterCount;++i)result.values[i]=raw[i]->load(std::memory_order_relaxed);
    return sanitizeSnapshot(result);
}
void AdlibProcessor::prepareToPlay(double rate,int maximumBlock) {
    prepared=false;
    processingRate=std::isfinite(rate)&&rate>=8000&&rate<=384000?rate:48000;
    preparedBlock=std::max(1,maximumBlock);
    const auto in=getTotalNumInputChannels(),out=getTotalNumOutputChannels();
    const auto layout=in==1?(out==1?ChannelLayout::monoMono:ChannelLayout::monoStereo):ChannelLayout::stereoStereo;
    audioSnapshot=snapshot();
    ParameterSnapshot discarded;
    for(int i=0;i<4;++i)if(!mailbox.tryConsume(discarded))break;
    processing->prepare({processingRate,static_cast<uint32_t>(preparedBlock),layout},audioSnapshot);
    correlationHistory.assign(static_cast<std::size_t>(std::ceil(.300*processingRate)),{});
    correlationPosition=correlationCount=0;sumLeft=sumRight=sumLL=sumRR=sumLR=0;
    samplePosition=0;clearRequested.store(false);meters.publish({});prepared=true;setLatencySamples(0);
}
void AdlibProcessor::reset() {
    if(!prepared)return;
    audioSnapshot=snapshot();processing->setParameters(audioSnapshot);processing->reset();
    std::fill(correlationHistory.begin(),correlationHistory.end(),StereoFrame{});
    correlationPosition=correlationCount=0;sumLeft=sumRight=sumLL=sumRR=sumLR=0;
    samplePosition=0;meters.publish({});
}
void AdlibProcessor::updateCorrelation(StereoFrame value) noexcept {
    if(correlationHistory.empty())return;
    auto& old=correlationHistory[correlationPosition];
    const double l=value.left,r=value.right,ol=old.left,orr=old.right;
    sumLeft+=l-ol;sumRight+=r-orr;sumLL+=l*l-ol*ol;sumRR+=r*r-orr*orr;sumLR+=l*r-ol*orr;
    old=value;correlationPosition=(correlationPosition+1)%correlationHistory.size();
    correlationCount=std::min(correlationCount+1,correlationHistory.size());
}
float AdlibProcessor::correlation() const noexcept {
    if(correlationHistory.empty())return std::numeric_limits<float>::quiet_NaN();
    if(correlationCount<correlationHistory.size()||getTotalNumOutputChannels()==1)return std::numeric_limits<float>::quiet_NaN();
    const double n=static_cast<double>(correlationCount);
    if(sumLL/n<1.e-8||sumRR/n<1.e-8)return std::numeric_limits<float>::quiet_NaN();
    const double ll=std::max(0.,sumLL-sumLeft*sumLeft/n),rr=std::max(0.,sumRR-sumRight*sumRight/n);
    const double denominator=std::sqrt(ll*rr);
    if(denominator<=1.e-20)return std::numeric_limits<float>::quiet_NaN();
    return static_cast<float>(std::clamp((sumLR-sumLeft*sumRight/n)/denominator,-1.,1.));
}
void AdlibProcessor::processBlock(juce::AudioBuffer<float>& buffer,juce::MidiBuffer& midi){midi.clear();process(buffer,false);}
void AdlibProcessor::processBlockBypassed(juce::AudioBuffer<float>& buffer,juce::MidiBuffer& midi){midi.clear();process(buffer,true);}
void AdlibProcessor::process(juce::AudioBuffer<float>& buffer,bool hostBypass) {
    juce::ScopedNoDenormals noDenormals;
    const int inputs=getTotalNumInputChannels(),outputs=getTotalNumOutputChannels(),frames=buffer.getNumSamples();
    if(!prepared||inputs<1||outputs<1||buffer.getNumChannels()<outputs){buffer.clear();return;}
    const auto revision=snapshotRevision.load(std::memory_order_acquire);
    if((revision&1u)==0) {
        auto candidate=snapshot();
        if(snapshotRevision.load(std::memory_order_acquire)==revision) {
            ParameterSnapshot incoming;
            if(mailbox.tryConsume(incoming)) {
                audioSnapshot=incoming;
                processing->request(incoming);
                processing->setParameters(audioSnapshot);
            } else if(snapshotRevision.load(std::memory_order_acquire)==revision) {
                audioSnapshot=candidate;
                processing->setParameters(audioSnapshot);
            }
        }
    }
    HostTiming timing;
    if(auto* playhead=getPlayHead())if(auto position=playhead->getPosition()) {
        if(auto bpm=position->getBpm();bpm&&std::isfinite(*bpm)&&*bpm>0){timing.bpm=*bpm;timing.bpmValid=true;}
        if(auto signature=position->getTimeSignature();signature&&signature->numerator>0&&signature->denominator>0){timing.numerator=signature->numerator;timing.denominator=signature->denominator;timing.signatureValid=true;}
    }
    processing->setTiming(timing);processing->setBypassed(hostBypass);
    if(clearRequested.exchange(false,std::memory_order_acq_rel))processing->clearTails();
    MeterSnapshot meter;float inputPeak=0,outputPeak=0;
    auto* left=buffer.getWritePointer(0);auto* right=outputs>1?buffer.getWritePointer(1):nullptr;
    if(frames==0)processing->serviceZeroBlock();
    for(int offset=0;offset<frames;) {
        const int end=offset+std::min(preparedBlock,frames-offset);
        for(;offset<end;++offset) {
            const StereoFrame in{left[offset],inputs>1&&right?right[offset]:left[offset]};
            const auto out=processing->process(in);
            left[offset]=outputs==1?static_cast<float>((static_cast<double>(out.left)+out.right)*.5):out.left;
            if(right)right[offset]=out.right;
            updateCorrelation(out);
            const auto m=processing->measurements();
            inputPeak=std::max(inputPeak,m.inputPeak);outputPeak=std::max(outputPeak,m.outputPeak);
            meter.gateReductionDb=std::max(meter.gateReductionDb,m.gateReductionDb);
            meter.deessReductionDb=std::max(meter.deessReductionDb,m.deessReductionDb);
            meter.limiterReductionDb=std::max(meter.limiterReductionDb,m.limiterReductionDb);
            ++samplePosition;
        }
    }
    for(int channel=outputs;channel<buffer.getNumChannels();++channel)buffer.clear(channel,0,frames);
    const auto m=processing->measurements();
    meter.inputPeakDb=peakDb(inputPeak);meter.outputPeakDb=peakDb(outputPeak);meter.tempo=m.tempo;
    meter.manualTempo=!timing.bpmValid;meter.delayClamped=m.delayClamped;meter.clearing=m.clearing;
    meter.frozen=m.freezeHeld;meter.listen=audioSnapshot[Param::DeessListen]>.5f;
    meter.correlation=correlation();meter.diagnostics=m.diagnostics;meters.publish(meter);
}
juce::AudioProcessorEditor* AdlibProcessor::createEditor(){return new AdlibEditor(*this);}
// Internal performance bypass resumes off. JUCE owns the distinct VST3 host
// bypass so its processor/controller persistence remains host-compatible.
juce::AudioProcessorParameter* AdlibProcessor::getBypassParameter() const {return nullptr;}

void AdlibProcessor::applySnapshot(ParameterSnapshot value,bool notify) {
    value=sanitizeSnapshot(value);
    for(std::size_t i=0;i<parameterCount;++i) {
        const float normalized=ranged[i]->convertTo0to1(value.values[i]);
        if(ranged[i]->getValue()==normalized)continue;
        if(notify)ranged[i]->beginChangeGesture();
        // JUCE/APVTS listeners require this notification even on full state
        // recall. No host/UI notification is issued from processBlock.
        ranged[i]->setValueNotifyingHost(normalized);
        if(notify)ranged[i]->endChangeGesture();
    }
}
void AdlibProcessor::requestSnapshot(ParameterSnapshot value,bool notify) {
    const juce::ScopedLock guard(stateMutex);
    value=persistentSnapshot(value);
    writingSnapshot.store(true,std::memory_order_release);snapshotRevision.fetch_add(1,std::memory_order_acq_rel);
    applySnapshot(value,notify);
    // Serialized producers plus one bounded consumer leave a publishable slot;
    // replacement coalesces rapid selections instead of allocating queue nodes.
    // A consumer can turn Ready slots into Free between the mailbox's two
    // scans. Retain this producer's latest value and retry off the audio thread
    // instead of dropping a valid full-state request on that rare race.
    while(!mailbox.tryPublish(value))juce::Thread::yield();
    snapshotRevision.fetch_add(1,std::memory_order_release);writingSnapshot.store(false,std::memory_order_release);
    saved.parameters=value;saved.slots[static_cast<std::size_t>(activeSlot.load())]=value;
}
void AdlibProcessor::getStateInformation(juce::MemoryBlock& destination) {
    const juce::ScopedLock guard(stateMutex);
    auto state=saved;state.parameters=persistentSnapshot(snapshot());state.activeSlot=activeSlot.load();
    state.presetBaseline=persistentSnapshot(presetBaseline);state.hasPresetBaseline=true;
    state.slots[static_cast<std::size_t>(state.activeSlot)]=state.parameters;
    state.ui.modified=state.ui.modified||!sameSnapshot(state.parameters,applyCalibrationLocks(presetBaseline,state.parameters,state.locks));
    const auto bytes=encodeStateBytes(state);destination.replaceAll(bytes.data(),bytes.size());
}
void AdlibProcessor::setStateInformation(const void* data,int bytes) {
    if(bytes<=0||static_cast<std::size_t>(bytes)>maximumStateBytes){const juce::ScopedLock guard(stateMutex);errorText="State is empty or exceeds 256 KiB";return;}
    const auto decoded=decodeState(data,static_cast<std::size_t>(bytes));
    const juce::ScopedLock guard(stateMutex);
    if(!decoded){errorText=juce::String(decoded.error);return;}
    saved=decoded.state;activeSlot.store(saved.activeSlot);
    presetBaseline=saved.hasPresetBaseline?saved.presetBaseline:saved.parameters;
    if(!saved.hasPresetBaseline)
        for(const auto& factory:factoryPresets())if(saved.ui.preset==factory.name)presetBaseline=factory.parameters;
    requestSnapshot(saved.parameters,false);errorText.clear();
}
bool AdlibProcessor::loadFactory(int index) {
    if(index<0||index>=static_cast<int>(factoryPresets().size()))return false;
    const juce::ScopedLock guard(stateMutex);const auto current=persistentSnapshot(snapshot());
    saved.slots[static_cast<std::size_t>(1-activeSlot.load())]=current;
    const auto& preset=factoryPresets()[static_cast<std::size_t>(index)];
    auto value=applyCalibrationLocks(preset.parameters,current,saved.locks);
    presetBaseline=preset.parameters;saved.ui.preset=preset.name;saved.ui.modified=false;
    requestSnapshot(value,true);errorText.clear();return true;
}
void AdlibProcessor::selectAB(int index) {
    if(index<0||index>1)return;const juce::ScopedLock guard(stateMutex);
    const int previous=activeSlot.load();if(previous==index)return;
    const auto current=persistentSnapshot(snapshot());saved.slots[static_cast<std::size_t>(previous)]=current;
    const auto incoming=applyCalibrationLocks(saved.slots[static_cast<std::size_t>(index)],current,saved.locks);
    activeSlot.store(index);saved.activeSlot=index;requestSnapshot(incoming,true);
    saved.ui.modified=!sameSnapshot(incoming,applyCalibrationLocks(presetBaseline,incoming,saved.locks));
}
void AdlibProcessor::copyAB() {
    const juce::ScopedLock guard(stateMutex);const auto current=persistentSnapshot(snapshot());
    saved.slots[static_cast<std::size_t>(activeSlot.load())]=current;saved.slots[static_cast<std::size_t>(1-activeSlot.load())]=current;
}
void AdlibProcessor::resetPreset(bool full) {
    const juce::ScopedLock guard(stateMutex);
    if(full){saved.locks={false,false,false};presetBaseline=makeInitSnapshot();saved.ui.preset="Init";}
    const auto value=applyCalibrationLocks(presetBaseline,snapshot(),saved.locks);
    requestSnapshot(value,true);saved.ui.modified=false;errorText.clear();
}
void AdlibProcessor::clearTails() {
    setPerformance(Param::ThrowActive,false);setPerformance(Param::FreezeActive,false);
    clearRequested.store(true,std::memory_order_release);
}
void AdlibProcessor::setPerformance(Param parameter,bool enabled) {
    if(parameter!=Param::ThrowActive&&parameter!=Param::FreezeActive&&parameter!=Param::DeessListen&&parameter!=Param::BypassInternal)return;
    auto* value=ranged[static_cast<std::size_t>(parameter)];value->beginChangeGesture();value->setValueNotifyingHost(enabled?1.f:0.f);value->endChangeGesture();
}
CalibrationLocks AdlibProcessor::calibrationLocks() const {const juce::ScopedLock guard(stateMutex);return saved.locks;}
void AdlibProcessor::setCalibrationLocks(CalibrationLocks locks){const juce::ScopedLock guard(stateMutex);saved.locks=locks;}
UiState AdlibProcessor::uiState() const {
    const juce::ScopedLock guard(stateMutex);auto value=saved.ui;
    const auto current=persistentSnapshot(snapshot());
    value.modified=value.modified||!sameSnapshot(current,applyCalibrationLocks(presetBaseline,current,saved.locks));return value;
}
void AdlibProcessor::setUiState(const UiState& value) {
    const juce::ScopedLock guard(stateMutex);
    saved.ui.scale=std::isfinite(value.scale)?std::clamp(value.scale,.75f,1.5f):1;
    saved.ui.page=std::clamp(value.page,0,5);
}
juce::File AdlibProcessor::userPresetDirectory() const {
    try {const PresetStore store;return juce::File(juce::String(store.root().wstring().c_str()));}
    catch(const std::exception& error){const juce::ScopedLock guard(stateMutex);errorText=error.what();return {};}
}
bool AdlibProcessor::saveUserPreset(const juce::String& name) {
    const juce::ScopedLock guard(stateMutex);
    try {
        const PresetStore store;const auto value=persistentSnapshot(snapshot());
        const auto result=store.save({{},name.toStdString(),value});
        if(!result){errorText=juce::String(result.error);return false;}
        presetBaseline=value;saved.ui.preset=name.toStdString();saved.ui.modified=false;errorText.clear();return true;
    } catch(const std::exception& error){errorText=error.what();return false;}
}
bool AdlibProcessor::loadUserPreset(const juce::File& file) {
    const juce::ScopedLock guard(stateMutex);
    try {
        const PresetStore store;const auto result=store.load(std::filesystem::path(file.getFullPathName().toWideCharPointer()));
        if(!result){errorText=juce::String(result.error);return false;}
        const auto current=persistentSnapshot(snapshot());saved.slots[static_cast<std::size_t>(1-activeSlot.load())]=current;
        const auto value=applyCalibrationLocks(result.preset.parameters,current,saved.locks);
        presetBaseline=result.preset.parameters;saved.ui.preset=result.preset.name;saved.ui.modified=false;requestSnapshot(value,true);errorText.clear();return true;
    } catch(const std::exception& error){errorText=error.what();return false;}
}
juce::String AdlibProcessor::lastError() const {const juce::ScopedLock guard(stateMutex);return errorText;}
juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter(){return new AdlibProcessor();}

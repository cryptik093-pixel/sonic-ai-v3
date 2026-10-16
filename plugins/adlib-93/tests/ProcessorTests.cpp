#include "TestSupport.h"
#include "plugin/PluginProcessor.h"
#include "core/Types.h"
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <limits>
#include <new>
#include <thread>

namespace {
thread_local bool trackCallback=false;
thread_local std::size_t callbackAllocations=0,callbackFrees=0;
}
void* operator new(std::size_t bytes){if(trackCallback)++callbackAllocations;if(auto* p=std::malloc(bytes?bytes:1))return p;throw std::bad_alloc();}
void* operator new[](std::size_t bytes){return ::operator new(bytes);}
void operator delete(void* pointer) noexcept {if(trackCallback&&pointer)++callbackFrees;std::free(pointer);}
void operator delete[](void* pointer) noexcept {::operator delete(pointer);}
void operator delete(void* pointer,std::size_t) noexcept {::operator delete(pointer);}
void operator delete[](void* pointer,std::size_t) noexcept {::operator delete(pointer);}

using namespace adlib93;
namespace {
void set(AdlibProcessor& processor,Param parameter,float value) {
    auto* p=processor.parameters.getParameter(parameterDefinition(parameter).id);
    require(p!=nullptr,"Registered stable parameter ID");
    p->setValueNotifyingHost(p->convertTo0to1(value));
}
bool near(float a,float b,float epsilon=1.e-5f){return std::abs(a-b)<=epsilon;}
void layout(AdlibProcessor& processor,int input,int output) {
    auto buses=processor.getBusesLayout();buses.inputBuses.set(0,juce::AudioChannelSet::canonicalChannelSet(input));
    buses.outputBuses.set(0,juce::AudioChannelSet::canonicalChannelSet(output));
    require(processor.setBusesLayout(buses),"Supported requested bus layout");
}
void runCallback(AdlibProcessor& processor,juce::AudioBuffer<float>& buffer,bool bypass=false) {
    juce::MidiBuffer midi;
    callbackAllocations=callbackFrees=0;trackCallback=true;
    if(bypass)processor.processBlockBypassed(buffer,midi);else processor.processBlock(buffer,midi);
    trackCallback=false;
    require(callbackAllocations==0&&callbackFrees==0,"No C++ new/delete in production callback");
}
class Clock final:public juce::AudioPlayHead {
public:
    juce::Optional<PositionInfo> position;
    juce::Optional<PositionInfo> getPosition() const override{return position;}
};
}

TEST_CASE("Processor.Parameters") {
    AdlibProcessor p;
    require(parameterCount==70&&p.getParameters().size()==70,"Exactly 70 approved stable host parameters");
    require(p.getNumPrograms()==1&&!p.acceptsMidi()&&!p.producesMidi(),"One inert host state and no MIDI");
    const auto initial=p.snapshot();
    for(std::size_t i=0;i<parameterCount;++i) {
        const auto& d=parameterDefinitions()[i];auto* parameter=p.parameters.getParameter(d.id);
        require(parameter!=nullptr,"All stable IDs exposed through APVTS");
        require(near(initial.values[i],d.initial,std::max(1.e-6f,std::abs(d.initial)*1.e-6f)),"Physical Init value matches registry within float normalization precision");
        const auto& range=parameter->getNormalisableRange();
        require(range.start==d.min&&range.end==d.max,"Physical range remains backward compatible");
    }
    auto* frequency=p.parameters.getParameter("deess.frequency");
    require(!p.uiState().modified,"Float normalization roundoff cannot dirty Init");
    require(near(frequency->convertFrom0to1(.5f),6000,.01f),"Log frequency midpoint is physical 6000Hz");
    require(near(frequency->convertFrom0to1(frequency->getValueForText("6 kHz")),6000,.01f),"Host text entry parses physical frequency units");
    auto* level=p.parameters.getParameter("direct.level");require(level->getText(0,32).contains("inf"),"Host exposes exact branch mute label");
    auto* mix=p.parameters.getParameter("mix.amount");require(mix->getText(.5f,32).contains("50"),"Host percentage text uses physical fractional parameter mapping");
    require(p.getBypassParameter()==nullptr&&p.parameters.getParameter("bypass.internal")!=nullptr,"JUCE supplies persistent host bypass separately from the stable transient internal bypass");
    set(p,Param::OutputGain,3);p.setCurrentProgram(0);
    require(near(p.snapshot()[Param::OutputGain],3),"Host program selection cannot load a preset");
}

TEST_CASE("Processor.Layouts") {
    AdlibProcessor p;
    for(const auto pair:{std::pair<int,int>{1,1},{1,2},{2,2}}) {
        layout(p,pair.first,pair.second);
        for(double rate:{44100.,48000.,88200.,96000.}) {
            set(p,Param::LimiterEnabled,0);p.prepareToPlay(rate,128);
            require(p.getLatencySamples()==0&&p.getTailLengthSeconds()==180,"Actual zero through latency/conservative finite tail");
            for(int size:{0,1,16,64,128,256,512,1024,4097}) {
                juce::AudioBuffer<float> buffer(pair.second,size);
                for(int i=0;i<size;++i){buffer.setSample(0,i,.2f*std::sin(float(i)*.07f));if(pair.second>1)buffer.setSample(1,i,pair.first==2?-.1f*std::cos(float(i)*.1f):0);}
                const auto expected=juce::AudioBuffer<float>(buffer);
                runCallback(p,buffer);
                for(int i=0;i<size;++i) {
                    require(near(buffer.getSample(0,i),expected.getSample(0,i),1.e-6f),"Neutral in-place dry identity");
                    if(pair.second>1)require(near(buffer.getSample(1,i),expected.getSample(pair.first>1?1:0,i),1.e-6f),"Stereo identity or mono duplication without extra gain");
                }
            }
            p.reset();p.releaseResources();
        }
    }
    auto bad=p.getBusesLayout();bad.inputBuses.set(0,juce::AudioChannelSet::stereo());bad.outputBuses.set(0,juce::AudioChannelSet::mono());
    require(!p.isBusesLayoutSupported(bad),"Reject stereo to mono");
    bad.inputBuses.set(0,juce::AudioChannelSet::disabled());require(!p.isBusesLayoutSupported(bad),"Reject zero-channel input");
    bad=p.getBusesLayout();bad.inputBuses.add(juce::AudioChannelSet::mono());require(!p.isBusesLayoutSupported(bad),"Reject external sidechain bus");
}

TEST_CASE("Processor.State") {
    AdlibProcessor p;
    p.setCalibrationLocks({false,false,false});set(p,Param::InputGain,7);set(p,Param::OutputGain,-3);
    p.copyAB();p.selectAB(1);set(p,Param::DelayTime,372);p.selectAB(0);
    require(near(p.snapshot()[Param::DelayTime],250),"A/B restores outgoing stored values");
    p.selectAB(1);require(near(p.snapshot()[Param::DelayTime],372),"A/B preserves other slot edits");
    auto ui=p.uiState();ui.page=4;ui.scale=.75f;p.setUiState(ui);
    for(auto parameter:{Param::ThrowActive,Param::FreezeActive,Param::DeessListen,Param::BypassInternal})p.setPerformance(parameter,true);
    juce::MemoryBlock state;p.getStateInformation(state);
    auto parsed=decodeState(state.getData(),state.getSize());require(bool(parsed),"Actual host state decodes");
    AdlibProcessor restored;restored.setCalibrationLocks({true,true,true});restored.setStateInformation(state.getData(),static_cast<int>(state.getSize()));
    require(near(restored.snapshot()[Param::InputGain],7)&&near(restored.snapshot()[Param::OutputGain],-3),"Host recall ignores browsing calibration locks");
    require(restored.activeAB()==1&&restored.uiState().page==4&&restored.uiState().scale==.75f,"A/B and UI metadata recall");
    require(!restored.calibrationLocks().input&&!restored.calibrationLocks().gate&&!restored.calibrationLocks().output,"Project locks recall exactly");
    for(auto parameter:{Param::ThrowActive,Param::FreezeActive,Param::DeessListen,Param::BypassInternal})require(restored.snapshot()[parameter]==0,"Performance states never resume from stored audio state");
    restored.selectAB(0);require(near(restored.snapshot()[Param::DelayTime],250),"Inactive A slot recalls");
    const auto previous=restored.snapshot();
    const char invalid[]="{\"schema\":99}";restored.setStateInformation(invalid,sizeof(invalid)-1);
    require(restored.snapshot().values==previous.values&&!restored.lastError().isEmpty(),"Corrupt/future state preserves working values and reports error");
    restored.setStateInformation(nullptr,static_cast<int>(maximumStateBytes)+1);require(restored.snapshot().values==previous.values,"Oversize state refused before read");
    set(restored,Param::InputGain,5);set(restored,Param::OutputGain,-4);set(restored,Param::GateThreshold,-42);
    restored.setCalibrationLocks({true,true,true});require(restored.loadFactory(0),"Factory bank loads through processor");
    require(near(restored.snapshot()[Param::InputGain],5)&&near(restored.snapshot()[Param::OutputGain],-4)&&near(restored.snapshot()[Param::GateThreshold],-42),"Browsing honors calibration locks");
    require(!restored.loadFactory(-1)&&!restored.loadFactory(24),"Invalid factory selections refused");
    restored.resetPreset(true);require(!restored.calibrationLocks().input&&near(restored.snapshot()[Param::InputGain],0),"Explicit full reset clears calibration locks and returns Init");
    PersistedState user;user.parameters[Param::DelayTime]=777;user.parameters[Param::InputGain]=7;
    user.parameters[Param::OutputGain]=-3;user.parameters[Param::GateThreshold]=-42;
    user.ui.preset="Modified user-style recipe";user.ui.modified=true;
    auto userJson=encodeStateJson(user);
    userJson.insert(1,"\"presetBaseline\":{\"delay.time\":321,\"input.gain\":2,\"output.gain\":-8,\"gate.threshold\":-63},");
    restored.setStateInformation(userJson.data(),static_cast<int>(userJson.size()));
    juce::MemoryBlock recalled;restored.getStateInformation(recalled);
    AdlibProcessor afterReopen;afterReopen.setStateInformation(recalled.getData(),static_cast<int>(recalled.getSize()));
    afterReopen.resetPreset(false);
    require(near(afterReopen.snapshot()[Param::DelayTime],321)&&near(afterReopen.snapshot()[Param::InputGain],7)
        &&near(afterReopen.snapshot()[Param::OutputGain],-3)&&near(afterReopen.snapshot()[Param::GateThreshold],-42),"User baseline survives host save/reopen and Reset honors calibration locks");
    afterReopen.setCalibrationLocks({false,false,false});afterReopen.resetPreset(false);
    require(near(afterReopen.snapshot()[Param::InputGain],2)&&near(afterReopen.snapshot()[Param::OutputGain],-8)
        &&near(afterReopen.snapshot()[Param::GateThreshold],-63),"Unlock then Reset restores original user recipe calibration values");
}

TEST_CASE("Processor.Realtime") {
    AdlibProcessor p;p.setCalibrationLocks({false,false,false});p.prepareToPlay(48000,64);
    juce::AudioBuffer<float> buffer(2,97);
    for(int block=0;block<240;++block) {
        if(block%24==0)p.loadFactory((block/24)%24);
        if(block%13==0)p.setPerformance(Param::FreezeActive,(block/13)%2!=0);
        if(block%17==0)p.setPerformance(Param::ThrowActive,(block/17)%2!=0);
        if(block%31==0)p.clearTails();
        set(p,Param::MixAmount,float(block%101)/100);
        for(int i=0;i<buffer.getNumSamples();++i){buffer.setSample(0,i,.15f*std::sin(float(block*97+i)*.04f));buffer.setSample(1,i,.11f*std::sin(float(block*97+i)*.03f));}
        runCallback(p,buffer,block%19==0);
        for(int channel=0;channel<2;++channel)for(int i=0;i<buffer.getNumSamples();++i)require(std::isfinite(buffer.getSample(channel,i)),"Finite production output under preset/clear/performance/automation changes");
    }
    juce::AudioBuffer<float> zero(2,0);runCallback(p,zero);
    buffer.clear();p.reset();runCallback(p,buffer);
}

TEST_CASE("Processor.Meters") {
    AdlibProcessor p;set(p,Param::LimiterEnabled,0);p.prepareToPlay(48000,128);
    Clock clock;p.setPlayHead(&clock);
    juce::AudioBuffer<float> buffer(2,128);
    for(int block=0;block<120;++block) {
        for(int i=0;i<128;++i){const float value=.2f*std::sin(float(block*128+i)*.07f);buffer.setSample(0,i,value);buffer.setSample(1,i,-value);}
        runCallback(p,buffer);
        if(block==0)require(!std::isfinite(p.readMeters().correlation),"Correlation unavailable before completed 300ms window");
    }
    auto meter=p.readMeters();require(meter.correlation<-.999f,"Measured opposite-polarity stereo correlation");
    require(meter.inputPeakDb>-14.1f&&meter.inputPeakDb<-13.9f,"After-trim actual input sample peak");
    require(meter.manualTempo&&near(float(meter.tempo),120),"Missing host tempo has explicit manual fallback");
    juce::AudioPlayHead::PositionInfo position;position.setBpm(90);position.setTimeSignature(juce::AudioPlayHead::TimeSignature{3,4});clock.position=position;
    buffer.clear();runCallback(p,buffer);require(!p.readMeters().manualTempo&&near(float(p.readMeters().tempo),90),"Valid host timing forwarded without unsafe dereference");
    position.setBpm(std::numeric_limits<double>::quiet_NaN());clock.position=position;runCallback(p,buffer);
    require(p.readMeters().manualTempo,"Invalid host tempo uses manual fallback");
    p.setPlayHead(nullptr);layout(p,1,1);p.prepareToPlay(48000,128);
    juce::AudioBuffer<float> mono(1,15000);for(int i=0;i<15000;++i)mono.setSample(0,i,.2f*std::sin(float(i)*.07f));runCallback(p,mono);
    require(!std::isfinite(p.readMeters().correlation),"Mono output never invents stereo correlation");
    mono.clear();mono.setSample(0,0,std::numeric_limits<float>::quiet_NaN());runCallback(p,mono);
    require(std::isfinite(mono.getSample(0,0))&&p.readMeters().diagnostics>0,"Exceptional input exposes an actual diagnostic count outside callback");
}

TEST_CASE("Processor.Editor") {
    juce::ScopedJuceInitialiser_GUI gui;
    AdlibProcessor p;
    for(float scale:{.75f,1.f,1.5f}) {
        auto state=p.uiState();state.scale=scale;p.setUiState(state);
        std::unique_ptr<juce::AudioProcessorEditor> editor(p.createEditor());
        require(editor!=nullptr&&editor->getWidth()==static_cast<int>(1040*scale)&&editor->getHeight()==static_cast<int>(680*scale),"Actual native editor uses approved dimensions/scales");
        const auto image=editor->createComponentSnapshot(editor->getLocalBounds());
        require(image.isValid()&&image.getWidth()==editor->getWidth(),"Actual native editor renders offscreen");
        const auto captureDirectory=juce::SystemStats::getEnvironmentVariable("ADLIB93_CAPTURE_DIR",{});
        if(captureDirectory.isNotEmpty()) {
            juce::File directory(captureDirectory);require(directory.createDirectory().wasOk(),"Create explicitly requested editor capture directory");
            const auto file=directory.getChildFile("adlib93-"+juce::String(static_cast<int>(scale*100))+".png");
            require(!file.exists(),"Preserve existing editor capture");
            juce::FileOutputStream stream(file);require(stream.openedOk(),"Open native editor PNG");
            juce::PNGImageFormat format;require(format.writeImageToStream(image,stream),"Write actual native editor PNG");
        }
    }
}

TEST_CASE("Processor.ConcurrentRecall") {
    AdlibProcessor p;p.prepareToPlay(48000,128);
    PersistedState first,second;
    for(auto parameter:{Param::InputGain,Param::OutputGain,Param::CharacterTrim}){first.parameters[parameter]=-7;second.parameters[parameter]=-2;}
    const auto a=encodeStateBytes(first),b=encodeStateBytes(second);
    std::atomic<bool> stop{false},failed{false};std::atomic<unsigned> calls{0};
    std::thread audio([&] {
        juce::AudioBuffer<float> buffer(2,128);juce::MidiBuffer midi;
        while(!stop.load()) {
            for(int i=0;i<128;++i){buffer.setSample(0,i,.1f*std::sin(float(i)*.05f));buffer.setSample(1,i,-buffer.getSample(0,i));}
            callbackAllocations=callbackFrees=0;trackCallback=true;p.processBlock(buffer,midi);trackCallback=false;
            if(callbackAllocations||callbackFrees)failed.store(true);
            for(int i=0;i<128;++i)if(!std::isfinite(buffer.getSample(0,i))||!std::isfinite(buffer.getSample(1,i)))failed.store(true);
            calls.fetch_add(1);
        }
    });
    while(calls.load()==0)std::this_thread::yield();
    for(int i=0;i<32;++i) {
        const auto& data=i%2?a:b;p.setStateInformation(data.data(),static_cast<int>(data.size()));
        juce::MemoryBlock state;p.getStateInformation(state);const auto decoded=decodeState(state.getData(),state.getSize());
        if(!decoded||!near(decoded.state.parameters[Param::InputGain],decoded.state.parameters[Param::OutputGain],1.e-4f)
                ||!near(decoded.state.parameters[Param::InputGain],decoded.state.parameters[Param::CharacterTrim],1.e-4f))failed.store(true);
    }
    stop.store(true);audio.join();
    require(calls.load()>0&&!failed.load(),"Complete host recall while processing remains finite, allocation-free and serialized");
}

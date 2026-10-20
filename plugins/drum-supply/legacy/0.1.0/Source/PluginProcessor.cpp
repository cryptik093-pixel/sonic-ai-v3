#include "PluginProcessor.h"
#include "PluginEditor.h"
static_assert(std::atomic<float>::is_always_lock_free && std::atomic<int>::is_always_lock_free);
namespace { constexpr std::array<const char*,4> ids{"department","body","character","space"}; }
juce::AudioProcessorValueTreeState::ParameterLayout DrumProcessor::layout() {
    juce::AudioProcessorValueTreeState::ParameterLayout result;
    result.add(std::make_unique<juce::AudioParameterChoice>(juce::ParameterID{"department",1},"Department",
        juce::StringArray{"Kick","Snare","Hi-Hat","Cymbal","Tom","Percussion","Clap"},0));
    for(int i=1;i<4;++i) result.add(std::make_unique<juce::AudioParameterFloat>(juce::ParameterID{ids[static_cast<size_t>(i)],1},
        juce::String(ids[static_cast<size_t>(i)]).toUpperCase(),juce::NormalisableRange<float>(0,1),i==3?.25f:.5f));
    return result;
}
DrumProcessor::DrumProcessor():AudioProcessor(BusesProperties().withOutput("Drums",juce::AudioChannelSet::stereo(),true)),
    parameters(*this,nullptr,"DrumSupply",layout()) {
    for(size_t i=0;i<4;++i)raw[i]=parameters.getRawParameterValue(ids[i]);
    setLatencySamples(0);
}
bool DrumProcessor::isBusesLayoutSupported(const BusesLayout& b) const {
    return b.inputBuses.isEmpty() && b.outputBuses.size()==1 &&
        (b.getMainOutputChannelSet()==juce::AudioChannelSet::mono() || b.getMainOutputChannelSet()==juce::AudioChannelSet::stereo());
}
void DrumProcessor::prepareToPlay(double rate,int) {
    engine.prepare(rate,{raw[1]->load(),raw[2]->load(),raw[3]->load()});reset();
}
void DrumProcessor::reset() {
    engine.reset();
    preview.store(-1);peak.store(0);meterFrame.fetch_add(1);setLatencySamples(0);
}
void DrumProcessor::processBlock(juce::AudioBuffer<float>& audio,juce::MidiBuffer& midi) {
    juce::ScopedNoDenormals noDenormals;
    audio.clear();
    engine.setMacros({raw[1]->load(),raw[2]->load(),raw[3]->load()});
    const auto category=static_cast<int>(raw[0]->load());
    const int clicked=preview.exchange(-1);
    if(clicked>=0)engine.trigger(clicked,.8f,45);
    auto event=midi.cbegin();const auto end=midi.cend();float level=0;
    for(int i=0;i<audio.getNumSamples();++i) {
        while(event!=end && (*event).samplePosition<=i) {
            const auto message=*event;
            // Inspect bounded MIDI bytes directly. Constructing a MidiMessage
            // for an arbitrary SysEx packet can allocate on the audio thread.
            const auto* bytes=message.data;
            if(message.numBytes==3 && (bytes[0]&0xf0)==0x90 && bytes[1]<128 && bytes[2]>0 && bytes[2]<128) {
                // C3/MIDI 60 auditions the selected department; GM notes play a kit.
                const int note=bytes[1];
                engine.trigger(note==60?category:ohdrum::departmentForNote(note),static_cast<float>(bytes[2])/127, note==60?45:note);
            } else if(message.numBytes==3 && (bytes[0]&0xf0)==0xb0 && (bytes[1]==120 || bytes[1]==123))engine.reset();
            ++event;
        }
        const auto out=engine.tick();
        if(audio.getNumChannels()>0)audio.setSample(0,i,audio.getNumChannels()==1?(out[0]+out[1])*.5f:out[0]);
        if(audio.getNumChannels()>1)audio.setSample(1,i,out[1]);
        level=std::max(level,std::max(std::abs(out[0]),std::abs(out[1])));
    }
    midi.clear();peak.store(level,std::memory_order_relaxed);meterFrame.fetch_add(1,std::memory_order_release);
}
void DrumProcessor::getStateInformation(juce::MemoryBlock& dest) {
    auto state=std::make_unique<juce::DynamicObject>();state->setProperty("version",1);
    for(size_t i=0;i<4;++i)state->setProperty(ids[i],raw[i]->load());
    const auto text=juce::JSON::toString(juce::var(state.release()),true);
    dest.replaceAll(text.toRawUTF8(),static_cast<size_t>(text.getNumBytesAsUTF8()));
}
bool DrumProcessor::restoreState(const void* data,int size) {
    if(data==nullptr || size<=0 || size>4096)return false;
    const auto state=juce::JSON::parse(juce::String::fromUTF8(static_cast<const char*>(data),size));
    const auto* object=state.getDynamicObject();
    if(object==nullptr || object->getProperties().size()!=5 || !state.hasProperty("version") ||
        !state["version"].isInt() || static_cast<int>(state["version"])!=1)return false;
    std::array<float,4> values{};
    for(size_t i=0;i<4;++i) {
        const auto v=state[ids[i]];
        if(!v.isInt() && !v.isDouble())return false;
        const double n=static_cast<double>(v);
        if(!std::isfinite(n) || n<0 || n>(i==0?6:1) || (i==0 && std::floor(n)!=n))return false;
        values[i]=static_cast<float>(n);
    }
    // Validate the complete snapshot before touching the current sound.
    for(size_t i=0;i<4;++i) {
        auto* p=parameters.getParameter(ids[i]);p->setValueNotifyingHost(p->convertTo0to1(values[i]));
    }
    return true;
}
void DrumProcessor::setStateInformation(const void* data,int size) { (void)restoreState(data,size); }
juce::AudioProcessorEditor* DrumProcessor::createEditor() { return new DrumEditor(*this); }
juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() { return new DrumProcessor(); }

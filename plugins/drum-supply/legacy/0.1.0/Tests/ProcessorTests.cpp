#include "PluginProcessor.h"
#include <juce_graphics/juce_graphics.h>
#include <iostream>
#include <cstdlib>
#include <new>
#include <cstring>
namespace {thread_local bool watching=false;thread_local size_t allocations=0;}
void* operator new(std::size_t n){if(watching)++allocations;if(auto* p=std::malloc(n?n:1))return p;throw std::bad_alloc();}
void* operator new[](std::size_t n){return ::operator new(n);}
void operator delete(void* p)noexcept{std::free(p);}void operator delete[](void* p)noexcept{std::free(p);}
void operator delete(void* p,std::size_t)noexcept{std::free(p);}void operator delete[](void* p,std::size_t)noexcept{std::free(p);}
void require(bool ok,const char* message){if(!ok){std::cerr<<"FAIL "<<message<<'\n';std::exit(1);}}
void set(DrumProcessor& p,const char* id,float v){auto* a=p.parameters.getParameter(id);a->setValueNotifyingHost(a->convertTo0to1(v));}
std::vector<float> render(int block){
    DrumProcessor p;p.prepareToPlay(48000,block);std::vector<float> out;
    for(int offset=0;offset<24000;offset+=block){const int n=std::min(block,24000-offset);juce::AudioBuffer<float> audio(2,n);juce::MidiBuffer midi;
        for(int t:{17,519,10001})if(t>=offset&&t<offset+n)midi.addEvent(juce::MidiMessage::noteOn(1,38,.8f),t-offset);
        allocations=0;watching=true;p.processBlock(audio,midi);watching=false;require(allocations==0,"no processor callback allocations");out.insert(out.end(),audio.getReadPointer(0),audio.getReadPointer(0)+n);}
    return out;
}
int main(int argc,char** argv){
    juce::ScopedJuceInitialiser_GUI gui;DrumProcessor p;
    require(p.acceptsMidi()&&!p.producesMidi(),"instrument MIDI contract");
    auto buses=p.getBusesLayout();require(p.isBusesLayoutSupported(buses),"stereo output");
    buses.outputBuses.set(0,juce::AudioChannelSet::mono());require(p.isBusesLayoutSupported(buses),"mono output");
    buses.outputBuses.set(0,juce::AudioChannelSet::create5point1());require(!p.isBusesLayoutSupported(buses),"reject unsupported layout");
    const auto params=p.getParameters();require(params.size()==4,"stable four parameter contract");
    for(const char* id:{"department","body","character","space"})require(p.parameters.getParameter(id)!=nullptr,"parameter IDs exist");
    set(p,"department",6);set(p,"body",.83f);set(p,"character",.17f);set(p,"space",.61f);
    juce::MemoryBlock state;p.getStateInformation(state);DrumProcessor restored;
    require(restored.restoreState(state.getData(),static_cast<int>(state.getSize())),"version 1 state roundtrip");
    for(const char* id:{"department","body","character","space"})require(std::abs(p.parameters.getRawParameterValue(id)->load()-restored.parameters.getRawParameterValue(id)->load())<1e-6f,"every parameter recalled");
    for(const char* bad:{"{}","{\"version\":2}","{\"version\":1,\"department\":0,\"body\":2,\"character\":0,\"space\":0}","{\"version\":1,\"department\":0.5,\"body\":0,\"character\":0,\"space\":0}"}){
        require(!restored.restoreState(bad,static_cast<int>(std::strlen(bad))),"reject invalid state");
        require(std::abs(restored.parameters.getRawParameterValue("body")->load()-.83f)<1e-6f,"bad state preserves sound");}
    const auto partition=render(64);
    require(partition==render(511),"sample-accurate MIDI independent of unequal partitions");
    const auto onset=std::find_if(partition.begin(),partition.end(),[](float x){return std::abs(x)>1.0e-7f;});
    const auto firstSample=std::distance(partition.begin(),onset);
    require(firstSample>=17 && firstSample<=18,"MIDI onset within one sample of event; no block/lookahead delay");
    p.prepareToPlay(48000,128);
    {juce::AudioBuffer<float> audio(2,128);juce::MidiBuffer midi;std::array<uint8_t,256> sysex{};
        midi.addEvent(juce::MidiMessage::createSysExMessage(sysex.data(),static_cast<int>(sysex.size())),0);
        allocations=0;watching=true;p.processBlock(audio,midi);watching=false;
        require(allocations==0,"unsupported SysEx ignored without allocation");}
    for(double rate:{44100.0,48000.0,96000.0}){
        p.prepareToPlay(rate,64);require(p.getLatencySamples()==0,"reported latency");
        for(int category=0;category<7;++category){set(p,"department",static_cast<float>(category));
            for(int block:{0,1,7,64,511,1024}){juce::AudioBuffer<float> audio(2,block);juce::MidiBuffer midi;if(block)midi.addEvent(juce::MidiMessage::noteOn(1,60,.8f),0);p.processBlock(audio,midi);
                for(int i=0;i<block;++i)require(std::isfinite(audio.getSample(0,i)),"finite processor output");}}
    }
    // Actual JUCE component bindings, separate from host mouse/keyboard tests.
    {
        juce::MemoryBlock before,after;p.getStateInformation(before);
        std::unique_ptr<juce::AudioProcessorEditor> editor(p.createEditor());p.getStateInformation(after);
        require(before==after,"opening editor preserves parameter state");
        int mapped=0;
        for(int i=0;i<editor->getNumChildComponents();++i){auto* child=editor->getChildComponent(i);
            if(auto* slider=dynamic_cast<juce::Slider*>(child)){
                const auto id=slider->getName().toLowerCase();auto* raw=p.parameters.getRawParameterValue(id);
                require(raw!=nullptr&&std::abs(slider->getValue()-raw->load())<1e-6,"recalled parameter appears in editor");
                slider->setValue(.2*(mapped+1),juce::sendNotificationSync);
                require(std::abs(raw->load()-slider->getValue())<1e-6,"native knob changes actual processor parameter");++mapped;
            }
            if(auto* choice=dynamic_cast<juce::ComboBox*>(child)){
                choice->setSelectedId(2,juce::sendNotificationSync);
                require(p.parameters.getRawParameterValue("department")->load()==1,"department selector binding");
            }
        }
        require(mapped==3,"all three native macro bindings exercised");
    }
    // Render actual compiled editor at all supported size bounds.
    if(argc>1){const juce::File output=juce::File::getCurrentWorkingDirectory().getChildFile(argv[1]);output.createDirectory();
        std::unique_ptr<juce::AudioProcessorEditor> editor(p.createEditor());
        for(auto size:{juce::Point<int>(700,460),juce::Point<int>(900,560),juce::Point<int>(1200,780)}){
            editor->setSize(size.x,size.y);auto snapshot=editor->createComponentSnapshot(editor->getLocalBounds());
            auto file=output.getChildFile("editor-"+juce::String(size.x)+".png");auto stream=file.createOutputStream();require(stream!=nullptr,"editor file");stream->setPosition(0);stream->truncate();juce::PNGImageFormat png;require(png.writeImageToStream(snapshot,*stream),"native editor render");
        }}
    std::cout<<"PASS processor layout, sample-accurate MIDI partitions/onset, state, rates and native editor bindings\n";
    if(argc>1)std::cout<<"PASS compiled native editor rendering at 700, 900 and 1200 pixels\n";
}

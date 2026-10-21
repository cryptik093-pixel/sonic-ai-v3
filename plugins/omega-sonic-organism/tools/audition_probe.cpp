// Render demonstrations through the shipped DLL and its VST3 event/automation API.
#define NOMINMAX
#include <windows.h>
#include "Plugin.h"
#include "omega/FactoryBank.h"
#include "omega/Preset.h"
#include "public.sdk/source/common/memorystream.h"
#include "public.sdk/source/vst/hosting/hostclasses.h"
#include "public.sdk/source/vst/hosting/eventlist.h"
#include "public.sdk/source/vst/hosting/parameterchanges.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <cstdlib>
#define CHECK(c) do {if(!(c)){std::cerr<<"FAIL "<<__LINE__<<" "<<#c<<'\n';std::exit(1);}}while(false)
using namespace Steinberg;using namespace Steinberg::Vst;
static void integer(std::ostream& o,uint32_t v,int bytes){for(int i=0;i<bytes;++i)o.put(char(v>>(8*i)));}
struct Demo {std::string name;omega::ParameterValues patch;int sweep=-1;double from=0,to=1;int role=0;};
int wmain(int argc,wchar_t** argv){
    CHECK(argc==3||argc==4);const bool cpuRegression=argc==4&&std::wstring(argv[3])==L"--cpu-regression";CHECK(argc==3||cpuRegression);const auto module=LoadLibraryW(argv[1]);CHECK(module);
    auto init=reinterpret_cast<bool(*)()>(GetProcAddress(module,"InitDll"));CHECK(init&&init());
    auto getFactory=reinterpret_cast<IPluginFactory*(*)()>(GetProcAddress(module,"GetPluginFactory"));CHECK(getFactory);auto* factory=getFactory();CHECK(factory);
    HostApplication host;std::filesystem::path folder(argv[2]);std::filesystem::create_directories(folder);
    std::vector<Demo> demos;const char* anchors[]={"bass","bells","lead","synth","percussion"};
    for(int i=0;i<5;++i){auto p=omega::defaults();p[0]=i*.25;demos.push_back({std::string("anchor-")+anchors[i],p,-1,0,1,i==4?2:0});}
    for(int i=0;i<4;++i){auto p=omega::defaults();p[0]=i*.25;demos.push_back({std::string("transition-")+anchors[i]+"-to-"+anchors[i+1],p,0,i*.25,(i+1)*.25});}
    for(int i=0;i<5;++i){auto p=omega::defaults();p[0]=.5;p[i]=0;demos.push_back({"macro-"+std::string(omega::parameterDefinitions[i].key),p,i,0,1});}
    for(int role=0;role<4;++role){auto p=omega::defaults();p[0]=role==0?0:role==1?.5:role==2?1:.75;demos.push_back({std::string("performance-")+(role==0?"bass":role==1?"melody":role==2?"percussion":"polyphonic"),p,-1,0,1,role});}
    int number=0;for(auto* document:omega::factoryDocuments){omega::Preset preset;std::string error;CHECK(omega::parsePreset(document,preset,error));demos.push_back({"factory-"+std::to_string(++number),preset.params,-1,0,1,preset.params[0]>.9?2:0});}
    if(cpuRegression){demos.clear();for(int quality=0;quality<2;++quality)for(int anchor=0;anchor<5;++anchor){auto p=omega::defaults();p[0]=anchor*.25;p[10]=quality;demos.push_back({std::string("cpu-held-")+anchors[anchor]+(quality?"-hq":"-eco"),p,-1,0,1,4});}}
    std::ofstream report(folder/"audition-results.json");report<<"{\"format\":\"PCM signed 24-bit stereo 48000 Hz, undithered; no normalization\",\"source\":\"actual VST3 DLL\",\"listening\":\"PENDING\",\"renders\":[";
    bool first=true;
    for(const auto& demo:demos){
        IComponent* component=nullptr;CHECK(factory->createInstance(oso::processorID.toTUID(),IComponent::iid,reinterpret_cast<void**>(&component))==kResultOk);CHECK(component->initialize(&host)==kResultOk);FUnknownPtr<IAudioProcessor> processor(component);CHECK(processor);
        auto bytes=omega::encodeState(demo.patch);MemoryStream state(bytes.data(),bytes.size());CHECK(component->setState(&state)==kResultOk);
        ProcessSetup setup{};setup.sampleRate=48000;setup.maxSamplesPerBlock=256;setup.symbolicSampleSize=kSample32;setup.processMode=kOffline;CHECK(processor->setupProcessing(setup)==kResultOk);CHECK(component->activateBus(kAudio,kOutput,0,true)==kResultOk);CHECK(component->activateBus(kEvent,kInput,0,true)==kResultOk);CHECK(component->setActive(true)==kResultOk);CHECK(processor->setProcessing(true)==kResultOk);
        const int frames=48000*(cpuRegression?24:6);std::vector<float> audio(frames*2);std::array<float,256> l{},r{};float* channels[]={l.data(),r.data()};AudioBusBuffers bus{};bus.numChannels=2;bus.channelBuffers32=channels;EventList events;ParameterChanges changes(5);ProcessData data{};data.symbolicSampleSize=kSample32;data.processMode=kOffline;data.numOutputs=1;data.outputs=&bus;data.inputEvents=&events;data.inputParameterChanges=&changes;
        auto event=[&](int absolute,int block,bool on,int pitch,int id){if(absolute<block||absolute>=block+data.numSamples)return;Event e{};e.sampleOffset=absolute-block;if(on){e.type=Event::kNoteOnEvent;e.noteOn.pitch=int16(pitch);e.noteOn.velocity=float(.55+.1*(id%4));e.noteOn.noteId=id;}else{e.type=Event::kNoteOffEvent;e.noteOff.pitch=int16(pitch);e.noteOff.noteId=id;}CHECK(events.addEvent(e)==kResultOk);};
        for(int frame=0;frame<frames;frame+=256){data.numSamples=std::min(256,frames-frame);events.clear();changes.clearQueue();
            if(demo.role==4){event(0,frame,true,48,1);event(48000*22,frame,false,48,1);event(48000*20,frame,true,72,2);event(48000*23,frame,false,72,2);if(frame>=48000*18){int32 index=0;auto* q=changes.addParameterData(100,index);CHECK(q);CHECK(q->addPoint(0,.75,index)==kResultOk);}}
            else if(demo.sweep>=0){int32 index=0;auto* q=changes.addParameterData(100+demo.sweep,index);CHECK(q);const double t=std::clamp(frame/(48000.*4.5),0.,1.);CHECK(q->addPoint(0,demo.from+(demo.to-demo.from)*t,index)==kResultOk);event(0,frame,true,48,1);event(48000*5,frame,false,48,1);}
            else if(demo.role==3){for(int note=0;note<4;++note){const int pitch=48+std::array<int,4>{0,4,7,11}[note];event(note*1200,frame,true,pitch,note);event(48000*4,frame,false,pitch,note);}}
            else {const int steps=demo.role==2?16:8;for(int step=0;step<steps;++step){const int at=step*(48000*4/steps);const int pitch=demo.role==2?36+step%4*7:(demo.role==0?36:60)+std::array<int,8>{0,0,7,10,12,7,3,0}[step%8];event(at,frame,true,pitch,step);event(at+(demo.role==2?3600:12000),frame,false,pitch,step);}}
            CHECK(processor->process(data)==kResultOk);for(int n=0;n<data.numSamples;++n){audio[(frame+n)*2]=l[n];audio[(frame+n)*2+1]=r[n];}
        }
        double peak=0,power=0,dc=0,jump=0;int clipped=0;for(size_t n=0;n<audio.size();++n){const double x=audio[n];CHECK(std::isfinite(x)&&std::abs(x)<=1);peak=std::max(peak,std::abs(x));power+=x*x;dc+=x;if(std::abs(x)>=.999)++clipped;if(n>=2)jump=std::max(jump,std::abs(x-audio[n-2]));}CHECK(power>1e-6&&clipped==0);
        if(cpuRegression){std::ofstream raw(folder/(demo.name+".f32"),std::ios::binary);raw.write(reinterpret_cast<const char*>(audio.data()),std::streamsize(audio.size()*sizeof(float)));CHECK(raw);}
        std::ofstream wav(folder/(demo.name+".wav"),std::ios::binary);CHECK(wav);wav.write("RIFF",4);integer(wav,36+uint32_t(audio.size()*3),4);wav.write("WAVEfmt ",8);integer(wav,16,4);integer(wav,1,2);integer(wav,2,2);integer(wav,48000,4);integer(wav,48000*6,4);integer(wav,6,2);integer(wav,24,2);wav.write("data",4);integer(wav,uint32_t(audio.size()*3),4);for(float sample:audio){const int32_t pcm=int32_t(std::llround(std::clamp(double(sample),-1.,1.)*8388607));integer(wav,uint32_t(pcm),3);}CHECK(wav);
        if(!first)report<<',';first=false;report<<"{\"file\":\""<<demo.name<<".wav\",\"peak\":"<<peak<<",\"rms\":"<<std::sqrt(power/audio.size())<<",\"mean\":"<<dc/audio.size()<<",\"maxAdjacentSampleDelta\":"<<jump<<",\"clippedSamples\":"<<clipped<<",\"finiteNonzeroBounded\":true}";
        CHECK(processor->setProcessing(false)==kResultOk);CHECK(component->setActive(false)==kResultOk);processor=nullptr;CHECK(component->terminate()==kResultOk);component->release();std::cout<<demo.name<<" peak="<<peak<<" rms="<<std::sqrt(power/audio.size())<<'\n';
    }
    report<<"]}\n";factory->release();auto exit=reinterpret_cast<bool(*)()>(GetProcAddress(module,"ExitDll"));CHECK(exit&&exit());FreeLibrary(module);std::cout<<"PASS "<<demos.size()<<" actual DLL 24-bit demonstrations; listening pending.\n";
}

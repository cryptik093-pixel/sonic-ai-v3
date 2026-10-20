// Headless integration host: load the actual Windows DLL, do not link its processor.
#define NOMINMAX
#include <windows.h>
#include "Plugin.h"
#include "omega/Preset.h"
#include "omega/FactoryBank.h"
#include "public.sdk/source/vst/hosting/hostclasses.h"
#include "public.sdk/source/vst/hosting/eventlist.h"
#include "public.sdk/source/common/memorystream.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <cstdlib>
#define CHECK(c) do{if(!(c)){std::cerr<<"FAIL "<<__LINE__<<": "<<#c<<'\n';std::exit(1);}}while(false)
using namespace Steinberg;
using namespace Steinberg::Vst;
static void u32(std::ostream& o,uint32_t v){char b[4];for(int i=0;i<4;++i)b[i]=char(v>>(i*8));o.write(b,4);}
static void u16(std::ostream& o,uint16_t v){char b[2]={char(v),char(v>>8)};o.write(b,2);}
static void wav(const std::filesystem::path& path,const std::vector<float>& samples){std::ofstream o(path,std::ios::binary);CHECK(o);o.write("RIFF",4);u32(o,36+uint32_t(samples.size()*4));o.write("WAVEfmt ",8);u32(o,16);u16(o,3);u16(o,2);u32(o,48000);u32(o,48000*8);u16(o,8);u16(o,32);o.write("data",4);u32(o,uint32_t(samples.size()*4));o.write(reinterpret_cast<const char*>(samples.data()),samples.size()*4);CHECK(o);}
int wmain(int argc,wchar_t** argv){
    CHECK(argc==3||argc==4||argc==5);const bool restoreMode=argc==5&&std::wstring(argv[3])==L"--restore";CHECK(argc!=5||restoreMode);const bool bankMode=argc==4&&std::wstring(argv[3])==L"--bank";const bool hq=argc==4&&argv[3][0]==L'1';HMODULE module=LoadLibraryW(argv[1]);CHECK(module);
    auto init=reinterpret_cast<bool(*)()>(GetProcAddress(module,"InitDll"));CHECK(init&&init());
    auto getFactory=reinterpret_cast<IPluginFactory*(*)()>(GetProcAddress(module,"GetPluginFactory"));CHECK(getFactory);auto* factory=getFactory();CHECK(factory);
    HostApplication host;std::filesystem::path output(argv[2]);std::filesystem::create_directories(output);
    struct RenderCase{std::string name;omega::ParameterValues params;int pitch;std::vector<uint8_t> originalState{};};std::vector<RenderCase> cases;
    if(restoreMode){for(const auto& entry:std::filesystem::directory_iterator(argv[4]))if(entry.path().extension()==L".bin"){
        std::ifstream in(entry.path(),std::ios::binary);CHECK(in);std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(in)),{});omega::ParameterValues params;CHECK(omega::decodeState(bytes.data(),bytes.size(),params));const auto stem=entry.path().stem().string();const auto marker=stem.rfind("-note-");CHECK(marker!=std::string::npos);const int note=std::stoi(stem.substr(marker+6));cases.push_back({stem+".wav",params,note,std::move(bytes)});}CHECK(cases.size()==27);}
    else if(bankMode){int patchIndex=0;for(auto* doc:omega::factoryDocuments){omega::Preset p;std::string error;CHECK(omega::parsePreset(doc,p,error));for(int pitch:{36,48,60,72})cases.push_back({"patch-"+std::to_string(patchIndex)+"-note-"+std::to_string(pitch)+".wav",p.params,pitch});++patchIndex;}}
    else for(int anchor=0;anchor<9;++anchor)for(int pitch:{36,48,60}){auto p=omega::defaults();p[0]=anchor/8.;p[10]=hq?1.:0.;cases.push_back({"morph-"+std::to_string(anchor)+"-note-"+std::to_string(pitch)+".wav",p,pitch});}
    for(const auto& render:cases){const int pitch=render.pitch;
        IComponent* component=nullptr;CHECK(factory->createInstance(oso::processorID.toTUID(),IComponent::iid,reinterpret_cast<void**>(&component))==kResultOk);
        CHECK(component->initialize(&host)==kResultOk);
        FUnknownPtr<IAudioProcessor> processor(component);CHECK(processor);
        auto encoded=omega::encodeState(render.params);std::vector<uint8_t> bytes=render.originalState.empty()?std::vector<uint8_t>(encoded.begin(),encoded.end()):render.originalState;MemoryStream state(bytes.data(),bytes.size());CHECK(component->setState(&state)==kResultOk);
        ProcessSetup setup{};setup.sampleRate=48000;setup.maxSamplesPerBlock=256;setup.symbolicSampleSize=kSample32;setup.processMode=kOffline;CHECK(processor->setupProcessing(setup)==kResultOk);
        CHECK(component->activateBus(kAudio,kOutput,0,true)==kResultOk);CHECK(component->activateBus(kEvent,kInput,0,true)==kResultOk);CHECK(component->setActive(true)==kResultOk);
        std::vector<float> result(96000*2),reference;double power=0,peak=0;
        for(int repeat=0;repeat<2;++repeat){
            CHECK(processor->setProcessing(true)==kResultOk);
            std::array<float,256> l{},r{};float* channels[]={l.data(),r.data()};AudioBusBuffers bus{};bus.numChannels=2;bus.channelBuffers32=channels;EventList events;
            ProcessData data{};data.symbolicSampleSize=kSample32;data.processMode=kOffline;data.numOutputs=1;data.outputs=&bus;data.inputEvents=&events;
            for(int frame=0;frame<96000;frame+=256){data.numSamples=std::min(256,96000-frame);events.clear();
                if(frame==0){Event e{};e.type=Event::kNoteOnEvent;e.noteOn.pitch=int16(pitch);e.noteOn.velocity=.85f;e.noteOn.noteId=7;CHECK(events.addEvent(e)==kResultOk);}
                if(frame<=36000&&frame+data.numSamples>36000){Event e{};e.type=Event::kNoteOffEvent;e.sampleOffset=36000-frame;e.noteOff.pitch=int16(pitch);e.noteOff.noteId=7;CHECK(events.addEvent(e)==kResultOk);}
                CHECK(processor->process(data)==kResultOk);
                for(int n=0;n<data.numSamples;++n){CHECK(std::isfinite(l[n])&&std::isfinite(r[n]));CHECK(std::abs(l[n])<=1&&std::abs(r[n])<=1);result[(frame+n)*2]=l[n];result[(frame+n)*2+1]=r[n];}
            }
            CHECK(processor->setProcessing(false)==kResultOk);
            if(repeat==0){
                reference=result;
                MemoryStream recalled;CHECK(component->getState(&recalled)==kResultOk);
                CHECK(component->setActive(false)==kResultOk);processor=nullptr;
                CHECK(component->terminate()==kResultOk);component->release();component=nullptr;
                CHECK(factory->createInstance(oso::processorID.toTUID(),IComponent::iid,reinterpret_cast<void**>(&component))==kResultOk);
                CHECK(component->initialize(&host)==kResultOk);CHECK(recalled.seek(0,IBStream::kIBSeekSet,nullptr)==kResultOk);CHECK(component->setState(&recalled)==kResultOk);
                processor=FUnknownPtr<IAudioProcessor>(component);CHECK(processor);CHECK(processor->setupProcessing(setup)==kResultOk);
                CHECK(component->activateBus(kAudio,kOutput,0,true)==kResultOk);CHECK(component->activateBus(kEvent,kInput,0,true)==kResultOk);CHECK(component->setActive(true)==kResultOk);
            }else CHECK(result==reference);
        }
        MemoryStream saved;CHECK(component->getState(&saved)==kResultOk);CHECK(saved.getSize()==omega::stateSize);CHECK(std::memcmp(saved.getData(),encoded.data(),encoded.size())==0);
        auto statePath=output/render.name;statePath.replace_extension(".bin");std::ofstream stateFile(statePath,std::ios::binary);CHECK(stateFile);stateFile.write(static_cast<const char*>(saved.getData()),saved.getSize());CHECK(stateFile);
        for(float sample:result){power+=sample*sample;peak=std::max(peak,double(std::abs(sample)));}CHECK(power>1e-4);
        wav(output/render.name,result);
        std::cout<<render.name<<" rms="<<std::sqrt(power/result.size())<<" peak="<<peak<<" deterministic=bit-identical\n";
        CHECK(component->setActive(false)==kResultOk);processor=nullptr;CHECK(component->terminate()==kResultOk);component->release();
    }
    factory->release();auto exitModule=reinterpret_cast<bool(*)()>(GetProcAddress(module,"ExitDll"));CHECK(exitModule&&exitModule());FreeLibrary(module);
    std::cout<<"PASS actual VST3 binary: "<<cases.size()<<" nonzero finite renders, bit-identical output after instance destruction/recreation and native state recall. Not an FL Studio test or listening review.\n";
}

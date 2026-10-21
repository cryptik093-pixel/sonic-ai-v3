#include "Plugin.h"
#include "public.sdk/source/common/memorystream.h"
#include "public.sdk/source/vst/hosting/eventlist.h"
#include "public.sdk/source/vst/hosting/parameterchanges.h"
#include "pluginterfaces/vst/ivstmidicontrollers.h"
#include <cstdlib>
#include <iostream>
#include <new>
#include <vector>
#include <fstream>
static thread_local bool measuring=false;
static size_t allocations=0;
void* operator new(std::size_t n){if(measuring)++allocations;if(auto* p=std::malloc(n?n:1))return p;throw std::bad_alloc();}
void* operator new[](std::size_t n){return ::operator new(n);}
void operator delete(void* p) noexcept{std::free(p);}
void operator delete[](void* p) noexcept{std::free(p);}
void operator delete(void* p,std::size_t) noexcept{std::free(p);}
void operator delete[](void* p,std::size_t) noexcept{std::free(p);}
#define CHECK(c) do{if(!(c)){std::cerr<<"FAIL "<<__LINE__<<": "<<#c<<'\n';std::exit(1);}}while(false)
using namespace Steinberg;
using namespace Steinberg::Vst;
void setup(oso::Processor& p,double rate){CHECK(p.initialize(nullptr)==kResultOk);ProcessSetup s{};s.sampleRate=rate;s.maxSamplesPerBlock=1024;s.symbolicSampleSize=kSample32;s.processMode=kRealtime;CHECK(p.setupProcessing(s)==kResultOk);CHECK(p.setActive(true)==kResultOk);CHECK(p.setProcessing(true)==kResultOk);}
void finish(oso::Processor& p){CHECK(p.setProcessing(false)==kResultOk);CHECK(p.setActive(false)==kResultOk);CHECK(p.terminate()==kResultOk);}
int main(){
    for(double rate:{44100.,48000.,96000.}){
        oso::Processor p;setup(p,rate);
        CHECK(p.getBusCount(kAudio,kInput)==0);CHECK(p.getBusCount(kAudio,kOutput)==1);CHECK(p.getBusCount(kEvent,kInput)==1);CHECK(p.canProcessSampleSize(kSample64)==kResultFalse);
        for(int frames:{1,7,64,128,257,1024}){
            CHECK(p.setProcessing(false)==kResultOk);CHECK(p.setProcessing(true)==kResultOk);
            std::vector<float> l(frames),r(frames),expectedL(frames),expectedR(frames);float* channels[]={l.data(),r.data()};AudioBusBuffers bus{};bus.numChannels=2;bus.channelBuffers32=channels;
            ProcessData data{};data.numSamples=frames;data.symbolicSampleSize=kSample32;data.numOutputs=1;data.outputs=&bus;
            EventList events;Event on{};on.type=Event::kNoteOnEvent;on.sampleOffset=frames/3;on.noteOn.pitch=60;on.noteOn.velocity=.8f;on.noteOn.noteId=1;CHECK(events.addEvent(on)==kResultOk);data.inputEvents=&events;
            ParameterChanges changes(15);int32 index=0;auto* queue=changes.addParameterData(100,index);CHECK(queue);CHECK(queue->addPoint(frames/3,.625,index)==kResultOk);data.inputParameterChanges=&changes;
            omega::OrganismCore reference;reference.setMorph(0);reference.prepare(rate);
            // Native state reset makes each timed test independent.
            auto initial=omega::defaults();auto bytes=omega::encodeState(initial);MemoryStream initialState(bytes.data(),bytes.size());CHECK(p.setState(&initialState)==kResultOk);CHECK(p.setProcessing(true)==kResultOk);
            measuring=true;CHECK(p.process(data)==kResultOk);measuring=false;
            for(int n=0;n<frames;++n){if(n==frames/3){reference.setMorph(.625f);reference.noteOn(60,.8f);}reference.render(expectedL.data()+n,expectedR.data()+n,1);CHECK(l[n]==expectedL[n]);CHECK(r[n]==expectedR[n]);}
            events.clear();data.inputEvents=nullptr;data.inputParameterChanges=nullptr;
            for(int block=0;block<20;++block){measuring=true;CHECK(p.process(data)==kResultOk);measuring=false;for(float x:l)CHECK(std::isfinite(x)&&std::abs(x)<=1);}
            MemoryStream stream;CHECK(p.getState(&stream)==kResultOk);CHECK(stream.getSize()==omega::stateSize);CHECK(stream.seek(0,IBStream::kIBSeekSet,nullptr)==kResultOk);
            oso::Controller controller;CHECK(controller.initialize(nullptr)==kResultOk);CHECK(controller.setComponentState(&stream)==kResultOk);CHECK(controller.getParameterCount()==23);CHECK(controller.getParamNormalized(100)==.625);CHECK(p.getLatencySamples()==omega::OrganismCore::latencySamples);CHECK(controller.terminate()==kResultOk);
        }
        // Exercise the actual hidden MIDI mapping at nonzero sample offsets.
        {
            auto patch=omega::defaults();patch[0]=.5;patch[2]=0;
            auto bytes=omega::encodeState(patch);MemoryStream state(bytes.data(),bytes.size());CHECK(p.setState(&state)==kResultOk);CHECK(p.setProcessing(true)==kResultOk);
            std::array<float,256> l{},r{},expectedL{},expectedR{};float* channels[]={l.data(),r.data()};AudioBusBuffers bus{};bus.numChannels=2;bus.channelBuffers32=channels;
            EventList events;Event on{};on.type=Event::kNoteOnEvent;on.noteOn.pitch=60;on.noteOn.velocity=.8f;on.noteOn.noteId=44;events.addEvent(on);
            Event off{};off.type=Event::kNoteOffEvent;off.sampleOffset=96;off.noteOff.pitch=60;off.noteOff.noteId=44;events.addEvent(off);
            ParameterChanges midi(4);int32 index=0;
            auto* bend=midi.addParameterData(1000,index);bend->addPoint(37,1,index);
            auto* sustain=midi.addParameterData(1001,index);sustain->addPoint(0,1,index);sustain->addPoint(128,0,index);
            midi.addParameterData(1002,index)->addPoint(192,0,index);midi.addParameterData(1003,index)->addPoint(240,0,index);
            ProcessData data{};data.numSamples=256;data.symbolicSampleSize=kSample32;data.numOutputs=1;data.outputs=&bus;data.inputEvents=&events;data.inputParameterChanges=&midi;
            omega::OrganismCore reference;reference.setMorph(.5f);reference.setMotion(0);reference.prepare(rate);
            measuring=true;CHECK(p.process(data)==kResultOk);measuring=false;
            for(int n=0;n<256;++n){if(n==0){reference.setSustain(true);reference.noteOn(60,.8f,44);}if(n==37)reference.setPitchBend(1);if(n==96)reference.noteOff(60,44);if(n==128)reference.setSustain(false);if(n==192)reference.allNotesOff();if(n==240)reference.resetVoices();reference.render(expectedL.data()+n,expectedR.data()+n,1);CHECK(l[size_t(n)]==expectedL[size_t(n)]);CHECK(r[size_t(n)]==expectedR[size_t(n)]);}
            oso::Controller controller;CHECK(controller.initialize(nullptr)==kResultOk);
            ParamID mapped=0;CHECK(controller.getMidiControllerAssignment(0,0,kPitchBend,mapped)==kResultOk&&mapped==1000);CHECK(controller.getMidiControllerAssignment(0,0,kCtrlSustainOnOff,mapped)==kResultOk&&mapped==1001);CHECK(controller.getMidiControllerAssignment(0,1,kPitchBend,mapped)==kResultFalse);
            void* mapping=nullptr;CHECK(controller.queryInterface(IMidiMapping::iid,&mapping)==kResultOk&&mapping);static_cast<IMidiMapping*>(mapping)->release();
            for(int32 i=0;i<15;++i){ParameterInfo info{};CHECK(controller.getParameterInfo(i,info)==kResultOk);const auto& def=omega::parameterDefinitions[size_t(i)];CHECK(info.id==def.id&&info.stepCount==def.steps);CHECK(bool(info.flags&ParameterInfo::kCanAutomate)==def.automatable);CHECK(!(info.flags&ParameterInfo::kIsReadOnly));}
            CHECK(controller.terminate()==kResultOk);
        }
        // Exercise real processor meter output with host-owned queues primed
        // outside the callback. UI probe values alone do not prove telemetry.
        {
            CHECK(p.setProcessing(false)==kResultOk);auto patch=omega::defaults();auto bytes=omega::encodeState(patch);
            MemoryStream state(bytes.data(),bytes.size());CHECK(p.setState(&state)==kResultOk);CHECK(p.setProcessing(true)==kResultOk);
            ParameterChanges meters(4);int32 index=0;
            for(ParamID id=1010;id<=1013;++id){auto* q=meters.addParameterData(id,index);CHECK(q);CHECK(q->addPoint(0,0,index)==kResultOk);}
            std::array<float,256> l{},r{};float* channels[]={l.data(),r.data()};AudioBusBuffers bus{};bus.numChannels=2;bus.channelBuffers32=channels;EventList events;
            Event on{};on.type=Event::kNoteOnEvent;on.noteOn.pitch=72;on.noteOn.velocity=.7f;on.noteOn.noteId=55;CHECK(events.addEvent(on)==kResultOk);
            ProcessData data{};data.numSamples=256;data.symbolicSampleSize=kSample32;data.numOutputs=1;data.outputs=&bus;data.inputEvents=&events;data.outputParameterChanges=&meters;
            for(int block=0;block<4;++block){meters.clearQueue();measuring=true;CHECK(p.process(data)==kResultOk);measuring=false;events.clear();CHECK(meters.getParameterCount()==4);
                for(int32 i=0;i<4;++i){auto* q=meters.getParameterData(i);CHECK(q&&q->getParameterId()==ParamID(1010+i)&&q->getPointCount()==1);int32 offset=-1;double value=-1;CHECK(q->getPoint(0,offset,value)==kResultOk);CHECK(offset==255&&std::isfinite(value)&&value>=0&&value<=1);
                    if(i==0)CHECK(value>0);if(i==1)CHECK(value==1./32);if(i==2)CHECK(value==73./128);if(i==3)CHECK(std::abs(value-.7)<1e-6);}
            }
        }
        finish(p);
    }
    CHECK(allocations==0);
    std::cout<<"Adapter passed: 3 rates x 6 block sizes, timed notes/automation collision compared sample-for-sample, stereo, state/controller recall, finite audio; 0 C++ new allocations during measured process calls.\n";
}

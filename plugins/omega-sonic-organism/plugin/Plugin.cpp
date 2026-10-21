#include "Plugin.h"
#include "pluginterfaces/base/ibstream.h"
#include "pluginterfaces/vst/ivstevents.h"
#include "pluginterfaces/vst/ivstparameterchanges.h"
#include "pluginterfaces/vst/ivstmidicontrollers.h"
#include "pluginterfaces/vst/ivstprocesscontext.h"
#include "pluginterfaces/base/ustring.h"
#include "public.sdk/source/main/pluginfactory.h"
#include <algorithm>
#include <cstring>
#if OSO_WITH_EDITOR
#include "Editor.h"
#endif

namespace oso {
using namespace Steinberg;
using namespace Steinberg::Vst;
namespace {
bool readState(IBStream* stream,omega::ParameterValues& result) {
    if(!stream)return false;
    omega::StateBytes b{};int32 got=0;
    if(stream->read(b.data(),16,&got)!=kResultOk||got!=16)return false;
    auto count=omega::get32(b.data()+8);if(count<6||count>15)return false;
    int32 remaining=static_cast<int32>(4+count*8);
    if(stream->read(b.data()+16,remaining,&got)!=kResultOk||got!=remaining)return false;
    return omega::decodeState(b.data(),16+remaining,result);
}
class ContractParameter final : public Parameter {
public:
    explicit ContractParameter(const omega::ParameterDefinition& p):Parameter(p.title,p.id,p.unit,p.initial,p.steps,(p.automatable?ParameterInfo::kCanAutomate:0)|(p.steps?ParameterInfo::kIsList:0)),def(p) {}
    ParamValue toPlain(ParamValue n) const override { return omega::physical(def,n); }
    ParamValue toNormalized(ParamValue p) const override { return def.logarithmic?std::log(p/def.minimum)/std::log(def.maximum/def.minimum):(p-def.minimum)/(def.maximum-def.minimum); }
    void toString(ParamValue n,String128 out) const override {
        if(def.steps){UString(out,128).assign(def.choices[std::clamp(int(std::round(n*def.steps)),0,def.steps)]);return;}
        UString(out,128).printFloat(toPlain(n),3);
    }
    bool fromString(const TChar* text,ParamValue& n) const override {
        if(def.steps){for(int i=0;i<=def.steps;++i){const auto* a=text;const auto* b=def.choices[i];while(*a&&*a==*b){++a;++b;}if(*a==*b){n=double(i)/def.steps;return true;}}return false;}
        double p=0;if(!UString(const_cast<TChar*>(text),128).scanFloat(p))return false;n=toNormalized(p);return std::isfinite(n)&&n>=0&&n<=1;
    }
private:
    omega::ParameterDefinition def;
};
}
Processor::Processor(){setControllerClass(controllerID);processContextRequirements.needTempo();}
tresult PLUGIN_API Processor::initialize(FUnknown* context) {
    auto r=AudioEffect::initialize(context);if(r!=kResultOk)return r;
    addEventInput(STR16("MIDI"),1);addAudioOutput(STR16("Stereo"),SpeakerArr::kStereo);return kResultOk;
}
tresult PLUGIN_API Processor::setupProcessing(ProcessSetup& setup) {
    if(setup.symbolicSampleSize!=kSample32||!std::isfinite(setup.sampleRate)||setup.sampleRate<8000||setup.sampleRate>384000||setup.maxSamplesPerBlock<1)return kResultFalse;
    auto r=AudioEffect::setupProcessing(setup);if(r!=kResultOk)return r;
    try {core.prepare(setup.sampleRate);}catch(...){return kOutOfMemory;}
    for(size_t i=0;i<values.size();++i)apply(i,values[i]);return kResultOk;
}
tresult PLUGIN_API Processor::setBusArrangements(SpeakerArrangement*,int32 ni,SpeakerArrangement* out,int32 no){return ni==0&&no==1&&out&&out[0]==SpeakerArr::kStereo?kResultOk:kResultFalse;}
tresult PLUGIN_API Processor::canProcessSampleSize(int32 size){return size==kSample32?kResultTrue:kResultFalse;}
tresult PLUGIN_API Processor::setProcessing(TBool){core.resetVoices();return kResultOk;}
void Processor::apply(size_t i,double n) noexcept {
    if(!std::isfinite(n))return;
    if(i>=values.size()){
        n=std::clamp(n,0.0,1.0);
        switch(i){case 15:core.setPitchBend(float(n*2-1));break;case 16:core.setSustain(n>=.5);break;case 17:core.allNotesOff();break;case 18:core.resetVoices();break;default:break;}
        return;
    }
    n=std::clamp(n,0.0,1.0);const int steps=omega::parameterDefinitions[i].steps;
    if(steps)n=std::round(n*steps)/steps;values[i]=n;
    core.setParameter(omega::parameterDefinitions[i].id,n);
}
tresult PLUGIN_API Processor::process(ProcessData& data) {
    if(data.symbolicSampleSize!=kSample32||data.numSamples<0)return kInvalidArgument;
    const auto initialFaults=core.nonFiniteFaults();
    struct Cursor { IParamValueQueue* queue=nullptr;int32 index=0,count=0,offset=0;double value=0;bool valid=false; };
    std::array<Cursor,19> cursors{};
    if(data.processContext&&(data.processContext->state&ProcessContext::kTempoValid))core.setTempo(data.processContext->tempo);else core.setTempo(120);
    if(data.inputParameterChanges)for(int32 q=0;q<data.inputParameterChanges->getParameterCount();++q){
        auto* queue=data.inputParameterChanges->getParameterData(q);if(!queue)continue;const auto id=queue->getParameterId();int i=omega::parameterIndex(id);
        if(id>=1000&&id<=1003)i=int(id-1000)+15;if(i<0)continue;
        auto& c=cursors[size_t(i)];c.queue=queue;c.count=queue->getPointCount();c.valid=c.count>0&&queue->getPoint(0,c.offset,c.value)==kResultTrue;
    }
    float* left=nullptr;float* right=nullptr;
    if(data.numOutputs>0&&data.outputs&&data.outputs[0].numChannels==2&&data.outputs[0].channelBuffers32){left=data.outputs[0].channelBuffers32[0];right=data.outputs[0].channelBuffers32[1];}
    if(data.numSamples>0&&(!left||!right))return kResultFalse;
    int32 eventIndex=0;const int32 eventCount=data.inputEvents?data.inputEvents->getEventCount():0;
    Event event{};bool hasEvent=eventIndex<eventCount&&data.inputEvents->getEvent(eventIndex,event)==kResultTrue;
    bool silent=true;
    // Split at event/automation boundaries rather than re-entering the core
    // and scanning nineteen queues for every audio sample. Collision order
    // and zero-frame flush semantics remain identical to the original path.
    for(int32 sample=0;sample<std::max<int32>(data.numSamples,1);){
        for(size_t i=0;i<cursors.size();++i){auto& c=cursors[i];while(c.valid&&c.offset<=sample){apply(i,c.value);++c.index;c.valid=c.index<c.count&&c.queue->getPoint(c.index,c.offset,c.value)==kResultTrue;}}
        while(hasEvent&&event.sampleOffset<=sample){
            if(event.busIndex==0){if(event.type==Event::kNoteOnEvent){core.noteOn(event.noteOn.pitch,event.noteOn.velocity,event.noteOn.noteId);lastNote=event.noteOn.pitch;lastVelocity=std::clamp(double(event.noteOn.velocity),0.,1.);}else if(event.type==Event::kNoteOffEvent)core.noteOff(event.noteOff.pitch,event.noteOff.noteId);}
            ++eventIndex;hasEvent=eventIndex<eventCount&&data.inputEvents->getEvent(eventIndex,event)==kResultTrue;
        }
        if(!data.numSamples)break;
        int32 next=data.numSamples;
        for(const auto& c:cursors)if(c.valid&&c.offset>sample)next=std::min(next,c.offset);
        if(hasEvent&&event.sampleOffset>sample)next=std::min(next,event.sampleOffset);
        core.render(left+sample,right+sample,next-sample);sample=next;
    }
    if(left&&right)for(int32 n=0;n<data.numSamples;++n)silent=silent&&left[n]==0&&right[n]==0;
    if(data.numOutputs>0&&data.outputs)data.outputs[0].silenceFlags=silent?3:0;
    double peak=0;if(left&&right)for(int32 n=0;n<data.numSamples;++n)peak=std::max(peak,std::max(std::abs(double(left[n])),std::abs(double(right[n]))));
    meterPeak=std::max(peak,meterPeak*std::exp(-double(data.numSamples)/(std::max(1.,processSetup.sampleRate)*.25)));
    if(data.outputParameterChanges){const double meters[]={meterPeak,double(core.activeVoices())/32,double(lastNote+1)/128,lastVelocity};for(int i=0;i<4;++i){int32 queueIndex=0,pointIndex=0;if(auto* q=data.outputParameterChanges->addParameterData(1010+i,queueIndex))q->addPoint(std::max<int32>(0,data.numSamples-1),std::clamp(meters[i],0.,1.),pointIndex);}}
    return core.nonFiniteFaults()==initialFaults?kResultOk:kResultFalse;
}
tresult PLUGIN_API Processor::getState(IBStream* stream){if(!stream)return kInvalidArgument;auto b=omega::encodeState(values);int32 wrote=0;return stream->write(b.data(),int32(b.size()),&wrote)==kResultOk&&wrote==int32(b.size())?kResultOk:kResultFalse;}
tresult PLUGIN_API Processor::setState(IBStream* stream){auto p=values;if(!readState(stream,p))return kResultFalse;for(size_t i=0;i<p.size();++i)apply(i,p[i]);return kResultOk;}
tresult PLUGIN_API Controller::initialize(FUnknown* context){
    auto r=EditControllerEx1::initialize(context);if(r!=kResultOk)return r;
    for(const auto& p:omega::parameterDefinitions)parameters.addParameter(new ContractParameter(p));
    const int32 flags=ParameterInfo::kIsHidden|ParameterInfo::kCanAutomate;
    parameters.addParameter(STR16("MIDI Pitch Bend"),nullptr,0,.5,flags,1000);
    parameters.addParameter(STR16("MIDI Sustain"),nullptr,0,0,flags,1001);
    parameters.addParameter(STR16("MIDI All Notes Off"),nullptr,0,0,flags,1002);
    parameters.addParameter(STR16("MIDI All Sounds Off"),nullptr,0,0,flags,1003);
    const int32 meterFlags=ParameterInfo::kIsHidden|ParameterInfo::kIsReadOnly;
    parameters.addParameter(STR16("Output Peak"),nullptr,0,0,meterFlags,1010);
    parameters.addParameter(STR16("Active Voices"),nullptr,0,0,meterFlags,1011);
    parameters.addParameter(STR16("Last MIDI Note"),nullptr,0,0,meterFlags,1012);
    parameters.addParameter(STR16("Last Velocity"),nullptr,0,0,meterFlags,1013);
    return kResultOk;
}
IPlugView* PLUGIN_API Controller::createView(FIDString name){
#if OSO_WITH_EDITOR
    if(name&&std::strcmp(name,ViewType::kEditor)==0)return createOrganismEditor(this);
#else
    (void)name;
#endif
    return nullptr;
}
tresult PLUGIN_API Controller::setComponentState(IBStream* stream){auto p=omega::defaults();if(!readState(stream,p))return kResultFalse;for(size_t i=0;i<p.size();++i)setParamNormalized(omega::parameterDefinitions[i].id,p[i]);return kResultOk;}
tresult PLUGIN_API Controller::queryInterface(const TUID iid,void** obj){QUERY_INTERFACE(iid,obj,IMidiMapping::iid,IMidiMapping)return EditControllerEx1::queryInterface(iid,obj);}
tresult PLUGIN_API Controller::getMidiControllerAssignment(int32 bus,int16 channel,CtrlNumber cc,ParamID& id){
    if(bus!=0||channel!=0)return kResultFalse;
    switch(cc){case kPitchBend:id=1000;break;case kCtrlSustainOnOff:id=1001;break;case kCtrlAllNotesOff:id=1002;break;case kCtrlAllSoundsOff:id=1003;break;default:return kResultFalse;}return kResultOk;
}
}
using namespace Steinberg;
using namespace Steinberg::Vst;
BEGIN_FACTORY_DEF("Omega House Studio LLC","https://omega-house.online","")
DEF_CLASS2(INLINE_UID_FROM_FUID(oso::processorID),PClassInfo::kManyInstances,kVstAudioEffectClass,"OMEGA SONIC ORGANISM",Vst::kDistributable,"Instrument|Synth","1.0.0-rc.2",kVstVersionString,oso::Processor::create)
DEF_CLASS2(INLINE_UID_FROM_FUID(oso::controllerID),PClassInfo::kManyInstances,kVstComponentControllerClass,"OMEGA SONIC ORGANISM Controller",0,"","1.0.0-rc.2",kVstVersionString,oso::Controller::create)
END_FACTORY

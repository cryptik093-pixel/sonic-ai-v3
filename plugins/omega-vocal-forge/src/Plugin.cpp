#include "Plugin.h"
#include "base/source/fstreamer.h"
#include "pluginterfaces/vst/ivstparameterchanges.h"
#include "pluginterfaces/base/ustring.h"
#include "public.sdk/source/main/pluginfactory.h"
#include <array>
#include <cstring>
namespace ovf {
using namespace Steinberg;using namespace Steinberg::Vst;
namespace {
bool read(IBStream* stream,Targets& t){if(!stream)return false;IBStreamer s(stream,kLittleEndian);int32 magic=0,version=0,b=0;double i=0,o=0;if(!s.readInt32(magic)||!s.readInt32(version)||magic!=0x3146564f||version!=1||!s.readDouble(i)||!s.readDouble(o)||!s.readInt32(b)||!std::isfinite(i)||!std::isfinite(o)||i<0||i>1||o<0||o>1||(b!=0&&b!=1))return false;t={i,o,b==1};return true;}
class GainParameter:public Parameter {
public:GainParameter(const TChar* name,ParamID id):Parameter(name,id,STR16("dB"),.5,0,ParameterInfo::kCanAutomate){}
 ParamValue toPlain(ParamValue n)const override{return db(n);}
 ParamValue toNormalized(ParamValue p)const override{return normalized((p+24.)/48.);}
 void toString(ParamValue n,String128 s)const override{UString(s,128).printFloat(toPlain(n),2);}
 bool fromString(const TChar* s,ParamValue& n)const override{double p=0;if(!UString(const_cast<TChar*>(s),128).scanFloat(p)||!std::isfinite(p)||p < -24.||p>24.)return false;n=toNormalized(p);return true;}
};
}
tresult PLUGIN_API Processor::initialize(FUnknown* c){auto r=AudioEffect::initialize(c);if(r!=kResultOk)return r;addAudioInput(STR16("Vocal Input"),SpeakerArr::kStereo);addAudioOutput(STR16("Stereo Output"),SpeakerArr::kStereo);return kResultOk;}
tresult PLUGIN_API Processor::canProcessSampleSize(int32 n){return n==kSample32?kResultTrue:kResultFalse;}
tresult PLUGIN_API Processor::setupProcessing(ProcessSetup& s){if(s.symbolicSampleSize!=kSample32||s.maxSamplesPerBlock<1||!std::isfinite(s.sampleRate)||s.sampleRate<8000||s.sampleRate>384000)return kResultFalse;auto r=AudioEffect::setupProcessing(s);if(r==kResultOk)engine.prepare(s.sampleRate,targets());return r;}
tresult PLUGIN_API Processor::setProcessing(TBool on){if(on)engine.prepare(processSetup.sampleRate>0?processSetup.sampleRate:48000,targets());return kResultOk;}
tresult PLUGIN_API Processor::setBusArrangements(SpeakerArrangement* i,int32 ni,SpeakerArrangement* o,int32 no){if(ni!=1||no!=1||!i||!o||(i[0]!=SpeakerArr::kMono&&i[0]!=SpeakerArr::kStereo)||o[0]!=SpeakerArr::kStereo)return kResultFalse;return AudioEffect::setBusArrangements(i,ni,o,no);}
void Processor::apply(ParamID id,double n) noexcept {if(!std::isfinite(n))return;n=normalized(n);switch(id){case inputId:input.store(n);break;case outputId:output.store(n);break;case bypassId:bypass.store(n>=.5);break;default:break;}}
tresult PLUGIN_API Processor::process(ProcessData& d){
 if(d.symbolicSampleSize!=kSample32||d.numSamples<0)return kInvalidArgument;
 struct Cursor{IParamValueQueue* q=nullptr;int32 index=0,count=0,offset=0;double value=0;bool valid=false;};std::array<Cursor,3> cursors{};
 if(d.inputParameterChanges)for(int32 q=0;q<std::min<int32>(d.inputParameterChanges->getParameterCount(),1024);++q){auto* v=d.inputParameterChanges->getParameterData(q);if(!v||v->getParameterId()<inputId||v->getParameterId()>bypassId)continue;auto& c=cursors[v->getParameterId()-inputId];c.q=v;c.count=std::min<int32>(v->getPointCount(),65536);c.valid=c.count>0&&v->getPoint(0,c.offset,c.value)==kResultOk;}
 float* out[2]{};const float* in[2]{};
 if(d.numOutputs&&d.outputs&&d.outputs[0].numChannels==2&&d.outputs[0].channelBuffers32){out[0]=d.outputs[0].channelBuffers32[0];out[1]=d.outputs[0].channelBuffers32[1];}
 if(d.numSamples&&(!out[0]||!out[1]))return kResultFalse;
 if(d.numInputs&&d.inputs&&d.inputs[0].channelBuffers32){auto& bus=d.inputs[0];if(bus.numChannels>=1)in[0]=(bus.silenceFlags&1)?nullptr:bus.channelBuffers32[0];if(bus.numChannels==1)in[1]=in[0];else if(bus.numChannels==2)in[1]=(bus.silenceFlags&2)?nullptr:bus.channelBuffers32[1];}
 engine.set(targets());bool silent=true;
 for(int32 s=0;s<std::max<int32>(1,d.numSamples);++s){bool changed=false;for(auto& c:cursors){while(c.valid&&c.offset<=s){apply(c.q->getParameterId(),c.value);changed=true;c.valid=++c.index<c.count&&c.q->getPoint(c.index,c.offset,c.value)==kResultOk;}}if(changed)engine.set(targets());if(!d.numSamples)break;
  const float l=in[0]?in[0][s]:0,r=in[1]?in[1][s]:0;float a,b;engine.sample(l,r,a,b);out[0][s]=a;out[1][s]=b;silent=silent&&a==0&&b==0;
 }
 if(d.numOutputs&&d.outputs)d.outputs[0].silenceFlags=silent?3:0;return kResultOk;
}
tresult PLUGIN_API Processor::getState(IBStream* stream){if(!stream)return kInvalidArgument;IBStreamer s(stream,kLittleEndian);auto t=targets();return s.writeInt32(0x3146564f)&&s.writeInt32(1)&&s.writeDouble(t.input)&&s.writeDouble(t.output)&&s.writeInt32(t.bypass?1:0)?kResultOk:kResultFalse;}
tresult PLUGIN_API Processor::setState(IBStream* stream){Targets t;if(!read(stream,t))return kResultFalse;input.store(t.input);output.store(t.output);bypass.store(t.bypass);return kResultOk;}
tresult PLUGIN_API Controller::initialize(FUnknown* c){auto r=EditControllerEx1::initialize(c);if(r!=kResultOk)return r;parameters.addParameter(new GainParameter(STR16("Input Gain"),inputId));parameters.addParameter(new GainParameter(STR16("Output Gain"),outputId));parameters.addParameter(STR16("Bypass"),nullptr,1,0,ParameterInfo::kCanAutomate|ParameterInfo::kIsBypass,bypassId);return kResultOk;}
tresult PLUGIN_API Controller::setComponentState(IBStream* s){Targets t;if(!read(s,t))return kResultFalse;setParamNormalized(inputId,t.input);setParamNormalized(outputId,t.output);setParamNormalized(bypassId,t.bypass?1.:0.);return kResultOk;}
Steinberg::IPlugView* makeEditor(Controller*);
IPlugView* PLUGIN_API Controller::createView(FIDString n){return n&&std::strcmp(n,ViewType::kEditor)==0?makeEditor(this):nullptr;}
}
#ifndef OVF_NO_FACTORY
using namespace Steinberg;using namespace Steinberg::Vst;
BEGIN_FACTORY_DEF("Omega House Studio LLC","https://omega-house.online","")
DEF_CLASS2(INLINE_UID_FROM_FUID(ovf::processorId),PClassInfo::kManyInstances,kVstAudioEffectClass,"Omega Vocal Forge",Vst::kDistributable,"Fx|Tools","0.1.0",kVstVersionString,ovf::Processor::create)
DEF_CLASS2(INLINE_UID_FROM_FUID(ovf::controllerId),PClassInfo::kManyInstances,kVstComponentControllerClass,"Omega Vocal Forge Controller",0,"","0.1.0",kVstVersionString,ovf::Controller::create)
END_FACTORY
#endif

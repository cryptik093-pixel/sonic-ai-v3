#include "AdlibEngine.h"
#include <algorithm>
#include <cmath>
#include <stdexcept>
namespace adlib93 {
namespace {
StereoFrame scale(StereoFrame x,double g) noexcept { return {static_cast<float>(x.left*g),static_cast<float>(x.right*g)}; }
StereoFrame add(StereoFrame a,StereoFrame b) noexcept { return {a.left+b.left,a.right+b.right}; }
float safe(float x,uint64_t& diagnostics) noexcept {
 if(!std::isfinite(x)){++diagnostics;return 0;}
 // Keep intermediate sums representable for adversarial finite host samples.
 return std::clamp(x,-1.e12f,1.e12f);
}
}
void AdlibEngine::prepare(const PrepareSpec& spec,ParameterSnapshot initial) {
 if(!std::isfinite(spec.sampleRate)||spec.sampleRate<8000||spec.sampleRate>384000||spec.maxBlockSize==0)
  throw std::invalid_argument("ADLIB-93 invalid preparation rate/block");
 switch(spec.layout){case ChannelLayout::monoMono:case ChannelLayout::monoStereo:case ChannelLayout::stereoStereo:break;default:throw std::invalid_argument("ADLIB-93 unsupported layout");}
 spec_=spec;parameters_=sanitizeSnapshot(initial,spec.sampleRate);
 cleanup_.prepare(spec);character_.prepare(spec);movement_.prepare(spec);echo_.prepare(spec);space_.prepare(spec);freeze_.prepare(spec);output_.prepare(spec);
 reset();
}
void AdlibEngine::initializeSmall() noexcept {
 cleanup_.setParameters(parameters_);character_.setParameters(parameters_);cleanup_.reset();character_.reset();output_.setParameters(parameters_);output_.reset();
 const auto rate=spec_.sampleRate;
 inputGain_.prepare(rate,20,dbToGain(parameters_[Param::InputGain]));
 direct_.prepare(rate,20,levelToGain(parameters_[Param::DirectLevel]));
 double_.prepare(rate,20,levelToGain(parameters_[Param::DoubleLevel]));
 chorus_.prepare(rate,20,levelToGain(parameters_[Param::ChorusLevel]));
 echoLevel_.prepare(rate,20,levelToGain(parameters_[Param::DelayLevel]));
 reverb_.prepare(rate,20,levelToGain(parameters_[Param::ReverbLevel]));
 mix_.prepare(rate,20,parameters_[Param::MixAmount]);width_.prepare(rate,20,parameters_[Param::StereoWidth]);pan_.prepare(rate,20,parameters_[Param::StereoPan]);
 bypass_.reset(hostBypass_||parameters_[Param::BypassInternal]>.5f?1:0);
 send_.reset(parameters_[Param::RoutingMode]>.5f?1:0);
 silenceSamples_=0;tailExpired_=automaticClear_=false;meters_={};tailGain_=1;
 setParameters(parameters_);setTiming(timing_);
}
void AdlibEngine::reset(){movement_.reset();echo_.reset();space_.reset();freeze_.reset();clearing_=false;clearModule_=0;initializeSmall();}
void AdlibEngine::setParameters(const ParameterSnapshot& p) noexcept {
 parameters_=sanitizeSnapshot(p,spec_.sampleRate);
 cleanup_.setParameters(parameters_);character_.setParameters(parameters_);movement_.setParameters(parameters_);echo_.setParameters(parameters_);space_.setParameters(parameters_);output_.setParameters(parameters_);
 inputGain_.setTarget(dbToGain(parameters_[Param::InputGain]));direct_.setTarget(levelToGain(parameters_[Param::DirectLevel]));double_.setTarget(levelToGain(parameters_[Param::DoubleLevel]));chorus_.setTarget(levelToGain(parameters_[Param::ChorusLevel]));echoLevel_.setTarget(levelToGain(parameters_[Param::DelayLevel]));reverb_.setTarget(levelToGain(parameters_[Param::ReverbLevel]));
 mix_.setTarget(parameters_[Param::MixAmount]);width_.setTarget(parameters_[Param::StereoWidth]);pan_.setTarget(parameters_[Param::StereoPan]);
 bypass_.setTarget(hostBypass_||parameters_[Param::BypassInternal]>.5f?1:0,static_cast<uint32_t>(std::lround(.020*spec_.sampleRate)));
 send_.setTarget(parameters_[Param::RoutingMode]>.5f?1:0,static_cast<uint32_t>(std::lround(.020*spec_.sampleRate)));
}
void AdlibEngine::setTiming(const HostTiming& timing) noexcept {timing_=timing;echo_.setTiming(timing);}
void AdlibEngine::setBypassed(bool value) noexcept {hostBypass_=value;bypass_.setTarget(value||parameters_[Param::BypassInternal]>.5f?1:0,static_cast<uint32_t>(std::lround(.020*spec_.sampleRate)));}
StereoFrame AdlibEngine::process(StereoFrame input) noexcept {
 meters_.clearedWrites=0;
 if(automaticClear_){meters_.clearedWrites=128;if(clearStep(128)){automaticClear_=false;finishClear(parameters_,false);}}
 input.left=safe(input.left,meters_.diagnostics);input.right=spec_.layout==ChannelLayout::stereoStereo?safe(input.right,meters_.diagnostics):input.left;
 const auto x=scale(input,inputGain_.next());
 meters_.inputPeak=std::max(std::abs(x.left),std::abs(x.right));
 const double bypass=bypass_.next();const bool bypassRequested=hostBypass_||parameters_[Param::BypassInternal]>.5f;
 const bool freezeRequested=parameters_[Param::FreezeActive]>.5f&&!bypassRequested&&!clearing_&&tailGain_>=1;
 if(meters_.inputPeak>0){silenceSamples_=0;tailExpired_=false;}else if(silenceSamples_<static_cast<uint64_t>(180*spec_.sampleRate))++silenceSamples_;
 double expiry=1;
 if(!freezeRequested && silenceSamples_>=static_cast<uint64_t>(179*spec_.sampleRate))
  expiry=std::clamp((180*spec_.sampleRate-static_cast<double>(silenceSamples_))/spec_.sampleRate,0.0,1.0);
 // Held-loop duration is independent of the normal-tail deadline. Preserve
 // the full 250-ms frozen release even after more than 180 s of silence.
 if(!freezeRequested && freeze_.blend()<=0 && silenceSamples_>=static_cast<uint64_t>(180*spec_.sampleRate))tailExpired_=true;
 const auto clean=cleanup_.process(x);const auto character=character_.process(clean);
 const auto cleanMeters=cleanup_.measurements();meters_.gateReductionDb=cleanMeters.gateReductionDb;meters_.deessReductionDb=cleanMeters.deessReductionDb;
 const double send=send_.next();
 const double directGain=direct_.next(),doubleGain=double_.next(),chorusGain=chorus_.next(),delayGain=echoLevel_.next(),reverbGain=reverb_.next();
 const double excitation=(freezeRequested?0.0:(1.0-freeze_.blend())*(1.0-bypass))*tailGain_*expiry;
 StereoFrame movement{},spatial{};
 if(!clearing_){
  const auto motion=movement_.processBranches(scale(character,(1-bypass)*tailGain_));
  movement=add(scale(motion.doubler,doubleGain),scale(motion.chorus,chorusGain));
  const auto delay=scale(echo_.process(scale(character,excitation),parameters_[Param::ThrowActive]),delayGain);
  // Delay send is leveled, pre-duck. During Freeze no new reverb excitation,
  // including existing delay->reverb send, enters the underlying network.
  const auto room=space_.process(scale(character,excitation),scale(delay,freezeRequested?0:(1.0-freeze_.blend())*tailGain_*expiry),x);
  const auto normal=scale(add(delay,scale(room.reverb,reverbGain)),room.duckGain*expiry);
  spatial=freeze_.process(normal,freezeRequested);
 }
 const auto branches=add(movement,spatial);
 auto wet=add(scale(character,(1-send)*directGain*(1-bypass)),scale(branches,tailGain_));
 const double width=width_.next(),pan=pan_.next();
 const double mid=(static_cast<double>(wet.left)+wet.right)*.5,side=(static_cast<double>(wet.left)-wet.right)*.5*width;
 wet={static_cast<float>((mid+side)*(pan>0?1-pan:1)),static_cast<float>((mid-side)*(pan<0?1+pan:1))};
 const double storedMix=mix_.next(),mix=storedMix+(1-storedMix)*send;
 auto blended=add(scale(x,(1-send)*((1-storedMix)+storedMix*bypass)),scale(wet,mix));
 if(parameters_[Param::DeessListen]>.5f)blended=cleanup_.highBand();
 if(tailExpired_&&!freezeRequested){ // At 180 s only spatial state is retired, incrementally.
  if(!clearing_){beginClear();tailExpired_=false;automaticClear_=true;}
 }
 auto result=output_.process(blended);
 if(spec_.layout==ChannelLayout::monoMono){const auto mono=static_cast<float>((static_cast<double>(result.left)+result.right)*.5);result={mono,mono};}
 const auto out=output_.meters();meters_.outputPeak=std::max(std::abs(result.left),std::abs(result.right));meters_.limiterReductionDb=out.limiterReductionDb;
 meters_.diagnostics=std::max(meters_.diagnostics,out.diagnostics);meters_.freezeHeld=freezeRequested||freeze_.blend()>0;
 meters_.clearing=clearing_;const auto time=echo_.timing();meters_.delayClamped=time.clamped;meters_.usingManualTempo=time.usingManual;
 meters_.tempo=timing_.bpmValid&&std::isfinite(timing_.bpm)&&timing_.bpm>0?timing_.bpm:parameters_[Param::DelayManualBpm];meters_.allocatedBytes=allocatedBytes();
 return result;
}
void AdlibEngine::process(const float* const* in,float* const* out,uint32_t frames,const ParameterSnapshot& parameters,const ProcessContext& context) noexcept {
 setParameters(parameters);setTiming(context.timing);
 if(frames==0&&automaticClear_){meters_.clearedWrites=64;if(clearStep(64)){automaticClear_=false;finishClear(parameters_,false);}}
 for(uint32_t n=0;n<frames;++n){const float left=in&&in[0]?in[0][n]:0;const float right=spec_.layout==ChannelLayout::stereoStereo&&in&&in[1]?in[1][n]:left;const auto y=process({left,right});if(out&&out[0])out[0][n]=y.left;if(spec_.layout!=ChannelLayout::monoMono&&out&&out[1])out[1][n]=y.right;}
}
void AdlibEngine::beginClear() noexcept {if(clearing_)return;clearing_=true;clearModule_=0;movement_.beginClear();echo_.beginClear();space_.beginClear();freeze_.beginClear();}
bool AdlibEngine::clearStep(uint32_t budget) noexcept {
 if(!clearing_)return true;
 bool done=false;
 switch(clearModule_){case 0:done=movement_.clearStep(budget);break;case 1:done=echo_.clearStep(budget);break;case 2:done=space_.clearStep(budget);break;case 3:done=freeze_.clearStep(budget);break;default:done=true;}
 if(done)++clearModule_;
 if(clearModule_>=4)clearing_=false;
 return !clearing_;
}
void AdlibEngine::finishClear(const ParameterSnapshot& p,bool small) noexcept {parameters_=sanitizeSnapshot(p,spec_.sampleRate);if(small)initializeSmall();else {setParameters(parameters_);silenceSamples_=0;tailExpired_=false;}clearing_=false;}
std::size_t AdlibEngine::allocatedBytes() const noexcept{return movement_.allocatedBytes()+echo_.allocatedBytes()+space_.allocatedBytes()+freeze_.allocatedBytes();}
}

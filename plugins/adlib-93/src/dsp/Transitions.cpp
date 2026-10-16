#include "Transitions.h"
#include <algorithm>
#include <cmath>
namespace adlib93 {
void Transitions::prepare(const PrepareSpec& spec,ParameterSnapshot initial){
 spec_=spec;current_=sanitizeSnapshot(initial,spec.sampleRate);for(auto& engine:engines_)engine.prepare(spec,current_);
 crossfadeLength_=std::max(1u,static_cast<uint32_t>(std::lround(.050*spec.sampleRate)));
 clearLength_=std::max(1u,static_cast<uint32_t>(std::lround(.020*spec.sampleRate)));
 active_=position_=lastWrites_=reportedWrites_=0;phase_=Phase::idle;hasPending_=clearRequested_=hostBypass_=inhibitFreeze_=inhibitThrow_=false;
}
void Transitions::reset(){for(auto& engine:engines_){engine.setParameters(current_);engine.reset();engine.setTiming(timing_);engine.setBypassed(hostBypass_);}phase_=Phase::idle;hasPending_=clearRequested_=false;position_=lastWrites_=reportedWrites_=0;}
void Transitions::request(const ParameterSnapshot& p) noexcept {
 pending_=sanitizeSnapshot(p,spec_.sampleRate);pending_[Param::ThrowActive]=pending_[Param::FreezeActive]=pending_[Param::DeessListen]=pending_[Param::BypassInternal]=0;
 hasPending_=true;inhibitFreeze_=inhibitThrow_=true;
}
void Transitions::setParameters(const ParameterSnapshot& p) noexcept {
 auto parameters=sanitizeSnapshot(p,spec_.sampleRate);
 if(parameters[Param::FreezeActive]<.5f)inhibitFreeze_=false;else if(inhibitFreeze_)parameters[Param::FreezeActive]=0;
 if(parameters[Param::ThrowActive]<.5f)inhibitThrow_=false;else if(inhibitThrow_)parameters[Param::ThrowActive]=0;
 if(phase_==Phase::idle&&hasPending_){pending_=parameters;return;}
 if(phase_==Phase::prepareIncoming||phase_==Phase::incomingReady||phase_==Phase::crossfade){incoming_=parameters;engines_[1-active_].setParameters(incoming_);return;}
 current_=parameters;engines_[active_].setParameters(current_);
 // Normal automation is never a new preset request. Keep the incoming engine
 // coherent during its prepared 50-ms transition without restarting clearing.
}
void Transitions::setTiming(const HostTiming& t) noexcept {timing_=t;for(auto& engine:engines_)engine.setTiming(t);}
void Transitions::setBypassed(bool b) noexcept {hostBypass_=b;for(auto& engine:engines_)engine.setBypassed(b);}
void Transitions::clearTails() noexcept {clearRequested_=true;inhibitFreeze_=inhibitThrow_=true;}
void Transitions::startPending() noexcept {
 if(clearRequested_){clearRequested_=false;current_[Param::ThrowActive]=current_[Param::FreezeActive]=0;engines_[active_].setParameters(current_);phase_=Phase::clearFadeOut;position_=0;return;}
 if(hasPending_){incoming_=pending_;hasPending_=false;engines_[1-active_].setParameters(incoming_);engines_[1-active_].beginClear();phase_=Phase::prepareIncoming;}
}
void Transitions::service(uint32_t budget,bool allowFinalize) noexcept {
 lastWrites_=0;
 if(phase_==Phase::idle&&allowFinalize)startPending();
 if(phase_==Phase::prepareIncoming){
  // Coalesce changes during preparation; no additional taps/engines are born.
  if(hasPending_){incoming_=pending_;hasPending_=false;engines_[1-active_].setParameters(incoming_);}
  lastWrites_=budget;
  if(engines_[1-active_].clearStep(budget))phase_=Phase::incomingReady;
 }
 if(phase_==Phase::incomingReady&&allowFinalize){
   if(hasPending_){incoming_=pending_;hasPending_=false;engines_[1-active_].setParameters(incoming_);}
   engines_[1-active_].finishClear(incoming_);engines_[1-active_].setTiming(timing_);engines_[1-active_].setBypassed(hostBypass_);
   current_[Param::ThrowActive]=current_[Param::FreezeActive]=0;engines_[active_].setParameters(current_);
   phase_=Phase::crossfade;position_=0;
 }else if(phase_==Phase::clearMemory){
  lastWrites_=budget;
  if(engines_[active_].clearStep(budget))phase_=Phase::clearReady;
 }
 if(phase_==Phase::clearReady&&allowFinalize){engines_[active_].finishClear(current_,false);engines_[active_].setTailGain(0);phase_=Phase::clearFadeIn;position_=0;}
}
StereoFrame Transitions::process(StereoFrame x) noexcept {
 // 128 writes reserved for controller clearing plus 128 for a playing
 // engine's automatic 180-second-tail retirement. Dual processing while
 // crossfading has no controller clear and remains within 256 total.
 service(128);
 if(phase_==Phase::clearFadeOut){const float gain=1-static_cast<float>(++position_)/clearLength_;engines_[active_].setTailGain(gain);}
 if(phase_==Phase::clearFadeIn){const float gain=static_cast<float>(++position_)/clearLength_;engines_[active_].setTailGain(gain);}
 auto result=engines_[active_].process(x);
 reportedWrites_=lastWrites_+engines_[active_].measurements().clearedWrites;
 if(phase_==Phase::crossfade){
  const auto next=engines_[1-active_].process(x);const float weight=static_cast<float>(++position_)/crossfadeLength_;
  reportedWrites_+=engines_[1-active_].measurements().clearedWrites;
  result={result.left+(next.left-result.left)*weight,result.right+(next.right-result.right)*weight};
  if(position_>=crossfadeLength_){active_=1-active_;current_=incoming_;phase_=Phase::idle;position_=0;}
 }else if(phase_==Phase::clearFadeOut&&position_>=clearLength_){engines_[active_].beginClear();phase_=Phase::clearMemory;position_=0;}
 else if(phase_==Phase::clearFadeIn&&position_>=clearLength_){engines_[active_].setTailGain(1);phase_=Phase::idle;position_=0;}
 lastOutputPeak_=std::max(std::abs(result.left),std::abs(result.right));return result;
}
void Transitions::process(const float* const* in,float* const* out,uint32_t frames,const ParameterSnapshot& p,const ProcessContext& context) noexcept {
 setParameters(p);process(in,out,frames,context);
}
void Transitions::process(const float* const* in,float* const* out,uint32_t frames,const ProcessContext& context) noexcept {
 setTiming(context.timing);if(frames==0){serviceZeroBlock();return;}
 for(uint32_t n=0;n<frames;++n){const float left=in&&in[0]?in[0][n]:0;const float right=spec_.layout==ChannelLayout::stereoStereo&&in&&in[1]?in[1][n]:left;const auto y=process({left,right});if(out&&out[0])out[0][n]=y.left;if(spec_.layout!=ChannelLayout::monoMono&&out&&out[1])out[1][n]=y.right;}
}
void Transitions::serviceZeroBlock() noexcept {service(64,false);reportedWrites_=lastWrites_;}
EngineMeasurements Transitions::measurements() const noexcept {
 auto m=engines_[active_].measurements();m.clearedWrites=reportedWrites_;m.outputPeak=lastOutputPeak_;
 m.clearing=m.clearing||phase_==Phase::clearFadeOut||phase_==Phase::clearMemory||phase_==Phase::clearReady||phase_==Phase::clearFadeIn;
 m.transitioning=hasPending_||phase_==Phase::prepareIncoming||phase_==Phase::incomingReady||phase_==Phase::crossfade;m.allocatedBytes=allocatedBytes();return m;
}
std::size_t Transitions::allocatedBytes() const noexcept {return engines_[0].allocatedBytes()+engines_[1].allocatedBytes();}
}

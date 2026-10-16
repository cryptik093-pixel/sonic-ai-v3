#include "Echo.h"
#include <algorithm>
#include <cmath>
#include <stdexcept>
namespace adlib93 {
namespace {
constexpr double pi=3.14159265358979323846;
double bounded(double x,double lo,double hi,double fallback) noexcept { return std::isfinite(x)?std::clamp(x,lo,hi):fallback; }
float finiteSample(float x) noexcept { return std::isfinite(x)&&std::abs(x)>=1.e-25f?std::clamp(x,-1000000.f,1000000.f):0.f; }
}
DelayTiming resolveDelayTime(const ParameterSnapshot& p,const HostTiming& h) noexcept {
 DelayTiming r;
 double ms=bounded(p[Param::DelayTime],10,4000,250);
 if(p[Param::DelaySync]>=.5f) {
  r.usingManual=!(h.bpmValid&&std::isfinite(h.bpm)&&h.bpm>0);
  const double bpm=r.usingManual?bounded(p[Param::DelayManualBpm],30,300,120):h.bpm;
  const double notes[]={.125,.25,.5,1,2,4};
  const int division=static_cast<int>(bounded(p[Param::DelayDivision],0,5,2));
  double quarters=notes[division];
  if(division==5&&!r.usingManual&&h.signatureValid&&h.numerator>0&&h.denominator>0)
   quarters=static_cast<double>(h.numerator)*4/h.denominator;
  const int modifier=static_cast<int>(bounded(p[Param::DelayModifier],0,2,0));
  ms=60000/bpm*quarters*(modifier==1?1.5:modifier==2?2./3:1.);
 }
 r.clamped=!std::isfinite(ms)||ms<10||ms>4000;
 r.milliseconds=std::isfinite(ms)?std::clamp(ms,10.,4000.):4000.; return r;
}
void Echo::prepare(const PrepareSpec& s) {
 if(!std::isfinite(s.sampleRate)||s.sampleRate<8000||s.sampleRate>384000) throw std::invalid_argument("Echo sample rate");
 sampleRate_=s.sampleRate; smooth_=1-std::exp(-1/(.020*sampleRate_)); fadeLength_=static_cast<uint32_t>(std::lround(.100*sampleRate_));
 for(auto& b:delay_) b.assign(static_cast<size_t>(std::ceil(4*sampleRate_))+2,0);
 constexpr double times[]={3.1,4.7,7.3,11.3,3.7,5.3,8.3,12.7};
 for(size_t i=0;i<8;++i) allpass_[i].data.assign(std::max<size_t>(1,static_cast<size_t>(std::lround(times[i]*.001*sampleRate_))),0);
 reset();
}
void Echo::reset() {
 for(auto& b:delay_) std::fill(b.begin(),b.end(),0.f);
 for(auto& a:allpass_) { std::fill(a.data.begin(),a.data.end(),0.f);a.write=0; }
 filter_.fill(0); write_=0; fade_=0;primed_=false; maximumState_=0; clearing_=false;
}
void Echo::setParameters(const ParameterSnapshot& p) noexcept {
 parameters_=p; setTiming(host_);
 feedbackTarget_=static_cast<float>(bounded(p[Param::DelayFeedback],0,.9,0));pingTarget_=static_cast<float>(bounded(p[Param::DelayPingpong],0,1,0));diffuseTarget_=static_cast<float>(bounded(p[Param::DelayDiffusion],0,1,0));enabledTarget_=p[Param::DelayEnabled]>=.5f?1.f:0.f;
 hpTarget_=static_cast<float>(1-std::exp(-2*pi*bounded(p[Param::DelayHp],20,std::min(1000.,.45*sampleRate_),100)/sampleRate_));lpTarget_=static_cast<float>(1-std::exp(-2*pi*bounded(p[Param::DelayLp],1000,std::min(20000.,.45*sampleRate_),8000)/sampleRate_));
 if(!primed_) {
  feedback_=static_cast<float>(bounded(p[Param::DelayFeedback],0,.9,0)); ping_=static_cast<float>(bounded(p[Param::DelayPingpong],0,1,0));
  diffuse_=static_cast<float>(bounded(p[Param::DelayDiffusion],0,1,0)); enabled_=p[Param::DelayEnabled]>=.5f?1.f:0.f;
  hp_=static_cast<float>(1-std::exp(-2*pi*bounded(p[Param::DelayHp],20,std::min(1000.,.45*sampleRate_),100)/sampleRate_));
  lp_=static_cast<float>(1-std::exp(-2*pi*bounded(p[Param::DelayLp],1000,std::min(20000.,.45*sampleRate_),8000)/sampleRate_));
  throwGain_=throwTarget_=p[Param::DelayThrowMode]>=.5f?0.f:1.f;throwRemaining_=0; primed_=true;
 }
}
void Echo::setTiming(const HostTiming& h) noexcept {
 host_=h;resolved_=resolveDelayTime(parameters_,host_);pending_=resolved_.milliseconds*.001*sampleRate_;
 if(!primed_) tapA_=tapB_=pending_;
 else if(fade_==0&&std::abs(pending_-tapA_)>1.e-8) {tapB_=pending_;fade_=1;}
}
float Echo::read(size_t channel,double samples) const noexcept {
 const auto& b=delay_[channel];double position=static_cast<double>(write_)-samples;
 if(position<0) position+=b.size();
 const auto i=static_cast<size_t>(position);const auto j=(i+1)%b.size();const float f=static_cast<float>(position-i);
 return b[i]+f*(b[j]-b[i]);
}
StereoFrame Echo::process(StereoFrame in,float throwGate) noexcept {
 if(delay_[0].empty()||clearing_) return {};
 const auto& p=parameters_;
 auto approach=[this](float& v,double target) {v+=static_cast<float>(smooth_*(target-v));};
 approach(feedback_,feedbackTarget_);approach(ping_,pingTarget_);approach(diffuse_,diffuseTarget_);approach(enabled_,enabledTarget_);approach(hp_,hpTarget_);approach(lp_,lpTarget_);
 const bool held=std::isfinite(throwGate)&&throwGate>=.5f;
 const float target=p[Param::DelayThrowMode]>=.5f?(held?1.f:0.f):(held?1.995262315f:1.f);
 if(target!=throwTarget_){throwTarget_=target;throwRemaining_=static_cast<uint32_t>(std::lround(.005*sampleRate_));throwStep_=(target-throwGain_)/static_cast<float>(throwRemaining_);}
 if(throwRemaining_){throwGain_+=throwStep_;if(--throwRemaining_==0)throwGain_=throwTarget_;}
 float y[2]{};const float fade=fade_?static_cast<float>(fade_-1)/fadeLength_:0;
 for(size_t c=0;c<2;++c) {
  const float raw=read(c,tapA_); const float tapped=fade_?raw+(read(c,tapB_)-raw)*fade:raw;
  filter_[c*2]+=hp_*(tapped-filter_[c*2]); const float high=tapped-filter_[c*2];
  filter_[c*2+1]+=lp_*(high-filter_[c*2+1]); const float filtered=filter_[c*2+1];float diffuse=filtered;
  for(size_t j=0;j<4;++j) {auto& a=allpass_[c*4+j];const float delayed=a.data[a.write];const float output=delayed-.65f*diffuse;a.data[a.write]=finiteSample(diffuse+.65f*output);a.write=(a.write+1)%a.data.size();diffuse=output;}
  y[c]=finiteSample(filtered+diffuse_*(diffuse-filtered));
 }
 if(fade_) {if(++fade_>fadeLength_) {tapA_=tapB_;fade_=0;if(std::abs(pending_-tapA_)>1.e-8){tapB_=pending_;fade_=1;}}}
 const float left=finiteSample(in.left),right=finiteSample(in.right),mono=.5f*(left+right);
 const float injectionL=(left+ping_*(mono-left))*throwGain_*enabled_;
 const float injectionR=right*(1-ping_)*throwGain_*enabled_;
 const float safeL=feedback_==0?0.f:4*std::tanh(y[0]*.25f),safeR=feedback_==0?0.f:4*std::tanh(y[1]*.25f);
 delay_[0][write_]=finiteSample(injectionL+feedback_*((1-ping_)*safeL+ping_*safeR));
 delay_[1][write_]=finiteSample(injectionR+feedback_*((1-ping_)*safeR+ping_*safeL));
 maximumState_=std::max({maximumState_,std::abs(delay_[0][write_]),std::abs(delay_[1][write_])});write_=(write_+1)%delay_[0].size();
 for(auto& v:filter_) if(std::abs(v)<1.e-25f)v=0;
 return {y[0]*enabled_,y[1]*enabled_};
}
void Echo::beginClear() noexcept {clearing_=true;clearBuffer_=clearOffset_=0;write_=0;fade_=0;primed_=false;maximumState_=0;for(auto& a:allpass_)a.write=0;}
bool Echo::clearStep(uint32_t budget) noexcept {
 while(budget&&clearBuffer_<11) {
  float* data=nullptr;size_t count=0;
  if(clearBuffer_<2){data=delay_[clearBuffer_].data();count=delay_[clearBuffer_].size();}
  else if(clearBuffer_<10){data=allpass_[clearBuffer_-2].data.data();count=allpass_[clearBuffer_-2].data.size();}
  else {data=filter_.data();count=filter_.size();}
  while(budget&&clearOffset_<count){data[clearOffset_++]=0;--budget;}
  if(clearOffset_==count){++clearBuffer_;clearOffset_=0;}
 }
 if(clearBuffer_==11)clearing_=false;return !clearing_;
}
size_t Echo::allocatedBytes() const noexcept {size_t n=0;for(const auto& b:delay_)n+=b.capacity()*sizeof(float);for(const auto& a:allpass_)n+=a.data.capacity()*sizeof(float);return n;}
}

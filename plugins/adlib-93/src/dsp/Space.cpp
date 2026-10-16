#include "Space.h"
#include <algorithm>
#include <cmath>
#include <stdexcept>
namespace adlib93 {
namespace {
constexpr double pi=3.14159265358979323846;
constexpr double times[8]={29.7,37.1,41.1,43.7,53.1,59.3,67.7,71.9};
constexpr float invSqrt8=.3535533905932738f,invSqrt2=.7071067811865475f;
constexpr int inputR[8]={1,-1,1,-1,1,-1,1,-1};
constexpr int outputL[8]={1,1,-1,-1,1,1,-1,-1},outputR[8]={1,-1,-1,1,1,-1,-1,1};
double bounded(double x,double lo,double hi,double fallback) noexcept {return std::isfinite(x)?std::clamp(x,lo,hi):fallback;}
float finiteSample(float x) noexcept {return std::isfinite(x)&&std::abs(x)>=1.e-25f?std::clamp(x,-1000000.f,1000000.f):0;}
}
void Space::prepare(const PrepareSpec& s) {
 if(!std::isfinite(s.sampleRate)||s.sampleRate<8000||s.sampleRate>384000)throw std::invalid_argument("Space sample rate");
 sampleRate_=s.sampleRate;smooth_=1-std::exp(-1/(.020*sampleRate_));
 size_t previous=0;
 for(size_t i=0;i<8;++i){const auto length=std::max(previous+1,static_cast<size_t>(std::lround(times[i]*.001*sampleRate_)));lines_[i].assign(length,0);previous=length;}
 for(auto& b:predelay_)b.assign(static_cast<size_t>(std::ceil(.150*sampleRate_))+2,0);
 reset();
}
void Space::reset() {
 for(auto& b:lines_)std::fill(b.begin(),b.end(),0.f);
 for(auto& b:predelay_)std::fill(b.begin(),b.end(),0.f);
 dampingState_.fill(0);positions_.fill(0);preWrite_=0;duckDb_=0;primed_=false;clearing_=false;maximumState_=0;
}
void Space::setParameters(const ParameterSnapshot& p) noexcept {
 const double decay=bounded(p[Param::ReverbDecay],.2,12,2);
 for(size_t i=0;i<8;++i){
  // Convert the unsigned buffer length before applying the negative RT60
  // exponent; unsigned multiplication would overflow into a positive gain.
  const double delaySeconds=static_cast<double>(lines_[i].size())/sampleRate_;
  gainTarget_[i]=std::pow(10.,-3.*delaySeconds/decay);
 }
 dampingTarget_=1-std::exp(-2*pi*bounded(p[Param::ReverbDamping],1000,std::min(20000.,.45*sampleRate_),6000)/sampleRate_);
 predelayTarget_=bounded(p[Param::ReverbPredelay],0,150,20)*sampleRate_*.001;
 sendTarget_=levelToGain(p[Param::ReverbDelaySend]);enabledTarget_=p[Param::ReverbEnabled]>=.5f?1.f:0.f;
 duckEnabled_=p[Param::DuckEnabled]>=.5f;duckThreshold_=static_cast<float>(bounded(p[Param::DuckThreshold],-60,0,-30));duckMax_=static_cast<float>(bounded(p[Param::DuckMaxReduction],0,18,6));
 duckAttack_=std::exp(-1/(.001*bounded(p[Param::DuckAttack],1,50,5)*sampleRate_));
 duckRelease_=std::exp(-1/(.001*bounded(p[Param::DuckRelease],50,1000,250)*sampleRate_));
 if(!primed_){gain_=gainTarget_;damping_=dampingTarget_;predelaySamples_=predelayTarget_;send_=sendTarget_;enabled_=enabledTarget_;primed_=true;}
}
SpaceReturns Space::process(StereoFrame clean,StereoFrame delay,StereoFrame detector) noexcept {
 if(lines_[0].empty()||clearing_)return {};
 const float peak=std::max(std::abs(finiteSample(detector.left)),std::abs(finiteSample(detector.right)));
 const float detectorDb=duckEnabled_?20*std::log10(std::max(1.e-12f,peak)):-240.f;
 const float reduction=duckEnabled_?std::min(duckMax_,std::max(0.f,detectorDb-duckThreshold_)*.75f):0.f;
 const double coefficient=reduction>duckDb_?duckAttack_:duckRelease_;
 duckDb_=static_cast<float>(coefficient*duckDb_+(1-coefficient)*reduction);
 if(duckDb_<1.e-20f)duckDb_=0;
 damping_+=smooth_*(dampingTarget_-damping_);predelaySamples_+=smooth_*(predelayTarget_-predelaySamples_);
 send_+=static_cast<float>(smooth_*(sendTarget_-send_));enabled_+=static_cast<float>(smooth_*(enabledTarget_-enabled_));
 float input[2]={finiteSample(clean.left+delay.left*send_)*enabled_,finiteSample(clean.right+delay.right*send_)*enabled_};
 for(size_t c=0;c<2;++c){auto& b=predelay_[c];b[preWrite_]=input[c];double pos=static_cast<double>(preWrite_)-predelaySamples_;if(pos<0)pos+=b.size();const auto a=static_cast<size_t>(pos),z=(a+1)%b.size();input[c]=b[a]+static_cast<float>(pos-a)*(b[z]-b[a]);}
 preWrite_=(preWrite_+1)%predelay_[0].size();
 float values[8]{};double sum=0,left=0,right=0;
 for(size_t i=0;i<8;++i){const float raw=lines_[i][positions_[i]];left+=outputL[i]*invSqrt8*raw;right+=outputR[i]*invSqrt8*raw;dampingState_[i]+=static_cast<float>(damping_*(raw-dampingState_[i]));if(std::abs(dampingState_[i])<1.e-25f)dampingState_[i]=0;values[i]=dampingState_[i];sum+=values[i];}
 for(size_t i=0;i<8;++i){gain_[i]+=smooth_*(gainTarget_[i]-gain_[i]);const double injection=(input[0]+inputR[i]*input[1])*invSqrt8*invSqrt2;const float state=finiteSample(static_cast<float>((values[i]-.25*sum)*gain_[i]+injection));lines_[i][positions_[i]]=state;maximumState_=std::max(maximumState_,std::abs(state));positions_[i]=(positions_[i]+1)%lines_[i].size();}
 return {{finiteSample(static_cast<float>(left))*enabled_,finiteSample(static_cast<float>(right))*enabled_},duckDb_==0?1.f:static_cast<float>(std::pow(10.,-.05*duckDb_))};
}
void Space::beginClear() noexcept {clearing_=true;clearBuffer_=clearOffset_=0;positions_.fill(0);preWrite_=0;primed_=false;duckDb_=0;maximumState_=0;}
bool Space::clearStep(uint32_t budget) noexcept {
 while(budget&&clearBuffer_<11){float* data=nullptr;size_t count=0;
  if(clearBuffer_<8){data=lines_[clearBuffer_].data();count=lines_[clearBuffer_].size();}
  else if(clearBuffer_<10){data=predelay_[clearBuffer_-8].data();count=predelay_[clearBuffer_-8].size();}
  else{data=dampingState_.data();count=dampingState_.size();}
  while(budget&&clearOffset_<count){data[clearOffset_++]=0;--budget;}
  if(clearOffset_==count){++clearBuffer_;clearOffset_=0;}
 }
 if(clearBuffer_==11)clearing_=false;return !clearing_;
}
size_t Space::allocatedBytes()const noexcept{size_t n=0;for(const auto& b:lines_)n+=b.capacity()*sizeof(float);for(const auto& b:predelay_)n+=b.capacity()*sizeof(float);return n;}
}

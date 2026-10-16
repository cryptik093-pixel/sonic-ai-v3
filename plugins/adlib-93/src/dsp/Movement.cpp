#include "Movement.h"
#include <algorithm>
#include <cmath>
#include <stdexcept>
namespace adlib93 {
namespace {constexpr double tau=6.2831853071795864769;}
void Movement::prepare(const PrepareSpec& s){if(!std::isfinite(s.sampleRate)||s.sampleRate<8000||s.sampleRate>384000)throw std::invalid_argument("Movement sample rate");rate_=s.sampleRate;smoothCoefficient_=std::exp(-1/(.020*rate_));const auto length=static_cast<std::size_t>(std::ceil(.050*rate_))+4;for(auto& m:memory_)m.assign(length,0);reset();}
void Movement::setParameters(const ParameterSnapshot& p) noexcept {parameters_=sanitizeSnapshot(p,rate_);}
void Movement::resetSmall() noexcept {write_=0;phases_={0,tau/4,0,tau/4};delays_={parameters_[Param::DoubleDelayL],parameters_[Param::DoubleDelayR],parameters_[Param::ChorusDelay],parameters_[Param::ChorusDelay]};depths_={parameters_[Param::DoubleDepthL],parameters_[Param::DoubleDepthR],parameters_[Param::ChorusDepth],parameters_[Param::ChorusDepth]};rates_={parameters_[Param::DoubleRateL],parameters_[Param::DoubleRateR],parameters_[Param::ChorusRate],parameters_[Param::ChorusRate]};doubleWet_=parameters_[Param::DoubleEnabled];chorusWet_=parameters_[Param::ChorusEnabled];}
void Movement::reset() noexcept {for(auto& m:memory_)std::fill(m.begin(),m.end(),0.f);clearCursor_=0;clearing_=false;resetSmall();}
void Movement::beginClear() noexcept {clearCursor_=0;clearing_=true;}
bool Movement::clearStep(uint32_t budget) noexcept {const std::size_t size=memory_[0].size(),total=2*size;while(budget>0&&clearCursor_<total){memory_[clearCursor_/size][clearCursor_%size]=0;--budget;++clearCursor_;}if(clearCursor_>=total){clearing_=false;resetSmall();return true;}return false;}
std::size_t Movement::allocatedBytes() const noexcept {return (memory_[0].capacity()+memory_[1].capacity())*sizeof(float);}
float Movement::read(unsigned c,double samples) const noexcept {const auto& m=memory_[c];samples=std::clamp(samples,1.,double(m.size()-2));double index=double(write_)-samples;if(index<0)index+=double(m.size());const auto i=static_cast<std::size_t>(index);const auto j=(i+1)%m.size();return float(m[i]+(index-double(i))*(double(m[j])-m[i]));}
MovementReturns Movement::processBranches(StereoFrame x) noexcept {if(clearing_||memory_[0].empty())return {};const double a=smoothCoefficient_;auto smooth=[a](double t,double& y){y=t+a*(y-t);if(std::abs(y-t)<1e-12)y=t;};smooth(parameters_[Param::DoubleEnabled],doubleWet_);smooth(parameters_[Param::ChorusEnabled],chorusWet_);
const double td[4]={parameters_[Param::DoubleDelayL],parameters_[Param::DoubleDelayR],parameters_[Param::ChorusDelay],parameters_[Param::ChorusDelay]},depth[4]={parameters_[Param::DoubleDepthL],parameters_[Param::DoubleDepthR],parameters_[Param::ChorusDepth],parameters_[Param::ChorusDepth]},rate[4]={parameters_[Param::DoubleRateL],parameters_[Param::DoubleRateR],parameters_[Param::ChorusRate],parameters_[Param::ChorusRate]};
memory_[0][write_]=std::isfinite(x.left)?x.left:0;memory_[1][write_]=std::isfinite(x.right)?x.right:0;float output[4]{};for(unsigned v=0;v<4;++v){smooth(td[v],delays_[v]);smooth(depth[v],depths_[v]);smooth(rate[v],rates_[v]);output[v]=read(v%2,(delays_[v]+depths_[v]*std::sin(phases_[v]))*rate_/1000);phases_[v]+=tau*rates_[v]/rate_;if(phases_[v]>=tau)phases_[v]-=tau;}write_=(write_+1)%memory_[0].size();return {{float(output[0]*doubleWet_),float(output[1]*doubleWet_)},{float(output[2]*chorusWet_),float(output[3]*chorusWet_)}};
}
}

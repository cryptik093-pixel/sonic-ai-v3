#include "Cleanup.h"
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <limits>
namespace adlib93 {
namespace {
double coefficient(double ms,double sr) noexcept { return std::exp(-1000.0/(std::max(.01,ms)*sr)); }
double follow(double x,double y,double a) noexcept { const double v=x+a*(y-x); return std::abs(v)<1e-30?0:v; }
double level(double x) noexcept { return 20*std::log10(std::max(x,1e-15)); }
float safe(float x) noexcept { return std::isfinite(x)?x:0.f; }
float bounded(double x) noexcept {return float(std::clamp(x,-double(std::numeric_limits<float>::max()),double(std::numeric_limits<float>::max())));}
}
void Cleanup::prepare(const PrepareSpec& s) { if(!std::isfinite(s.sampleRate)||s.sampleRate<8000||s.sampleRate>384000) throw std::invalid_argument("Cleanup sample rate"); rate_=s.sampleRate; reset(); }
void Cleanup::reset() noexcept { detector_=deessDetector_=gateDb_=deessDb_=lowL_=lowR_=0; holdRemaining_=0; open_=true; gateWet_=parameters_[Param::GateEnabled]; deessWet_=parameters_[Param::DeessEnabled]; cutoff_=parameters_[Param::DeessFrequency]>0?parameters_[Param::DeessFrequency]:6000; meters_={}; }
void Cleanup::setParameters(const ParameterSnapshot& p) noexcept { parameters_=sanitizeSnapshot(p,rate_); }
StereoFrame Cleanup::process(StereoFrame x) noexcept {
 x={safe(x.left),safe(x.right)};
 const double peak=std::max(std::abs(double(x.left)),std::abs(double(x.right)));
 // Causal peak follower: instantaneous rise, 1 ms exponential fall. Gain
 // attack/release use tau (63.2% in one tau, >99% in five tau).
 detector_=peak>detector_?peak:follow(peak,detector_,coefficient(1,rate_));
 const double db=level(detector_),threshold=parameters_[Param::GateThreshold];
 if(db>=threshold) { open_=true; holdRemaining_=static_cast<unsigned>(std::llround(parameters_[Param::GateHold]*rate_/1000)); }
 else if(db<threshold-3) { if(holdRemaining_>0) --holdRemaining_; else open_=false; }
 else if(open_) holdRemaining_=static_cast<unsigned>(std::llround(parameters_[Param::GateHold]*rate_/1000));
 const double target=open_?0:-parameters_[Param::GateAttenuation];
 gateDb_=follow(target,gateDb_,coefficient(open_?parameters_[Param::GateAttack]:parameters_[Param::GateRelease],rate_));
 gateWet_=follow(parameters_[Param::GateEnabled],gateWet_,coefficient(20,rate_));
 const double gateGain=std::pow(10.0,gateDb_*gateWet_/20);
 x={float(x.left*gateGain),float(x.right*gateGain)};
 cutoff_=std::exp(follow(std::log(parameters_[Param::DeessFrequency]),std::log(std::max(1.,cutoff_)),coefficient(20,rate_)));
 const double a=std::exp(-6.283185307179586*std::min(cutoff_,.45*rate_)/rate_);
 lowL_=follow(x.left,lowL_,a); lowR_=follow(x.right,lowR_,a);
 const double highL=double(x.left)-lowL_,highR=double(x.right)-lowR_;
 const StereoFrame high{bounded(highL),bounded(highR)};
 const double highPeak=std::max(std::abs(highL),std::abs(highR));
 deessDetector_=follow(highPeak,deessDetector_,coefficient(highPeak>deessDetector_?1:80,rate_));
 const double reduction=std::min(double(parameters_[Param::DeessMaxReduction]),std::max(0.,level(deessDetector_)-parameters_[Param::DeessThreshold])*.75);
 // Detector is attack/release smoothed; additional 1 ms gain smoothing avoids
 // a threshold corner while retaining the documented maximum reduction.
 deessDb_=follow(reduction,deessDb_,coefficient(1,rate_));
 deessWet_=follow(parameters_[Param::DeessEnabled],deessWet_,coefficient(20,rate_));
 const double gain=std::pow(10.,-deessDb_*deessWet_/20);
 meters_={float(-gateDb_*gateWet_),float(deessDb_*deessWet_),high,open_};
 // Residual formulation is exactly neutral when gain==1.
 return {bounded(x.left+(gain-1)*highL),bounded(x.right+(gain-1)*highR)};
}
}

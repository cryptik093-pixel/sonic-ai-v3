#include "Character.h"
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <limits>
namespace adlib93 {
namespace { constexpr double pi=3.14159265358979323846; double flush(double x) noexcept {return std::isfinite(x)&&std::abs(x)>=1e-30?x:0.;} }
double Character::Biquad::run(double x) noexcept { const double y=b0*x+z1; z1=flush(b1*x-a1*y+z2); z2=flush(b2*x-a2*y); return flush(y); }
void Character::Biquad::coefficients(double f,double sr,bool high) noexcept { const double w=2*pi*std::clamp(f,1.,.45*sr)/sr,c=std::cos(w),alpha=std::sin(w)/std::sqrt(2.),a0=1+alpha; b0=(1+(high?c:-c))*.5/a0; b1=(high?-(1+c):(1-c))/a0; b2=b0; a1=-2*c/a0; a2=(1-alpha)/a0; }
void Character::prepare(const PrepareSpec& s) { if(!std::isfinite(s.sampleRate)||s.sampleRate<8000||s.sampleRate>384000) throw std::invalid_argument("Character sample rate");rate_=s.sampleRate;smoothCoefficient_=std::exp(-1/(.020*rate_));dcCoefficient_=std::exp(-2*pi*10/rate_);reset(); }
void Character::setParameters(const ParameterSnapshot& p) noexcept {parameters_=sanitizeSnapshot(p,rate_);}
void Character::reset() noexcept { hp_=std::max(20.f,parameters_[Param::CharacterHp]);lp_=std::max(1000.f,parameters_[Param::CharacterLp]);drive_=parameters_[Param::CharacterDrive];trim_=parameters_[Param::CharacterTrim];wet_=parameters_[Param::CharacterEnabled];hpWet_=parameters_[Param::CharacterHpEnabled];lpWet_=parameters_[Param::CharacterLpEnabled]; weights_={0,0,0,0};weights_[std::clamp(int(parameters_[Param::CharacterMode]),0,3)]=1;hpFilters_={};lpFilters_={};dcIn_={};dcOut_={};coefficientCounter_=0; }
StereoFrame Character::process(StereoFrame in) noexcept {
 const double a=smoothCoefficient_; const auto smooth=[a](double target,double& state){state=target+a*(state-target);if(std::abs(state-target)<1e-12)state=target;};
 hp_=std::exp(std::log(parameters_[Param::CharacterHp])+a*(std::log(hp_)-std::log(parameters_[Param::CharacterHp])));
 lp_=std::exp(std::log(parameters_[Param::CharacterLp])+a*(std::log(lp_)-std::log(parameters_[Param::CharacterLp])));
 smooth(parameters_[Param::CharacterDrive],drive_);smooth(parameters_[Param::CharacterTrim],trim_);
 smooth(parameters_[Param::CharacterEnabled],wet_);smooth(parameters_[Param::CharacterHpEnabled],hpWet_);smooth(parameters_[Param::CharacterLpEnabled],lpWet_);
 if(coefficientCounter_++%16==0) for(unsigned c=0;c<2;++c){hpFilters_[c].coefficients(hp_,rate_,true);lpFilters_[c].coefficients(lp_,rate_,false);}
 const int mode=std::clamp(int(parameters_[Param::CharacterMode]),0,3);for(int m=0;m<4;++m)smooth(m==mode?1.:0.,weights_[m]);
 const double gain=std::pow(10.,drive_/20),trim=std::pow(10.,trim_/20),dc=dcCoefficient_;
 StereoFrame out{};const float input[2]={in.left,in.right};float* output[2]={&out.left,&out.right};
 for(unsigned c=0;c<2;++c){const double x=std::isfinite(input[c])?input[c]:0.;double y=x;const double h=hpFilters_[c].run(y);y+=hpWet_*(h-y);const double l=lpFilters_[c].run(y);y+=lpWet_*(l-y);double z=weights_[0]*y;const double driven=gain*y;double shaped[3]={std::tanh(driven),std::clamp(driven,-1.,1.),std::tanh(driven+.2)-std::tanh(.2)};for(unsigned m=0;m<3;++m){const double blocked=flush(shaped[m]-dcIn_[m][c]+dc*dcOut_[m][c]);dcIn_[m][c]=shaped[m];dcOut_[m][c]=blocked;z+=weights_[m+1]*blocked;}*output[c]=float(std::clamp(x+wet_*(z*trim-x),-double(std::numeric_limits<float>::max()),double(std::numeric_limits<float>::max())));}
 return out;
}
}

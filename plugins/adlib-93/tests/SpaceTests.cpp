#include "TestSupport.h"
#include "dsp/Space.h"
#include <algorithm>
#include <cmath>
#include <iostream>
#include <vector>
using namespace adlib93;
namespace {
// Offline measurement only: constant-peak-gain second-order bandpass at
// f0=1000 Hz, Q=sqrt(2) (nominal one-octave bandwidth). With w=2*pi*f0/Fs,
// alpha=sin(w)/(2Q): b=(alpha,0,-alpha)/(1+alpha),
// a=(1,-2*cos(w)/(1+alpha),(1-alpha)/(1+alpha)).
// Reference: W3C Audio EQ Cookbook (2021-06-08), BPF, 0 dB peak gain:
// https://www.w3.org/TR/audio-eq-cookbook/ . Digital warping means this is
// a nominal octave analysis band, not an octave-filter certification.
// This independent analysis filter excludes intentional high-frequency
// damping from the specification's mid-band RT60 acceptance measurement.
struct MidbandAnalysis {
 double b0,b2,a1,a2,z1[2]{},z2[2]{};
 explicit MidbandAnalysis(double rate){const double w=6.283185307179586*1000/rate,alpha=std::sin(w)/(2*std::sqrt(2.)),denominator=1+alpha;b0=alpha/denominator;b2=-b0;a1=-2*std::cos(w)/denominator;a2=(1-alpha)/denominator;}
 double process(double x,unsigned channel){const double y=b0*x+z1[channel];z1[channel]=-a1*y+z2[channel];z2[channel]=b2*x-a2*y;return y;}
};
double schroederRt60(std::vector<double>& energy,double rate){
 for(size_t n=energy.size()-1;n>0;--n)energy[n-1]+=energy[n];
 if(energy[0]<=0)return 0;
 size_t minus5=0,minus25=0;
 for(size_t n=0;n<energy.size();++n){const double db=10*std::log10(std::max(energy[n]/energy[0],1.e-30));if(!minus5&&db<=-5)minus5=n;if(!minus25&&db<=-25){minus25=n;break;}}
 return minus25>minus5?3.*(minus25-minus5)/rate:0;
}
}
TEST_CASE("Space.Decay") {
 // Schroeder T20 extrapolation to RT60, 1 kHz mid-band, damping open, no
 // limiter. Retain broadband values to expose frequency-dependent decay.
 bool allWithinTolerance=true;
 for(double rate:{44100.,48000.,88200.,96000.})for(float target:{.5f,2.f,6.f,12.f}){
  Space room;room.prepare({rate,128,ChannelLayout::stereoStereo});auto p=makeInitSnapshot();p[Param::ReverbEnabled]=1;p[Param::ReverbPredelay]=0;p[Param::ReverbDecay]=target;p[Param::ReverbDamping]=20000;room.setParameters(p);
  const size_t count=static_cast<size_t>(rate*(target*1.4+1));std::vector<double> energy(count),midband(count);MidbandAnalysis analysis(rate);
  for(size_t n=0;n<count;++n){const auto y=room.process(n==0?StereoFrame{1,0}:StereoFrame{},{},{}).reverb;energy[n]=static_cast<double>(y.left)*y.left+static_cast<double>(y.right)*y.right;const double left=analysis.process(y.left,0),right=analysis.process(y.right,1);midband[n]=left*left+right*right;require(std::isfinite(energy[n])&&std::isfinite(midband[n]),"finite reverb and mid-band energy");}
  const double broadband=schroederRt60(energy,rate),measured=schroederRt60(midband,rate);require(energy[0]>.001,"reverb emits impulse energy");
  require(broadband>0&&measured>0,"decay crosses measurement interval");
  const bool accepted=std::abs(measured-target)<=target*.25;allWithinTolerance=allWithinTolerance&&accepted;
  std::cout<<"Space.Decay sampleRate="<<rate<<" targetSeconds="<<target<<" midbandSeconds="<<measured<<" broadbandSeconds="<<broadband<<" impulseEnergy="<<energy[0]<<" within25Percent="<<accepted<<'\n';
  require(room.maximumState()<1,"normalized FDN input and feedback bounded");
 }
 require(allWithinTolerance,"open damping mid-band RT60 within 25 percent for all targets and rates");
}
TEST_CASE("Space.Duck") {
 Space room;room.prepare({});auto p=makeInitSnapshot();p[Param::DuckEnabled]=1;p[Param::DuckMaxReduction]=12;p[Param::DuckAttack]=5;p[Param::DuckRelease]=100;room.setParameters(p);
 float settled=1;for(int n=0;n<4800;++n){const auto y=room.process({},{},{1,.1f});require(y.duckGain>=std::pow(10.f,-12.2f/20),"duck maximum bounded");settled=y.duckGain;}
 require(std::abs(20*std::log10(settled)+12)<.02,"duck settles at configured maximum");
 float previous=settled;for(int n=0;n<48000;++n){const auto y=room.process({},{},{});require(y.duckGain>=previous-1.e-7f,"duck release monotonic");previous=y.duckGain;}require(previous>.999,"duck releases to unity");
 // Detector is independent from reverb excitation and feedback.
 Space loud,quiet;loud.prepare({});quiet.prepare({});p[Param::ReverbEnabled]=1;loud.setParameters(p);quiet.setParameters(p);
 for(int n=0;n<24000;++n){const StereoFrame input=n==0?StereoFrame{1,0}:StereoFrame{};const auto a=loud.process(input,{},{1,1}),b=quiet.process(input,{},{});require(a.reverb.left==b.reverb.left&&a.reverb.right==b.reverb.right,"duck detection cannot alter network feedback");}
}
TEST_CASE("Space.Stereo") {
 for(double rate:{44100.,48000.,88200.,96000.}){
 Space room;room.prepare({rate,1,ChannelLayout::stereoStereo});auto p=makeInitSnapshot();p[Param::ReverbEnabled]=1;p[Param::ReverbDecay]=12;room.setParameters(p);double left=0,right=0,difference=0;
 for(int n=0;n<int(rate);++n){const auto y=room.process(n==0?StereoFrame{1,0}:StereoFrame{},{},{}).reverb;left+=y.left*y.left;right+=y.right*y.right;difference+=std::abs(y.left-y.right);}
 std::cout<<"Space.Stereo sampleRate="<<rate<<" leftEnergy="<<left<<" rightEnergy="<<right<<" absoluteDifference="<<difference<<'\n';
 require(left>.001&&right>.001&&difference>.01,"one input channel excites nonidentical stereo returns");
 room.beginClear();require(!room.clearStep(0),"zero clear budget");size_t steps=0;while(!room.clearStep(63))require(++steps<10000,"bounded space clear");room.setParameters(p);
 for(int n=0;n<10000;++n){const auto y=room.process({},{},{}).reverb;require(y.left==0&&y.right==0,"cleared FDN silent");}
 }
}
TEST_CASE("Space.Injection") {
 for(double rate:{44100.,48000.,88200.,96000.})for(unsigned channel=0;channel<2;++channel){
  Space room;room.prepare({rate,128,ChannelLayout::stereoStereo});auto p=makeInitSnapshot();p[Param::ReverbEnabled]=1;p[Param::ReverbPredelay]=0;room.setParameters(p);
  const int first=int(std::lround(.0297*rate));
  for(int n=0;n<=first;++n){
   const auto input=n==0?(channel==0?StereoFrame{1,0}:StereoFrame{0,1}):StereoFrame{};
   const auto y=room.process(input,{},{}).reverb;
   if(n==0)require(std::abs(room.maximumState()-.25f)<1e-6f,"finite feedback initialization preserves normalized FDN impulse injection");
   if(n<first)require(y.left==0&&y.right==0,"FDN has no hidden direct output before its first line");
   else {const double expected=.25/std::sqrt(8.);require(std::abs(y.left-expected)<1e-6&&std::abs(y.right-expected)<1e-6,"first FDN return follows approved normalized input and output vectors");}
  }
 }
}

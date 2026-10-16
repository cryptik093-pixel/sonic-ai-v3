#include "TestSupport.h"
#include "dsp/Echo.h"
#include <algorithm>
#include <cmath>
using namespace adlib93;
namespace {
ParameterSnapshot echoParameters(){auto p=makeInitSnapshot();p[Param::DelayEnabled]=1;p[Param::DelayTime]=20;p[Param::DelayHp]=20;p[Param::DelayLp]=20000;return p;}
}
TEST_CASE("Echo.Impulse") {
 for(double rate:{44100.,48000.,88200.,96000.}){
  Echo echo;echo.prepare({rate,128,ChannelLayout::stereoStereo});auto p=echoParameters();echo.setParameters(p);
  int first=-1;float peak=0;
  for(int n=0;n<static_cast<int>(rate*.05);++n){const auto y=echo.process(n==0?StereoFrame{1,.5f}:StereoFrame{},0);if(first<0&&std::abs(y.left)>1.e-9f)first=n;peak=std::max(peak,std::abs(y.left));require(std::isfinite(y.right),"finite echo");}
  require(std::abs(first-static_cast<int>(std::lround(rate*.020)))<=1,"first echo within one sample");require(peak>.1f,"real audible echo");
 }
 Echo a,b;a.prepare({});b.prepare({});auto p=echoParameters();a.setParameters(p);p[Param::DelayDiffusion]=.85f;b.setParameters(p);double difference=0;
 for(int n=0;n<6000;++n){const StereoFrame in=n==0?StereoFrame{1,1}:StereoFrame{};const auto x=a.process(in,0),y=b.process(in,0);difference+=std::abs(x.left-y.left);}
 require(difference>.1,"diffusion changes audible first return with zero feedback");
}
TEST_CASE("Echo.PingPong") {
 Echo echo;echo.prepare({});auto p=echoParameters();p[Param::DelayFeedback]=.5f;p[Param::DelayPingpong]=1;echo.setParameters(p);
 double energy[4][2]{};
 for(int n=0;n<4800;++n){const auto y=echo.process(n==0?StereoFrame{.2f,.2f}:StereoFrame{},0);for(int repeat=0;repeat<4;++repeat)if(n>=960*(repeat+1)&&n<960*(repeat+1)+120){energy[repeat][0]+=y.left*y.left;energy[repeat][1]+=y.right*y.right;}}
 for(int i=0;i<4;++i)require(energy[i][i%2]>10*energy[i][1-i%2]+1.e-10,"mono ping-pong alternating dominant channels");
 Echo stereo;stereo.prepare({});p[Param::DelayPingpong]=0;p[Param::DelayFeedback]=0;stereo.setParameters(p);
 for(int n=0;n<2000;++n){const auto y=stereo.process(n==0?StereoFrame{1,0}:StereoFrame{},0);require(y.right==0,"independent stereo injection at zero ping-pong");}
}
TEST_CASE("Echo.Throw") {
 Echo quiet,normal,boost;quiet.prepare({});normal.prepare({});boost.prepare({});auto p=echoParameters();p[Param::DelayThrowMode]=1;quiet.setParameters(p);p[Param::DelayThrowMode]=0;normal.setParameters(p);boost.setParameters(p);
 for(int n=0;n<300;++n){quiet.process({},0);normal.process({},0);boost.process({},1);}
 double ratio=0;bool seen=false;
 for(int n=0;n<2000;++n){const StereoFrame input=n==0?StereoFrame{.1f,.1f}:StereoFrame{};const auto a=quiet.process(input,0),b=normal.process(input,0),c=boost.process(input,1);require(a.left==0&&a.right==0,"throw-only closed input is silent");if(std::abs(b.left)>.001){ratio=c.left/b.left;seen=true;}}
 require(seen&&std::abs(ratio-std::pow(10.,6./20))<.0001,"continuous Throw exactly +6dB settled injection");
 Echo gated;gated.prepare({});p[Param::DelayThrowMode]=1;p[Param::DelayFeedback]=.4f;gated.setParameters(p);for(int n=0;n<300;++n)gated.process({},1);
 float afterRelease=0;for(int n=0;n<4000;++n){const auto y=gated.process(n==0?StereoFrame{.2f,.2f}:StereoFrame{},n<10?1.f:0.f);if(n>1500)afterRelease=std::max(afterRelease,std::abs(y.left));}require(afterRelease>.001,"throw release preserves existing repeats");
}
TEST_CASE("Echo.Stability") {
 for(float diffuse:{0.f,1.f})for(float ping:{0.f,1.f}){
  Echo echo;echo.prepare({});auto p=echoParameters();p[Param::DelayFeedback]=.9f;p[Param::DelayDiffusion]=diffuse;p[Param::DelayPingpong]=ping;p[Param::DelayTime]=10;echo.setParameters(p);
  for(int n=0;n<96000;++n){if(n%997==0){p[Param::DelayTime]=10+static_cast<float>((n/997)%19)*83;echo.setParameters(p);}const auto y=echo.process(n<1000?StereoFrame{10,-8}:StereoFrame{},n%200<100?1.f:0.f);require(std::isfinite(y.left)&&std::isfinite(y.right),"finite max feedback retargets");require(std::abs(y.left)<100&&std::abs(y.right)<100,"bounded un-limited internal return");}
  require(echo.maximumState()<30,"bounded internal feedback storage");echo.beginClear();require(!echo.clearStep(0),"zero budget performs no clearing");unsigned steps=0;while(!echo.clearStep(127)){require(++steps<10000,"bounded clearing completes");}echo.setParameters(p);for(int n=0;n<10000;++n){const auto y=echo.process({},0);require(y.left==0&&y.right==0,"cleared echo silent");}
 }
}

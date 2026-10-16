#include "TestSupport.h"
#include "dsp/AdlibEngine.h"
#include <array>
#include <cmath>
#include <vector>
using namespace adlib93;
namespace {ParameterSnapshot neutral(){auto p=makeInitSnapshot();p[Param::LimiterEnabled]=0;return p;}}
TEST_CASE("Routing.Identity") {
 for(double rate:{44100.,48000.,88200.,96000.})for(float mix:{0.f,.25f,.5f,.75f,1.f}){
  auto p=neutral();p[Param::MixAmount]=mix;AdlibEngine engine;engine.prepare({rate,128,ChannelLayout::stereoStereo},p);
  for(unsigned n=0;n<8192;++n){const StereoFrame x{.4f*std::sin(n*.131f),.3f*std::cos(n*.073f)};const auto y=engine.process(x);require(std::abs(y.left-x.left)<=1.e-6f&&std::abs(y.right-x.right)<=1.e-6f,"neutral linear blend must remain unity");}
 }
}
TEST_CASE("Routing.Layouts") {
 auto p=neutral();
 for(auto layout:{ChannelLayout::monoMono,ChannelLayout::monoStereo,ChannelLayout::stereoStereo}){
  AdlibEngine engine;engine.prepare({48000,128,layout},p);const auto y=engine.process({.3f,-.1f});
  require(std::abs(y.left-.3f)<1.e-6f,"left identity");require(std::abs(y.right-(layout==ChannelLayout::stereoStereo?-.1f:.3f))<1.e-6f,"mono duplicated at unity");
 }
 bool rejected=false;try{AdlibEngine engine;engine.prepare({48000,128,static_cast<ChannelLayout>(99)},p);}catch(...){rejected=true;}require(rejected,"unsupported channel layout rejected");
 p[Param::StereoWidth]=0;AdlibEngine monoWidth;monoWidth.prepare({48000,128,ChannelLayout::stereoStereo},p);const auto y=monoWidth.process({.3f,-.1f});require(std::abs(y.left-.1f)<1.e-6f&&std::abs(y.right-.1f)<1.e-6f,"single wet width stage uses arithmetic mid");
}
TEST_CASE("Routing.Blocks") {
 const auto p=neutral();
 for(auto layout:{ChannelLayout::monoMono,ChannelLayout::monoStereo,ChannelLayout::stereoStereo}){
  AdlibEngine engine;engine.prepare({48000,128,layout},p);engine.process(nullptr,nullptr,0,p,{});
  for(uint32_t count:{0u,1u,17u,128u,4097u}){
   std::vector<float> left(count+2,.123f),right(count+2,-.234f);const float* input[]={left.data()+1,right.data()+1};float* output[]={left.data()+1,right.data()+1};
   engine.process(input,output,count,p,{});
   require(left.front()==.123f&&left.back()==.123f&&right.front()==-.234f&&right.back()==-.234f,"arbitrary block cannot overwrite guard samples");
   for(uint32_t n=1;n<=count;++n){require(left[n]==.123f,"in-place left identity");require(right[n]==(layout==ChannelLayout::monoStereo?.123f:-.234f),"in-place stereo/mono output contract");}
  }
 }
}
TEST_CASE("Routing.SendBypass") {
 auto p=neutral();p[Param::RoutingMode]=1;p[Param::MixAmount]=.25f;
 AdlibEngine engine;engine.prepare({48000,128,ChannelLayout::stereoStereo},p);
 auto y=engine.process({.25f,-.2f});require(y.left==0&&y.right==0,"send overrides direct without dry leakage");
 engine.setBypassed(true);for(int n=0;n<4800;++n){y=engine.process({.25f,-.2f});require(y.left==0&&y.right==0,"send bypass cannot introduce dry vocal");}
 require(engine.parameters()[Param::MixAmount]==.25f&&engine.parameters()[Param::DirectLevel]==1,"send overrides preserve stored insert values");
 engine.setBypassed(false);p[Param::RoutingMode]=0;engine.setParameters(p);for(int n=0;n<4800;++n)y=engine.process({.25f,-.2f});require(std::abs(y.left-.25f)<1.e-6f,"returning insert restores unity blend");
 p[Param::DirectLevel]=0;engine.setParameters(p);engine.setBypassed(true);for(int n=0;n<4800;++n)y=engine.process({.25f,-.2f});require(std::abs(y.left-.25f)<1.e-6f,"insert bypass returns trimmed dry even with direct muted");
}
TEST_CASE("Routing.ListenAndDuck") {
 auto p=neutral();p[Param::DeessListen]=1;p[Param::MixAmount]=0;AdlibEngine engine;engine.prepare({48000,128,ChannelLayout::stereoStereo},p);
 Cleanup reference;reference.prepare({48000,128,ChannelLayout::stereoStereo});reference.setParameters(p);
 for(int n=0;n<2048;++n){const StereoFrame x{.25f*std::sin(n*.9f),-.17f*std::cos(n*.7f)};reference.process(x);const auto high=reference.highBand(),y=engine.process(x);require(std::abs(y.left-high.left)<1.e-6f&&std::abs(y.right-high.right)<1.e-6f,"listen overrides dry/mix with detector high band through output stage");}
 p=neutral();p[Param::DuckEnabled]=1;p[Param::DuckMaxReduction]=18;engine.prepare({48000,128,ChannelLayout::stereoStereo},p);
 for(int n=0;n<4096;++n){const auto y=engine.process({.5f,-.25f});require(std::abs(y.left-.5f)<1.e-6f&&std::abs(y.right+.25f)<1.e-6f,"duck cannot attenuate direct voice");}
}

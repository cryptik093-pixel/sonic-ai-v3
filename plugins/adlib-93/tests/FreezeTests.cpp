#include "TestSupport.h"
#include "dsp/Freeze.h"
#include <algorithm>
#include <cmath>
using namespace adlib93;
TEST_CASE("Performance.Freeze") {
 Freeze hold;hold.prepare({});
 for(int n=0;n<20000;++n){const auto y=hold.process({},true);require(y.left==0&&y.right==0,"freeze silence stays silent");}require(hold.suppressesExcitation(),"held freeze suppresses new excitation");
 hold.reset();
 for(int n=0;n<12000;++n)hold.process({.25f,-.125f},false);
 for(int n=0;n<2400;++n){const auto y=hold.process({},true);require(std::abs(y.left)<=.250001f,"capture crossfade cannot grow");if(n==2398)require(hold.blend()<1,"50ms attack not prematurely complete");}
 require(hold.blend()==1,"50ms capture fade complete within one sample");
 for(int n=0;n<48000*60;++n){const auto y=hold.process({},true);require(std::abs(y.left-.25f)<1.e-6f&&std::abs(y.right+.125f)<1.e-6f,"immutable unity texture holds for 60 seconds");}
 for(int n=0;n<12000;++n){hold.process({},false);require(!hold.suppressesExcitation(),"release resumes normal excitation");if(n==11998)require(hold.blend()>0,"250ms release not prematurely complete");}require(hold.blend()==0,"250ms release complete within one sample");
 for(int n=0;n<12000;++n)hold.process({},false);
 for(int n=0;n<3000;++n){const auto y=hold.process({},true);require(y.left==0&&y.right==0,"new capture excludes previously frozen layer");}
 hold.beginClear();require(!hold.clearStep(0),"freeze zero write budget");size_t count=0;while(!hold.clearStep(1))require(++count<=48000,"one-float budget must clear four history channels");require(count==47999,"clearStep honors total float budget across all histories");
 const auto y=hold.process({},true);require(y.left==0&&y.right==0,"freeze clear releases captured audio");require(hold.allocatedBytes()==48000*sizeof(float),"two stereo 250ms histories allocated only during prepare");
}
TEST_CASE("Performance.FreezeOverlap") {
 Freeze hold;hold.prepare({});for(int n=0;n<12000;++n){const float x=std::sin(static_cast<float>(n)*.007f)*.4f;hold.process({x,-x},false);}
 float max=0;for(int n=0;n<96000;++n){const auto y=hold.process({},true);max=std::max(max,std::abs(y.left));require(std::isfinite(y.left)&&std::abs(y.left+y.right)<1.e-6f,"complementary overlap preserves stereo relation");}require(max<=.400001f&&max>.3f,"overlap weights convex without growth");
}
TEST_CASE("Performance.FreezeRetrigger") {
 Freeze hold;hold.prepare({});for(int n=0;n<12000;++n)hold.process({.2f,.2f},false);
 hold.process({},true);hold.process({},false);for(int n=0;n<3000;++n)hold.process({},true);
 const auto reused=hold.process({},true);require(std::abs(reused.left-.2f)<1.e-6f,"rapid re-trigger reuses complete window instead of stale partial spare");
 for(int n=0;n<12000;++n)hold.process({},false);for(int n=0;n<2500;++n)hold.process({},true);
 const auto fresh=hold.process({},true);require(fresh.left==0&&fresh.right==0,"fresh full rolling window replaces old texture");
}
TEST_CASE("Performance.FreezeRetriggerContinuity") {
 // Exercise both a partially refreshed spare and a complete spare after a
 // prolonged hold. Neither may replace an audible held voice on re-trigger.
 for(int heldSamples:{5000,20000}){
  Freeze hold;hold.prepare({});
  for(int n=0;n<12000;++n){const float x=float(.4*std::sin(n*.007));hold.process({x,-x},false);}
  StereoFrame previous{};
  for(int n=0;n<heldSamples;++n)previous=hold.process({},true);
  const auto released=hold.process({},false);
  require(std::abs(released.left-previous.left)<.01f,"release starts continuously on nonconstant held audio");
  previous=released;
  for(int n=0;n<2400;++n){const auto current=hold.process({},true);require(std::abs(current.left-previous.left)<.01f,"rapid re-trigger preserves held playhead and immutable voice");previous=current;}
  require(hold.blend()==1,"re-trigger preserves the 50 ms fade duration");
 }
}

#include "TestSupport.h"
#include "dsp/Transitions.h"
#include <cmath>
using namespace adlib93;
TEST_CASE("Performance.LongFreezeRelease") {
 auto p=makeInitSnapshot();p[Param::LimiterEnabled]=0;p[Param::DirectLevel]=0;p[Param::DelayEnabled]=1;p[Param::DelayTime]=10;p[Param::DelayLevel]=1;
 AdlibEngine engine;engine.prepare({8000,128,ChannelLayout::stereoStereo},p);
 for(unsigned n=0;n<8000;++n){const float x=.25f*std::sin(n*.7853981633974483f);engine.process({x,x});}
 p[Param::FreezeActive]=1;engine.setParameters(p);float held=0;
 for(unsigned n=0;n<181u*8000u;++n){const auto y=engine.process({});held=std::max(held,std::abs(y.left));}
 require(held>.01f,"held texture actually captured audible signal");
 p[Param::FreezeActive]=0;engine.setParameters(p);double firstHalfEnergy=0;float remaining=0;
 for(unsigned n=0;n<2400;++n){const auto y=engine.process({});if(n<1000)firstHalfEnergy+=static_cast<double>(y.left)*y.left;if(n>=2000)remaining=std::max(remaining,std::abs(y.left));}
 require(firstHalfEnergy>.01,"long-held Freeze must keep its 250ms release instead of being cleared at 180s");
 require(remaining<1.e-5f,"frozen voice is gone after full 250ms release");
}
TEST_CASE("Performance.PendingAutomation") {
 auto old=makeInitSnapshot();old[Param::LimiterEnabled]=0;Transitions engine;engine.prepare({48000,128,ChannelLayout::stereoStereo},old);
 auto next=old;next[Param::RoutingMode]=1;next[Param::DirectLevel]=0;engine.request(next);engine.setParameters(next);
 for(unsigned n=0;n<500;++n){const auto y=engine.process({.25f,-.125f});require(std::abs(y.left-.25f)<1.e-6f&&std::abs(y.right+.125f)<1.e-6f,"pending preset must not overwrite audible old engine before incoming preparation");}
 require(engine.measurements().transitioning,"incoming engine still being prepared within bounded work budget");
}
TEST_CASE("Performance.Switches") {
 auto initial=makeInitSnapshot();initial[Param::LimiterEnabled]=0;Transitions engine;engine.prepare({48000,128,ChannelLayout::stereoStereo},initial);
 auto target=initial;target[Param::DirectLevel]=0;target[Param::MixAmount]=1;target[Param::ThrowActive]=target[Param::FreezeActive]=1;
 engine.request(target);float previous=.25f;bool observed=false;unsigned fadeSamples=0;
 for(unsigned n=0;n<100000;++n){const bool before=engine.measurements().transitioning;const auto y=engine.process({.25f,.25f});require(std::isfinite(y.left)&&std::abs(y.left-previous)<.001f,"preset switching is finite with bounded linear crossfade");require(engine.maxClearWritesLastFrame()<=256,"aggregate per-frame clearing budget");previous=y.left;const auto m=engine.measurements();if(before&&m.transitioning&&engine.maxClearWritesLastFrame()==0)++fadeSamples;if(m.transitioning)observed=true;if(observed&&!m.transitioning){require(std::abs(y.left)<1.e-6f,"completed incoming preset is audible");require(!m.freezeHeld,"preset load releases freeze");break;}}
 require(observed,"preset transition actually started");require(fadeSamples>=2398&&fadeSamples<=2400,"50ms preset fade has required sample count");
 for(unsigned n=0;n<1000;++n){target[Param::MixAmount]=static_cast<float>(n%101)/100;engine.request(target);engine.serviceZeroBlock();require(engine.maxClearWritesLastFrame()<=64,"zero-block clearing budget");}
 for(unsigned n=0;n<20000;++n){const auto y=engine.process({.1f,-.1f});require(std::isfinite(y.left)&&std::isfinite(y.right),"rapid requests coalesce without instability");}
 require(!engine.measurements().transitioning,"latest rapid request completes");
}
TEST_CASE("Performance.Clear") {
 auto p=makeInitSnapshot();p[Param::LimiterEnabled]=0;p[Param::DelayEnabled]=1;p[Param::DelayTime]=10;p[Param::DelayFeedback]=.8f;p[Param::DelayLevel]=1;
 Transitions engine;engine.prepare({48000,128,ChannelLayout::stereoStereo},p);
 for(unsigned n=0;n<4800;++n)engine.process({.2f*std::sin(n*.2f),.2f*std::sin(n*.2f)});
 engine.clearTails();bool observed=false;unsigned duration=0;
 for(unsigned n=0;n<20000;++n){const auto y=engine.process({});const auto m=engine.measurements();require(std::isfinite(y.left)&&std::isfinite(y.right),"clear remains finite");require(engine.maxClearWritesLastFrame()<=256,"clear budget bounded");if(m.clearing){observed=true;++duration;}if(observed&&!m.clearing)break;}
 require(observed&&duration>=1920,"clear includes 20ms fade-out and fade-in plus bounded zeroing");
 for(unsigned n=0;n<4800;++n){const auto y=engine.process({});require(std::abs(y.left)<1.e-6f&&std::abs(y.right)<1.e-6f,"cleared tail cannot reappear");}
 require(engine.allocatedBytes()<=64u*1024u*1024u,"two-engine DSP buffer budget");
}

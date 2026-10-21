#include "DrumEngine.h"
// Test-only golden source: never linked into the instrument.
#define ohdrum ohlegacy
#include "../legacy/0.1.0/Source/DrumEngine.h"
#undef ohdrum
#include <iostream>
#include <cstdlib>
#include <limits>
#include <numeric>
#include <vector>
void check(bool x,const char* m){if(!x){std::cerr<<"FAIL "<<m<<'\n';std::exit(1);}}
using Controls=std::array<ohdrum::SlotControls,8>;
Controls defaults(){Controls c{};for(size_t i=0;i<8;++i){c[i].note=static_cast<float>(ohdrum::defaultNotes[i]);c[i].choke=(i==2||i==7)?1.0f:0.0f;}return c;}
std::vector<float> render(int slot,Controls c,float velocity=.8f,double rate=48000){ohdrum::Engine e;e.setSlotControls(c,-6);e.prepare(rate,{.5f,.5f,0});e.triggerSlot(slot,velocity);std::vector<float> a(static_cast<size_t>(rate));for(auto& x:a){const auto o=e.tick();check(std::isfinite(o[0])&&std::isfinite(o[1])&&std::abs(o[0])<=.98f&&std::abs(o[1])<=.98f,"finite protected stereo");x=o[0];}return a;}
double energy(const std::vector<float>& a){return std::inner_product(a.begin(),a.end(),a.begin(),0.0);}
int main(){
 for(int slot=0;slot<7;++slot){auto c=defaults();for(auto& sc:c){sc.gain=0;sc.choke=0;}ohlegacy::Engine legacy;ohdrum::Engine current;legacy.prepare(48000);current.setSlotControls(c,0);current.prepare(48000);legacy.trigger(slot,.8f,45);current.triggerSlot(slot,.8f,45);float error=0;for(int i=0;i<48000;++i){if(i==2000||i==2100){legacy.trigger(slot,.8f,45);current.triggerSlot(slot,.8f,45);}const auto a=legacy.tick(),b=current.tick();error=std::max(error,std::max(std::abs(a[0]-b[0]),std::abs(a[1]-b[1])));}check(error<1.e-6f,"original seven synthesis maps retained at neutral/unity controls");}
 int scenarios=0;for(double rate:{44100.,48000.,96000.})for(int slot=0;slot<8;++slot){auto c=defaults();const auto base=render(slot,c,.8f,rate);check(energy(base)>.0001,"each synthesis slot audible without samples");auto quiet=render(slot,c,.2f,rate);check(energy(quiet)<energy(base)*.2,"velocity amplitude");
 for(int macro=0;macro<3;++macro){auto lo=c,hi=c;if(macro==0){lo[slot].punch=0;hi[slot].punch=1;}if(macro==1){lo[slot].tone=0;hi[slot].tone=1;}if(macro==2){lo[slot].texture=0;hi[slot].texture=1;}const auto a=render(slot,lo,.8f,rate),b=render(slot,hi,.8f,rate);double diff=0;for(size_t i=0;i<a.size();++i)diff+=std::abs(a[i]-b[i]);check(diff>.001,"each per-slot macro measurably changes audio");++scenarios;}
 c[slot].mute=1;check(energy(render(slot,c,.8f,rate))==0,"slot mute");c=defaults();c[(slot+1)%8].solo=1;check(energy(render(slot,c,.8f,rate))==0,"other solo excludes slot");c=defaults();c[slot].pan=1;check(energy(render(slot,c,.8f,rate))==0,"hard right clears left");
 for(bool maximum:{false,true}){c=defaults();auto& p=c[slot];p.punch=p.tone=p.texture=maximum?1:0;p.decay=maximum?3:.1f;p.tune=maximum?24:-24;p.pitchDepth=maximum?2:0;p.pitchTime=maximum?200:2;p.gain=12;p.filter=maximum?20000:40;render(slot,c,1,rate);++scenarios;}}
 ohdrum::Engine e;auto c=defaults();e.setSlotControls(c,0);e.prepare(48000,{.5f,.5f,0});for(int i=0;i<100;++i)check(e.tick()==std::array<float,2>{0,0},"initial exact silence");e.triggerSlot(7,1);for(int i=0;i<400;++i)e.tick();e.triggerSlot(2,1);double tail=0;for(int i=0;i<48000;++i){const auto a=e.tick();if(i>40000)tail+=a[0]*a[0];}check(tail<1.e-6,"closed hat chokes open hat");
 c[0].choke=2;c[1].choke=2;e.setSlotControls(c,0);e.prepare(48000,{.5f,.5f,0});e.triggerSlot(0,1);e.panic(false);for(int i=0;i<200;++i)e.tick();check(e.tick()==std::array<float,2>{0,0},"bounded panic fade");for(int v=0;v<100;++v)e.triggerSlot(v%8,1);for(int i=0;i<48000;++i){const auto o=e.tick();check(std::isfinite(o[0]),"bounded stealing");}e.panic(true);check(e.tick()==std::array<float,2>{0,0},"immediate panic clears tails");
 c[0].tone=std::numeric_limits<float>::quiet_NaN();c[0].gain=std::numeric_limits<float>::infinity();render(0,c);std::cout<<"PASS synthesis: "<<scenarios<<" macro/extreme scenarios; original seven-map neutral regression, eight dry voices, rates, velocity, mute/solo, pan, hats, panic and finite guard\n";}

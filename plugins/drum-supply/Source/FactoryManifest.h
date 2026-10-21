#pragma once
#include "DrumEngine.h"
namespace ohdrum {
inline constexpr std::array<const char*,6> factoryNames{"Factory Synthesis","Hip-Hop Foundation","Boom-Bap Room","Trap Circuit","Electronic Pulse","Experimental Foundry"};
inline float factorySpace(int profile) noexcept {constexpr std::array<float,6> values{.25f,.1f,.4f,.12f,.28f,.8f};return values[static_cast<size_t>(std::clamp(profile,0,5))];}
inline std::array<SlotControls,8> factoryControls(int profile) noexcept {
 std::array<SlotControls,8> c{};for(size_t s=0;s<8;++s){c[s].note=static_cast<float>(defaultNotes[s]);c[s].choke=s==2||s==7?1.0f:0.0f;}
 auto macros=[&](int s,float p,float t,float x,float decay){auto& a=c[static_cast<size_t>(s)];a.punch=p;a.tone=t;a.texture=x;a.decay=decay;};
 switch(profile){
 case 1:for(auto& a:c){a.punch=.72f;a.tone=.4f;a.texture=.6f;}macros(0,.82f,.25f,.55f,1.25f);c[0].tune=-2;macros(1,.78f,.42f,.65f,.9f);c[2].decay=.45f;c[7].decay=1.2f;c[5].pan=-.15f;break;
 case 2:for(auto& a:c){a.punch=.65f;a.tone=.3f;a.texture=.72f;a.tune=-1;a.filter=12000;}macros(0,.65f,.2f,.72f,.8f);c[0].tune=-3;c[0].filter=4500;macros(1,.82f,.3f,.8f,.8f);macros(6,.6f,.28f,.68f,.8f);c[2].decay=.4f;c[7].decay=.75f;c[5].pan=.15f;break;
 case 3:macros(0,.8f,.1f,.35f,2.1f);c[0].tune=-5;c[0].pitchDepth=.7f;macros(1,.72f,.75f,.85f,.5f);macros(2,.7f,.85f,.8f,.22f);macros(7,.6f,.8f,.82f,.65f);macros(3,.65f,.75f,.8f,.7f);c[3].pan=.18f;macros(6,.8f,.6f,.85f,.65f);macros(4,.7f,.35f,.55f,.7f);macros(5,.75f,.75f,.85f,.5f);break;
 case 4:for(size_t s=0;s<8;++s){auto& a=c[s];a.punch=.9f;a.tone=.65f;a.texture=.65f;a.decay=.65f;a.pitchDepth=1.4f;a.pitchTime=12;a.pan=s==0||s==1?0:(s%2?.2f:-.2f);}c[0].tune=3;c[0].tone=.55f;c[0].texture=.7f;c[5].texture=.92f;break;
 case 5:for(size_t s=0;s<8;++s){auto& a=c[s];a.punch=.55f;a.tone=.13f+static_cast<float>(s)*.1f;a.texture=.94f;a.decay=1.7f;a.tune=static_cast<float>(static_cast<int>(s%3)-1)*9;a.pitchDepth=1.8f;a.pitchTime=100;a.filter=s==0?5000.0f:14000.0f;a.pan=s==0?0:(s%2?.35f:-.35f);a.gain=-10;}break;
 default:break;
 }return c;
}
}

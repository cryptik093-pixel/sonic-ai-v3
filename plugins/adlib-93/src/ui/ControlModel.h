#pragma once
#include "core/Parameters.h"
#include <array>
namespace adlib93::ui {
enum class BrowserAction { navigation, pointerActivation, confirm };
inline bool shouldLoadPreset(BrowserAction action,bool clearing) noexcept { return !clearing&&action!=BrowserAction::navigation; }
inline constexpr std::array<Param,10> mainParameters{{Param::GateThreshold,Param::DeessMaxReduction,Param::CharacterDrive,Param::DoubleLevel,Param::DelayLevel,Param::DelayDiffusion,Param::ReverbLevel,Param::DuckMaxReduction,Param::MixAmount,Param::OutputGain}};
inline constexpr std::array<int,10> mainPages{{0,0,1,2,3,3,4,4,5,5}};
inline bool controlEnabled(Param p,const ParameterSnapshot& s) noexcept {if((p==Param::MixAmount||p==Param::DirectLevel)&&s[Param::RoutingMode]>.5f)return false;if(p==Param::CharacterDrive&&s[Param::CharacterMode]<.5f)return false;return true;}
inline float effectiveValue(Param p,const ParameterSnapshot& s) noexcept {if(s[Param::RoutingMode]>.5f){if(p==Param::MixAmount)return 1;if(p==Param::DirectLevel)return 0;}return s[p];}
class ThrowGesture {
public:
 bool down(bool latch,bool current) noexcept {held=!latch;return latch?!current:true;}
 bool up(bool latch,bool current) noexcept {held=false;return latch?current:false;}
 bool lostFocus(bool latch,bool current) noexcept {held=false;return latch?current:false;}
 bool isHeld()const noexcept{return held;}
private:bool held=false;
};
}

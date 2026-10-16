#include "Freeze.h"
#include <algorithm>
#include <cmath>
#include <stdexcept>
namespace adlib93 {
void Freeze::prepare(const PrepareSpec& s){
 if(!std::isfinite(s.sampleRate)||s.sampleRate<8000||s.sampleRate>384000)throw std::invalid_argument("Freeze sample rate");
 length_=static_cast<size_t>(std::lround(.250*s.sampleRate));overlap_=static_cast<size_t>(std::lround(.020*s.sampleRate));
 attack_=static_cast<uint32_t>(std::lround(.050*s.sampleRate));release_=static_cast<uint32_t>(std::lround(.250*s.sampleRate));
 for(auto& b:history_)b.assign(length_,0);reset();
}
void Freeze::reset(){for(auto& b:history_)std::fill(b.begin(),b.end(),0.f);record_=0;held_=1;write_=heldStart_=phase_=fresh_=0;remaining_=0;blend_=step_=0;requested_=hasHeld_=clearing_=false;}
StereoFrame Freeze::process(StereoFrame normal,bool active)noexcept{
 if(history_[0].empty()||clearing_)return {};
 normal.left=std::isfinite(normal.left)?normal.left:0;normal.right=std::isfinite(normal.right)?normal.right:0;
 if(active!=requested_){
  requested_=active;
  if(active){
   // A rapid re-trigger reuses the last complete immutable window until the
   // rolling spare has collected a full 250ms; never expose stale ring data.
   if(!hasHeld_||fresh_>=length_){held_=record_;record_=1-record_;heldStart_=write_;fresh_=0;hasHeld_=true;}
   phase_=overlap_;remaining_=attack_;step_=(1-blend_)/static_cast<float>(attack_);
  }
  else{remaining_=release_;step_=-blend_/static_cast<float>(release_);}
 }
 // Only the un-frozen, already ducked spatial return enters capture memory.
 history_[record_*2][write_]=normal.left;history_[record_*2+1][write_]=normal.right;write_=(write_+1)%length_;fresh_=std::min(length_,fresh_+1);
 StereoFrame held{};
 if(hasHeld_){float* channels[]={&held.left,&held.right};for(size_t c=0;c<2;++c){const auto& b=history_[held_*2+c];const float head=b[(heldStart_+phase_)%length_];if(phase_<overlap_){const float t=static_cast<float>(phase_)/static_cast<float>(overlap_);const float tail=b[(heldStart_+length_-overlap_+phase_)%length_];*channels[c]=tail+(head-tail)*t;}else *channels[c]=head;}phase_=(phase_+1)%(length_-overlap_);}
 if(remaining_){blend_+=step_;if(--remaining_==0)blend_=requested_?1.f:0.f;}
 return {normal.left+(held.left-normal.left)*blend_,normal.right+(held.right-normal.right)*blend_};
}
void Freeze::beginClear()noexcept{clearing_=true;clearBuffer_=clearOffset_=0;record_=0;held_=1;write_=heldStart_=phase_=fresh_=0;remaining_=0;blend_=step_=0;requested_=hasHeld_=false;}
bool Freeze::clearStep(uint32_t budget)noexcept{
 while(budget&&clearBuffer_<history_.size()){auto& b=history_[clearBuffer_];while(budget&&clearOffset_<b.size()){b[clearOffset_++]=0;--budget;}if(clearOffset_==b.size()){++clearBuffer_;clearOffset_=0;}}
 if(clearBuffer_==history_.size())clearing_=false;return !clearing_;
}
size_t Freeze::allocatedBytes()const noexcept{size_t n=0;for(const auto& b:history_)n+=b.capacity()*sizeof(float);return n;}
}

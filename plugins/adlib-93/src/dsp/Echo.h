#pragma once
#include "../core/Parameters.h"
#include "../core/Types.h"
#include <array>
#include <vector>
#include <cstddef>
namespace adlib93 {
struct DelayTiming { double milliseconds=250; bool clamped=false, usingManual=false; };
DelayTiming resolveDelayTime(const ParameterSnapshot&,const HostTiming&) noexcept;
class Echo {
public:
 void prepare(const PrepareSpec&); void reset();
 void setParameters(const ParameterSnapshot&) noexcept;
 void setTiming(const HostTiming&) noexcept;
 StereoFrame process(StereoFrame,float throwGate) noexcept;
 void beginClear() noexcept; bool clearStep(uint32_t maxWrites) noexcept;
 size_t allocatedBytes() const noexcept;
 DelayTiming timing() const noexcept { return resolved_; }
 float maximumState() const noexcept { return maximumState_; }
private:
 struct Allpass { std::vector<float> data; size_t write=0; };
 std::array<std::vector<float>,2> delay_;
 std::array<Allpass,8> allpass_;
 std::array<float,4> filter_{};
 ParameterSnapshot parameters_{}; HostTiming host_{}; DelayTiming resolved_{};
 double sampleRate_=48000, smooth_=0, tapA_=12000,tapB_=12000,pending_=12000;
 float feedback_=0,ping_=0,diffuse_=0,enabled_=0,throwGain_=1,hp_=0,lp_=1, maximumState_=0;
 float feedbackTarget_=0,pingTarget_=0,diffuseTarget_=0,enabledTarget_=0,hpTarget_=0,lpTarget_=1,throwTarget_=1,throwStep_=0;
 uint32_t throwRemaining_=0;
 size_t write_=0; uint32_t fade_=0,fadeLength_=4800; bool primed_=false;
 size_t clearBuffer_=0,clearOffset_=0; bool clearing_=false;
 float read(size_t channel,double samples) const noexcept;
};
}

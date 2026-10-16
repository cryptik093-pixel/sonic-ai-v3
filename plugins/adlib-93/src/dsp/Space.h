#pragma once
#include "../core/Parameters.h"
#include "../core/Types.h"
#include <array>
#include <vector>
#include <cstddef>
namespace adlib93 {
struct SpaceReturns { StereoFrame reverb{}; float duckGain=1; };
class Space {
public:
 void prepare(const PrepareSpec&); void reset();
 void setParameters(const ParameterSnapshot&) noexcept;
 SpaceReturns process(StereoFrame clean,StereoFrame leveledDelay,StereoFrame detectorInput) noexcept;
 void beginClear() noexcept; bool clearStep(uint32_t maxWrites) noexcept;
 size_t allocatedBytes() const noexcept;
 float maximumState() const noexcept { return maximumState_; }
private:
 std::array<std::vector<float>,8> lines_; std::array<size_t,8> positions_{};
 std::array<std::vector<float>,2> predelay_; size_t preWrite_=0;
 std::array<float,8> dampingState_{};
 std::array<double,8> gain_{},gainTarget_{};
 double sampleRate_=48000,smooth_=0,damping_=1,dampingTarget_=1,predelaySamples_=0,predelayTarget_=0;
 float send_=0,sendTarget_=0,enabled_=0,enabledTarget_=0,duckDb_=0,duckMax_=0,duckThreshold_=-30,maximumState_=0;
 double duckAttack_=0,duckRelease_=0; bool duckEnabled_=false,primed_=false;
 size_t clearBuffer_=0,clearOffset_=0; bool clearing_=false;
};
}

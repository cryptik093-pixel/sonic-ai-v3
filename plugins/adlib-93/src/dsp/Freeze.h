#pragma once
#include "../core/Types.h"
#include <array>
#include <vector>
#include <cstddef>
namespace adlib93 {
class Freeze {
public:
 void prepare(const PrepareSpec&); void reset();
 StereoFrame process(StereoFrame normalSpatial,bool active) noexcept;
 bool suppressesExcitation() const noexcept { return requested_; }
 void beginClear() noexcept; bool clearStep(uint32_t maxWrites) noexcept;
 size_t allocatedBytes() const noexcept;
 float blend() const noexcept { return blend_; }
private:
 std::array<std::vector<float>,4> history_;
 size_t length_=12000,overlap_=960,record_=0,held_=1,write_=0,heldStart_=0,phase_=0;
 size_t fresh_=0;
 uint32_t attack_=2400,release_=12000,remaining_=0;
 float blend_=0,step_=0; bool requested_=false,hasHeld_=false,clearing_=false;
 size_t clearBuffer_=0,clearOffset_=0;
};
}

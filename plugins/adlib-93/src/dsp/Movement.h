#pragma once
#include "../core/Parameters.h"
#include "../core/Types.h"
#include <array>
#include <vector>
#include <cstddef>
#include <cstdint>
namespace adlib93 {
struct MovementReturns { StereoFrame doubler{},chorus{}; };
class Movement {
public:
 void prepare(const PrepareSpec&);void reset() noexcept;void setParameters(const ParameterSnapshot&) noexcept;
 MovementReturns processBranches(StereoFrame) noexcept;
 void beginClear() noexcept;bool clearStep(uint32_t maxWrites) noexcept;
 std::size_t allocatedBytes() const noexcept;
private:
 ParameterSnapshot parameters_{makeInitSnapshot()};double rate_{48000},smoothCoefficient_{};std::array<std::vector<float>,2> memory_{};
 std::size_t write_{},clearCursor_{};bool clearing_{};
 std::array<double,4> phases_{{0,1.5707963267948966,0,1.5707963267948966}};
 std::array<double,4> delays_{{14,22,15,15}},depths_{{.4,.4,3,3}},rates_{{.3,.3,.8,.8}};
 double doubleWet_{},chorusWet_{};float read(unsigned,double) const noexcept;void resetSmall() noexcept;
};
}

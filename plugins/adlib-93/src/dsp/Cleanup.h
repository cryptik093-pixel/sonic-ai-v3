#pragma once
#include "../core/Parameters.h"
#include "../core/Types.h"
namespace adlib93 {
struct CleanupMeasurements { float gateReductionDb{}, deessReductionDb{}; StereoFrame diagnosticHigh{}; bool gateOpen{}; };
class Cleanup {
public:
 void prepare(const PrepareSpec&); void reset() noexcept;
 void setParameters(const ParameterSnapshot&) noexcept;
 StereoFrame process(StereoFrame) noexcept;
 CleanupMeasurements measurements() const noexcept { return meters_; }
 StereoFrame highBand() const noexcept { return meters_.diagnosticHigh; }
private:
 ParameterSnapshot parameters_{makeInitSnapshot()};
 double rate_{48000}, detector_{}, gateDb_{}, deessDetector_{}, deessDb_{}, cutoff_{6000}, lowL_{},lowR_{}, gateWet_{},deessWet_{};
 unsigned holdRemaining_{}; bool open_{true}; CleanupMeasurements meters_{};
};
}

#pragma once
#include "AdlibEngine.h"
#include <array>
namespace adlib93 {
class Transitions {
public:
 void prepare(const PrepareSpec&,ParameterSnapshot initial=makeInitSnapshot());
 void reset();
 void request(const ParameterSnapshot&) noexcept;
 void setParameters(const ParameterSnapshot&) noexcept;
 void setTiming(const HostTiming&) noexcept;
 void setBypassed(bool) noexcept;
 void clearTails() noexcept;
 StereoFrame process(StereoFrame) noexcept;
 void process(const float* const*,float* const*,uint32_t,const ParameterSnapshot&,const ProcessContext&) noexcept;
 void process(const float* const*,float* const*,uint32_t,const ProcessContext&) noexcept;
 void serviceZeroBlock() noexcept;
 EngineMeasurements measurements() const noexcept;
 std::size_t allocatedBytes() const noexcept;
 uint32_t maxClearWritesLastFrame() const noexcept { return reportedWrites_; }
private:
 enum class Phase { idle,prepareIncoming,incomingReady,crossfade,clearFadeOut,clearMemory,clearReady,clearFadeIn };
 std::array<AdlibEngine,2> engines_;
 PrepareSpec spec_{};ParameterSnapshot current_{makeInitSnapshot()},pending_{makeInitSnapshot()},incoming_{makeInitSnapshot()};HostTiming timing_{};
 Phase phase_{Phase::idle};unsigned active_{};bool hasPending_{},clearRequested_{},hostBypass_{},inhibitFreeze_{},inhibitThrow_{};
 uint32_t position_{},crossfadeLength_{2400},clearLength_{960},lastWrites_{},reportedWrites_{};
 float lastOutputPeak_{};
 void startPending() noexcept;
 void service(uint32_t budget,bool allowFinalize=true) noexcept;
};
}

#pragma once
#include "Cleanup.h"
#include "Character.h"
#include "Movement.h"
#include "Echo.h"
#include "Space.h"
#include "Freeze.h"
#include "OutputStage.h"
#include <cstddef>
namespace adlib93 {
struct EngineMeasurements {
 float inputPeak{},outputPeak{},gateReductionDb{},deessReductionDb{},limiterReductionDb{},correlation{};
 bool correlationAvailable{},clearing{},transitioning{},freezeHeld{},delayClamped{},usingManualTempo{};
 double tempo{120}; uint64_t diagnostics{}; uint32_t clearedWrites{}; std::size_t allocatedBytes{};
};
class AdlibEngine {
public:
 void prepare(const PrepareSpec&,ParameterSnapshot initial=makeInitSnapshot());
 void reset(); // Lifecycle only, never called by the audio-thread transition controller.
 void setParameters(const ParameterSnapshot&) noexcept;
 void setTiming(const HostTiming&) noexcept;
 void setBypassed(bool) noexcept;
 StereoFrame process(StereoFrame) noexcept;
 void process(const float* const*,float* const*,uint32_t,const ParameterSnapshot&,const ProcessContext&) noexcept;
 void beginClear() noexcept;
 bool clearStep(uint32_t maxWrites) noexcept;
 void finishClear(const ParameterSnapshot&,bool resetSmall=true) noexcept;
 void setTailGain(float gain) noexcept { tailGain_=std::clamp(gain,0.0f,1.0f); }
 EngineMeasurements measurements() const noexcept { return meters_; }
 std::size_t allocatedBytes() const noexcept;
 const ParameterSnapshot& parameters() const noexcept { return parameters_; }
private:
 PrepareSpec spec_{}; ParameterSnapshot parameters_{makeInitSnapshot()};HostTiming timing_{};
 Cleanup cleanup_;Character character_;Movement movement_;Echo echo_;Space space_;Freeze freeze_;OutputStage output_;
 Smooth inputGain_,direct_,double_,chorus_,echoLevel_,reverb_,mix_,width_,pan_;
 LinearRamp bypass_,send_;bool hostBypass_{};unsigned clearModule_{};bool clearing_{};
 uint64_t silenceSamples_{};bool tailExpired_{},automaticClear_{};float tailGain_{1};EngineMeasurements meters_{};
 void initializeSmall() noexcept;
};
}

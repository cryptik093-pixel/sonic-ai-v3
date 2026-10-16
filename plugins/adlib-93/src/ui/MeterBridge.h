#pragma once
#include <atomic>
#include <cstdint>
#include <limits>
namespace adlib93 {
struct MeterSnapshot {
 float inputPeakDb=-100,outputPeakDb=-100,gateReductionDb=0,deessReductionDb=0,limiterReductionDb=0,correlation=std::numeric_limits<float>::quiet_NaN();
 double tempo=120;uint64_t diagnostics=0;bool manualTempo=true,delayClamped=false,clearing=false,frozen=false,listen=false;
};
class MeterBridge {
public:
 void publish(const MeterSnapshot& s) noexcept {input.store(s.inputPeakDb);output.store(s.outputPeakDb);gate.store(s.gateReductionDb);deess.store(s.deessReductionDb);limiter.store(s.limiterReductionDb);corr.store(s.correlation);tempo.store(s.tempo);diagnostics.store(s.diagnostics);flags.store((s.manualTempo?1u:0u)|(s.delayClamped?2u:0u)|(s.clearing?4u:0u)|(s.frozen?8u:0u)|(s.listen?16u:0u),std::memory_order_release);}
 MeterSnapshot read() const noexcept {MeterSnapshot s;auto f=flags.load(std::memory_order_acquire);s.inputPeakDb=input.load();s.outputPeakDb=output.load();s.gateReductionDb=gate.load();s.deessReductionDb=deess.load();s.limiterReductionDb=limiter.load();s.correlation=corr.load();s.tempo=tempo.load();s.diagnostics=diagnostics.load();s.manualTempo=(f&1)!=0;s.delayClamped=(f&2)!=0;s.clearing=(f&4)!=0;s.frozen=(f&8)!=0;s.listen=(f&16)!=0;return s;}
private:
 static_assert(std::atomic<float>::is_always_lock_free&&std::atomic<double>::is_always_lock_free&&std::atomic<unsigned>::is_always_lock_free&&std::atomic<uint64_t>::is_always_lock_free,"Meter atomics must be lock free");
 std::atomic<float> input{-100},output{-100},gate{0},deess{0},limiter{0},corr{std::numeric_limits<float>::quiet_NaN()};std::atomic<double> tempo{120};std::atomic<uint64_t> diagnostics{0};std::atomic<unsigned>flags{1};
};
}

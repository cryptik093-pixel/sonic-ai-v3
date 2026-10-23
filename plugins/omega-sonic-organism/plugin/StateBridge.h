#pragma once
#include "omega/State.h"
#include <atomic>
#include <mutex>

namespace oso {
// Host state publication may run concurrently with process(). The host side
// serializes producers; the audio side only performs bounded lock-free loads
// and stores. Atomic payloads make unsuccessful seqlock reads race-free too.
class StateBridge final {
    static_assert(std::atomic<double>::is_always_lock_free);
    static_assert(std::atomic<uint32_t>::is_always_lock_free);
    struct Slot {
        std::array<std::atomic<double>,15> values{};
        std::atomic<uint32_t> sequence{0};
        Slot(){const auto initial=omega::defaults();for(size_t i=0;i<15;++i)values[i].store(initial[i],std::memory_order_relaxed);}
        void write(const omega::ParameterValues& source) noexcept {
            // Sequential consistency orders the odd marker before all payload
            // writes, including on machines with weaker memory ordering.
            sequence.fetch_add(1);
            for(size_t i=0;i<15;++i)values[i].store(source[i]);
            sequence.fetch_add(1);
        }
        bool read(omega::ParameterValues& result,uint32_t& revision) const noexcept {
            const uint32_t before=sequence.load();if(before&1)return false;
            omega::ParameterValues candidate{};
            for(size_t i=0;i<15;++i)candidate[i]=values[i].load();
            if(sequence.load()!=before)return false;
            result=candidate;revision=before;return true;
        }
    };
public:
    // Never called by process(), setProcessing(), or an audio-owned helper.
    void publishFromHost(const omega::ParameterValues& values) {
        const std::lock_guard<std::mutex> lock(producer_);pending_.write(values);
    }
    bool pendingForAudio(omega::ParameterValues& values,uint32_t& revision) const noexcept {
        if(pending_.sequence.load()==consumed_.load())return false;
        uint32_t candidate=0;
        if(!pending_.read(values,candidate)||candidate==consumed_.load())return false;
        revision=candidate;return true;
    }
    // Single writer: processing/lifecycle thread, following VST3 lifecycle.
    void publishFromAudio(const omega::ParameterValues& values,uint32_t consumedRevision) noexcept {
        audio_.write(values);consumed_.store(consumedRevision);
    }
    bool captureForHost(omega::ParameterValues& values) const noexcept {
        for(int attempt=0;attempt<8;++attempt) {
            uint32_t revision=0;
            if(pending_.sequence.load()!=consumed_.load()) {
                if(pending_.read(values,revision))return true;
            } else if(audio_.read(values,revision))return true;
        }
        return false;
    }
private:
    mutable std::mutex producer_; // host producers only
    Slot pending_,audio_;
    std::atomic<uint32_t> consumed_{0};
};
}

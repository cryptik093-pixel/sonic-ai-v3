#pragma once
#include "Parameters.h"
#include <atomic>
#include <cstdint>
namespace adlib93 {
// Ownership is exclusive: producer only writes Writing; consumer only reads Reading.
// No seqlock over ordinary data. Concurrent producers use CAS, never an audio lock.
class SnapshotMailbox {
 enum Status:unsigned { Free,Writing,Ready,Reading };
 struct Slot { std::atomic<unsigned> status{Free}; std::atomic<uint64_t> generation{0}; ParameterSnapshot snapshot{}; };
 std::array<Slot,4> slots{};
 std::atomic<uint64_t> serial{0};
 uint64_t lastConsumed=0; // Single audio consumer only.
public:
 static_assert(std::atomic<unsigned>::is_always_lock_free&&std::atomic<uint64_t>::is_always_lock_free);
 bool tryPublish(const ParameterSnapshot& value) noexcept {
  for(unsigned pass=0;pass<2;++pass)for(auto& s:slots){unsigned expected=pass==0?Free:Ready;
   if(s.status.compare_exchange_strong(expected,Writing,std::memory_order_acquire)){
    s.snapshot=value;s.generation.store(serial.fetch_add(1,std::memory_order_relaxed)+1,std::memory_order_relaxed);
    s.status.store(Ready,std::memory_order_release);return true;
   }}return false;
 }
 bool tryConsume(ParameterSnapshot& out) noexcept {
  Slot* chosen=nullptr;uint64_t newest=lastConsumed;
  for(auto& s:slots)if(s.status.load(std::memory_order_acquire)==Ready){auto n=s.generation.load(std::memory_order_relaxed);if(n>newest){newest=n;chosen=&s;}}
  if(!chosen)return false;unsigned expected=Ready;
  if(!chosen->status.compare_exchange_strong(expected,Reading,std::memory_order_acquire))return false;
  // A producer may have replaced a Ready slot after the scan; read its owned generation.
  newest=chosen->generation.load(std::memory_order_relaxed);
  if(newest<=lastConsumed){chosen->status.store(Free,std::memory_order_release);return false;}
  out=chosen->snapshot;lastConsumed=newest;chosen->status.store(Free,std::memory_order_release);return true;
 }
};
}

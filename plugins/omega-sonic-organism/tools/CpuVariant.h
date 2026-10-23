#pragma once
#include <cstdint>
// Offline A/B harness only. Both shims call the actual production core.
struct CpuVariant {
    void* state;
    void (*destroy)(void*);
    void (*morph)(void*,float);
    void (*render)(void*,float*,float*,int);
    uint64_t (*faults)(void*);
};
CpuVariant makeBaseline(int quality);
CpuVariant makeCurrent(int quality);

#include "TestSupport.h"
#include "dsp/Transitions.h"
#include "presets/FactoryBank.h"
#include <cstdlib>
#include <new>
#include <cmath>
#include <iostream>
#if defined(_MSC_VER)
#include <malloc.h>
#endif
namespace {
thread_local bool observe=false;
thread_local uint64_t allocations=0,deallocations=0;
void* allocate(size_t n){if(observe)++allocations;if(auto p=std::malloc(n?n:1))return p;throw std::bad_alloc();}
void dispose(void*p)noexcept{if(p&&observe)++deallocations;std::free(p);}
void* allocateAligned(size_t n,size_t alignment){if(observe)++allocations;
#if defined(_MSC_VER)
    auto p=_aligned_malloc(n?n:1,alignment);
#else
    auto p=std::aligned_alloc(alignment,((n?n:1)+alignment-1)/alignment*alignment);
#endif
    if(p)return p;throw std::bad_alloc();
}
void disposeAligned(void*p)noexcept{if(p&&observe)++deallocations;
#if defined(_MSC_VER)
    _aligned_free(p);
#else
    std::free(p);
#endif
}
}
void* operator new(size_t n){return allocate(n);}void* operator new[](size_t n){return allocate(n);}
void operator delete(void*p)noexcept{dispose(p);}void operator delete[](void*p)noexcept{dispose(p);}
void operator delete(void*p,size_t)noexcept{dispose(p);}void operator delete[](void*p,size_t)noexcept{dispose(p);}
void* operator new(size_t n,const std::nothrow_t&)noexcept{try{return allocate(n);}catch(...){return nullptr;}}
void* operator new[](size_t n,const std::nothrow_t&)noexcept{try{return allocate(n);}catch(...){return nullptr;}}
void operator delete(void*p,const std::nothrow_t&)noexcept{dispose(p);}void operator delete[](void*p,const std::nothrow_t&)noexcept{dispose(p);}
void* operator new(size_t n,std::align_val_t a){return allocateAligned(n,size_t(a));}void* operator new[](size_t n,std::align_val_t a){return allocateAligned(n,size_t(a));}
void operator delete(void*p,std::align_val_t)noexcept{disposeAligned(p);}void operator delete[](void*p,std::align_val_t)noexcept{disposeAligned(p);}
void operator delete(void*p,size_t,std::align_val_t)noexcept{disposeAligned(p);}void operator delete[](void*p,size_t,std::align_val_t)noexcept{disposeAligned(p);}
void* operator new(size_t n,std::align_val_t a,const std::nothrow_t&)noexcept{try{return allocateAligned(n,size_t(a));}catch(...){return nullptr;}}
void* operator new[](size_t n,std::align_val_t a,const std::nothrow_t&)noexcept{try{return allocateAligned(n,size_t(a));}catch(...){return nullptr;}}
void operator delete(void*p,std::align_val_t,const std::nothrow_t&)noexcept{disposeAligned(p);}void operator delete[](void*p,std::align_val_t,const std::nothrow_t&)noexcept{disposeAligned(p);}
TEST_CASE("Realtime.NoAllocation") {
    using namespace adlib93;Transitions dsp;dsp.prepare({48000,128,ChannelLayout::stereoStereo},factoryPresets()[23].parameters);
    const auto& bank=factoryPresets();auto p=makeInitSnapshot();bool finite=true;allocations=deallocations=0;
    observe=true;
    for(unsigned i=0;i<100000;++i){if(i%100==0){p=bank[(i/100)%24].parameters;dsp.request(p);}if(i%137==0){p[Param::FreezeActive]=p[Param::FreezeActive]>.5f?0.f:1.f;p[Param::ThrowActive]=p[Param::FreezeActive];dsp.setParameters(p);}if(i%7001==0)dsp.clearTails();
        auto y=dsp.process({.1f,-.07f});finite=finite&&std::isfinite(y.left)&&std::isfinite(y.right);if(i%97==0)dsp.serviceZeroBlock();}
    observe=false;
    require(finite,"transition/performance stress finite");require(allocations==0&&deallocations==0,"no intercepted C++ new/delete including aligned/nothrow in production DSP");
}
TEST_CASE("Realtime.Budget") {
    using namespace adlib93;Transitions dsp;dsp.prepare({96000,128,ChannelLayout::stereoStereo},factoryPresets()[23].parameters);
    const auto bytes=dsp.allocatedBytes();require(bytes<=64u*1024u*1024u,"both engines DSP buffer budget <=64 MiB at96k");
    dsp.request(factoryPresets()[11].parameters);bool bounded=true;
    for(unsigned i=0;i<100000;++i){if(i%100==0)dsp.request(factoryPresets()[(i/100)%24].parameters);if(i%12001==0)dsp.clearTails();dsp.process({0,0});bounded=bounded&&dsp.maxClearWritesLastFrame()<=256;if(i%29==0){dsp.serviceZeroBlock();bounded=bounded&&dsp.maxClearWritesLastFrame()<=64;}}
    require(bounded,"global clearing budget respected including zero-frame service");require(dsp.allocatedBytes()==bytes,"buffer allocation stable over1000preset switches");
    std::cout<<"DSP buffer bytes (two engines,96kHz): "<<bytes<<". Timed10minute CPU budget belongs to benchmark, not this assertion.\n";
}

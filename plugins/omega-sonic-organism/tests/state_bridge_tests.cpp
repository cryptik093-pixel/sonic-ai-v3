#include "StateBridge.h"
#include <atomic>
#include <cstdlib>
#include <iostream>
#include <new>
#include <thread>
static thread_local bool measuring=false;
static std::atomic<unsigned> allocations{0},deallocations{0};
void* operator new(size_t n){if(measuring)++allocations;if(auto* p=std::malloc(n?n:1))return p;throw std::bad_alloc();}
void* operator new[](size_t n){return ::operator new(n);}
void operator delete(void* p) noexcept {if(measuring&&p)++deallocations;std::free(p);}
void operator delete[](void* p) noexcept {::operator delete(p);}
void operator delete(void* p,size_t) noexcept {::operator delete(p);}
void operator delete[](void* p,size_t) noexcept {::operator delete(p);}
#define CHECK(x) do { if (!(x)) { std::cerr << "FAIL " << __LINE__ << ": " << #x << '\n'; std::exit(1); } } while(false)
static void uniform(const omega::ParameterValues& p){CHECK(p[0]==0.||p[0]==1.);for(double x:p)CHECK(x==p[0]);}
int main(){
    oso::StateBridge bridge;
    omega::ParameterValues values{};CHECK(bridge.captureForHost(values));CHECK(values==omega::defaults());
    values.fill(0);bridge.publishFromHost(values);
    std::atomic<int> writersDone{0};std::atomic<unsigned> consumed{0};
    auto producer=[&](int offset){for(int n=0;n<4000;++n){omega::ParameterValues p{};p.fill(double((n+offset)&1));bridge.publishFromHost(p);}++writersDone;};
    std::thread a(producer,0),b(producer,1);
    std::thread audio([&]{
        omega::ParameterValues current{};uint32_t revision=0;
        do{
            measuring=true;
            if(bridge.pendingForAudio(current,revision))++consumed;
            bridge.publishFromAudio(current,revision);
            measuring=false;uniform(current);
        }while(writersDone.load()!=2);
    });
    unsigned captures=0;
    while(writersDone.load()!=2){if(bridge.captureForHost(values)){uniform(values);++captures;}}
    a.join();b.join();audio.join();
    CHECK(consumed>0);
    values.fill(1);bridge.publishFromHost(values);
    omega::ParameterValues final{};CHECK(bridge.captureForHost(final));CHECK(final==values);
    uint32_t revision=0;CHECK(bridge.pendingForAudio(final,revision));CHECK(final==values);
    measuring=true;bridge.publishFromAudio(final,revision);measuring=false;
    CHECK(!bridge.pendingForAudio(final,revision));CHECK(bridge.captureForHost(final));CHECK(final==values);
    CHECK(allocations==0&&deallocations==0);
    std::cout << "PASS 8000 concurrent host publications; " << captures << " coherent captures; " << consumed
              << " audio consumes; zero measured ordinary C++ audio-side allocations/deallocations.\n";
}

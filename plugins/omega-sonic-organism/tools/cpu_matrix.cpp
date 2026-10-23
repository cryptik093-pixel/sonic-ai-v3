// Production-core stress matrix. Offline instrumentation, never plugin code.
#include "omega/OrganismCore.h"
#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <vector>
#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
static double threadMs() {
    FILETIME c{},e{},k{},u{};
    if (!GetThreadTimes(GetCurrentThread(),&c,&e,&k,&u)) return -1;
    ULARGE_INTEGER a{},b{};
    a.LowPart=k.dwLowDateTime;a.HighPart=k.dwHighDateTime;
    b.LowPart=u.dwLowDateTime;b.HighPart=u.dwHighDateTime;
    return double(a.QuadPart+b.QuadPart)/10000.;
}
#else
static double threadMs() { return -1; }
#endif
#define CHECK(x) do { if (!(x)) { std::cerr << "FAIL " << __LINE__ << ": " << #x << '\n'; return 1; } } while(false)
int main(int argc,char** argv) {
    CHECK(argc==2||argc==3);
    const int callbacks=argc==3?std::atoi(argv[2]):256;
    CHECK(callbacks>=32&&callbacks<=100000);
    std::ofstream out(argv[1]);CHECK(out);
    out << std::setprecision(10)
        << "{\"kind\":\"unpaced production-core stress matrix; not G07 or DAW acceptance\","
        << "\"warmupCallbacks\":32,\"callbacksPerCase\":" << callbacks
        << ",\"workload\":\"maximum Energy Motion Material Space; continuous Morph and pitch bend; sustained voices\",\"cases\":[";
    bool first=true;
    for(double rate:{44100.,48000.,96000.}) for(int frames:{64,256,1024})
    for(int voices:{1,8,16,32}) for(int quality:{0,1}) {
        omega::OrganismCore synth;
        synth.setParameter(110,quality);
        for(uint32_t id=101;id<=104;++id)synth.setParameter(id,1);
        synth.prepare(rate,voices);
        for(int i=0;i<voices;++i)synth.noteOn(36+i,.95f,i);
        std::vector<float> l(size_t(frames),0),r(size_t(frames),0);
        for(int i=0;i<32;++i)synth.render(l.data(),r.data(),frames);
        std::vector<double> costs;costs.reserve(size_t(callbacks));
        const double cpuStart=threadMs(),deadline=1000.*frames/rate;
        int overruns=0;double checksum=0,peak=0;
        for(int block=0;block<callbacks;++block) {
            synth.setMorph(float(block%257)/256.f);
            synth.setPitchBend(float((block%129)-64)/64.f);
            const auto start=std::chrono::steady_clock::now();
            synth.render(l.data(),r.data(),frames);
            const double cost=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
            costs.push_back(cost);if(cost>deadline)++overruns;
            for(int i=0;i<frames;++i) {
                CHECK(std::isfinite(l[size_t(i)])&&std::isfinite(r[size_t(i)]));
                peak=std::max(peak,std::max(std::abs(double(l[size_t(i)])),std::abs(double(r[size_t(i)]))));
                checksum+=double(l[size_t(i)])+r[size_t(i)];
            }
            CHECK(synth.nonFiniteFaults()==0);
        }
        CHECK(peak<=.980001);
        const double cpuTotal=threadMs()-cpuStart;
        std::sort(costs.begin(),costs.end());
        auto p=[&](double x){return costs[size_t(std::ceil(x*callbacks))-1];};
        if(!first)out << ',';first=false;
        out << "{\"sampleRate\":" << rate << ",\"frames\":" << frames
            << ",\"voices\":" << voices << ",\"quality\":\"" << (quality?"HQ":"Eco")
            << "\",\"deadlineMs\":" << deadline << ",\"medianMs\":" << p(.5)
            << ",\"p95Ms\":" << p(.95) << ",\"p99Ms\":" << p(.99)
            << ",\"maximumMs\":" << costs.back() << ",\"overruns\":" << overruns
            << ",\"threadCpuTotalMs\":" << cpuTotal << ",\"peak\":" << peak
            << ",\"outputChecksum\":" << checksum << ",\"nonFiniteFaults\":0}";
        out.flush();
    }
    out << "]}\n";CHECK(out);
    std::cout << "Recorded 72 stress cases; finite/bounded output passed. CPU gates require separate evaluation.\n";
}

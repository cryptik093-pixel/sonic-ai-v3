#include "CpuVariant.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <thread>
#include <vector>
#define NOMINMAX
#include <windows.h>
#define CHECK(x) do { if (!(x)) { std::cerr << "FAIL " << __LINE__ << ": " << #x << '\n'; return 1; } } while(false)
using Clock=std::chrono::steady_clock;
int main(int argc,char** argv) {
    CHECK(argc==2||argc==3);
    const int count=argc==3?std::atoi(argv[2]):1024;CHECK(count>=128&&count<=100000);
    std::ofstream out(argv[1]);CHECK(out);
    out << std::setprecision(10)
        << "{\"kind\":\"interleaved production-core A/B; diagnostic, not G07 or DAW acceptance\","
        << "\"sampleRate\":48000,\"frames\":256,\"voices\":16,\"warmupCallbacks\":100,"
        << "\"callbacksPerVariant\":" << count << ",\"order\":\"AB BA alternating; paired deadline 2*256/48000 seconds\",\"modes\":[";
    for(int quality=0;quality<2;++quality) {
        std::array<CpuVariant,2> variants{makeBaseline(quality),makeCurrent(quality)};
        std::array<std::array<float,256>,2> l{},r{};
        std::array<std::vector<double>,2> wall,cycles;
        for(int v=0;v<2;++v){wall[v].reserve(size_t(count));cycles[v].reserve(size_t(count));
            for(int i=0;i<100;++i)variants[v].render(variants[v].state,l[v].data(),r[v].data(),256);}
        double maxError=0,error=0,power=0,checksum=0;
        const auto start=Clock::now();
        for(int block=0;block<count;++block) {
            const float morph=float(.5+.5*std::sin(2*3.14159265358979323846*block/count*2));
            for(auto& v:variants)v.morph(v.state,morph);
            for(int order=0;order<2;++order) {
                const int v=(block+order)&1;
                ULONG64 beforeCycles=0,afterCycles=0;
                CHECK(QueryThreadCycleTime(GetCurrentThread(),&beforeCycles));
                const auto before=Clock::now();
                variants[v].render(variants[v].state,l[v].data(),r[v].data(),256);
                const auto after=Clock::now();
                CHECK(QueryThreadCycleTime(GetCurrentThread(),&afterCycles));
                wall[v].push_back(std::chrono::duration<double,std::milli>(after-before).count());
                cycles[v].push_back(double(afterCycles-beforeCycles));
                CHECK(variants[v].faults(variants[v].state)==0);
            }
            for(int i=0;i<256;++i)for(const auto* channel:{&l,&r}) {
                const double a=(*channel)[0][size_t(i)],b=(*channel)[1][size_t(i)];
                CHECK(std::isfinite(a)&&std::isfinite(b));
                maxError=std::max(maxError,std::abs(a-b));error+=(a-b)*(a-b);power+=a*a;checksum+=b;
            }
            std::this_thread::sleep_until(start+std::chrono::duration_cast<Clock::duration>(std::chrono::duration<double>((block+1)*512./48000)));
        }
        if(quality)out << ',';
        const double relative=std::sqrt(error/std::max(power,1e-30));
        out << "{\"quality\":\"" << (quality?"HQ":"Eco") << "\",\"maximumAudioError\":" << maxError
            << ",\"relativeRmsError\":" << relative << ",\"checksum\":" << checksum << ",\"variants\":[";
        for(int v=0;v<2;++v) {
            const auto overruns=std::count_if(wall[v].begin(),wall[v].end(),[](double ms){return ms>256./48.;});
            std::sort(wall[v].begin(),wall[v].end());std::sort(cycles[v].begin(),cycles[v].end());
            auto p=[&](const std::vector<double>& values,double x){return values[size_t(std::ceil(x*count))-1];};
            if(v)out << ',';
            out << "{\"variant\":\"" << (v?"current":"baseline")
                << "\",\"medianMs\":" << p(wall[v],.5) << ",\"p95Ms\":" << p(wall[v],.95)
                << ",\"p99Ms\":" << p(wall[v],.99) << ",\"maximumMs\":" << wall[v].back()
                << ",\"overruns\":" << overruns << ",\"medianThreadCycles\":" << p(cycles[v],.5)
                << ",\"p95ThreadCycles\":" << p(cycles[v],.95) << '}';
            variants[v].destroy(variants[v].state);
        }
        out << "]}";out.flush();CHECK(maxError<=1e-7&&relative<=1e-6);
    }
    out << "]}\n";CHECK(out);
    std::cout << "Paired timings recorded; audio-preservation limits passed. All wall-clock outliers retained.\n";
}

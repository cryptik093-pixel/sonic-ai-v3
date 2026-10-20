#include "omega/OrganismCore.h"
#include <algorithm>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <thread>
#include <vector>
#include <cstdlib>
#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
static double threadMilliseconds(){FILETIME c{},e{},k{},u{};if(!GetThreadTimes(GetCurrentThread(),&c,&e,&k,&u))return -1;ULARGE_INTEGER a{},b{};a.LowPart=k.dwLowDateTime;a.HighPart=k.dwHighDateTime;b.LowPart=u.dwLowDateTime;b.HighPart=u.dwHighDateTime;return double(a.QuadPart+b.QuadPart)/10000.;}
#else
static double threadMilliseconds(){return -1;}
#endif
#define CHECK(c) do{if(!(c)){std::cerr<<"FAIL "<<__LINE__<<" "<<#c<<'\n';std::exit(1);}}while(false)
namespace fs=std::filesystem;
using Clock=std::chrono::steady_clock;
static void raw(const fs::path& path,const std::vector<float>& data){std::ofstream out(path,std::ios::binary);CHECK(out);out.write(reinterpret_cast<const char*>(data.data()),std::streamsize(data.size()*4));CHECK(out);}
int main(int argc,char** argv){
    CHECK(argc==2||argc==3);const fs::path folder(argv[1]);fs::create_directories(folder);const int seconds=argc==3?std::atoi(argv[2]):30;CHECK(seconds>=1&&seconds<=600);
    omega::dsp::Tables tables;tables.prepare();
    constexpr int fftSize=65536,warmup=8192,bin=13717;const double frequency=double(bin)*48000/fftSize,drive=3,amplitude=.8;
    for(int hq=0;hq<2;++hq){omega::dsp::DriveStage stage;std::vector<float> result(fftSize);
        for(int n=0;n<warmup+fftSize;++n){const double x=amplitude*std::sin(2*omega::dsp::pi*frequency*n/48000.);const double y=stage.tick(x,drive,1/tables.saturate(drive),hq,tables);if(n>=warmup)result[size_t(n-warmup)]=float(y);}
        raw(folder/(hq?"drive-hq.f32":"drive-eco.f32"),result);
    }
    std::ofstream config(folder/"alias-input.json");config<<"{\"sampleRate\":48000,\"fftSize\":"<<fftSize<<",\"window\":\"rectangular coherent\",\"warmup\":"<<warmup<<",\"fundamentalBin\":"<<bin<<",\"frequencyHz\":"<<frequency<<",\"amplitude\":"<<amplitude<<",\"drive\":"<<drive<<",\"latencySamples\":15}";config.close();
    // Steady notes for tuning: no motion/space, last window well after bass pitch drop.
    for(int family=0;family<4;++family)for(int note:{36,48,60,72,84}){
        omega::OrganismCore synth;synth.setMorph(float(family*.25));synth.setMotion(0);synth.prepare(48000);synth.noteOn(note,.85f,1);
        std::vector<float> l(144000),r(l.size());for(int n=0;n<144000;n+=256)synth.render(l.data()+n,r.data()+n,std::min(256,144000-n));
        CHECK(synth.nonFiniteFaults()==0);raw(folder/("tuning-family-"+std::to_string(family)+"-note-"+std::to_string(note)+".f32"),l);
    }
    std::ofstream benchmark(folder/"benchmark.json");benchmark<<"{\"kind\":\"portable core callback benchmark; not DAW proof\",\"sampleRate\":48000,\"frames\":256,\"voices\":16,\"secondsPerMode\":"<<seconds<<",\"modes\":[";
    for(int hq=0;hq<2;++hq){
        omega::OrganismCore synth;synth.setParameter(110,hq);synth.setParameter(101,.65);synth.setParameter(102,.7);synth.setParameter(103,.65);synth.setParameter(104,.3);synth.prepare(48000,16);
        for(int i=0;i<16;++i)synth.noteOn(36+i,.65f,i);
        std::array<float,256> l{},r{};for(int i=0;i<100;++i)synth.render(l.data(),r.data(),256);
        const int callbacks=int(std::ceil(seconds*48000./256));std::vector<double> costs;costs.reserve(size_t(callbacks));int overruns=0;
        const auto start=Clock::now();const double cpuStart=threadMilliseconds();
        for(int block=0;block<callbacks;++block){
            const double morph=.5+.5*std::sin(2*omega::dsp::pi*block/callbacks*2);synth.setMorph(float(morph));
            const auto before=Clock::now();synth.render(l.data(),r.data(),256);const auto after=Clock::now();
            const double ms=std::chrono::duration<double,std::milli>(after-before).count();costs.push_back(ms);if(ms>256./48000*1000)++overruns;
            for(int n=0;n<256;++n)CHECK(std::isfinite(l[size_t(n)])&&std::isfinite(r[size_t(n)]));CHECK(synth.nonFiniteFaults()==0);
            std::this_thread::sleep_until(start+std::chrono::duration_cast<Clock::duration>(std::chrono::duration<double>((block+1)*256./48000)));
        }
        const double cpuTotal=threadMilliseconds()-cpuStart,wallTotal=std::chrono::duration<double,std::milli>(Clock::now()-start).count();
        std::sort(costs.begin(),costs.end());auto percentile=[&](double p){return costs[std::min(costs.size()-1,size_t(std::ceil(p*costs.size())-1))];};
        if(hq)benchmark<<',';benchmark<<"{\"quality\":\""<<(hq?"HQ":"Eco")<<"\",\"callbacks\":"<<callbacks<<",\"medianMs\":"<<percentile(.5)<<",\"p95Ms\":"<<percentile(.95)<<",\"p99Ms\":"<<percentile(.99)<<",\"maximumMs\":"<<costs.back()<<",\"overruns\":"<<overruns<<",\"nonFiniteFaults\":"<<synth.nonFiniteFaults()<<",\"threadCpuTotalMs\":"<<cpuTotal<<",\"wallTotalMs\":"<<wallTotal<<'}';
        std::cout<<(hq?"HQ":"Eco")<<" callback median="<<percentile(.5)<<" p95="<<percentile(.95)<<" p99="<<percentile(.99)<<" max="<<costs.back()<<" ms; overruns="<<overruns<<'\n';
    }
    benchmark<<"]}\n";std::cout<<"PASS measurements recorded; alias/tuning analysis and reference CPU goals require separate evaluation.\n";
}

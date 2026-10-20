#include "DrumEngine.h"
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <new>
#include <chrono>
#include <ctime>
#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#endif
double processSeconds(){
#ifdef _WIN32
    FILETIME created{},exited{},kernel{},user{};
    GetProcessTimes(GetCurrentProcess(),&created,&exited,&kernel,&user);
    auto seconds=[](FILETIME t){return static_cast<double>((static_cast<uint64_t>(t.dwHighDateTime)<<32)|t.dwLowDateTime)*1.0e-7;};
    return seconds(kernel)+seconds(user);
#else
    return static_cast<double>(std::clock())/CLOCKS_PER_SEC;
#endif
}
namespace { thread_local bool watching=false;thread_local size_t allocations=0; }
void* operator new(std::size_t n){if(watching)++allocations;if(auto* p=std::malloc(n?n:1))return p;throw std::bad_alloc();}
void* operator new[](std::size_t n){return ::operator new(n);}
void operator delete(void* p)noexcept{std::free(p);} void operator delete[](void* p)noexcept{std::free(p);}
void operator delete(void* p,std::size_t)noexcept{std::free(p);} void operator delete[](void* p,std::size_t)noexcept{std::free(p);}
void require(bool ok,const char* message){if(!ok){std::cerr<<"FAIL: "<<message<<'\n';std::exit(1);}}
std::vector<float> render(int category,ohdrum::Macros m,double rate=48000,int seconds=3){
    ohdrum::Engine engine;engine.prepare(rate,m);std::vector<float> out(static_cast<size_t>(rate)*static_cast<size_t>(seconds)*2);
    allocations=0;watching=true;engine.trigger(category,.8f,45);
    for(size_t i=0;i<out.size();i+=2){auto sample=engine.tick();out[i]=sample[0];out[i+1]=sample[1];}
    watching=false;require(allocations==0,"no DSP allocations");return out;
}
double energy(const std::vector<float>& a){double sum=0;for(float x:a){require(std::isfinite(x)&&std::abs(x)<=.98f,"finite bounded samples");sum+=x*x;}return sum;}
double difference(const std::vector<float>& a,const std::vector<float>& b){double sum=0;for(size_t i=0;i<a.size();++i){double d=a[i]-b[i];sum+=d*d;}return sum;}
void wave(const std::filesystem::path& path,const std::vector<float>& a){
    std::ofstream f(path,std::ios::binary);auto word=[&](uint32_t x,int bytes){for(int n=0;n<bytes;++n)f.put(static_cast<char>((x>>(n*8))&255));};
    const auto size=static_cast<uint32_t>(a.size()*2);f.write("RIFF",4);word(36+size,4);f.write("WAVEfmt ",8);word(16,4);word(1,2);word(2,2);word(48000,4);word(192000,4);word(4,2);word(16,2);f.write("data",4);word(size,4);
    for(float x:a)word(static_cast<uint16_t>(static_cast<int16_t>(x*32767)),2);
    require(f.good(),"write listening fixture");
}
int main(int argc,char** argv){
    const bool benchmarkOnly=argc>1&&std::string(argv[1])=="--benchmark";
    const bool exportAudio=argc>1&&!benchmarkOnly;std::filesystem::path directory=exportAudio?argv[1]:".";
    if(exportAudio)std::filesystem::create_directories(directory);
    std::ofstream metrics;if(exportAudio){metrics.open(directory/"macro-metrics.csv");metrics<<"department,macro,relative_difference\n";}
    for(int category=0;category<(benchmarkOnly?0:7);++category){
        const auto baseline=render(category,{.5f,.5f,.25f});const double e=energy(baseline);require(e>1,"every category plays without samples");
        require(difference(baseline,render(category,{.5f,.5f,.25f}))==0,"reproducible excitation");
        if(exportAudio)wave(directory/(std::to_string(category)+"-default.wav"),baseline);
        for(int macro=0;macro<3;++macro){
            ohdrum::Macros lo{.5f,.5f,.25f},hi=lo;
            if(macro==0){lo.body=0;hi.body=1;}if(macro==1){lo.character=0;hi.character=1;}if(macro==2){lo.space=0;hi.space=1;}
            const auto a=render(category,lo),b=render(category,hi);energy(a);energy(b);
            const double delta=std::sqrt(difference(a,b)/std::max(energy(a),1.0e-12));
            require(delta>.02,"all three macros materially change every department");
            std::cout<<ohdrum::names[static_cast<size_t>(category)]<<" macro "<<macro<<" relative delta "<<delta<<'\n';
            if(exportAudio){metrics<<category<<','<<macro<<','<<delta<<'\n';wave(directory/(std::to_string(category)+"-macro"+std::to_string(macro)+"-low.wav"),a);wave(directory/(std::to_string(category)+"-macro"+std::to_string(macro)+"-high.wav"),b);}
        }
        for(double rate:{44100.0,48000.0,96000.0,192000.0})for(float x:{0.0f,1.0f})energy(render(category,{x,x,x},rate,1));
    }
    ohdrum::Engine engine;engine.prepare(48000);engine.trigger(0,1);for(int i=0;i<100;++i)engine.tick();engine.reset();
    for(int i=0;i<2048;++i){auto out=engine.tick();require(out[0]==0&&out[1]==0,"reset clears voices and ambience");}
    engine.prepare(96000,{NAN,INFINITY,-INFINITY});engine.trigger(999,INFINITY);
    for(int i=0;i<4096;++i){auto x=engine.tick();require(std::isfinite(x[0]),"invalid input sanitized");}
    engine.prepare(48000);for(int i=0;i<16;++i)engine.trigger(i%7,1,45);
    const auto start=std::chrono::steady_clock::now();
    const auto cpuStart=processSeconds();
    allocations=0;watching=true;
    for(int i=0;i<48000;++i){if(i%4096==0)engine.trigger((i/4096)%7,1,45);if(i%64==0)engine.setMacros({i%128?0.0f:1.0f,.7f,.8f});auto out=engine.tick();require(std::isfinite(out[0])&&std::abs(out[0])<=.98f,"polyphonic automation and voice stealing bounded");}
    watching=false;require(allocations==0,"no allocations during polyphonic automation and voice stealing");
    std::cout<<"16-voice 48k one-second render wall ms: "<<std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count()<<'\n';
    std::cout<<"16-voice 48k one-second render process CPU ms: "<<(processSeconds()-cpuStart)*1000<<'\n';
    if(!benchmarkOnly)std::cout<<"PASS sample-free synthesis, all 21 macro mappings, deterministic renders, rates, safety, reset, no audio allocations\n";
}

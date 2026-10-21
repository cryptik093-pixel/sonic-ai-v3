#include "omega/OrganismCore.h"
#include <chrono>
#include <iostream>
#include <iomanip>
namespace omega {
struct CoreProfiler {
    template<class F> static double time(int count,F work){
        const auto start=std::chrono::steady_clock::now();
        for(int i=0;i<count;++i)work(i);
        return std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
    }
    static void run(){
        std::cout<<std::setprecision(10)<<"{\"kind\":\"isolated production-function microbenchmarks; not additive callback percentages or DAW proof\",\"sampleRate\":48000,\"voices\":16,\"modes\":[";
        for(int quality=0;quality<2;++quality){
            OrganismCore engine;engine.setParameter(110,quality);engine.setMorph(.5f);engine.setEnergy(.65f);engine.setMotion(.7f);engine.setMaterial(.65f);engine.prepare(48000,16);
            for(int i=0;i<16;++i)engine.noteOn(36+i,.65f,i);
            std::array<float,256> left{},right{};for(int i=0;i<100;++i)engine.render(left.data(),right.data(),256);
            double sink=0;
            const auto full=time(600,[&](int i){engine.setMorph(float(.5+.5*std::sin(i*.01)));engine.render(left.data(),right.data(),256);sink+=left[100];});
            // Force morph trait calculation to measure the actual moving-control path.
            const auto control=time(10000,[&](int i){engine.smooth_[0]=double(i%1000)/1000;engine.lastMorph_=-1;engine.refreshCoefficients();});
            const auto voice=time(100000,[&](int i){sink+=engine.voiceSample(engine.voices_[size_t(i&15)]);});
            const auto room=time(100000,[&](int){sink+=engine.room_.tick(.01,-.01,.3)[0];});
            if(quality)std::cout<<',';
            std::cout<<"{\"quality\":\""<<(quality?"HQ":"Eco")<<"\",\"render600CallbacksMs\":"<<full<<",\"movingControl10000CallsMs\":"<<control<<",\"voice100000SamplesMs\":"<<voice<<",\"room100000SamplesMs\":"<<room<<",\"outputChecksum\":"<<sink<<'}';
        }
        std::cout<<"]}\n";
    }
};
}
int main(){omega::CoreProfiler::run();}

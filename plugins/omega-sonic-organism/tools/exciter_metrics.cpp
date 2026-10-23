#include "omega/Exciter.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include <cstdlib>
#define CHECK(x) do { if (!(x)) { std::cerr << "FAIL " << __LINE__ << ": " << #x << '\n'; return 1; } } while(false)
int main(int argc,char** argv){
    CHECK(argc==2);const std::filesystem::path output(argv[1]);std::filesystem::create_directories(output);
    constexpr int frames=65536;omega::dsp::Tables table;table.prepare();
    std::array<double,8> weights{};double weight=0;
    for(size_t i=0;i<8;++i){weights[i]=1./double((i+1)*(i+1));weight+=weights[i];}
    for(auto& w:weights)w/=weight;
    std::ofstream manifest(output/"stimulus.json");CHECK(manifest);
    manifest << "{\"sampleRate\":48000,\"frames\":65536,\"window\":\"rectangular coherent\",\"blepImprovementLimitDb\":10,\"additiveResidualLimitDb\":-80,\"cases\":[";
    bool first=true;
    for(int bin:{17011,20011,24007,27011,30011}){
        const double step=double(bin)/frames;std::array<double,8> fades{};
        for(size_t k=0;k<8;++k)fades[k]=std::clamp((.48-step*double(k+1))/.06,0.,1.);
        std::array<std::vector<float>,5> data;for(auto& d:data)d.resize(frames);
        double phase=0;
        for(int n=0;n<frames;++n){
            const auto half=omega::dsp::Exciter::periodic(phase,step,.5,0.,weights,fades,table);
            data[0][size_t(n)]=float(2*phase-1);data[1][size_t(n)]=float(half.saw);
            data[2][size_t(n)]=phase<.5?1.f:-1.f;data[3][size_t(n)]=float(half.pulse);data[4][size_t(n)]=float(half.spectral);
            phase+=step;if(phase>=1)phase-=1;
        }
        const char* names[]={"saw-naive","saw-blep","pulse-naive","pulse-blep","additive"};
        for(size_t i=0;i<data.size();++i){
            const std::string name="bin-"+std::to_string(bin)+"-"+names[i]+".f32";
            for(float x:data[i])CHECK(std::isfinite(x));
            std::ofstream file(output/name,std::ios::binary);CHECK(file);
            file.write(reinterpret_cast<const char*>(data[i].data()),frames*sizeof(float));CHECK(file);
            if(!first)manifest << ',';first=false;
            manifest << "{\"file\":\"" << name << "\",\"bin\":" << bin << ",\"source\":\"" << names[i] << "\"}";
        }
    }
    manifest << "]}\n";CHECK(manifest);CHECK(table.nonFiniteFaults==0);
    std::cout << "Recorded 25 coherent 48 kHz production-exciter captures. Spectral acceptance requires analysis.\n";
}

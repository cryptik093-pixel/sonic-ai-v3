#include "omega/Preset.h"
#include "omega/OrganismCore.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <cstdlib>
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "<<#x<<'\n';std::exit(1);}}while(false)
namespace fs=std::filesystem;
std::array<double,2> measure(const omega::ParameterValues& params){
    double power=0,peak=0;size_t samples=0;
    for(int note:{36,48,60,72}){omega::OrganismCore engine;for(size_t i=0;i<params.size();++i)engine.setParameter(omega::parameterDefinitions[i].id,params[i]);engine.prepare(48000);engine.noteOn(note,.85f,7);
        std::array<float,256> l{},r{};for(int frame=0;frame<24000;frame+=256){int count=std::min(256,24000-frame);engine.render(l.data(),r.data(),count);for(int n=0;n<count;++n){CHECK(std::isfinite(l[n])&&std::isfinite(r[n]));power+=double(l[n])*l[n]+double(r[n])*r[n];peak=std::max(peak,std::max(std::abs(double(l[n])),std::abs(double(r[n]))));samples+=2;}}CHECK(engine.nonFiniteFaults()==0);}
    return {std::sqrt(power/samples),peak};
}
int main(int argc,char** argv){CHECK(argc==3||argc==4);bool apply=argc==4&&std::string(argv[3])=="--apply";std::vector<fs::path> paths;for(const auto& entry:fs::directory_iterator(argv[1]))if(entry.path().extension()==".json")paths.push_back(entry.path());std::sort(paths.begin(),paths.end());CHECK(paths.size()==30);
    std::ofstream report(argv[2]);CHECK(report);report<<"{\"method\":\"48000 Hz; MIDI 36/48/60/72; velocity .85; stereo RMS over first 500 ms per held note; target -32 dBFS; not a listening review\",\"targetDbfs\":-32,\"applied\":"<<(apply?"true":"false")<<",\"patches\":[";
    bool first=true;
    for(const auto& path:paths){std::ifstream in(path,std::ios::binary);const std::string document((std::istreambuf_iterator<char>(in)),{});in.close();omega::Preset p;std::string error;CHECK(omega::parsePreset(document,p,error));const auto initial=measure(p.params);auto measured=initial;
        if(apply){for(int iteration=0;iteration<3;++iteration){CHECK(measured[0]>1e-8);const double db=20*std::log10(measured[0]);p.params[5]=std::clamp(p.params[5]+(-32-db)/30.,0.,1.);measured=measure(p.params);}std::ofstream out(path,std::ios::binary);out<<omega::exportPreset(p);CHECK(out);}
        if(!first)report<<',';first=false;report<<"{\"file\":\""<<path.filename().string()<<"\",\"rmsDbfs\":"<<20*std::log10(measured[0])<<",\"peak\":"<<measured[1]<<",\"outputNormalized\":"<<p.params[5]<<'}';CHECK(measured[0]>1e-5&&measured[1]<=.98);std::cout<<path.filename().string()<<" rms="<<20*std::log10(measured[0])<<" dBFS peak="<<measured[1]<<'\n';}
    report<<"]}\n";CHECK(report);std::cout<<"PASS 30 patch measurements. Musical listening review remains separate.\n";
}

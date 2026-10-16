#include "dsp/Transitions.h"
#include "presets/FactoryBank.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <string>
#include <thread>
#include <vector>
namespace {
using Clock=std::chrono::steady_clock;
struct Result { std::string mode;double p50=0,p99=0,maximum=0,elapsed=0;uint64_t blocks=0;bool finite=true; };
Result measure(double rate,unsigned block,unsigned seconds,bool transitions,bool paced) {
    adlib93::Transitions engine;engine.prepare({rate,block,adlib93::ChannelLayout::stereoStereo},adlib93::factoryPresets()[23].parameters);
    engine.setTiming({120,4,4,true,true});
    const auto blocks=uint64_t(std::ceil(seconds*rate/block));std::vector<double> costs;costs.reserve(static_cast<size_t>(blocks));
    Result result;result.mode=transitions?"transitions":"steady";result.blocks=blocks;
    // All allocations, input generation and timing-vector writes are outside the measured DSP section.
    std::vector<adlib93::StereoFrame> input(block),output(block);uint64_t cursor=0;unsigned selected=23;
    const auto start=Clock::now();
    for(uint64_t b=0;b<blocks;++b){
        for(unsigned i=0;i<block;++i){const double t=(cursor+i)/rate;input[i]={float(.18*std::sin(2*3.141592653589793*137*t)),float(.17*std::sin(2*3.141592653589793*191*t))};}
        const bool change=transitions&&b%std::max<uint64_t>(1,uint64_t(rate*.075/block))==0;
        if(change)selected=(selected+1)%24;
        const auto begin=Clock::now();
        if(change)engine.request(adlib93::factoryPresets()[selected].parameters);
        for(unsigned i=0;i<block;++i)output[i]=engine.process(input[i]);
        const auto end=Clock::now();costs.push_back(std::chrono::duration<double,std::milli>(end-begin).count());
        for(auto y:output)if(!std::isfinite(y.left)||!std::isfinite(y.right))result.finite=false;
        cursor+=block;
        if(paced)std::this_thread::sleep_until(start+std::chrono::duration_cast<Clock::duration>(std::chrono::duration<double>(cursor/rate)));
    }
    result.elapsed=std::chrono::duration<double>(Clock::now()-start).count();std::sort(costs.begin(),costs.end());
    result.p50=costs[costs.size()/2];result.p99=costs[std::min(costs.size()-1,size_t(std::ceil(costs.size()*.99))-1)];result.maximum=costs.back();return result;
}
}
int main(int argc,char** argv){
    try{
        if(argc==2&&std::string(argv[1])=="--help"){std::cout<<"adlib93_benchmark --sample-rate 48000 --block-size 128 --seconds 600 --report <new.json> [--mode both|steady|transitions] [--paced true|false]\nDefault both: 600 seconds per mode, paced in wall time. Unpaced/short runs are diagnostic only.\n";return 0;}
        std::map<std::string,std::string> args;for(int i=1;i<argc;i+=2){if(i+1>=argc||!args.emplace(argv[i],argv[i+1]).second)throw std::runtime_error("Expected unique argument/value pairs");}
        for(const auto&a:args)if(a.first!="--sample-rate"&&a.first!="--block-size"&&a.first!="--seconds"&&a.first!="--report"&&a.first!="--mode"&&a.first!="--paced")throw std::runtime_error("Unknown benchmark argument");
        auto integer=[&](const char*key){size_t n=0;auto v=std::stoul(args.at(key),&n);if(n!=args.at(key).size())throw std::runtime_error("Invalid integer");return v;};
        const auto rate=integer("--sample-rate"),block=integer("--block-size"),seconds=integer("--seconds");const std::string mode=args.count("--mode")?args.at("--mode"):"both";
        const auto pacedText=args.count("--paced")?args.at("--paced"):"true";if(pacedText!="true"&&pacedText!="false")throw std::runtime_error("--paced must be true or false");const bool paced=pacedText=="true";
        if(rate<8000||rate>192000||block<1||block>8192||seconds<1||seconds>3600||(mode!="both"&&mode!="steady"&&mode!="transitions"))throw std::runtime_error("Benchmark arguments outside bounds");
        const std::filesystem::path report=args.at("--report");if(std::filesystem::exists(report))throw std::runtime_error("Report exists; preserving it");
        std::vector<Result> results;if(mode!="transitions")results.push_back(measure(rate,block,seconds,false,paced));if(mode!="steady")results.push_back(measure(rate,block,seconds,true,paced));
        const double deadline=1000.*block/rate;bool pass=true;for(auto&r:results)pass=pass&&r.finite&&r.p99<deadline*(r.mode=="steady"?.2:.4)&&r.maximum<deadline;
        const bool reference=rate==48000&&block==128&&seconds>=600&&paced&&mode=="both";
        std::ofstream out(report);if(!out)throw std::runtime_error("Cannot create benchmark report");
        out<<"{\n  \"schemaVersion\":1,\n  \"sampleRate\":"<<rate<<",\n  \"blockSize\":"<<block<<",\n  \"requestedSecondsPerMode\":"<<seconds<<",\n  \"paced\":"<<(paced?"true":"false")<<",\n  \"deadlineMilliseconds\":"<<deadline<<",\n  \"hardwareIdentityEvidence\":\"docs/ENVIRONMENT.md; record machine alongside this report\",\n  \"measurement\":\"steady_clock around request plus sample DSP only; preparation, generator, checks and pacing excluded; timer overhead not subtracted\",\n  \"cpuBudget\":\""<<(reference?(pass?"PASS":"FAIL"):"PENDING")<<"\",\n  \"diagnosticCriteriaMet\":"<<(pass?"true":"false")<<",\n  \"modes\":[\n";
        for(size_t i=0;i<results.size();++i){auto&r=results[i];out<<"    {\"mode\":\""<<r.mode<<"\",\"blocks\":"<<r.blocks<<",\"wallSeconds\":"<<r.elapsed<<",\"p50Milliseconds\":"<<r.p50<<",\"p99Milliseconds\":"<<r.p99<<",\"maxMilliseconds\":"<<r.maximum<<",\"finite\":"<<(r.finite?"true":"false")<<"}"<<(i+1==results.size()?"\n":",\n");}
        out<<"  ],\n  \"flStudio\":\"PENDING\",\n  \"listening\":\"PENDING\"\n}\n";if(!out)throw std::runtime_error("Benchmark report write failed");
        std::cout<<"Benchmark report: "<<report.string()<<"; CPU budget "<<(reference?(pass?"PASS":"FAIL"):"PENDING (diagnostic profile)")<<'\n';return reference&&!pass?1:0;
    }catch(const std::exception&e){std::cerr<<"Benchmark failed: "<<e.what()<<'\n';return 1;}
}

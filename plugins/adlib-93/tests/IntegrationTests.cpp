#include "TestSupport.h"
#include "dsp/Transitions.h"
#include "presets/FactoryBank.h"
#include <array>
#include <cmath>
#include <limits>
#include <random>
#include <vector>
namespace {
std::vector<adlib93::StereoFrame> render(unsigned block) {
    using namespace adlib93;Transitions dsp;dsp.prepare({48000,128,ChannelLayout::stereoStereo},factoryPresets()[4].parameters);
    constexpr size_t length=48000;std::vector<float> inL(length),inR(length),outL(length),outR(length);
    for(size_t n=0;n<length;++n){inL[n]=float(.1*std::sin(n*.031));inR[n]=float(.09*std::sin(n*.047));}
    auto p=factoryPresets()[4].parameters;size_t start=0;
    while(start<length){
        if(start==7000){p[Param::DelayTime]=173;dsp.setParameters(p);}if(start==11000){p[Param::StereoPan]=.31f;dsp.setParameters(p);}
        if(start==15000){p=factoryPresets()[16].parameters;dsp.request(p);}if(start==29000)dsp.clearTails();
        size_t end=std::min(length,start+block);for(size_t event:{7000u,11000u,15000u,29000u})if(event>start)end=std::min(end,event);
        const float* input[]={inL.data()+start,inR.data()+start};float* output[]={outL.data()+start,outR.data()+start};
        dsp.process(input,output,static_cast<uint32_t>(end-start),ProcessContext{{120,4,4,true,true},start});start=end;
    }
    std::vector<StereoFrame> result(length);for(size_t n=0;n<length;++n)result[n]={outL[n],outR[n]};return result;
}
}
TEST_CASE("Integration.OfflineParity") {
    const auto reference=render(128);
    for(unsigned block:{1u,17u,512u,4097u}){auto value=render(block);float error=0;for(size_t i=0;i<value.size();++i)error=std::max(error,std::max(std::abs(value[i].left-reference[i].left),std::abs(value[i].right-reference[i].right)));require(error<=1e-5f,"sample scheduled automation/preset/clear invariant to callback partition");}
}
TEST_CASE("Integration.Matrix") {
    using namespace adlib93;
    for(double rate:{44100.,48000.,88200.,96000.})for(auto layout:{ChannelLayout::monoMono,ChannelLayout::monoStereo,ChannelLayout::stereoStereo}){
        Transitions dsp;dsp.prepare({rate,128,layout},factoryPresets()[23].parameters);
        std::vector<float> left(4097,.01f),right(4097,-.02f),outL(4097),outR(4097);
        for(unsigned block:{0u,1u,16u,64u,128u,256u,512u,1024u,4097u}){
            const float* input[]={left.data(),right.data()};float* output[]={outL.data(),outR.data()};
            dsp.process(block?input:nullptr,block?output:nullptr,block,ProcessContext{});
            for(unsigned i=0;i<block;++i)require(std::isfinite(outL[i])&&std::isfinite(outR[i]),"sample/block/layout matrix finite");
        }
    }
}
TEST_CASE("Integration.Fuzz") {
    using namespace adlib93;Transitions dsp;dsp.prepare({48000,128,ChannelLayout::stereoStereo});auto p=makeInitSnapshot();std::mt19937 rng(93);
    const auto& defs=parameterDefinitions();
    for(unsigned i=0;i<10000;++i){const auto index=rng()%parameterCount;const auto& d=defs[index];const float fraction=float(rng()%10001)/10000;
        p.values[index]=d.min+fraction*(d.max-d.min);
        if(i%67==0)p.values[index]=std::numeric_limits<float>::quiet_NaN();if(i%97==0)p.values[index]=std::numeric_limits<float>::infinity();
        p=sanitizeSnapshot(p,48000);dsp.setParameters(p);if(i%23==0)dsp.request(factoryPresets()[rng()%24].parameters);if(i%101==0)dsp.clearTails();
        auto y=dsp.process({float(int(rng()%2001)-1000)/1000,float(int(rng()%2001)-1000)/1000});require(std::isfinite(y.left)&&std::isfinite(y.right),"10000 randomized operations finite");
    }
}

#include "TestSupport.h"
#include "dsp/OutputStage.h"
#include <cmath>
#include <limits>
using namespace adlib93;
TEST_CASE("Output.Ceiling") {
    OutputStage stage;stage.prepare({48000,128,ChannelLayout::stereoStereo});
    auto p=makeInitSnapshot();p[Param::OutputGain]=12;stage.setParameters(p);
    const float ceiling=static_cast<float>(std::pow(10.0,-1.0/20));
    for(int i=0;i<10000;++i) {
        const auto out=stage.process({15.848932f*std::sin(i*.17f),4.0f*std::sin(i*.13f)});
        require(std::abs(out.left)<=ceiling+1e-6f && std::abs(out.right)<=ceiling+1e-6f,"limiter must bound both samples after output gain");
    }
}
TEST_CASE("Output.Linked") {
    OutputStage stage;stage.prepare({48000,128,ChannelLayout::stereoStereo});stage.setParameters(makeInitSnapshot());
    auto out=stage.process({4,1});require(std::abs(out.left-4*out.right)<1e-6f,"identical stereo limiter gain");
}
TEST_CASE("Output.Exceptional") {
    OutputStage stage;stage.prepare({48000,128,ChannelLayout::stereoStereo});auto p=makeInitSnapshot();p[Param::LimiterEnabled]=0;stage.setParameters(p);
    auto out=stage.process({2,-3});require(out.left==2 && out.right==-3,"disabled limiter must not secretly clip ordinary audio");
    out=stage.process({std::numeric_limits<float>::quiet_NaN(),std::numeric_limits<float>::infinity()});require(out.left==0 && out.right==0,"nonfinite input becomes zero");
}

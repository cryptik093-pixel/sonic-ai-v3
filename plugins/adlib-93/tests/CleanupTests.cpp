#include "TestSupport.h"
#include "dsp/Cleanup.h"
#include <cmath>
using namespace adlib93;
TEST_CASE("Cleanup.Gate") {
 for(double rate:{44100.,48000.,88200.,96000.}) {auto p=makeInitSnapshot();p[Param::GateEnabled]=1;p[Param::GateThreshold]=-30;p[Param::GateHold]=0;p[Param::GateAttack]=2;p[Param::GateRelease]=20;p[Param::GateAttenuation]=40;Cleanup c;c.setParameters(p);c.prepare({rate,128,ChannelLayout::stereoStereo});for(int n=0;n<int(rate);++n)c.process({.1f,.05f});require(c.measurements().gateReductionDb<.001f,"gate opens on either channel");for(int n=0;n<int(rate*.12);++n)c.process({0,0});require(c.measurements().gateReductionDb>39.5f,"gate release settles within five tau after detector fall");for(int n=0;n<int(rate*.02);++n)c.process({0,.1f});require(c.measurements().gateReductionDb<.01f,"stereo linked gate opens from right");}
}
TEST_CASE("Cleanup.Deess") {
 for(double rate:{44100.,48000.,88200.,96000.}){auto p=makeInitSnapshot();p[Param::DeessEnabled]=1;p[Param::DeessMaxReduction]=0;Cleanup c;c.setParameters(p);c.prepare({rate,128,ChannelLayout::stereoStereo});for(int n=0;n<5000;++n){float x=float(std::sin(n*.27)*.4);auto y=c.process({x,-x*.3f});require(y.left==x&&y.right==-x*.3f,"zero reduction reconstructs exactly");}p[Param::DeessMaxReduction]=6;p[Param::DeessThreshold]=-40;c.setParameters(p);for(int n=0;n<int(rate);++n)c.process({float(.8*std::sin(6.283185307179586*10000*n/rate)),0});require(c.measurements().deessReductionDb>5.9f&&c.measurements().deessReductionDb<=6.0001f,"linked high band reduction bounded and active");}
}
TEST_CASE("Cleanup.Listen") {auto p=makeInitSnapshot();Cleanup c;c.setParameters(p);c.prepare({48000,128,ChannelLayout::stereoStereo});c.process({1,.5f});auto h=c.highBand();require(h.left>0&&h.left<1&&std::abs(h.right-h.left*.5f)<1e-6,"diagnostic exposes complementary linked high band");}

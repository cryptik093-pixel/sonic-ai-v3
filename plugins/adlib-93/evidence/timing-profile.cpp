#include "dsp/Cleanup.h"
#include "dsp/Character.h"
#include "dsp/Movement.h"
#include "dsp/Echo.h"
#include "dsp/Space.h"
#include "dsp/OutputStage.h"
#include "dsp/Transitions.h"
#include "presets/FactoryBank.h"
#include <chrono>
#include <algorithm>
#include <array>
#include <cmath>
#include <iostream>
#include <vector>
using namespace adlib93;
volatile double sink=0;
template<class F> void measure(const char* name,F run,bool comma=true){std::vector<double> times;times.reserve(1000);for(int b=0;b<1000;++b){double sum=0;auto start=std::chrono::steady_clock::now();for(int n=0;n<128;++n)sum+=run(n);auto stop=std::chrono::steady_clock::now();sink=sum;times.push_back(std::chrono::duration<double,std::milli>(stop-start).count());}std::sort(times.begin(),times.end());std::cout<<"{\"module\":\""<<name<<"\",\"p50Milliseconds\":"<<times[500]<<",\"p99Milliseconds\":"<<times[989]<<",\"maxMilliseconds\":"<<times.back()<<"}"<<(comma?",\n":"\n");}
int main(){PrepareSpec spec{48000,128,ChannelLayout::stereoStereo};const auto p=factoryPresets()[23].parameters;std::array<StereoFrame,128> input;for(int n=0;n<128;++n)input[n]={float(.18*std::sin(6.283185307179586*137*n/48000)),float(.17*std::sin(6.283185307179586*191*n/48000))};Cleanup cleanup;Character character;Movement movement;Echo echo;Space space;OutputStage output;Transitions engine;cleanup.prepare(spec);cleanup.setParameters(p);cleanup.reset();character.prepare(spec);character.setParameters(p);character.reset();movement.prepare(spec);movement.setParameters(p);movement.reset();echo.prepare(spec);echo.setParameters(p);space.prepare(spec);space.setParameters(p);output.prepare(spec);output.setParameters(p);output.reset();engine.prepare(spec,p);std::cout<<"{\"profileOnly\":true,\"acceptance\":false,\"method\":\"1000 unpaced blocks per production module, fixed generated 128-frame input repeated; isolated module inputs differ from full chain; not a replacement for reference run\",\"modules\":[\n";measure("Cleanup",[&](int n){return cleanup.process(input[n]).left;});measure("Character",[&](int n){return character.process(input[n]).left;});measure("Movement",[&](int n){return movement.processBranches(input[n]).doubler.left;});measure("Echo",[&](int n){return echo.process(input[n],0).left;});measure("Space",[&](int n){return space.process(input[n],{},input[n]).reverb.left;});measure("OutputStage",[&](int n){return output.process(input[n]).left;});measure("Transitions",[&](int n){return engine.process(input[n]).left;},false);std::cout<<"]}\n";}

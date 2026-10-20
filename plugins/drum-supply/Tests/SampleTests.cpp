#include "SampleEngine.h"
#include <iostream>
#include <cstdlib>
#include <random>
void check(bool b,const char* message){if(!b){std::cerr<<"FAIL "<<message<<'\n';std::exit(1);}}
ohsample::Sample sample(double rate,bool stereo=true){ohsample::Sample s;s.rate=rate;for(auto& ch:s.audio)ch.resize(static_cast<size_t>(rate));for(size_t i=0;i<s.frames();++i){const float t=static_cast<float>(i/rate);s.audio[0][i]=.5f*std::sin(t*440*6.2831853f);s.audio[1][i]=stereo?.3f*std::sin(t*660*6.2831853f):s.audio[0][i];}return s;}
double energy(const std::vector<float>& a){double result=0;for(float x:a){check(std::isfinite(x),"finite output");result+=x*x;}return result;}
std::vector<float> render(const ohsample::Sample& data,double rate,ohsample::Controls c={},ohsample::Mix m={.5f,.5f,0,0},float velocity=1){ohsample::Engine e;e.setControls({c,c,c,c,c,c,c},m);e.prepare(rate);e.replace({&data,&data,&data,&data,&data,&data,&data});e.trigger(0,velocity);std::vector<float> r;for(int i=0;i<static_cast<int>(rate*1.2);++i)r.push_back(e.tick()[0]);return r;}
int main(){int scenarios=0;for(double assetRate:{44100.,48000.,96000.,192000.})for(double hostRate:{44100.,48000.,96000.,192000.})for(bool stereo:{false,true}){
    auto s=sample(assetRate,stereo);ohsample::Controls c;c.gain=0;c.release=0;
    auto audio=render(s,hostRate,c);check(energy(audio)>100,"sample audible after conversion");
    int crossings=0;for(size_t i=100;i<static_cast<size_t>(hostRate*.5);++i)if(audio[i-1]<=0&&audio[i]>0)++crossings;check(std::abs(crossings-219)<=3,"pitch correct across sample-rate conversion");
    const auto quiet=render(s,hostRate,c,{.5f,.5f,0,0},.5f);check(std::abs(energy(quiet)/energy(audio)-.25)<1.e-5,"velocity amplitude contract");
    c.pan=1;check(energy(render(s,hostRate,c))==0,"right pan isolates left channel");c.pan=0;c.mute=1;check(energy(render(s,hostRate,c))==0,"mute silences dry output");++scenarios;}
    auto s=sample(48000);ohsample::Controls c;c.gain=0;c.release=0;const auto dry=render(s,48000,c);
    c.tune=12;auto pitched=render(s,48000,c);int crossing=0;for(int i=100;i<24000;++i)if(pitched[static_cast<size_t>(i-1)]<=0&&pitched[static_cast<size_t>(i)]>0)++crossing;check(crossing>430&&crossing<445,"octave tune");
    c.tune=0;c.start=.25f;c.end=.5f;auto region=render(s,48000,c);for(size_t i=13000;i<region.size();++i)check(region[i]==0,"region end terminates voice");
    c={};c.reverse=1;check(energy(render(s,48000,c))>1,"reverse audible");
    for(auto mix:{ohsample::Mix{0,0,0,0},ohsample::Mix{1,1,1,0}}){auto a=render(s,48000,{},mix);check(a!=dry,"macros change sample processing");}
    ohsample::Engine engine;engine.prepare(48000);engine.replace({&s,&s,&s,&s,&s,&s,&s});
    for(int i=0;i<16;++i)engine.trigger(i%7,1);for(int i=0;i<1000;++i)check(std::isfinite(engine.tick()[0]),"dense output finite");engine.panic();for(int i=0;i<144000;++i)engine.tick();check(std::abs(engine.tick()[0])<1.e-8,"panic bounded release and ambience decay");
    engine.trigger(0,1);engine.panic(true);check(engine.tick()[0]==0,"All Sound Off clears audio");
    engine.replace({});engine.trigger(0,1);check(engine.tick()[0]==0,"missing sample is silent");
    c.tune=NAN;c.gain=INFINITY;c.pan=-INFINITY;c.filter=NAN;engine.setControls({c,c,c,c,c,c,c},{NAN,INFINITY,-INFINITY,NAN});engine.replace({&s,&s,&s,&s,&s,&s,&s});engine.trigger(0,1);for(int i=0;i<4096;++i)check(std::isfinite(engine.tick()[0]),"non-finite parameter fuzz contained");
    std::cout<<"PASS "<<scenarios<<" asset/host/channel scenarios; rate conversion, velocity, pan, mute, tune, region, reverse, macros, polyphony and panic\n";
}

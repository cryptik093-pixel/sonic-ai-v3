#include "omega/OrganismCore.h"
#include <algorithm>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <new>
#ifdef _WIN32
#include <malloc.h>
#endif
#include <vector>
static thread_local bool measuring=false;
static size_t allocations=0;
static size_t deallocations=0;
void* operator new(size_t n){if(measuring)++allocations;if(void* p=std::malloc(n?n:1))return p;throw std::bad_alloc();}
void* operator new[](size_t n){return ::operator new(n);}
void operator delete(void* p) noexcept {if(measuring&&p)++deallocations;std::free(p);}
void operator delete[](void* p) noexcept {::operator delete(p);}
void operator delete(void* p,size_t) noexcept {::operator delete(p);}
void operator delete[](void* p,size_t) noexcept {::operator delete(p);}
#ifdef _WIN32
void* operator new(size_t n,std::align_val_t alignment){if(measuring)++allocations;if(void* p=_aligned_malloc(n?n:1,size_t(alignment)))return p;throw std::bad_alloc();}
void* operator new[](size_t n,std::align_val_t alignment){return ::operator new(n,alignment);}
void operator delete(void* p,std::align_val_t) noexcept {if(measuring&&p)++deallocations;_aligned_free(p);}
void operator delete[](void* p,std::align_val_t a) noexcept {::operator delete(p,a);}
void operator delete(void* p,size_t,std::align_val_t a) noexcept {::operator delete(p,a);}
void operator delete[](void* p,size_t,std::align_val_t a) noexcept {::operator delete(p,a);}
#endif
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<" "<<#x<<'\n';std::exit(1);}}while(false)
size_t checks=0;
double contextRate=0,contextQuality=0;int contextNote=-1;
void finite(omega::OrganismCore& synth,int count=512){
    std::array<float,512> l{},r{};
    measuring=true;synth.render(l.data(),r.data(),count);measuring=false;
    for(int n=0;n<count;++n){CHECK(std::isfinite(l[n])&&std::isfinite(r[n]));CHECK(std::abs(l[n])<=.98f&&std::abs(r[n])<=.98f);++checks;}
    if(synth.nonFiniteFaults())std::cerr<<"Context sr="<<contextRate<<" quality="<<contextQuality<<" note="<<contextNote<<" source="<<synth.firstFaultSource()<<" faults="<<synth.nonFiniteFaults()<<'\n';
    CHECK(synth.nonFiniteFaults()==0);
}
std::vector<float> capture(uint32_t id,double value,double morph=.5){
    omega::OrganismCore synth;synth.setMorph(float(morph));synth.setParameter(id,value);synth.prepare(48000);
    synth.noteOn(48,.85f);std::vector<float> l(32768),r(l.size());
    for(size_t n=0;n<l.size();n+=256){measuring=true;synth.render(l.data()+n,r.data()+n,256);measuring=false;}
    CHECK(synth.nonFiniteFaults()==0);return l;
}
double difference(const std::vector<float>& a,const std::vector<float>& b){double e=0;for(size_t i=0;i<a.size();++i)e+=std::abs(a[i]-b[i]);return e;}
int main(){
    omega::dsp::Tables table;table.prepare();
    // Compare the shipping polyphase implementation against the original
    // literal zero-insertion + FIR + decimation algorithm, including resets.
    for(double drive:{.5,1.,3.,6.}){
        omega::dsp::DriveStage optimized;omega::dsp::HalfBand31 referenceUp,referenceDown;uint32_t noise=17;
        for(int n=0;n<24000;++n){noise=noise*1664525u+1013904223u;double x=(double(noise)/4294967295.-.5)*1.4;
            double a=referenceUp.tick(2*x,table.halfband);double expected=referenceDown.tick(table.saturate(a*drive),table.halfband);double b=referenceUp.tick(0,table.halfband);referenceDown.tick(table.saturate(b*drive),table.halfband);
            CHECK(std::abs(optimized.tick(x,drive,1,1,table)-expected)<1e-12);
            if(n==12000){optimized.resetHQ();referenceUp.reset();referenceDown.reset();}}
    }
    for(int n=0;n<10000;++n){const double x=(n-5000)/700.;CHECK(std::abs(table.saturate(x)-std::tanh(x))<1e-6);}
    omega::dsp::HalfBand31 up,down;std::array<double,96> response{};
    for(size_t n=0;n<response.size();++n){const double a=up.tick(n==0?2.:0.,table.halfband);response[n]=down.tick(a,table.halfband);down.tick(up.tick(0,table.halfband),table.halfband);}
    CHECK(std::max_element(response.begin(),response.end())-response.begin()==omega::OrganismCore::latencySamples);
    double impulseSum=0;for(double x:response)impulseSum+=x;CHECK(std::abs(impulseSum-1)<1e-6);
    for(double rate:{44100.,48000.,88200.,96000.,192000.})for(double quality:{0.,1.}){
        omega::OrganismCore synth;synth.setParameter(110,quality);synth.prepare(rate,32);
        for(int note=0;note<128;++note){contextRate=rate;contextQuality=quality;contextNote=note;synth.setMorph(float(note/127.));synth.noteOn(note,.9f,note);finite(synth,127);}
        for(int k=0;k<32;++k){synth.setMorph(float((k%9)/8.));for(uint32_t id=101;id<=108;++id)synth.setParameter(id,(k+int(id))&1);finite(synth,256);}
        measuring=true;synth.setParameter(110,1-quality);synth.setVoiceLimit(8);synth.setSustain(true);synth.allNotesOff();synth.resetVoices();measuring=false;
        CHECK(synth.activeVoices()==0);CHECK(synth.nonFiniteFaults()==0);
    }
    for(uint32_t id:{100u,101u,102u,103u,104u,105u,106u,113u}){
        auto a=capture(id,0),b=capture(id,1);CHECK(difference(a,b)>.01);
    }
    CHECK(difference(capture(110,0),capture(110,1))>1e-5);
    // Morph must retain the voice and continue its current envelope.
    omega::OrganismCore morph;morph.setMorph(.5f);morph.setMotion(0);morph.prepare(48000);morph.noteOn(48,.9f,1);for(int n=0;n<20;++n)finite(morph);
    const auto serial=morph.voiceSerial();double lastEnvelope=morph.currentEnvelope();std::array<float,1> oneL{},oneR{};
    for(int n=0;n<8192;++n){if(n%64==0)morph.setMorph(float((n/64)%9/8.));morph.render(oneL.data(),oneR.data(),1);CHECK(morph.voiceSerial()==serial);CHECK(std::abs(morph.currentEnvelope()-lastEnvelope)<.005);lastEnvelope=morph.currentEnvelope();}CHECK(morph.nonFiniteFaults()==0);
    auto motionCapture=[](bool sync,double tempo){omega::OrganismCore s;s.setMorph(.5f);s.setMotion(.8f);s.setParameter(112,sync?1:0);s.setTempo(tempo);s.prepare(48000);s.noteOn(60,.9f);std::vector<float> l(16384),r(l.size());s.render(l.data(),r.data(),int(l.size()));return l;};
    const auto free=motionCapture(false,60),sync120=motionCapture(true,120),sync60=motionCapture(true,60);CHECK(free==sync120);CHECK(difference(sync60,sync120)>.01);
    auto bendCapture=[](double range){omega::OrganismCore s;s.setMorph(.5f);s.setMotion(0);s.setParameter(111,range);s.setPitchBend(1);s.prepare(48000);s.setPitchBend(1);s.noteOn(60,.9f);std::vector<float> l(8192),r(l.size());s.render(l.data(),r.data(),int(l.size()));return l;};CHECK(difference(bendCapture(0),bendCapture(1))>.01);
    omega::OrganismCore steal;steal.setParameter(109,0);steal.setMorph(.5f);steal.setMotion(0);steal.prepare(48000);steal.noteOn(48,1,1);std::array<float,4096> stealL{},stealR{};steal.render(stealL.data(),stealR.data(),4096);steal.noteOn(72,1,2);steal.render(oneL.data(),oneR.data(),1);CHECK(std::abs(oneL[0]-stealL.back())<1e-4);
    omega::OrganismCore mono;mono.setParameter(109,0);mono.setParameter(114,1);mono.setParameter(108,.05);mono.prepare(48000);
    mono.noteOn(48,1,1);finite(mono);mono.noteOn(60,1,2);CHECK(mono.currentPitch()==48);
    for(int n=0;n<10;++n)finite(mono);CHECK(std::abs(mono.currentPitch()-60)<1e-9);
    mono.noteOff(60,2);for(int n=0;n<10;++n)finite(mono);CHECK(std::abs(mono.currentPitch()-48)<1e-9);CHECK(mono.activeVoices()==1);
    mono.setSustain(true);mono.noteOff(48,1);for(int n=0;n<20;++n)finite(mono);CHECK(mono.activeVoices()==1);
    mono.setSustain(false);for(int n=0;n<100;++n)finite(mono);CHECK(mono.activeVoices()==0);
    omega::OrganismCore overlap;overlap.prepare(48000);overlap.noteOn(60,1,11);overlap.noteOn(60,1,12);overlap.noteOff(60,11);
    for(int n=0;n<100;++n)finite(overlap);CHECK(overlap.activeVoices()==1);overlap.noteOff(60,12);for(int n=0;n<100;++n)finite(overlap);CHECK(overlap.activeVoices()==0);
    omega::OrganismCore shortRelease,longRelease;shortRelease.setParameter(107,0);longRelease.setParameter(107,1);shortRelease.prepare(48000);longRelease.prepare(48000);
    shortRelease.noteOn(60,1);longRelease.noteOn(60,1);for(int n=0;n<10;++n){finite(shortRelease);finite(longRelease);}shortRelease.noteOff(60);longRelease.noteOff(60);
    for(int n=0;n<15;++n){finite(shortRelease);finite(longRelease);}CHECK(shortRelease.activeVoices()==0);CHECK(longRelease.activeVoices()==1);
    // A held zero-sustain percussion note must reach exact zero rather than
    // spending the rest of its life in a subnormal envelope tail. Use the
    // supported 8 kHz lower bound to cover sixty seconds at low test cost.
    omega::OrganismCore longHeld;longHeld.setMorph(1);longHeld.prepare(8000);longHeld.noteOn(36,.8f,99);
    for(int block=0;block<1875;++block){finite(longHeld,256);CHECK(std::fpclassify(longHeld.currentEnvelope())!=FP_SUBNORMAL);}
    CHECK(longHeld.currentEnvelope()==0);
    // A silent held identity must still become audible when morphed back to
    // a sustaining structure, without allocating or restarting its voice.
    const auto heldSerial=longHeld.voiceSerial();longHeld.setMorph(.75f);
    std::array<float,256> revivedL{},revivedR{};double revivedPower=0;
    for(int block=0;block<64;++block){measuring=true;longHeld.render(revivedL.data(),revivedR.data(),256);measuring=false;for(float x:revivedL){CHECK(std::isfinite(x));revivedPower+=double(x)*x;}}
    CHECK(revivedPower>1e-5);CHECK(longHeld.voiceSerial()==heldSerial);CHECK(longHeld.activeVoices()==1);CHECK(longHeld.nonFiniteFaults()==0);
    // Identical sample-timed events and automation must produce identical
    // stereo samples regardless of the surrounding host block partition.
    for(double rate:{44100.,48000.,96000.})for(double quality:{0.,1.}) {
        auto partitioned=[&](int blockSize) {
            omega::OrganismCore engine;engine.setParameter(110,quality);engine.prepare(rate,8);
            std::vector<float> audio(8192*2),l(1024),r(1024);
            const int boundaries[]={0,127,251,509,1021,2047,4093,8192};
            int at=0;
            for(int segment=0;segment<7;++segment) {
                measuring=true;
                switch(segment) {
                case 0:engine.noteOn(48,.8f,11);break;
                case 1:engine.setMorph(.25f);engine.noteOn(60,.6f,12);break;
                case 2:engine.setParameter(110,1-quality);break;
                case 3:engine.noteOff(48,11);engine.setPitchBend(.5f);break;
                case 4:engine.setMorph(.75f);engine.setTempo(173);break;
                case 5:engine.noteOff(60,12);break;
                case 6:engine.allNotesOff();break;
                }
                measuring=false;
                CHECK(at==boundaries[segment]);
                while(at<boundaries[segment+1]) {
                    const int count=std::min(blockSize,boundaries[segment+1]-at);
                    measuring=true;engine.render(l.data(),r.data(),count);measuring=false;
                    for(int n=0;n<count;++n){audio[size_t((at+n)*2)]=l[size_t(n)];audio[size_t((at+n)*2+1)]=r[size_t(n)];}
                    at+=count;
                }
            }
            CHECK(engine.nonFiniteFaults()==0);return audio;
        };
        const auto reference=partitioned(1);
        for(int size:{64,256,1024})CHECK(partitioned(size)==reference);
    }
    CHECK(allocations==0);
    CHECK(deallocations==0);
    std::cout<<"PASS engine checks: "<<checks<<" finite sample pairs; fixed FIR latency/unity; macro response; five rates/both quality modes; mono glide/legato; sustain; duplicate notes; release; zero C++ allocations in measured realtime operations.\n";
}

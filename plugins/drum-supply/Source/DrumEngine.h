#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <vector>
#include <cstring>
#include "SampleData.h"

namespace ohdrum {
enum class Department { kick, snare, hat, cymbal, tom, percussion, clap };
inline constexpr std::array<const char*,7> names{"Kick","Snare","Hi-Hat","Cymbal","Tom","Percussion","Clap"};
inline constexpr std::array<const char*,8> slotNames{"Kick","Snare","Closed Hat","Cymbal","Tom","Percussion","Clap","Open Hat"};
inline constexpr std::array<int,8> defaultNotes{36,38,42,49,45,56,39,46};
struct SlotControls {
    float tune=0,gain=-6,pan=0,start=0,end=1,attack=0,release=30,filter=20000,reverse=0,mute=0,solo=0;
    float punch=.5f,tone=.5f,texture=.5f,decay=1,pitchDepth=1,pitchTime=28.5f,blend=0,sampleLevel=0,note=36,choke=0,velocityTone=0;
};
struct Macros { float body=.5f, character=.5f, space=.25f; };
inline float unit(float x) noexcept { return std::isfinite(x)?std::clamp(x,0.0f,1.0f):.5f; }
inline int departmentForNote(int note) noexcept {
    switch(note) { case 35: case 36: return 0; case 38: case 40: return 1;
    case 42: case 44: case 46: return 2; case 49: case 51: case 57: return 3;
    case 41: case 43: case 45: case 47: case 48: case 50: return 4;
    case 39: return 6; default: return 5; }
}

// Audio-thread-owned modal/oscillator instrument. No sample loader, file access,
// mutex, randomness service or allocation in trigger()/tick(). Fixed 16 voices.
class Engine {
    struct Voice {
        bool active=false;
        int type=0, age=0, note=36, slot=-1;
        float fade=1, filtered=0, volume=.5f, sampleGain=1, pan=0, filterCoefficient=1;
        bool releasing=false;
        const ohsample::Sample* sample=nullptr;
        double samplePosition=0,sampleStep=1,sampleFirst=0,sampleLast=0;
        SlotControls shot{};
        float velocity=0, noiseLow=0, noiseHigh=0, pitch=1, pitchDecay=1;
        float noiseEnv=1, noiseDecay=1, lowCoefficient=.2f, highCoefficient=.2f;
        float pitchDepth=0, transient=1, transientDecay=1, tonalMix=.5f;
        float lastOutput=0,stolenOutput=0;
        int stolenFrames=0;
        uint32_t seed=1;
        std::array<float,8> sine{},cosine{1,1,1,1,1,1,1,1};
        std::array<float,8> stepSine{},stepCosine{},envelope{},decay{},frequency{};
        SlotControls mapped{};float mappedBody=-1,mappedCharacter=-1;bool mappedValid=false;
    };
    double rate=48000;
    bool slotMode=false;
    std::array<SlotControls,8> slots{},smoothSlots{};
    std::array<const ohsample::Sample*,8> samples{};
    float outputDb=-6,smoothedOutput=-6;
    bool clipFlag=false;
    std::array<float,2> lastOutput{},transitionOutput{};int transitionFrames=0,transitionLength=1;
    float finalGain=.5f;
    std::array<Voice,16> voices{};
    // Never rendered: fixed onset coefficient templates, with no sample ownership.
    std::array<Voice,8> onsetCoefficients{};
    Macros target{}, current{};
    float smoothing=0;
    uint64_t frame=0;
    std::array<std::vector<float>,2> delay;
    size_t write=0;
    int ambienceDepartment=0;
    float dampL=0,dampR=0;
    static constexpr double pi=3.14159265358979323846;
    float coefficient(float seconds) const noexcept { return std::exp(-1.0f/(static_cast<float>(rate)*seconds)); }
    static size_t modeCount(int type) noexcept {return type==0?2u:type==2?6u:8u;}
    void map(Voice& v) noexcept {
        const bool assigned=v.slot>=0;
        const auto& sc=assigned?smoothSlots[static_cast<size_t>(v.slot)]:smoothSlots[0];
        const float b=assigned?unit(sc.tone+current.body-.5f+sc.velocityTone*(v.velocity-.5f)*.4f):current.body;
        const float c=assigned?unit(sc.texture+current.character-.5f):current.character;
        static_assert(sizeof(SlotControls)==22*sizeof(float));
        const bool changed=!v.mappedValid||b!=v.mappedBody||c!=v.mappedCharacter||(assigned&&std::memcmp(&sc,&v.mapped,sizeof(sc))!=0);
        const auto count=modeCount(v.type);
        if(changed){
        // Each department owns a different mapping; BODY is not a generic EQ.
        float base=60, duration=.3f, noiseTime=.1f;
        std::array<float,8> ratios{1,2,3,4,5,6,7,8};
        switch(v.type) {
        case 0: base=38+42*b; duration=.09f+.65f*b; noiseTime=.004f+.012f*c;
            ratios={1,2.01f,3.98f,5,6,7,8,9};v.tonalMix=.92f-.22f*c;
            v.pitchDepth=1+5*c; break;
        case 1: base=130+150*b;duration=.045f+.24f*b;noiseTime=.07f+.21f*b;
            ratios={1,1.59f,2.31f,3.79f,5.1f,6.3f,7.9f,9};v.tonalMix=.68f-.52f*c;
            v.pitchDepth=.12f+.8f*c;break;
        case 2: base=650+900*b;duration=.018f+.18f*b;noiseTime=duration;
            ratios={1,1.342f,1.743f,2.13f,2.89f,3.93f,4.63f,5.17f};v.tonalMix=.82f-.48f*c;
            v.pitchDepth=0;break;
        case 3: base=270+480*b;duration=.35f+1.6f*b;noiseTime=.2f+1.1f*b;
            ratios={1,1.483f,2.173f,3.117f,4.391f,5.83f,7.13f,9.719f};v.tonalMix=.8f-.45f*c;
            v.pitchDepth=.02f*c;break;
        case 4: base=(65+110*b)*std::pow(2.0f,static_cast<float>(v.note-45)/24);
            duration=.12f+.65f*b;noiseTime=.012f+.03f*c;
            ratios={1,1.593f,2.136f,2.653f,3.16f,3.6f,4.2f,4.8f};v.tonalMix=.96f-.22f*c;
            v.pitchDepth=.3f+1.2f*c;break;
        case 5: base=180+650*b;duration=.05f+.65f*b;noiseTime=.015f+.075f*c;
            // Continuous wood -> membrane -> metal material morph.
            ratios={1,1.45f+c*.67f,2.05f+c*1.26f,2.8f+c*2.05f,3.9f+c*2.6f,5.2f+c*2.7f,6.3f+c*3,8.1f+c*3.8f};
            v.tonalMix=.9f-.2f*c;v.pitchDepth=.06f;break;
        default: base=450+850*b;duration=.03f+.11f*b;noiseTime=.035f+.12f*b;
            ratios={1,1.4f,2.3f,3.2f,4.6f,5.7f,6.8f,8};v.tonalMix=.03f+.09f*(1-c);
            v.pitchDepth=0;break;
        }
        if(assigned){
            base*=std::pow(2.0f,sc.tune/12);duration*=sc.decay;noiseTime*=sc.decay;
            if(v.slot==7){duration*=3.0f;noiseTime*=3.0f;}
            v.pitchDepth*=sc.pitchDepth*(.5f+sc.punch);
            v.volume=std::pow(10.0f,sc.gain*.05f)*(1-sc.mute);v.sampleGain=std::pow(10.0f,sc.sampleLevel*.05f);v.pan=sc.pan;
            v.filterCoefficient=1-std::exp(-2*static_cast<float>(pi)*std::min(sc.filter,static_cast<float>(rate)*.45f)/static_cast<float>(rate));
        }
        for(size_t i=0;i<count;++i){
            v.frequency[i]=std::min(base*ratios[i],static_cast<float>(rate)*(v.type==2?.22f:.42f));
            const float spectralDecay=1+static_cast<float>(i)*(.12f+.45f*(1-c));
            v.decay[i]=coefficient(duration/spectralDecay);
        }
        v.pitchDecay=coefficient(assigned?std::max(.002f,sc.pitchTime*.001f):.006f+.045f*b);
        v.noiseDecay=coefficient(noiseTime);
        v.transientDecay=coefficient(.0015f+.006f*c);
        const float lowHz=(v.type==0?1800.0f:v.type==4?2200.0f:4500.0f)+c*6500;
        const float highHz=(v.type==0?80.0f:v.type==1?650.0f:v.type==6?800.0f:2200.0f)*(1.2f-.6f*b);
        v.lowCoefficient=1-std::exp(-2*static_cast<float>(pi)*std::min(lowHz,static_cast<float>(rate)*.4f)/static_cast<float>(rate));
        v.highCoefficient=1-std::exp(-2*static_cast<float>(pi)*std::min(highHz,static_cast<float>(rate)*.2f)/static_cast<float>(rate));
        v.mapped=sc;v.mappedBody=b;v.mappedCharacter=c;v.mappedValid=true;
        }
        for(size_t i=0;i<count;++i){
            if(changed||v.pitchDepth!=0){
                const float hz=std::min(v.frequency[i]*(1+v.pitch*v.pitchDepth),static_cast<float>(rate)*.45f);
                const double angle=2*pi*hz/rate;
                v.stepSine[i]=static_cast<float>(std::sin(angle));v.stepCosine[i]=static_cast<float>(std::cos(angle));
            }
            const float normalization=1.5f-.5f*(v.sine[i]*v.sine[i]+v.cosine[i]*v.cosine[i]);
            v.sine[i]*=normalization;v.cosine[i]*=normalization;
        }
    }
    static void copyCoefficients(Voice& v,const Voice& cached) noexcept {
        v.pitchDecay=cached.pitchDecay;v.noiseDecay=cached.noiseDecay;v.lowCoefficient=cached.lowCoefficient;v.highCoefficient=cached.highCoefficient;
        v.pitchDepth=cached.pitchDepth;v.transientDecay=cached.transientDecay;v.tonalMix=cached.tonalMix;
        v.volume=cached.volume;v.sampleGain=cached.sampleGain;v.pan=cached.pan;v.filterCoefficient=cached.filterCoefficient;
        v.stepSine=cached.stepSine;v.stepCosine=cached.stepCosine;v.decay=cached.decay;v.frequency=cached.frequency;
        v.mapped=cached.mapped;v.mappedBody=cached.mappedBody;v.mappedCharacter=cached.mappedCharacter;v.mappedValid=true;
    }
    void beginTransition() noexcept {const auto previous=std::max(std::abs(lastOutput[0]),std::abs(lastOutput[1]))>1.e-8f?lastOutput:(transitionFrames>0?transitionOutput:lastOutput);reset();transitionOutput=previous;transitionLength=std::max(1,static_cast<int>(rate*.002));transitionFrames=std::max(std::abs(previous[0]),std::abs(previous[1]))>1.e-8f?transitionLength:0;}
public:
    void snapControls() noexcept {smoothSlots=slots;current=target;smoothedOutput=outputDb;finalGain=std::pow(10.0f,smoothedOutput*.05f);beginTransition();}
    bool clipped() const noexcept {return clipFlag;}
    void setSlotControls(const std::array<SlotControls,8>& values,float db) noexcept {
        slotMode=true;
        auto clean=[](float x,float lo,float hi,float fallback){return std::isfinite(x)?std::clamp(x,lo,hi):fallback;};
        bool solo=false;for(const auto& c:values)solo=solo||c.solo>.5f;
        for(size_t i=0;i<8;++i){const auto& x=values[i];auto& c=slots[i];
            c={clean(x.tune,-24,24,0),clean(x.gain,-60,12,-6),clean(x.pan,-1,1,0),clean(x.start,0,.999f,0),clean(x.end,.001f,1,1),clean(x.attack,0,500,0),clean(x.release,0,3000,30),clean(x.filter,40,20000,20000),clean(x.reverse,0,1,0),clean(x.mute,0,1,0),clean(x.solo,0,1,0),clean(x.punch,0,1,.5f),clean(x.tone,0,1,.5f),clean(x.texture,0,1,.5f),clean(x.decay,.1f,3,1),clean(x.pitchDepth,0,2,1),clean(x.pitchTime,2,200,28.5f),clean(x.blend,0,1,0),clean(x.sampleLevel,-60,12,0),clean(x.note,0,127,36),clean(x.choke,0,8,0),clean(x.velocityTone,0,1,0)};
            c.mute=(c.mute>.5f||(solo&&c.solo<.5f))?1.0f:0.0f;
        }outputDb=clean(db,-36,6,-6);
    }
    void replace(const std::array<const ohsample::Sample*,8>& data) noexcept {beginTransition();samples=data;}
    void panic(bool immediate=false) noexcept {if(immediate)reset();else for(auto& v:voices)if(v.active)v.releasing=true;}
    void triggerSlot(int slot,float velocity,int note=60) noexcept {
        if(slot<0||slot>7||!std::isfinite(velocity)||velocity<=0)return;
        const auto& c=slots[static_cast<size_t>(slot)];
        if(c.choke>=1)for(auto& v:voices)if(v.active&&v.slot>=0&&slots[static_cast<size_t>(v.slot)].choke==c.choke)v.releasing=true;
        static constexpr std::array<int,8> types{0,1,2,3,4,5,6,2};
        (void)note;triggerInternal(types[static_cast<size_t>(slot)],velocity,defaultNotes[static_cast<size_t>(slot)],slot);
    }
    void prepare(double sampleRate, Macros macros={}) {
        rate=std::isfinite(sampleRate)?std::clamp(sampleRate,8000.0,192000.0):48000;
        onsetCoefficients={};setMacros(macros);current=target;smoothing=1-coefficient(.02f);smoothSlots=slots;smoothedOutput=outputDb;finalGain=std::pow(10.0f,smoothedOutput*.05f);
        for(auto& channel:delay) channel.assign(static_cast<size_t>(rate*.16)+1,0);
        reset();
    }
    void reset() noexcept {
        voices={};lastOutput={};transitionOutput={};transitionFrames=0; frame=0;write=0;dampL=dampR=0;ambienceDepartment=0;
        for(auto& channel:delay) std::fill(channel.begin(),channel.end(),0.0f);
    }
    void setMacros(Macros m) noexcept { target={unit(m.body),unit(m.character),unit(m.space)}; }
    void trigger(int category,float velocity,int note=36) noexcept {triggerInternal(category,velocity,note,-1);}
private:
    void triggerInternal(int category,float velocity,int note,int slot) noexcept {
        if(!std::isfinite(velocity)||velocity<=0)return;
        Voice* chosen=&voices[0];
        for(auto& v:voices) { if(!v.active) { chosen=&v;break; } if(v.age>chosen->age) chosen=&v; }
        const float residual=chosen->active?chosen->lastOutput:0;
        *chosen=Voice{}; auto& v=*chosen;
        v.stolenOutput=residual;v.stolenFrames=static_cast<int>(rate*.002);
        v.slot=slot;if(slot>=0){v.shot=slots[static_cast<size_t>(slot)];v.sample=samples[static_cast<size_t>(slot)];if(v.sample&&v.sample->frames()>1){const auto& c=v.shot;v.sampleFirst=c.start*static_cast<double>(v.sample->frames()-1);v.sampleLast=std::max(v.sampleFirst+1,c.end*static_cast<double>(v.sample->frames()-1));v.samplePosition=c.reverse>.5f?v.sampleLast:v.sampleFirst;v.sampleStep=v.sample->rate/rate*std::pow(2.0,static_cast<double>(c.tune)/12)*(c.reverse>.5f?-1:1);}}
        v.active=true;v.type=std::clamp(category,0,6);ambienceDepartment=v.type;v.velocity=unit(velocity);v.note=std::clamp(note,0,127);
        v.seed=0x93a17u+static_cast<uint32_t>(v.type)*7919u; // Repeatable excitation, independent of process partition.
        for(size_t i=0;i<8;++i) v.envelope[i]=1.0f/(1+static_cast<float>(i)*1.8f);
        if(slot>=0){
            auto& cached=onsetCoefficients[static_cast<size_t>(slot)];const auto& sc=smoothSlots[static_cast<size_t>(slot)];
            const float b=unit(sc.tone+current.body-.5f+sc.velocityTone*(v.velocity-.5f)*.4f),c=unit(sc.texture+current.character-.5f);
            if(!cached.mappedValid||cached.note!=v.note||cached.mappedBody!=b||cached.mappedCharacter!=c||std::memcmp(&cached.mapped,&sc,sizeof(sc))!=0){
                cached=Voice{};cached.slot=slot;cached.type=v.type;cached.note=v.note;cached.velocity=v.velocity;map(cached);
            }copyCoefficients(v,cached);
        }else map(v);
    }
    public:
    std::array<float,2> tick() noexcept {
        clipFlag=false;
        if(slotMode&&frame%32==0){const float a=1-std::pow(1-smoothing,32.0f);for(size_t i=0;i<8;++i){auto& c=smoothSlots[i];const auto& t=slots[i];
#define SMOOTH(field) c.field+=a*(t.field-c.field)
            SMOOTH(gain);SMOOTH(pan);SMOOTH(filter);SMOOTH(mute);SMOOTH(punch);SMOOTH(tone);SMOOTH(texture);SMOOTH(decay);SMOOTH(pitchDepth);SMOOTH(pitchTime);SMOOTH(tune);SMOOTH(blend);SMOOTH(sampleLevel);SMOOTH(velocityTone);
#undef SMOOTH
        }smoothedOutput+=a*(outputDb-smoothedOutput);finalGain=std::pow(10.0f,smoothedOutput*.05f);}

        current.body+=smoothing*(target.body-current.body);
        current.character+=smoothing*(target.character-current.character);
        current.space+=smoothing*(target.space-current.space);
        float dry=0;std::array<float,2> stereo{};const int dominant=ambienceDepartment;
        for(auto& v:voices) if(v.active) {
            if(frame%32==0&&v.age>0) map(v);
            v.seed^=v.seed<<13;v.seed^=v.seed>>17;v.seed^=v.seed<<5;
            const float noise=static_cast<float>(v.seed>>8)*(2.0f/16777215.0f)-1;
            v.noiseLow+=v.lowCoefficient*(noise-v.noiseLow);
            v.noiseHigh+=v.highCoefficient*(v.noiseLow-v.noiseHigh);
            float excitation=(v.noiseLow-v.noiseHigh)*v.noiseEnv;
            if(v.type==6) {
                // Three separate noise excitations plus a diffused tail.
                const float t=static_cast<float>(v.age)/static_cast<float>(rate);
                const float spacing=.008f+.014f*(v.slot>=0?smoothSlots[static_cast<size_t>(v.slot)].texture:current.character);
                float burst=0;
                for(int n=0;n<3;++n) { const float dt=t-static_cast<float>(n)*spacing;
                    if(dt>=0) burst+=std::exp(-dt/(.002f+.002f*current.body)); }
                excitation=(v.noiseLow-v.noiseHigh)*(burst+v.noiseEnv*.24f);
            }
            std::array<float,8> modes{};
            float tone=0;
            for(size_t i=0;i<modeCount(v.type);++i) {
                const float sine=v.sine[i]*v.stepCosine[i]+v.cosine[i]*v.stepSine[i];
                v.cosine[i]=v.cosine[i]*v.stepCosine[i]-v.sine[i]*v.stepSine[i];
                v.sine[i]=sine;modes[i]=sine;
                tone+=modes[i]*v.envelope[i];v.envelope[i]*=v.decay[i];
            }
            if(v.type==2) tone=(modes[0]*modes[1]+modes[2]*modes[3]+modes[4]*modes[5])*.4f*v.envelope[0];
            if(v.type==0) tone= modes[0]*v.envelope[0]+modes[1]*v.envelope[1]*(.1f+.5f*current.character);
            const auto& sc=v.slot>=0?smoothSlots[static_cast<size_t>(v.slot)]:smoothSlots[0];
            const float punch=v.slot>=0?sc.punch:.5f;
            const float attackTime=v.slot>=0?std::max(.0002f,v.shot.attack*.001f+.0012f-.001f*punch):.0007f;
            const float attack=std::min(1.0f,static_cast<float>(v.age)/(static_cast<float>(rate)*attackTime));
            float contribution=.23f*v.velocity*attack*(tone*v.tonalMix+excitation*(1-v.tonalMix)*2+noise*v.transient*.08f*current.character);
            if(v.stolenFrames>0){contribution+=v.stolenOutput*static_cast<float>(v.stolenFrames)/(static_cast<float>(rate)*.002f);--v.stolenFrames;}
            if(v.slot>=0){
                contribution*=.6f+.8f*punch;
                const float drive=1+std::max(0.0f,sc.texture-.5f)*(v.type==0?3.0f:1.2f);contribution=contribution/(1+std::abs(contribution)*(drive-1));
                if(v.releasing)v.fade=std::max(0.0f,v.fade-1.0f/static_cast<float>(rate*.002));
                if(sc.filter>=19999.0f)v.filtered=contribution;else v.filtered+=v.filterCoefficient*(contribution-v.filtered);
                std::array<float,2> layer{};
                if(v.sample&&v.samplePosition>=v.sampleFirst&&v.samplePosition<=v.sampleLast){if(sc.blend>0){const auto index=static_cast<size_t>(v.samplePosition);const size_t next=std::min(index+1,v.sample->frames()-1);const float frac=static_cast<float>(v.samplePosition-static_cast<double>(index));
                    const float remaining=static_cast<float>(v.shot.reverse>.5f?v.samplePosition-v.sampleFirst:v.sampleLast-v.samplePosition);
                    const float tail=std::max(1.0f,v.shot.release*.001f*static_cast<float>(v.sample->rate));
                    const float env=attack*std::clamp(remaining/tail,0.0f,1.0f)*std::min(1.0f,static_cast<float>(v.age)/static_cast<float>(rate*.0002));
                    for(size_t ch=0;ch<2;++ch)layer[ch]=(v.sample->audio[ch][index]+frac*(v.sample->audio[ch][next]-v.sample->audio[ch][index]))*env*v.velocity*v.sampleGain;
                    }v.samplePosition+=v.sampleStep;
                }
                for(size_t ch=0;ch<2;++ch){const float pan=ch==0?std::min(1.0f,1-v.pan):std::min(1.0f,1+v.pan);
                    const float x=(v.filtered*(1-sc.blend)+layer[ch]*sc.blend)*v.volume*pan*v.fade;stereo[ch]+=x;}
            }
            v.lastOutput=contribution;dry+=contribution;
            v.pitch*=v.pitchDecay;v.noiseEnv*=v.noiseDecay;v.transient*=v.transientDecay;++v.age;
            const bool sampleDone=!v.sample||v.samplePosition<v.sampleFirst||v.samplePosition>v.sampleLast;
            if(v.fade<=0||v.age>rate*128 || ((v.envelope[0]<1.0e-6f && v.noiseEnv<1.0e-6f)&&sampleDone))v.active=false;
        }
        ++frame;
        if(delay[0].empty()) return {0,0};
        // Category-specific stereo ambience; fixed taps avoid moving-delay pitch
        // artefacts during macro automation. SPACE changes diffusion and damping.
        static constexpr std::array<float,7> taps{.041f,.067f,.023f,.113f,.079f,.053f,.037f};
        const size_t length=delay[0].size();
        const auto readL=(write+length-static_cast<size_t>(rate*taps[static_cast<size_t>(dominant)]))%length;
        const auto readR=(write+length-static_cast<size_t>(rate*(taps[static_cast<size_t>(dominant)]+.013f)))%length;
        const float s=current.space;
        const float damp=.12f+.6f*(1-s);
        dampL+=damp*(delay[0][readL]-dampL);dampR+=damp*(delay[1][readR]-dampR);
        const float feedback=.08f+.53f*s;
        delay[0][write]=(slotMode?stereo[0]:dry)+dampR*feedback;delay[1][write]=(slotMode?stereo[1]:dry)+dampL*feedback;
        if(++write>=length)write=0;
        const float wet=s*(.12f+.24f*static_cast<float>(dominant+1)/7);
        if(!slotMode)return {safe(dry*.65f+dampL*wet),safe(dry*.65f+dampR*wet)};
        const float gain=finalGain;
        std::array<float,2> result{(stereo[0]*.65f+dampL*wet)*gain,(stereo[1]*.65f+dampR*wet)*gain};
        if(transitionFrames>0){const float mix=static_cast<float>(transitionFrames)/static_cast<float>(transitionLength);for(size_t ch=0;ch<2;++ch)result[ch]=transitionOutput[ch]*mix+result[ch]*(1-mix);--transitionFrames;}for(auto& x:result){clipFlag=clipFlag||std::abs(x)>.98f;x=safe(x);}lastOutput=result;return result;
    }
    static float safe(float x) noexcept { return std::isfinite(x)?std::clamp(x,-.98f,.98f):0; }
};
}

#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <vector>

namespace ohdrum {
enum class Department { kick, snare, hat, cymbal, tom, percussion, clap };
inline constexpr std::array<const char*,7> names{"Kick","Snare","Hi-Hat","Cymbal","Tom","Percussion","Clap"};
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
        int type=0, age=0, note=36;
        float velocity=0, noiseLow=0, noiseHigh=0, pitch=1, pitchDecay=1;
        float noiseEnv=1, noiseDecay=1, lowCoefficient=.2f, highCoefficient=.2f;
        float pitchDepth=0, transient=1, transientDecay=1, tonalMix=.5f;
        float lastOutput=0,stolenOutput=0;
        int stolenFrames=0;
        uint32_t seed=1;
        std::array<float,8> sine{},cosine{1,1,1,1,1,1,1,1};
        std::array<float,8> stepSine{},stepCosine{},envelope{},decay{};
    };
    double rate=48000;
    std::array<Voice,16> voices{};
    Macros target{}, current{};
    float smoothing=0;
    uint64_t frame=0;
    std::array<std::vector<float>,2> delay;
    size_t write=0;
    int ambienceDepartment=0;
    float dampL=0,dampR=0;
    static constexpr double pi=3.14159265358979323846;
    float coefficient(float seconds) const noexcept { return std::exp(-1.0f/(static_cast<float>(rate)*seconds)); }
    void map(Voice& v) noexcept {
        const float b=current.body,c=current.character;
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
        for(size_t i=0;i<8;++i) {
            // Hat products generate sum/difference frequencies; keep each
            // operand below .22 Fs so the sum stays below Nyquist.
            const float frequency=std::min(base*ratios[i],static_cast<float>(rate)*(v.type==2?.22f:.42f));
            const float hz=std::min(frequency*(1+v.pitch*v.pitchDepth),static_cast<float>(rate)*.45f);
            const double angle=2*pi*hz/rate;
            v.stepSine[i]=static_cast<float>(std::sin(angle));
            v.stepCosine[i]=static_cast<float>(std::cos(angle));
            // Bounded Newton renormalization keeps long modal tails stable.
            const float normalization=1.5f-.5f*(v.sine[i]*v.sine[i]+v.cosine[i]*v.cosine[i]);
            v.sine[i]*=normalization;v.cosine[i]*=normalization;
            const float spectralDecay=1+static_cast<float>(i)*(.12f+.45f*(1-c));
            v.decay[i]=coefficient(duration/spectralDecay);
        }
        v.pitchDecay=coefficient(.006f+.045f*b);
        v.noiseDecay=coefficient(noiseTime);
        v.transientDecay=coefficient(.0015f+.006f*c);
        const float lowHz=(v.type==0?1800.0f:v.type==4?2200.0f:4500.0f)+c*6500;
        const float highHz=(v.type==0?80.0f:v.type==1?650.0f:v.type==6?800.0f:2200.0f)*(1.2f-.6f*b);
        v.lowCoefficient=1-std::exp(-2*static_cast<float>(pi)*std::min(lowHz,static_cast<float>(rate)*.4f)/static_cast<float>(rate));
        v.highCoefficient=1-std::exp(-2*static_cast<float>(pi)*std::min(highHz,static_cast<float>(rate)*.2f)/static_cast<float>(rate));
    }
public:
    void prepare(double sampleRate, Macros macros={}) {
        rate=std::isfinite(sampleRate)?std::clamp(sampleRate,8000.0,192000.0):48000;
        setMacros(macros);current=target;smoothing=1-coefficient(.02f);
        for(auto& channel:delay) channel.assign(static_cast<size_t>(rate*.16)+1,0);
        reset();
    }
    void reset() noexcept {
        voices={}; frame=0;write=0;dampL=dampR=0;ambienceDepartment=0;
        for(auto& channel:delay) std::fill(channel.begin(),channel.end(),0.0f);
    }
    void setMacros(Macros m) noexcept { target={unit(m.body),unit(m.character),unit(m.space)}; }
    void trigger(int category,float velocity,int note=36) noexcept {
        Voice* chosen=&voices[0];
        for(auto& v:voices) { if(!v.active) { chosen=&v;break; } if(v.age>chosen->age) chosen=&v; }
        const float residual=chosen->active?chosen->lastOutput:0;
        *chosen=Voice{}; auto& v=*chosen;
        v.stolenOutput=residual;v.stolenFrames=static_cast<int>(rate*.002);
        v.active=true;v.type=std::clamp(category,0,6);ambienceDepartment=v.type;v.velocity=unit(velocity);v.note=std::clamp(note,0,127);
        v.seed=0x93a17u+static_cast<uint32_t>(v.type)*7919u; // Repeatable excitation, independent of process partition.
        for(size_t i=0;i<8;++i) v.envelope[i]=1.0f/(1+static_cast<float>(i)*1.8f);
        map(v);
    }
    std::array<float,2> tick() noexcept {
        current.body+=smoothing*(target.body-current.body);
        current.character+=smoothing*(target.character-current.character);
        current.space+=smoothing*(target.space-current.space);
        float dry=0;const int dominant=ambienceDepartment;
        for(auto& v:voices) if(v.active) {
            if(frame%32==0) map(v);
            v.seed^=v.seed<<13;v.seed^=v.seed>>17;v.seed^=v.seed<<5;
            const float noise=static_cast<float>(v.seed>>8)*(2.0f/16777215.0f)-1;
            v.noiseLow+=v.lowCoefficient*(noise-v.noiseLow);
            v.noiseHigh+=v.highCoefficient*(v.noiseLow-v.noiseHigh);
            float excitation=(v.noiseLow-v.noiseHigh)*v.noiseEnv;
            if(v.type==6) {
                // Three separate noise excitations plus a diffused tail.
                const float t=static_cast<float>(v.age)/static_cast<float>(rate);
                const float spacing=.008f+.014f*current.character;
                float burst=0;
                for(int n=0;n<3;++n) { const float dt=t-static_cast<float>(n)*spacing;
                    if(dt>=0) burst+=std::exp(-dt/(.002f+.002f*current.body)); }
                excitation=(v.noiseLow-v.noiseHigh)*(burst+v.noiseEnv*.24f);
            }
            std::array<float,8> modes{};
            float tone=0;
            for(size_t i=0;i<8;++i) {
                const float sine=v.sine[i]*v.stepCosine[i]+v.cosine[i]*v.stepSine[i];
                v.cosine[i]=v.cosine[i]*v.stepCosine[i]-v.sine[i]*v.stepSine[i];
                v.sine[i]=sine;modes[i]=sine;
                tone+=modes[i]*v.envelope[i];v.envelope[i]*=v.decay[i];
            }
            if(v.type==2) tone=(modes[0]*modes[1]+modes[2]*modes[3]+modes[4]*modes[5])*.4f*v.envelope[0];
            if(v.type==0) tone= modes[0]*v.envelope[0]+modes[1]*v.envelope[1]*(.1f+.5f*current.character);
            const float attack=std::min(1.0f,static_cast<float>(v.age)/(static_cast<float>(rate)*.0007f));
            float contribution=.23f*v.velocity*attack*(tone*v.tonalMix+excitation*(1-v.tonalMix)*2+noise*v.transient*.08f*current.character);
            if(v.stolenFrames>0){contribution+=v.stolenOutput*static_cast<float>(v.stolenFrames)/(static_cast<float>(rate)*.002f);--v.stolenFrames;}
            v.lastOutput=contribution;dry+=contribution;
            v.pitch*=v.pitchDecay;v.noiseEnv*=v.noiseDecay;v.transient*=v.transientDecay;++v.age;
            if(v.age>rate*12 || (v.envelope[0]<1.0e-6f && v.noiseEnv<1.0e-6f)) v.active=false;
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
        delay[0][write]=dry+dampR*feedback;delay[1][write]=dry+dampL*feedback;
        if(++write>=length)write=0;
        const float wet=s*(.12f+.24f*static_cast<float>(dominant+1)/7);
        return {safe(dry*.65f+dampL*wet),safe(dry*.65f+dampR*wet)};
    }
    static float safe(float x) noexcept { return std::isfinite(x)?std::clamp(x,-.98f,.98f):0; }
};
}

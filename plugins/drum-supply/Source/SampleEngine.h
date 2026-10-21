#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <vector>
#include "SampleData.h"

namespace ohsample {

inline int slotForNote(int n) noexcept {
    switch(n) {case 35:case 36:return 0;case 38:case 40:return 1;case 42:case 44:case 46:return 2;
    case 49:case 51:case 57:return 3;case 41:case 43:case 45:case 47:case 48:case 50:return 4;case 39:return 6;default:return 5;}
}
struct Controls {float tune=0,gain=-6,pan=0,start=0,end=1,attack=0,release=30,filter=20000,reverse=0,mute=0,solo=0;};
struct Mix {float body=.5f,character=.5f,space=.25f,output=-6;};

class Engine {
    struct Voice {const Sample* sample=nullptr;Controls controls;int slot=0;uint64_t age=0;
        double position=0,step=1,first=0,last=0;float velocity=0,fade=1;bool releasing=false;
        std::array<float,2> low{},weight{},previous{},residual{};int stolen=0;
        float amplitudeGain=1,coefficient=1,bassCoefficient=.02f,drive=1;};
    std::array<Voice,16> voices{};
    std::array<Controls,7> controls{},targetControls{};
    std::array<const Sample*,7> samples{};
    std::array<std::vector<float>,2> delay;
    size_t write=0;
    double rate=48000;
    float smoothing=0;
    Mix current{},target{};
    uint64_t frame=0;
    float outputGain=1;
    std::array<float,2> lastOutput{},swapResidual{};
    int swapFade=0;
    static constexpr float pi=3.14159265358979323846f;
    static float gain(float db) noexcept {return std::pow(10.0f,db*.05f);}
    static float interpolate(const std::vector<float>& a,double position) noexcept {
        const auto i=static_cast<int64_t>(position);const float t=static_cast<float>(position-static_cast<double>(i));
        auto at=[&](int64_t index){return a[static_cast<size_t>(std::clamp<int64_t>(index,0,static_cast<int64_t>(a.size())-1))];};
        const float y0=at(i-1),y1=at(i),y2=at(i+1),y3=at(i+2);
        return y1+.5f*t*(y2-y0+t*(2*y0-5*y1+4*y2-y3+t*(3*(y1-y2)+y3-y0)));
    }
public:
    void prepare(double sampleRate) {
        rate=std::isfinite(sampleRate)?std::clamp(sampleRate,8000.0,192000.0):48000;
        smoothing=1-std::exp(-1.0f/(.02f*static_cast<float>(rate)));
        for(auto& channel:delay)channel.assign(static_cast<size_t>(rate*.151)+1,0);
        current=target;controls=targetControls;outputGain=gain(current.output);reset();
    }
    void reset() noexcept {voices={};write=0;frame=0;lastOutput={};swapResidual={};swapFade=0;for(auto& channel:delay)std::fill(channel.begin(),channel.end(),0.0f);}
    void replace(const std::array<const Sample*,7>& next) noexcept {const auto residual=lastOutput;reset();samples=next;swapResidual=residual;swapFade=static_cast<int>(rate*.002);}
    void setControls(const std::array<Controls,7>& c,Mix m) noexcept {
        auto clean=[](float x,float lo,float hi,float fallback){return std::isfinite(x)?std::clamp(x,lo,hi):fallback;};
        for(size_t s=0;s<7;++s){const auto& x=c[s];targetControls[s]={clean(x.tune,-24,24,0),clean(x.gain,-60,12,-6),clean(x.pan,-1,1,0),clean(x.start,0,.999f,0),clean(x.end,.001f,1,1),clean(x.attack,0,500,0),clean(x.release,0,3000,30),clean(x.filter,40,20000,20000),clean(x.reverse,0,1,0),clean(x.mute,0,1,0),clean(x.solo,0,1,0)};}
        target={clean(m.body,0,1,.5f),clean(m.character,0,1,.5f),clean(m.space,0,1,.25f),clean(m.output,-36,6,-6)};
    }
    void panic(bool immediate=false) noexcept {if(immediate)reset();else for(auto& v:voices)if(v.sample)v.releasing=true;}
    void trigger(int slot,float velocity,int note=60) noexcept {
        if(slot<0||slot>6||!std::isfinite(velocity)||velocity<=0)return;
        const auto* sample=samples[static_cast<size_t>(slot)];if(!sample||sample->frames()<2||sample->audio[1].size()!=sample->frames()||!std::isfinite(sample->rate)||sample->rate<8000||sample->rate>384000)return;
        if(slot==2)for(auto& v:voices)if(v.sample&&v.slot==2)v.releasing=true;
        auto* chosen=&voices[0];for(auto& v:voices){if(!v.sample){chosen=&v;break;}if(v.age>chosen->age)chosen=&v;}
        const auto residual=chosen->previous;const bool stolen=chosen->sample!=nullptr;
        *chosen=Voice{};auto& v=*chosen;v.sample=sample;v.slot=slot;v.controls=targetControls[static_cast<size_t>(slot)];
        const auto& c=v.controls;v.first=std::clamp<double>(c.start,0,.999)*static_cast<double>(sample->frames()-1);
        v.last=std::max(v.first+1,std::clamp<double>(c.end,.001,1)*static_cast<double>(sample->frames()-1));
        v.position=c.reverse>.5f?v.last:v.first;
        v.step=sample->rate/rate*std::pow(2.0,static_cast<double>(c.tune)/12.0)*(c.reverse>.5f?-1:1);
        v.velocity=std::clamp(velocity,0.0f,1.0f);
        if(stolen){v.residual=residual;v.stolen=static_cast<int>(rate*.002);}
        // GM tom note variations retain the slot's sound; tuning is explicit.
        (void)note;
    }
    std::array<float,2> tick() noexcept {
        current.body+=smoothing*(target.body-current.body);current.character+=smoothing*(target.character-current.character);
        current.space+=smoothing*(target.space-current.space);current.output+=smoothing*(target.output-current.output);
        bool anySolo=false;for(const auto& c:targetControls)anySolo=anySolo||c.solo>.5f;
        for(size_t s=0;s<7;++s) {
            auto& c=controls[s];const auto& t=targetControls[s];
            c.gain+=smoothing*(t.gain-c.gain);c.pan+=smoothing*(t.pan-c.pan);c.filter+=smoothing*(t.filter-c.filter);
            const float muted=(t.mute>.5f||(anySolo&&t.solo<.5f))?1.0f:0.0f;
            c.mute+=smoothing*(muted-c.mute);
        }
        std::array<float,2> dry{};
        for(auto& v:voices)if(v.sample) {
            const auto& c=controls[static_cast<size_t>(v.slot)];
            const auto& shot=v.controls;
            const float attack=std::max(1.0f,shot.attack*.001f*static_cast<float>(rate));
            const float travelled=static_cast<float>(std::abs(v.position-(shot.reverse>.5f?v.last:v.first)));
            const float remaining=static_cast<float>(shot.reverse>.5f?v.position-v.first:v.last-v.position);
            // Up to 0.1 ms edge fade; release region is explicit in milliseconds.
            const float edge=std::max(1.0f,static_cast<float>(v.sample->rate)*.0001f);
            const float tail=std::max(edge,shot.release*.001f*static_cast<float>(v.sample->rate)*(.5f+current.body));
            float envelope=std::min(1.0f,static_cast<float>(v.age+1)/attack)*std::min(1.0f,travelled/edge+.001f)*std::clamp(remaining/tail,0.0f,1.0f);
            if(v.releasing)v.fade=std::max(0.0f,v.fade-1.0f/static_cast<float>(rate*.002));
            if(v.age%32==0){v.amplitudeGain=gain(c.gain);
                const float cutoff=std::min(c.filter*std::pow(2.0f,(current.character-.5f)*2),static_cast<float>(rate)*.45f);
                v.coefficient=1-std::exp(-2*pi*cutoff/static_cast<float>(rate));
                v.bassCoefficient=1-std::exp(-2*pi*180/static_cast<float>(rate));
                v.drive=1+std::max(0.0f,current.character-.5f)*6;}
            const float amplitude=v.velocity*v.amplitudeGain*envelope*v.fade;
            for(size_t ch=0;ch<2;++ch) {
                float x=interpolate(v.sample->audio[ch],v.position);
                v.low[ch]+=v.coefficient*(x-v.low[ch]);v.weight[ch]+=v.bassCoefficient*(v.low[ch]-v.weight[ch]);
                x=v.low[ch]+v.weight[ch]*(current.body-.5f)*1.4f;
                const float drive=v.drive;
                // Bounded soft drive, neutral at CHARACTER <= .5. This is colour, not a limiter.
                if(drive>1)x=x/(1+std::abs(x)*(drive-1));
                const float pan=ch==0?std::min(1.0f,1-c.pan):std::min(1.0f,1+c.pan);
                x*=amplitude*pan;
                if(v.stolen>0)x+=v.residual[ch]*static_cast<float>(v.stolen)/static_cast<float>(rate*.002);
                v.previous[ch]=x;dry[ch]+=x*(1-c.mute);
            }
            if(v.stolen>0)--v.stolen;
            v.position+=v.step;++v.age;
            if(v.position<v.first||v.position>v.last||v.fade<=0)v.sample=nullptr;
        }
        std::array<float,2> out=dry;
        if(!delay[0].empty()) {
            const auto length=delay[0].size();
            const auto l=(write+length-static_cast<size_t>(rate*.071))%length;
            const auto r=(write+length-static_cast<size_t>(rate*.113))%length;
            const float wetL=delay[0][l],wetR=delay[1][r];
            delay[0][write]=dry[0]*current.space+wetR*.32f;delay[1][write]=dry[1]*current.space+wetL*.32f;
            out[0]+=wetL*.35f;out[1]+=wetR*.35f;if(++write==length)write=0;
        }
        if(frame++%32==0)outputGain=gain(current.output);
        for(size_t ch=0;ch<2;++ch){auto& x=out[ch];x*=outputGain;if(swapFade>0)x+=swapResidual[ch]*static_cast<float>(swapFade)/static_cast<float>(rate*.002);if(!std::isfinite(x))x=0;}
        if(swapFade>0)--swapFade;lastOutput=out;
        return out;
    }
};
}

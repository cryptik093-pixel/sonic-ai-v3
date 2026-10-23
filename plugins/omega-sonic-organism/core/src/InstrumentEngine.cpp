#include "omega/OrganismCore.h"
#include "omega/Exciter.h"
#include <algorithm>
#include <cmath>

namespace omega {
namespace {
double mix(double a,double b,double t) noexcept {return a+(b-a)*t;}
double normalized(double x) noexcept {return std::clamp(x,0.,1.);}
}

OrganismCore::Traits OrganismCore::traitsAt(double morph) noexcept {
    static constexpr std::array<Traits,5> anchors{{
        {.82,.24,.04,.02,.006,.08,.02, 3,130,.82,110,700,.72,3,80,1.8,0,1.4,.02, {1,2,3,4},{160,110,80,55},{1,.3,.15,.08}},
        {.07,0,0,.02,.025,1,.95, 2,1550,.25,1200,9000,.65,0,80,1.1,.12,.08,.02, {1,2.71,4.08,5.43},{2200,1700,1250,800},{1,.7,.4,.23}},
        {.16,.72,.24,.03,.008,.05,.03, 8,180,.72,240,4800,.8,0,80,2.1,.04,.12,.28, {1,2,3,4},{250,180,120,85},{1,.3,.1,.05}},
        {.24,.32,.24,.6,.025,.22,.32, 30,600,.65,650,2900,.8,0,80,1.7,.65,.7,.09, {1,2.08,3.17,4.37},{1200,850,650,400},{1,.45,.23,.12}},
        {.05,.03,.02,.02,.72,.75,.7, 1,220,0,130,6600,.7,5,45,2.5,.1,.4,.01, {1,1.59,2.77,4.07},{210,150,95,60},{1,.7,.4,.2}}
    }};
    // These logarithms depend only on the fixed anchors. First initialization
    // happens in prepare/reset before audio processing, never on a new note.
    static const auto logarithms=[]{
        auto values=anchors;
        for(auto& p:values){
            p.attack=std::log(p.attack);p.decay=std::log(p.decay);p.release=std::log(p.release);
            p.cutoff=std::log(p.cutoff);p.dropTime=std::log(p.dropTime);
            for(auto& d:p.modeDecay)d=std::log(d);
        }
        return values;
    }();
    const double u=normalized(morph)*4;const int i=std::min(3,int(u));const double t=u-i;
    const auto& a=anchors[size_t(i)];const auto& b=anchors[size_t(i+1)];Traits p=a;
    const auto& la=logarithms[size_t(i)];const auto& lb=logarithms[size_t(i+1)];
#define LINEAR(field) p.field=mix(a.field,b.field,t)
#define LOGARITHMIC(field) p.field=std::exp(mix(la.field,lb.field,t))
    LINEAR(sine);LINEAR(saw);LINEAR(pulse);LINEAR(spectral);LINEAR(noise);LINEAR(modal);LINEAR(inharm);
    LOGARITHMIC(attack);LOGARITHMIC(decay);LINEAR(sustain);LOGARITHMIC(release);LOGARITHMIC(cutoff);
    LINEAR(q);LINEAR(drop);LOGARITHMIC(dropTime);LINEAR(drive);LINEAR(spread);LINEAR(wobble);LINEAR(vibrato);
#undef LINEAR
#undef LOGARITHMIC
    for(size_t k=0;k<4;++k){p.ratios[k]=mix(a.ratios[k],b.ratios[k],t);p.modeDecay[k]=std::exp(mix(la.modeDecay[k],lb.modeDecay[k],t));p.modeGain[k]=mix(a.modeGain[k],b.modeGain[k],t);}
    return p;
}

void OrganismCore::prepare(double sampleRate,int voiceLimit) {
    sr_=std::isfinite(sampleRate)&&sampleRate>=8000&&sampleRate<=384000?sampleRate:48000;
    strikeDecay_=std::exp(-1/(.018*sr_));
    slew_=1-std::exp(-1/(.018*sr_));dcPole_=std::exp(-2*dsp::pi*5/sr_);
    stealLength_=std::max(1,int(sr_*.005));tables_.prepare();room_.prepare(sr_);
    stepMotion_.prepare(sr_,tempo_,v4::GenerativeState::Static,0x4f534f34u);
    if(voiceLimit>0)setVoiceLimit(voiceLimit);
    else {constexpr int counts[]={1,8,16,32};voiceLimit_=counts[int(std::round(targets_[9]*3))];}
    resetVoices();
}
void OrganismCore::setParameter(uint32_t id,double value) noexcept {
    const int index=parameterIndex(id);if(index<0||!std::isfinite(value))return;
    const auto i=size_t(index);value=normalized(value);const int steps=parameterDefinitions[i].steps;
    if(steps)value=std::round(value*steps)/steps;
    if(value==targets_[i]){
        if(i==9){constexpr int counts[]={1,8,16,32};setVoiceLimit(counts[int(std::round(value*3))]);}
        return;
    }
    if(i==10&&value>targets_[i])for(auto& v:voices_)v.drive.resetHQ();
    targets_[i]=value;if(steps)smooth_[i]=value;
    if(i==16)stepMotion_.setState(v4::GenerativeState(int(std::round(value*3))));
    if(i==9){constexpr int counts[]={1,8,16,32};setVoiceLimit(counts[int(std::round(value*3))]);}
    controlCounter_=0;
}
void OrganismCore::setTempo(double bpm) noexcept {if(std::isfinite(bpm)&&bpm>=20&&bpm<=400&&bpm!=tempo_){tempo_=bpm;stepMotion_.setTempo(bpm);controlCounter_=0;}}
void OrganismCore::setPitchBend(float bipolar) noexcept {if(std::isfinite(bipolar))bend_=std::clamp(double(bipolar),-1.,1.);}
void OrganismCore::setSustain(bool down) noexcept {
    if(sustain_&&!down)for(auto& v:voices_)if(!v.keyDown)releaseVoice(v);sustain_=down;
}
void OrganismCore::setVoiceLimit(int count) noexcept {
    voiceLimit_=std::clamp(count,1,kMaxVoices);
    for(int i=voiceLimit_;i<kMaxVoices;++i){auto& v=voices_[size_t(i)];if(v.stage!=Stage::Off){v.stealValue=v.lastOutput;v.stealRemaining=stealLength_;v.stage=Stage::Off;}}
}
void OrganismCore::resetVoices() noexcept {
    for(auto& voice:voices_)voice=Voice{};
    counter_=1;heldCount_=0;sustain_=false;bend_=bendSmooth_=0;
    stepMotion_.reset();stepMotion_.setDepth(1);stepMotion_.setState(v4::GenerativeState(int(std::round(targets_[16]*3))));stepValue_=0;
    smooth_=targets_;hqMix_=targets_[10];lfoPhase_=lfo_=0;
    dcL_=dcR_=prevL_=prevR_=0;controlCounter_=0;lastMorph_=lastEnergy_=lastOutputLevel_=-1;room_.reset();refreshCoefficients();
}
void OrganismCore::refreshCoefficients() noexcept {
    if(std::abs(smooth_[0]-lastMorph_)>1e-10){traits_=traitsAt(smooth_[0]);lastMorph_=smooth_[0];}
    const double motion=smooth_[2];lfo_=tables_.sine(lfoPhase_);
    const double cutoff=traits_.cutoff*(.55+2.2*smooth_[1])*std::exp2(traits_.wobble*motion*lfo_+stepValue_);
    filter_=dsp::LowPass::coefficients(cutoff,traits_.q,sr_);
    const double attack=traits_.attack*physical(parameterDefinitions[6],smooth_[6]);
    const double release=traits_.release*physical(parameterDefinitions[7],smooth_[7]);
    attackStep_=1/std::max(1.,attack*.001*sr_);
    decayRate_=1-std::exp(-std::log(100.)/(traits_.decay*.001*sr_));
    releaseRate_=std::exp(-std::log(1000.)/(release*.001*sr_));
    drive_=traits_.drive*(.65+1.8*smooth_[1]);driveComp_=1/std::max(.1,tables_.saturate(drive_));
    if(smooth_[5]!=lastOutputLevel_){outputGain_=std::pow(10.,physical(parameterDefinitions[5],smooth_[5])/20.);lastOutputLevel_=smooth_[5];}
    lfoRate_=physical(parameterDefinitions[13],smooth_[13])*(targets_[12]>.5?tempo_/120:1);
    if(smooth_[1]!=lastEnergy_){
        double weightSum=0;
        for(size_t k=0;k<8;++k){harmonicWeights_[k]=std::pow(1./double(k+1),1.1+1.4*(1-smooth_[1]));weightSum+=harmonicWeights_[k];}
        for(auto& w:harmonicWeights_)w/=weightSum;
        lastEnergy_=smooth_[1];
    }
    waveWeight_=traits_.sine+traits_.saw+traits_.pulse+traits_.spectral+traits_.modal;
    for(size_t i=0;i<4;++i)modeDecays_[i]=std::exp(-std::log(1000.)/(traits_.modeDecay[i]*.001*sr_));
    for(auto& v:voices_)if(v.stage!=Stage::Off)refreshVoice(v);
}
void OrganismCore::refreshVoice(Voice& v) noexcept {
    constexpr int ranges[]={2,12,24};const double range=ranges[int(std::round(targets_[11]*2))];
    const double drop=traits_.drop==0?0:traits_.drop*std::exp(-v.elapsed/(traits_.dropTime*.001));
    const double vibrato=traits_.vibrato*smooth_[2]*lfo_;
    const double hz=440*std::exp2((v.pitch-69+bendSmooth_*range+drop+vibrato)/12);
    v.phaseStep=std::min(.49,hz/sr_);v.nyquistGain=std::clamp((sr_*.48-hz)/(sr_*.06),0.,1.);
    for(size_t k=0;k<8;++k)v.harmonicFade[k]=std::clamp((.48-v.phaseStep*double(k+1))/.06,0.,1.);
    // These modes are excited only by startVoice. After zap makes all four
    // states exactly zero, homogeneous rotation cannot create new energy.
    // Oscillators, envelopes, RNG, filters and morph controls keep advancing.
    v.modesActive=false;
    for(const auto& mode:v.modes)if(mode.re!=0||mode.im!=0){v.modesActive=true;break;}
    if(!v.modesActive)return;
    v.modeWeight=0;
    for(size_t i=0;i<4;++i){auto& mode=v.modes[i];
        const double harmonic=double(i+1);const double ratio=harmonic+(traits_.ratios[i]-harmonic)*(.6+.8*smooth_[3]);
        const double frequency=hz*ratio;const double phase=std::clamp(frequency/sr_,0.,.49);
        mode.cosine=tables_.sine(phase+.25);mode.sine=tables_.sine(phase);
        // Sine-table values are bounded by one and this quadrature pair has
        // magnitude near one. A direct norm cannot overflow or underflow here;
        // hypot's arbitrary-magnitude scaling is unnecessary in this hot path.
        const double magnitude=std::sqrt(mode.cosine*mode.cosine+mode.sine*mode.sine);mode.cosine/=magnitude;mode.sine/=magnitude;
        mode.decay=modeDecays_[i];
        mode.weight=traits_.modeGain[i]*std::clamp((sr_*.48-frequency)/(sr_*.06),0.,1.);
        v.modeWeight+=mode.weight;
    }
}
void OrganismCore::startVoice(Voice& v,int note,float velocity,int32_t id,bool legato) noexcept {
    if(legato){v.note=note;v.noteId=id;v.keyDown=true;v.velocity=normalized(velocity);v.targetPitch=note;
        v.glideRemaining=int(physical(parameterDefinitions[8],targets_[8])*.001*sr_);
        v.glideStep=v.glideRemaining>0?(v.targetPitch-v.pitch)/v.glideRemaining:0;
        if(v.glideRemaining==0)v.pitch=v.targetPitch;refreshVoice(v);return;}
    const double previous=v.lastOutput;const bool stealing=v.stage!=Stage::Off||v.stealRemaining>0;
    v=Voice{};v.stage=Stage::Attack;v.note=note;v.noteId=id;v.keyDown=true;v.velocity=normalized(velocity);v.pitch=v.targetPitch=note;
    v.age=counter_++;v.rng=uint32_t(note+1)*747796405u^uint32_t(v.age)*2891336453u;if(v.rng==0)v.rng=1;
    v.panOffset=double(v.age%17)/17.;
    for(auto& mode:v.modes)mode.re=.7+.6*v.velocity;
    if(stealing){v.stealValue=previous;v.stealRemaining=stealLength_;}
    refreshVoice(v);
}
void OrganismCore::noteOn(int note,float velocity,int32_t id) noexcept {
    if(note<0||note>127||!std::isfinite(velocity))return;
    if(velocity<=0){noteOff(note,id);return;}
    if(heldCount_==128){for(int i=1;i<128;++i)held_[size_t(i-1)]=held_[size_t(i)];--heldCount_;}
    held_[size_t(heldCount_++)]={note,id,velocity};
    if(voiceLimit_==1){auto& v=voices_[0];startVoice(v,note,velocity,id,targets_[14]>.5&&v.stage!=Stage::Off&&v.stage!=Stage::Release);return;}
    Voice* victim=nullptr;
    for(int i=0;i<voiceLimit_;++i){auto& v=voices_[size_t(i)];
        if(v.stage==Stage::Off){victim=&v;break;}
        if(v.stage==Stage::Release&&(!victim||victim->stage!=Stage::Release||v.env<victim->env))victim=&v;}
    if(!victim){victim=&voices_[0];for(int i=1;i<voiceLimit_;++i)if(voices_[size_t(i)].age<victim->age)victim=&voices_[size_t(i)];}
    startVoice(*victim,note,velocity,id,false);
}
void OrganismCore::releaseVoice(Voice& v) noexcept {if(v.stage!=Stage::Off)v.stage=Stage::Release;}
void OrganismCore::noteOff(int note,int32_t id) noexcept {
    for(int i=0;i<heldCount_;++i)if(held_[size_t(i)].note==note&&(id<0||held_[size_t(i)].id==id)){
        for(int j=i+1;j<heldCount_;++j)held_[size_t(j-1)]=held_[size_t(j)];--heldCount_;break;}
    Voice* oldest=nullptr;
    for(int i=0;i<voiceLimit_;++i){auto& v=voices_[size_t(i)];
        if(v.stage==Stage::Off||v.stage==Stage::Release||!v.keyDown||v.note!=note||(id>=0&&v.noteId!=id))continue;
        if(!oldest||v.age<oldest->age)oldest=&v;}
    if(!oldest)return;
    if(voiceLimit_==1&&targets_[14]>.5&&heldCount_>0){const auto& h=held_[size_t(heldCount_-1)];startVoice(*oldest,h.note,h.velocity,h.id,true);return;}
    oldest->keyDown=false;if(!sustain_)releaseVoice(*oldest);
}
void OrganismCore::allNotesOff() noexcept {heldCount_=0;sustain_=false;for(auto& v:voices_){v.keyDown=false;releaseVoice(v);}}
int OrganismCore::activeVoices() const noexcept {int count=0;for(const auto& v:voices_)if(v.stage!=Stage::Off)++count;return count;}
double OrganismCore::currentPitch(int index) const noexcept {return index>=0&&index<kMaxVoices?voices_[size_t(index)].pitch:0;}

double OrganismCore::voiceSample(Voice& v) noexcept {
    double sample=0;
    if(v.stage!=Stage::Off){
        if(v.glideRemaining>0){v.pitch+=v.glideStep;if(--v.glideRemaining==0)v.pitch=v.targetPitch;}
        switch(v.stage){
            case Stage::Attack:v.env=std::min(1.,v.env+attackStep_);if(v.env>=1)v.stage=Stage::Decay;break;
            case Stage::Decay:v.env=dsp::zap(v.env+(traits_.sustain-v.env)*decayRate_);if(std::abs(v.env-traits_.sustain)<1e-6)v.stage=Stage::Sustain;break;
            case Stage::Sustain:v.env=dsp::zap(v.env+(traits_.sustain-v.env)*decayRate_);break;
            case Stage::Release:v.env*=releaseRate_;if(v.env<1e-7){v.env=0;v.stage=Stage::Off;}break;
            case Stage::Off:break;
        }
        // The bounded oscillator phase is initialized to zero and advances by
        // at most .49. Power-of-two index wrapping preserves table interpolation
        // including the original endpoint, without nine repeated phase wraps.
        if(!dsp::finite(v.phase)||v.phase<0||v.phase>=1){++tables_.nonFiniteFaults;if(!tables_.firstFaultSource)tables_.firstFaultSource=1;return 0;}
        const auto source=dsp::Exciter::periodic(v.phase,v.phaseStep,pulseWidth_,pulseDc_,harmonicWeights_,v.harmonicFade,tables_);
        const double sine=source.sine,saw=source.saw,pulse=source.pulse,spectral=source.spectral;
        v.rng^=v.rng<<13;v.rng^=v.rng>>17;v.rng^=v.rng<<5;
        const double noise=double(v.rng)/2147483647.5-1;
        double modal=0;
        if(v.modesActive){
            // Convex real-state exchange between two of the existing FOUR modes.
            // k <= .02 makes the exchange contractive; normalized rotation and
            // damping cannot increase total pair energy. No additional bank.
            if(smooth_[17]>0){const double delta=.02*smooth_[17]*(v.modes[1].re-v.modes[0].re);
                v.modes[0].re+=delta;v.modes[1].re-=delta;}
            for(auto& mode:v.modes){const double re=mode.re,im=mode.im;
                mode.re=dsp::zap((re*mode.cosine-im*mode.sine)*mode.decay);
                mode.im=dsp::zap((re*mode.sine+im*mode.cosine)*mode.decay);
                modal+=mode.re*mode.weight;}
            if(v.modeWeight>0)modal/=v.modeWeight;
        }
        const double impact=v.impact*(.4+.8*v.velocity);v.impact=dsp::zap(v.impact*strikeDecay_);
        const double noiseGain=noiseBase_*(.15+impact);
        const double weight=std::max(1.,waveWeight_+noiseGain);
        const double wave=(traits_.sine*sine+traits_.saw*saw+traits_.pulse*pulse+traits_.spectral*spectral+traits_.modal*modal+noiseGain*noise)/weight;
        const double filtered=v.filter.tick(wave,filter_);
        if(!dsp::finite(filtered)){++tables_.nonFiniteFaults;if(!tables_.firstFaultSource)tables_.firstFaultSource=3;}
        const double input=filtered*(.7+.3*v.velocity)*v.nyquistGain*tremolo_;
        const double envelope=v.envelopeDelay[size_t(v.envelopePosition)];v.envelopeDelay[size_t(v.envelopePosition)]=v.env;
        if(++v.envelopePosition==latencySamples)v.envelopePosition=0;
        sample=v.drive.tick(input,drive_,driveComp_,hqMix_,tables_)*envelope*v.velocity*.18;
        v.phase+=v.phaseStep;if(v.phase>=1)v.phase-=1;v.elapsed+=1/sr_;
    }
    if(v.stealRemaining>0){const double fade=double(v.stealRemaining)/stealLength_;sample=sample*(1-fade)+v.stealValue*fade;--v.stealRemaining;}
    v.lastOutput=sample;return sample;
}
void OrganismCore::render(float* left,float* right,int frames) noexcept {
    if(!left||!right||frames<=0)return;
    for(int n=0;n<frames;++n){
        for(size_t i=0;i<smooth_.size();++i)if(!parameterDefinitions[i].steps){const double difference=targets_[i]-smooth_[i];smooth_[i]=std::abs(difference)<1e-9?targets_[i]:smooth_[i]+slew_*difference;}
        bendSmooth_=dsp::zap(bendSmooth_+slew_*(bend_-bendSmooth_));
        const double hqStep=1/(sr_*.01);hqMix_+=std::clamp(targets_[10]-hqMix_,-hqStep,hqStep);
        stepValue_=smooth_[15]*stepMotion_.tick();
        if(controlCounter_--<=0){refreshCoefficients();controlCounter_=15;}
        pulseWidth_=.5+.12*smooth_[2]*traits_.spread*lfo_;pulseDc_=2*pulseWidth_-1;
        tremolo_=1-.25*traits_.wobble*smooth_[2]*(.5+.5*lfo_);
        noiseBase_=traits_.noise*(.2+1.6*smooth_[3]);
        double accL=0,accR=0;
        for(auto& voice:voices_)if(voice.stage!=Stage::Off||voice.stealRemaining>0){const double sample=voiceSample(voice);
            const double pan=traits_.spread*smooth_[2]*tables_.sine(lfoPhase_+voice.panOffset);
            accL+=sample*(1-pan*.4);accR+=sample*(1+pan*.4);}
        auto wet=room_.tick(accL,accR,smooth_[4]);
        const double xL=wet[0]*outputGain_,xR=wet[1]*outputGain_;
        dcL_=dsp::zap(xL-prevL_+dcPole_*dcL_);dcR_=dsp::zap(xR-prevR_+dcPole_*dcR_);prevL_=xL;prevR_=xR;
        left[n]=float(.98*tables_.saturate(dcL_/.98));right[n]=float(.98*tables_.saturate(dcR_/.98));
        lfoPhase_+=lfoRate_/sr_;if(lfoPhase_>=1)lfoPhase_-=1;
    }
}
}

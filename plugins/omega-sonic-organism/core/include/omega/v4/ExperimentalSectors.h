// Experimental OSO V4 modules: host-independent, fixed-memory C++17.
// NOT wired into RC2 audio path. Parameter IDs 100-114 and OSO1 state unchanged.
#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>

namespace omega::v4 {
enum class GenerativeState : uint8_t { Static=0, Pulse=1, Rise=2, Orbit=3 };

// The only permitted step generator is a deterministic timbral modulation lane,
// NOT a MIDI/song generator. Steps are prepared OFF the audio thread.
class Motion16 final {
public:
    void prepare(double sampleRate, double bpm, GenerativeState state, uint32_t seed) noexcept {
        sr_ = std::isfinite(sampleRate) ? std::clamp(sampleRate, 8000., 384000.) : 48000.;
        bpm_ = std::isfinite(bpm) ? std::clamp(bpm, 20., 400.) : 120.;
        // Preserve the original 48 kHz time constant at every sample rate.
        slew_ = sr_==48000. ? .004 : -std::expm1(std::log1p(-.004)*48000./sr_);
        mode_ = state;
        uint32_t rng = seed ? seed : 1u;
        for (int i=0;i<16;++i) {
            double value = 0.;
            switch (state) {
                case GenerativeState::Static: value=0.; break;
                case GenerativeState::Pulse: value=(i%4==0 ? 1. : (i%2==0 ? .25 : -.5)); break;
                case GenerativeState::Rise: value=(double(i)-7.5)/7.5; break;
                case GenerativeState::Orbit:
                    rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5;
                    value = double(rng) / 2147483647.5 - 1.;
                    break;
            }
            steps_[size_t(i)] = value;
        }
        samplesPerStep_ = sr_*60./(bpm_*4.);
        reset();
    }
    void setDepth(double depth) noexcept {depth_=std::isfinite(depth) ? std::clamp(depth,0.,1.) : 0.;}
    void setTempo(double bpm) noexcept {
        if(!std::isfinite(bpm)||bpm<20.||bpm>400.||bpm==bpm_)return;
        const double phase=position_/samplesPerStep_;
        bpm_=bpm;samplesPerStep_=sr_*60./(bpm_*4.);
        position_=phase*samplesPerStep_;
    }
    void reset() noexcept {position_=0.;index_=0;filtered_=0.;}
    double tick() noexcept {
        const double target=steps_[size_t(index_)];
        filtered_+=slew_*(target-filtered_);
        position_+=1.;
        if (position_>=samplesPerStep_){position_-=samplesPerStep_;index_=(index_+1)&15;}
        // Zero depth is exact silence, but transport phase keeps advancing.
        return depth_==0. ? 0. : filtered_*depth_;
    }
    int stepIndex() const noexcept {return index_;}
    double stepPhase() const noexcept {return position_/samplesPerStep_;}
    GenerativeState state() const noexcept {return mode_;}
private:
    std::array<double,16> steps_{};
    double sr_=48000.,bpm_=120.,samplesPerStep_=6000.,position_=0.,filtered_=0.,depth_=0.,slew_=.004;
    int index_=0;GenerativeState mode_=GenerativeState::Static;
};

enum class ContourState : uint8_t { Idle, Attack, Hold, Decay, Sustain, Release };
// Modulation envelope independent of existing LIFE amplitude envelope.
// Never replace legacy ADSR; this remains opt-in experimental control only.
class ModContour final {
public:
    void prepare(double sr, double aMs, double hMs, double dMs, double sustain, double rMs) noexcept {
        sr_=std::isfinite(sr)?std::clamp(sr,8000.,384000.):48000.;
        attack_=samples(aMs); hold_=samples(hMs);decay_=samples(dMs);release_=samples(rMs);
        sustain_=std::isfinite(sustain)?std::clamp(sustain,0.,1.):.5;reset();
    }
    void reset() noexcept {state_=ContourState::Idle;value_=0.;at_=0.;start_=0.;}
    void noteOn() noexcept {start_=value_;at_=0.;state_=ContourState::Attack;}
    void noteOff() noexcept {if(state_!=ContourState::Idle){start_=value_;at_=0.;state_=ContourState::Release;}}
    double tick() noexcept {
        switch(state_){
        case ContourState::Idle: value_=0.; break;
        case ContourState::Attack:
            value_=start_+(1.-start_)*double(++at_)/double(attack_);
            if(at_>=attack_){value_=1.;at_=0;state_=ContourState::Hold;}break;
        case ContourState::Hold:
            value_=1.;if(++at_>=hold_){at_=0;state_=ContourState::Decay;}break;
        case ContourState::Decay:
            value_=1.-(1.-sustain_)*double(++at_)/double(decay_);
            if(at_>=decay_){value_=sustain_;state_=ContourState::Sustain;}break;
        case ContourState::Sustain: value_=sustain_;break;
        case ContourState::Release:
            value_=start_*(1.-double(++at_)/double(release_));
            if(at_>=release_){value_=0.;state_=ContourState::Idle;}break;
        }
        return std::clamp(value_,0.,1.);
    }
    ContourState state()const noexcept{return state_;}
private:
    int samples(double ms) const noexcept{
        const double s=std::isfinite(ms)?std::clamp(ms,0.01,30000.):1.;
        return std::max(1,int(sr_*s*.001));
    }
    double sr_=48000.,value_=0.,start_=0.,sustain_=.5;
    int attack_=1,hold_=1,decay_=1,release_=1,at_=0;
    ContourState state_=ContourState::Idle;
};

// Two interacting *musical* resonators inspired by near-matched modes.
// This is NOT a calibrated reproduction of the Great Pyramid waveguide network.
// Purely offline-prepared coefficients, no buffers, allocs, locks or network.
class CoupledModes final {
public:
    void prepare(double sampleRate,double fA,double fB,double t60A,double t60B,double coupling) noexcept {
        sr_=std::isfinite(sampleRate)?std::clamp(sampleRate,8000.,384000.):48000.;
        configure(a_,fA,t60A);configure(b_,fB,t60B);
        k_=std::isfinite(coupling)?std::clamp(coupling,0.,.02):0.;
        reset();
    }
    void reset() noexcept {a_.re=a_.im=b_.re=b_.im=0.;}
    void excite(double amount) noexcept {
        const double x=std::isfinite(amount)?std::clamp(amount,-1.,1.):0.;
        a_.re+=x*.02;
    }
    double tick() noexcept {
        const double delta=k_*(b_.re-a_.re);
        const double ai=a_.re,aj=a_.im,bi=b_.re,bj=b_.im;
        a_.re=((ai+delta)*a_.c-aj*a_.s)*a_.d;
        a_.im=((ai+delta)*a_.s+aj*a_.c)*a_.d;
        b_.re=((bi-delta)*b_.c-bj*b_.s)*b_.d;
        b_.im=((bi-delta)*b_.s+bj*b_.c)*b_.d;
        return .5*(a_.re+b_.re);
    }
    double energy()const noexcept {return a_.re*a_.re+a_.im*a_.im+b_.re*b_.re+b_.im*b_.im;}
private:
    struct Mode {double re=0.,im=0.,c=1.,s=0.,d=.9;};
    void configure(Mode& m,double f,double t60) noexcept {
        constexpr double pi=3.14159265358979323846;
        const double hz=std::isfinite(f)?std::clamp(f,5.,sr_*.45):32.7;
        const double sec=std::isfinite(t60)?std::clamp(t60,.03,8.):.5;
        const double angle=2.*pi*hz/sr_;
        m.c=std::cos(angle);m.s=std::sin(angle);
        m.d=std::exp(-6.907755278982137/(sec*sr_));
    }
    Mode a_,b_;double sr_=48000.,k_=0.;
};
} // namespace omega::v4

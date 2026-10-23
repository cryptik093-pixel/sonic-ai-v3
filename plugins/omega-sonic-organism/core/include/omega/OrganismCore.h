#pragma once
#include "DspPrimitives.h"
#include "State.h"
#include "v4/ExperimentalSectors.h"

namespace omega {

// Portable instrument engine. No SDK types or runtime services enter this layer.
class OrganismCore final {
public:
    static constexpr int kMaxVoices = 32;
    static constexpr int latencySamples = dsp::DriveStage::latency;
    void prepare(double sampleRate, int voiceLimit = 0);
    void setParameter(uint32_t id, double normalized) noexcept;
    void setMorph(float x) noexcept {setParameter(100,x);}
    void setEnergy(float x) noexcept {setParameter(101,x);}
    void setMotion(float x) noexcept {setParameter(102,x);}
    void setMaterial(float x) noexcept {setParameter(103,x);}
    void setOutput(float x) noexcept {setParameter(105,x);}
    void setTempo(double bpm) noexcept;
    void setPitchBend(float bipolar) noexcept;
    void setSustain(bool down) noexcept;
    void noteOn(int note, float velocity, int32_t noteId = -1) noexcept;
    void noteOff(int note, int32_t noteId = -1) noexcept;
    void allNotesOff() noexcept;
    void resetVoices() noexcept;
    void setVoiceLimit(int count) noexcept;
    void render(float* left, float* right, int frames) noexcept;
    int activeVoices() const noexcept;
    double currentPitch(int index = 0) const noexcept;
    double currentEnvelope(int index=0) const noexcept {return index>=0&&index<kMaxVoices?voices_[size_t(index)].env:0;}
    uint64_t voiceSerial(int index=0) const noexcept {return index>=0&&index<kMaxVoices?voices_[size_t(index)].age:0;}
    uint64_t nonFiniteFaults() const noexcept {return tables_.nonFiniteFaults;}
    uint32_t firstFaultSource() const noexcept {return tables_.firstFaultSource;}

private:
    friend struct CoreProfiler; // Offline diagnostic only; no callback instrumentation.
    enum class Stage : uint8_t { Off, Attack, Decay, Sustain, Release };
    struct Voice {
        Stage stage = Stage::Off;
        int note=0;int32_t noteId=-1;bool keyDown=false;
        double velocity=0,env=0,phase=0,pitch=0,targetPitch=0,glideStep=0;
        int glideRemaining=0;
        double elapsed=0,impact=1,phaseStep=0,nyquistGain=1,lastOutput=0,stealValue=0;
        int stealRemaining=0;
        uint32_t rng=1;uint64_t age=0;
        struct Mode {double re=0,im=0,cosine=1,sine=0,decay=1,weight=0;};
        std::array<Mode,4> modes{};
        std::array<double,8> harmonicFade{};
        double modeWeight=0,panOffset=0;
        bool modesActive=false;
        dsp::LowPass filter;
        dsp::DriveStage drive;
        std::array<double,latencySamples> envelopeDelay{};
        int envelopePosition=0;
    };
    struct HeldNote {int note=0;int32_t id=-1;float velocity=0;};
    struct Traits {
        double sine=1,saw=0,pulse=0,spectral=0,noise=0,modal=0,inharm=0;
        double attack=3,decay=130,sustain=.82,release=110,cutoff=700,q=.7;
        double drop=0,dropTime=80,drive=1,spread=0,wobble=0,vibrato=0;
        std::array<double,4> ratios{{1,2,3,4}},modeDecay{{100,80,60,40}},modeGain{{1,.5,.25,.125}};
    };
    static Traits traitsAt(double) noexcept;
    void startVoice(Voice&,int,float,int32_t,bool) noexcept;
    void releaseVoice(Voice&) noexcept;
    void refreshCoefficients() noexcept;
    void refreshVoice(Voice&) noexcept;
    double voiceSample(Voice&) noexcept;
    std::array<Voice,kMaxVoices> voices_{};
    std::array<HeldNote,128> held_{};int heldCount_=0;
    ParameterValues targets_=defaults(),smooth_=defaults();
    Traits traits_;
    dsp::Tables tables_;
    dsp::Room room_;
    v4::Motion16 stepMotion_;
    double stepValue_=0;
    dsp::LowPass::Coefficients filter_;
    double sr_=48000,tempo_=120,bend_=0,bendSmooth_=0,slew_=0,lfoPhase_=0,lfo_=0,lfoRate_=2.1;
    double attackStep_=0,decayRate_=0,releaseRate_=0,drive_=1,driveComp_=1,outputGain_=1,hqMix_=0;
    double dcL_=0,dcR_=0,prevL_=0,prevR_=0,dcPole_=0,strikeDecay_=1,lastMorph_=-1;
    double lastEnergy_=-1,lastOutputLevel_=-1;
    double pulseWidth_=.5,pulseDc_=0,tremolo_=1,noiseBase_=0,waveWeight_=1;
    std::array<double,8> harmonicWeights_{};
    std::array<double,4> modeDecays_{};
    int voiceLimit_=16,controlCounter_=0,stealLength_=240;
    bool sustain_=false;
    uint64_t counter_=1;
};

} // namespace omega

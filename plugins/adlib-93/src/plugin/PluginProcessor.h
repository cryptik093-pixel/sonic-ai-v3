#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include "core/Parameters.h"
#include "core/Types.h"
#include "core/StateCodec.h"
#include "core/SnapshotMailbox.h"
#include "ui/MeterBridge.h"
#include <atomic>
#include <memory>
#include <vector>
namespace adlib93 { class Transitions; }
class AdlibProcessor final : public juce::AudioProcessor {
public:
    AdlibProcessor();~AdlibProcessor() override;
    const juce::String getName() const override { return "ADLIB-93"; }
    void prepareToPlay(double,int) override;void releaseResources() override {};
    void reset() override;
    bool isBusesLayoutSupported(const BusesLayout&) const override;
    void processBlock(juce::AudioBuffer<float>&,juce::MidiBuffer&) override;
    void processBlockBypassed(juce::AudioBuffer<float>&,juce::MidiBuffer&) override;
    using AudioProcessor::processBlock;
    bool acceptsMidi() const override { return false; }bool producesMidi() const override { return false; }
    double getTailLengthSeconds() const override { return 180; }
    bool hasEditor() const override { return true; }juce::AudioProcessorEditor* createEditor() override;
    juce::AudioProcessorParameter* getBypassParameter() const override;
    int getNumPrograms() override { return 1; }int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int) override {}const juce::String getProgramName(int) override { return "Current State"; }
    void changeProgramName(int,const juce::String&) override {}
    void getStateInformation(juce::MemoryBlock&) override;void setStateInformation(const void*,int) override;
    juce::AudioProcessorValueTreeState parameters;
    adlib93::ParameterSnapshot snapshot() const noexcept;
    bool loadFactory(int index);void selectAB(int index);void copyAB();int activeAB() const noexcept { return activeSlot.load(); }
    void resetPreset(bool full=false);void clearTails();
    void setPerformance(adlib93::Param,bool);
    adlib93::CalibrationLocks calibrationLocks() const;void setCalibrationLocks(adlib93::CalibrationLocks);
    adlib93::UiState uiState() const;void setUiState(const adlib93::UiState&);
    bool saveUserPreset(const juce::String& name);bool loadUserPreset(const juce::File&);
    juce::File userPresetDirectory() const;juce::String lastError() const;
    adlib93::MeterSnapshot readMeters() const noexcept { return meters.read(); }
private:
    static juce::AudioProcessorValueTreeState::ParameterLayout makeParameters();
    void process(juce::AudioBuffer<float>&,bool);void applySnapshot(adlib93::ParameterSnapshot,bool notify);
    void requestSnapshot(adlib93::ParameterSnapshot,bool notify);
    std::array<std::atomic<float>*,adlib93::parameterCount> raw{};
    std::array<juce::RangedAudioParameter*,adlib93::parameterCount> ranged{};
    mutable juce::CriticalSection stateMutex;
    adlib93::PersistedState saved;
    adlib93::SnapshotMailbox mailbox;
    std::unique_ptr<adlib93::Transitions> processing;
    adlib93::MeterBridge meters;
    std::atomic<int> activeSlot{0};std::atomic<bool> writingSnapshot{false},clearRequested{false};
    adlib93::ParameterSnapshot audioSnapshot=adlib93::makeInitSnapshot();
    adlib93::ParameterSnapshot presetBaseline=adlib93::makeInitSnapshot();
    std::atomic<uint64_t> snapshotRevision{0};
    std::vector<adlib93::StereoFrame> correlationHistory;
    std::size_t correlationPosition=0,correlationCount=0;
    double sumLeft=0,sumRight=0,sumLL=0,sumRR=0,sumLR=0;
    bool prepared=false;
    void updateCorrelation(adlib93::StereoFrame) noexcept;
    float correlation() const noexcept;
    double processingRate=48000;int preparedBlock=128;uint64_t samplePosition=0;
    mutable juce::String errorText;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(AdlibProcessor)
};

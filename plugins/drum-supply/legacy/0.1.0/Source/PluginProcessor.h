#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include "DrumEngine.h"
#include <atomic>

class DrumProcessor final : public juce::AudioProcessor {
public:
    DrumProcessor();
    const juce::String getName() const override { return "Omega Drum Supply"; }
    void prepareToPlay(double,int) override;
    void reset() override;
    void releaseResources() override {}
    bool isBusesLayoutSupported(const BusesLayout&) const override;
    void processBlock(juce::AudioBuffer<float>&,juce::MidiBuffer&) override;
    using juce::AudioProcessor::processBlock;
    bool acceptsMidi() const override { return true; }
    bool producesMidi() const override { return false; }
    double getTailLengthSeconds() const override { return 16; }
    bool hasEditor() const override { return true; }
    juce::AudioProcessorEditor* createEditor() override;
    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int) override {}
    const juce::String getProgramName(int) override { return "Current Sound"; }
    void changeProgramName(int,const juce::String&) override {}
    void getStateInformation(juce::MemoryBlock&) override;
    void setStateInformation(const void*,int) override;
    bool restoreState(const void*,int);
    juce::AudioProcessorValueTreeState parameters;
    std::atomic<int> preview{-1}; // One bounded UI -> audio trigger mailbox.
    std::atomic<float> peak{0};
    std::atomic<uint32_t> meterFrame{0};
private:
    static juce::AudioProcessorValueTreeState::ParameterLayout layout();
    std::array<std::atomic<float>*,4> raw{};
    ohdrum::Engine engine;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(DrumProcessor)
};

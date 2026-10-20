#pragma once
#include "PluginProcessor.h"
class DrumEditor final : public juce::AudioProcessorEditor,private juce::Timer {
public:
    explicit DrumEditor(DrumProcessor&);
    void paint(juce::Graphics&) override;
    void resized() override;
private:
    void timerCallback() override;
    DrumProcessor& processor;
    juce::ComboBox department;
    juce::TextButton hit{"AUDITION"};
    juce::Label routing,meter;
    std::array<juce::Slider,3> knobs;
    std::array<juce::Label,3> labels;
    std::array<std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment>,3> attachments;
    std::unique_ptr<juce::AudioProcessorValueTreeState::ComboBoxAttachment> departmentAttachment;
    uint32_t lastFrame=0;
    int stale=0;
    float displayedPeak=0;
};

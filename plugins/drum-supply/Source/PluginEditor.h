#pragma once
#include "PluginProcessor.h"
class DrumEditor final : public juce::AudioProcessorEditor,private juce::Timer,public juce::FileDragAndDropTarget {
public:
    explicit DrumEditor(DrumProcessor&);
    ~DrumEditor() override;
    void paint(juce::Graphics&) override;
    void resized() override;
    bool isInterestedInFileDrag(const juce::StringArray&) override;
    void filesDropped(const juce::StringArray&,int,int) override;
private:
    struct Style final : juce::LookAndFeel_V4 {Style();void drawRotarySlider(juce::Graphics&,int,int,int,int,float,float,float,juce::Slider&) override;};
    void timerCallback() override;
    void select(int);
    void choose(int);
    void portable();
    int selected=0;
    DrumProcessor& processor;
    Style style;
    juce::TooltipWindow tooltips{this,500};
    std::array<juce::TextButton,8> pads;
    juce::TextButton load{"LOAD / RELINK SAMPLE"},hit{"AUDITION"},save{"SAVE KIT"},open{"LOAD KIT"},ab{"A / B"},resetButton{"STARTER"},exportButton{"EXPORT PORTABLE"},panicButton{"PANIC"};
    juce::Label kit,source,status,meter,outputName,spaceName;
    std::array<juce::Slider,16> detail;
    std::array<juce::Label,16> detailNames;
    std::array<juce::ToggleButton,3> switches;
    std::array<juce::Slider,3> macros;
    std::array<juce::Label,3> macroNames;
    juce::Slider output,space;
    std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> spaceAttachment;
    std::array<uint32_t,8> lastActivity{};
    std::array<int,8> pulses{};
    std::array<std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment>,16> detailAttachments;
    std::array<std::unique_ptr<juce::AudioProcessorValueTreeState::ButtonAttachment>,3> switchAttachments;
    std::array<std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment>,3> macroAttachments;
    std::unique_ptr<juce::AudioProcessorValueTreeState::SliderAttachment> outputAttachment;
    std::unique_ptr<juce::FileChooser> chooser;
    DrumProcessor::View current;
    juce::Rectangle<int> waveform;
    uint32_t lastFrame=0;int stale=0;float displayedPeak=0;
};

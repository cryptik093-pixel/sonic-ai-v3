#include "PluginEditor.h"
DrumEditor::DrumEditor(DrumProcessor& p):AudioProcessorEditor(p),processor(p) {
    setResizable(true,true);setResizeLimits(700,460,1200,780);setSize(900,560);
    addAndMakeVisible(department);department.setName("Drum department");
    for(int i=0;i<7;++i)department.addItem(ohdrum::names[static_cast<size_t>(i)],i+1);
    departmentAttachment=std::make_unique<juce::AudioProcessorValueTreeState::ComboBoxAttachment>(p.parameters,"department",department);
    constexpr std::array<const char*,3> ids{"body","character","space"};
    constexpr std::array<const char*,3> titles{"BODY","CHARACTER","SPACE"};
    constexpr std::array<const char*,3> tips{"Tuning, modal decay and noise duration for this department.",
        "Excitation, material partials, pitch attack and spectral balance.","Stereo diffusion, feedback, damping and ambience level."};
    for(size_t i=0;i<3;++i) {
        auto& k=knobs[i];addAndMakeVisible(k);k.setName(titles[i]);k.setTooltip(tips[i]);
        k.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);k.setTextBoxStyle(juce::Slider::TextBoxBelow,false,100,28);
        k.setDoubleClickReturnValue(true,i==2?.25:.5);k.setWantsKeyboardFocus(true);k.setNumDecimalPlacesToDisplay(2);
        k.setColour(juce::Slider::rotarySliderFillColourId,juce::Colour(0xffd5ad68));
        addAndMakeVisible(labels[i]);labels[i].setText(titles[i],juce::dontSendNotification);
        labels[i].setJustificationType(juce::Justification::centred);
        attachments[i]=std::make_unique<juce::AudioProcessorValueTreeState::SliderAttachment>(p.parameters,ids[i],k);
    }
    addAndMakeVisible(hit);hit.onClick=[this]{processor.preview.store(department.getSelectedId()-1);};
    addAndMakeVisible(routing);routing.setText("100% SYNTHESIS  /  MIDI 60: selected drum  /  GM notes: kit",juce::dontSendNotification);
    addAndMakeVisible(meter);meter.setText("Audio inactive",juce::dontSendNotification);startTimerHz(30);
}
void DrumEditor::resized() {
    auto r=getLocalBounds().reduced(28);r.removeFromTop(85);
    auto row=r.removeFromTop(40);department.setBounds(row.removeFromLeft(220));row.removeFromLeft(16);hit.setBounds(row.removeFromLeft(140));
    r.removeFromTop(24);auto dials=r.removeFromTop(std::max(180,r.getHeight()-80));
    const int width=dials.getWidth()/3;
    for(size_t i=0;i<3;++i) {auto cell=dials.removeFromLeft(width);labels[i].setBounds(cell.removeFromTop(28));knobs[i].setBounds(cell);}
    routing.setBounds(r.removeFromTop(32));meter.setBounds(r.removeFromTop(30));
}
void DrumEditor::paint(juce::Graphics& g) {
    g.fillAll(juce::Colour(0xff111519));g.setColour(juce::Colour(0xffd5ad68));
    g.setFont(juce::Font(juce::FontOptions(15.0f)));g.drawText("OMEGA HOUSE STUDIO",28,22,getWidth()-56,24,juce::Justification::left);
    g.setColour(juce::Colours::whitesmoke);g.setFont(juce::Font(juce::FontOptions(30.0f,juce::Font::bold)));
    g.drawText("DRUM SUPPLY HEADQUARTERS",28,52,getWidth()-56,42,juce::Justification::left);
}
void DrumEditor::timerCallback() {
    const auto frame=processor.meterFrame.load(std::memory_order_acquire);
    if(frame==lastFrame)++stale;else {stale=0;lastFrame=frame;}
    displayedPeak=std::max(processor.peak.load(std::memory_order_relaxed),displayedPeak*.8f);
    if(stale>6)displayedPeak=0;
    meter.setText(stale>6?"Audio inactive":"Output peak: "+juce::String(juce::Decibels::gainToDecibels(displayedPeak,-90.0f),1)+" dBFS",juce::dontSendNotification);
}

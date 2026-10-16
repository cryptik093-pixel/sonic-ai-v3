#pragma once
#include "PluginProcessor.h"
#include "ui/PedalLookAndFeel.h"
#include "ui/ControlModel.h"
#include <memory>
#include <vector>
class AdlibEditor final:public juce::AudioProcessorEditor,private juce::Timer,private juce::ListBoxModel {
public:
 explicit AdlibEditor(AdlibProcessor&);~AdlibEditor() override;
 void paint(juce::Graphics&) override;void resized() override;void focusLost(FocusChangeType) override;
private:
 struct ParameterControl;
 class ThrowButton final:public juce::TextButton {
 public:
  using juce::TextButton::TextButton;std::function<void(bool)> edge;
  void mouseDown(const juce::MouseEvent&e)override{juce::TextButton::mouseDown(e);if(edge)edge(true);}
  void mouseUp(const juce::MouseEvent&e)override{juce::TextButton::mouseUp(e);if(edge)edge(false);}
  bool keyPressed(const juce::KeyPress&k)override{if(k==juce::KeyPress::spaceKey||k==juce::KeyPress::returnKey){if(!keyboardHeld){keyboardHeld=true;if(edge)edge(true);}return true;}return juce::TextButton::keyPressed(k);}
  bool keyStateChanged(bool down)override{if(keyboardHeld&&!juce::KeyPress::isKeyCurrentlyDown(juce::KeyPress::spaceKey)&&!juce::KeyPress::isKeyCurrentlyDown(juce::KeyPress::returnKey)){keyboardHeld=false;if(edge)edge(false);return true;}return juce::TextButton::keyStateChanged(down);}
  void focusLost(FocusChangeType type)override{keyboardHeld=false;if(edge)edge(false);juce::TextButton::focusLost(type);}
 private:bool keyboardHeld=false;
 };
 void timerCallback() override;void selectPage(int);void showBrowser(bool);void refreshBrowser();void loadSelected();void saveAs();void releaseThrow();
 int getNumRows() override;void paintListBoxItem(int,juce::Graphics&,int,int,bool) override;void returnKeyPressed(int) override;void listBoxItemClicked(int,const juce::MouseEvent&) override;
 AdlibProcessor& processor;adlib93::PedalLookAndFeel look;adlib93::ui::ThrowGesture throwGesture;
 std::vector<std::unique_ptr<ParameterControl>> mainControls,details,topControls;
 juce::Component detailBody,browserBody;juce::Viewport detailViewport;
 juce::TextButton browse{"BROWSE"},previous{"<"},next{">"},save{"SAVE AS"},reset{"RESET"},fullReset{"FULL RESET"},a{"A"},b{"B"},copy{"COPY"},clear{"CLEAR TAILS"},browserLoad{"LOAD"},browserClose{"CLOSE"},peakReset{"RESET PEAKS"};
 juce::TextButton bypass{"BYPASS"},freeze{"FREEZE"};ThrowButton throwButton{"THROW"};
 juce::ToggleButton latch{"LATCH"},inputLock{"INPUT LOCK"},gateLock{"GATE LOCK"},outputLock{"OUTPUT LOCK"};
 juce::ComboBox routing,scale;juce::TextEditor search;juce::ListBox list{"Preset browser",this};
 juce::Label presetLabel,statusLabel,meterLabel,overrideLabel,diagnosticLabel,browserNotice;
 std::array<juce::TextButton,6> tabs;
 std::vector<int> filteredFactories;juce::Array<juce::File> filteredUsers;juce::StringArray filteredUserNames;
 std::vector<std::unique_ptr<juce::AudioProcessorValueTreeState::ButtonAttachment>> buttonAttachments;
 std::unique_ptr<juce::AudioProcessorValueTreeState::ComboBoxAttachment> routingAttachment;
 juce::TooltipWindow tooltip{this,500};int page=0,factoryIndex=0;bool browserVisible=false,clearing=false;float heldInput=-100,heldOutput=-100;
 JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(AdlibEditor)
};

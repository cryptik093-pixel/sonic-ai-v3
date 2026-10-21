#pragma once
#include "DrumEngine.h"
#include <juce_core/juce_core.h>
#include <juce_cryptography/juce_cryptography.h>
#include <atomic>
class RenderService {
public:
 struct Settings {std::array<ohdrum::SlotControls,8> controls{};ohdrum::Macros macros{};float output=-6;double rate=48000;};
 struct Result {juce::File file;int64_t frames=0;int rate=48000;double peak=0,rms=0;bool truncated=false;juce::String sha256;};
 // Control worker only. Uses the exact production synth, independent of the live instance.
 static Result oneShot(const Settings&,const std::array<const ohsample::Sample*,8>&,int slot,const juce::File&,const std::atomic<bool>& cancel,bool overwrite=false);
 static juce::String safeName(const juce::String&);
};

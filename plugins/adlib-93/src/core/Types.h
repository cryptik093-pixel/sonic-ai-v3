#pragma once
#include <cstdint>
namespace adlib93 {
enum class ChannelLayout { monoMono, monoStereo, stereoStereo };
struct PrepareSpec { double sampleRate=48000; uint32_t maxBlockSize=128; ChannelLayout layout=ChannelLayout::stereoStereo; };
struct StereoFrame { float left=0, right=0; };
struct HostTiming { double bpm=120; int numerator=4, denominator=4; bool bpmValid=false, signatureValid=false; };
struct ProcessContext { HostTiming timing{}; uint64_t absoluteSample=0; };
}

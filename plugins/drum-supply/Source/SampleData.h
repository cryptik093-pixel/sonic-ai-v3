#pragma once
#include <array>
#include <vector>
#include <cstddef>
namespace ohsample {
inline constexpr std::array<const char*,7> names{"Kick","Snare","Hi-Hat","Cymbal","Tom","Percussion","Clap"};
// Immutable after publication. The control worker owns/reclaims these buffers.
struct Sample {
    double rate=48000;
    std::array<std::vector<float>,2> audio;
    std::array<float,256> waveform{};
    size_t frames() const noexcept {return audio[0].size();}
};
}

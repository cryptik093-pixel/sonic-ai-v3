#include "omega/OrganismCore.h"
#include <array>
#include <cstdlib>
#define CHECK(cond) do { if (!(cond)) { std::cerr << "FAIL " << __FILE__ << ":" << __LINE__ << " " << #cond << "\n"; std::exit(1); } } while (false)
#include <cmath>
#include <iostream>
#include <vector>

namespace {
std::vector<float> capture(float morph, bool split = false) {
    omega::OrganismCore synth;
    synth.setMorph(morph);
    synth.prepare(48000.0);
    synth.noteOn(48, 0.95f);
    std::vector<float> left(4096), right(4096);
    if (!split) synth.render(left.data(), right.data(), 4096);
    else {
        for (int i = 0; i < 4096; i += 64) synth.render(left.data()+i,right.data()+i,64);
    }
    double rms = 0.0;
    for (float sample : left) {
        CHECK(std::isfinite(sample));
        CHECK(std::abs(sample) <= 1.0f);
        rms += static_cast<double>(sample)*sample;
    }
    CHECK(rms > 1e-5);
    return left;
}
}
int main() {
    std::array<std::vector<float>,5> anchors;
    for (int i=0;i<5;++i) anchors[static_cast<size_t>(i)] = capture(i/4.0f);
    for (int i=0;i<4;++i) {
        auto midpoint = capture((i+0.5f)/4.0f);
        CHECK(midpoint.size() == 4096);
    }
    // Proof that regions are distinct; proper spectral/perceptual qualification is still necessary.
    for (int i=1;i<5;++i) {
        double difference = 0;
        for (size_t n=0;n<4096;++n) difference += std::abs(anchors[i][n]-anchors[i-1][n]);
        CHECK(difference > 0.2);
    }
    const auto normal = capture(0.625f), chunks = capture(0.625f,true);
    for (size_t i=0;i<normal.size();++i) CHECK(normal[i] == chunks[i]);

    omega::OrganismCore synth;
    synth.prepare(44100.0,1);
    synth.noteOn(60,1.0f);
    synth.noteOn(62,0.9f);
    CHECK(synth.activeVoices() == 1);
    synth.noteOff(62);
    std::array<float,256> left {}, right {};
    for (int i=0;i<1000;++i) synth.render(left.data(),right.data(),256);
    CHECK(synth.activeVoices() == 0);
    synth.prepare(96000.0,32);
    for (int i=0;i<40;++i) synth.noteOn(36 + i%48,0.8f);
    CHECK(synth.activeVoices() == 32);
    synth.allNotesOff();
    for (int i=0;i<2500;++i) synth.render(left.data(),right.data(),256);
    CHECK(synth.activeVoices() == 0);
    std::cout << "Omega DSP P0 smoke tests passed; host validation is reported separately.\n";
}

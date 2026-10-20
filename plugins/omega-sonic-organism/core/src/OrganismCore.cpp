#include "omega/OrganismCore.h"
#include <algorithm>
#include <cmath>
#include <limits>

namespace omega {
namespace {
constexpr double pi = 3.1415926535897932384626433832795;
constexpr double twopi = 2.0 * pi;

struct Traits {
    double sine, saw, modal, noise, inharm, attackMs, decayMs, sustain, releaseMs, cutoff, pitchDrop;
};
// Deliberately small provisional profiles: final modal/wavetable system is in the blueprint.
constexpr std::array<Traits, 5> anchors {{
    {0.87, 0.30, 0.10, 0.006, 0.08, 3, 130, 0.82, 110, 800, 3},
    {0.21, 0.018, 0.95, 0.025, 0.91, 2, 1550, 0.25, 1200, 8500, 0},
    {0.28, 0.90, 0.08, 0.010, 0.05, 8, 180, 0.72, 240, 4800, 0},
    {0.31, 0.61, 0.44, 0.080, 0.34, 30, 600, 0.65, 650, 2900, 0},
    {0.09, 0.08, 0.42, 0.84, 0.66, 1, 220, 0.00, 130, 6600, 5}
}};
inline double clamp01(double x) noexcept { return std::max(0.0, std::min(1.0, x)); }
inline double lerp(double a, double b, double t) noexcept { return a + (b - a) * t; }
inline double logLerp(double a, double b, double t) noexcept { return std::exp(lerp(std::log(a), std::log(b), t)); }
inline double polyBlep(double t, double dt) noexcept {
    if (t < dt) { t /= dt; return t + t - t*t - 1.0; }
    if (t > 1.0 - dt) { t = (t - 1.0) / dt; return t*t + t + t + 1.0; }
    return 0.0;
}
inline double hzOf(int note) noexcept { return 440.0 * std::exp2((note - 69) / 12.0); }
inline double perSampleAlpha(double ms, double sr) noexcept {
    return 1.0 - std::exp(-1000.0 / (sr * std::max(0.5, ms)));
}
Traits traitsAt(double morph) noexcept {
    double at = clamp01(morph) * 4.0;
    auto index = static_cast<int>(at);
    index = std::min(index, 3);
    double t = at - index;
    if (index == 3) t = clamp01(t);
    const auto& a = anchors[static_cast<size_t>(index)];
    const auto& b = anchors[static_cast<size_t>(index + 1)];
    return {lerp(a.sine,b.sine,t),lerp(a.saw,b.saw,t),lerp(a.modal,b.modal,t),
        lerp(a.noise,b.noise,t),lerp(a.inharm,b.inharm,t),
        logLerp(a.attackMs,b.attackMs,t), logLerp(a.decayMs,b.decayMs,t),
        lerp(a.sustain,b.sustain,t),logLerp(a.releaseMs,b.releaseMs,t),
        logLerp(a.cutoff,b.cutoff,t),lerp(a.pitchDrop,b.pitchDrop,t)};
}
} // namespace

void OrganismCore::prepare(double sampleRate, int voiceLimit) noexcept {
    sr_ = (std::isfinite(sampleRate) && sampleRate >= 8000.0 && sampleRate <= 384000.0) ? sampleRate : 48000.0;
    voiceLimit_ = std::max(1, std::min(kMaxVoices, voiceLimit));
    for (auto& voice : voices_) voice = Voice{};
    counter_ = 1;
    morphSmoothed_ = morphTarget_;
}
void OrganismCore::setMorph(float x) noexcept { if (std::isfinite(x)) morphTarget_ = static_cast<float>(clamp01(x)); }
void OrganismCore::setEnergy(float x) noexcept { if (std::isfinite(x)) energy_ = static_cast<float>(clamp01(x)); }
void OrganismCore::setMotion(float x) noexcept { if (std::isfinite(x)) motion_ = static_cast<float>(clamp01(x)); }
void OrganismCore::setMaterial(float x) noexcept { if (std::isfinite(x)) material_ = static_cast<float>(clamp01(x)); }
void OrganismCore::setOutput(float x) noexcept { if (std::isfinite(x)) output_ = static_cast<float>(clamp01(x)); }
void OrganismCore::noteOn(int note, float velocity, int32_t noteId) noexcept {
    if (note < 0 || note > 127 || !std::isfinite(velocity)) return;
    if (velocity <= 0.0f) { noteOff(note, noteId); return; }
    Voice* victim = nullptr;
    for (int i = 0; i < voiceLimit_; ++i) {
        auto& v = voices_[static_cast<size_t>(i)];
        if (v.stage == Stage::Off) { victim = &v; break; }
        if (v.stage == Stage::Release && (!victim || victim->stage != Stage::Release || v.env < victim->env)) victim = &v;
    }
    if (!victim) {
        victim = &voices_[0];
        for (int i = 1; i < voiceLimit_; ++i) {
            if (voices_[static_cast<size_t>(i)].age < victim->age) victim = &voices_[static_cast<size_t>(i)];
        }
    }
    *victim = Voice{};
    victim->stage = Stage::Attack;
    victim->note = note;
    victim->noteId = noteId;
    victim->velocity = static_cast<float>(clamp01(velocity));
    victim->age = counter_++;
    victim->rng = (static_cast<uint32_t>(note + 1) * 747796405u) ^ (static_cast<uint32_t>(victim->age) * 2891336453u);
    if (victim->rng == 0) victim->rng = 1;
}
void OrganismCore::noteOff(int note, int32_t noteId) noexcept {
    Voice* oldest = nullptr;
    for (int i = 0; i < voiceLimit_; ++i) {
        auto& v = voices_[static_cast<size_t>(i)];
        if (v.note != note || v.stage == Stage::Off || v.stage == Stage::Release) continue;
        if (noteId >= 0) { if(v.noteId == noteId) { v.stage = Stage::Release; return; } }
        else if(!oldest || v.age < oldest->age) oldest = &v;
    }
    if(oldest) oldest->stage = Stage::Release;
}
void OrganismCore::allNotesOff() noexcept {
    for (int i = 0; i < voiceLimit_; ++i)
        if (voices_[static_cast<size_t>(i)].stage != Stage::Off) voices_[static_cast<size_t>(i)].stage = Stage::Release;
}
void OrganismCore::resetVoices() noexcept {
    for (auto& voice : voices_) voice = Voice{};
    counter_ = 1;
    morphSmoothed_ = morphTarget_;
}
void OrganismCore::setVoiceLimit(int count) noexcept {
    voiceLimit_ = std::clamp(count, 1, kMaxVoices);
    for (int i=voiceLimit_;i<kMaxVoices;++i) voices_[static_cast<size_t>(i)]=Voice{};
}
int OrganismCore::activeVoices() const noexcept {
    int total = 0;
    for (int i=0; i < voiceLimit_; ++i) if (voices_[static_cast<size_t>(i)].stage != Stage::Off) ++total;
    return total;
}
void OrganismCore::render(float* left, float* right, int frames) noexcept {
    if (!left || !right || frames <= 0) return;
    const double slew = perSampleAlpha(18.0, sr_);
    const double db = -24.0 + static_cast<double>(output_) * 30.0;
    const double gain = std::pow(10.0, db / 20.0);
    for (int n = 0; n < frames; ++n) {
        morphSmoothed_ += static_cast<float>((morphTarget_ - morphSmoothed_) * slew);
        const Traits t = traitsAt(morphSmoothed_);
        const double cutoff = std::clamp(t.cutoff * (0.7 + 1.4 * energy_), 35.0, sr_ * 0.42);
        const double filt = 1.0 - std::exp(-twopi * cutoff / sr_);
        const double att = perSampleAlpha(t.attackMs, sr_);
        const double dec = perSampleAlpha(t.decayMs, sr_);
        const double rel = perSampleAlpha(t.releaseMs, sr_);
        const double inharm = std::min(1.0, t.inharm * (0.55 + material_ * 0.9));
        const double noiseAmount = std::min(0.9, t.noise * (0.25 + 1.5 * material_));
        double acc = 0.0;
        for (int vIndex = 0; vIndex < voiceLimit_; ++vIndex) {
            auto& v = voices_[static_cast<size_t>(vIndex)];
            if (v.stage == Stage::Off) continue;
            switch (v.stage) {
                case Stage::Attack:
                    v.env += static_cast<float>((1.0 - v.env) * att);
                    if (v.env > 0.993f) v.stage = Stage::Decay;
                    break;
                case Stage::Decay:
                    v.env += static_cast<float>((t.sustain - v.env) * dec);
                    if (std::abs(v.env - t.sustain) < 0.002f) v.stage = Stage::Sustain;
                    break;
                case Stage::Sustain: v.env += static_cast<float>((t.sustain - v.env) * dec); break;
                case Stage::Release:
                    v.env += static_cast<float>((0.0 - v.env) * rel);
                    if (v.env < 0.00001f) { v.stage = Stage::Off; v.env = 0; continue; }
                    break;
                case Stage::Off: break;
            }
            const double pitchEnv = t.pitchDrop * std::exp(-v.elapsed / 0.065);
            const double lfo = std::sin(v.lfoPhase * twopi) * 0.018 * motion_;
            const double hz = hzOf(v.note) * std::exp2((pitchEnv + lfo) / 12.0);
            double dt = hz / sr_;
            dt = std::min(0.49, dt);
            const double fundamental = std::sin(v.phase * twopi);
            const double saw = 2.0 * v.phase - 1.0 - polyBlep(v.phase, dt);
            const double ratio1 = 2.0 + 0.71 * inharm;
            const double ratio2 = 3.0 + 1.08 * inharm;
            const double modalA = (hz * ratio1 < sr_ * 0.45) ? std::sin(v.modal1 * twopi) : 0.0;
            const double modalB = (hz * ratio2 < sr_ * 0.45) ? std::sin(v.modal2 * twopi) : 0.0;
            const double modal = 0.72 * modalA + 0.28 * modalB;
            v.rng ^= v.rng << 13;
            v.rng ^= v.rng >> 17;
            v.rng ^= v.rng << 5;
            const double noise = (static_cast<double>(v.rng) / 4294967295.0) * 2.0 - 1.0;
            const double sumWeights = 0.01 + t.sine + t.saw + t.modal + noiseAmount;
            const double wave = (t.sine * fundamental + t.saw * saw + t.modal * modal + noiseAmount * noise) / sumWeights;
            v.filterMemory += filt * (wave - v.filterMemory);
            const double drive = 1.0 + 2.0 * energy_;
            const double shaped = std::tanh(v.filterMemory * drive) / std::tanh(drive);
            acc += shaped * v.env * v.velocity * 0.19;
            v.phase += dt; if (v.phase >= 1.0) v.phase -= 1.0;
            v.modal1 += dt * ratio1; v.modal1 -= std::floor(v.modal1);
            v.modal2 += dt * ratio2; v.modal2 -= std::floor(v.modal2);
            v.lfoPhase += 2.1 / sr_; if (v.lfoPhase >= 1.0) v.lfoPhase -= 1.0;
            v.elapsed += 1.0 / sr_;
        }
        // Prototype uses gain and soft saturation only. Production stereo Space and limiter are future M2 work.
        const float sample = static_cast<float>(std::tanh(acc * gain));
        left[n] = sample;
        right[n] = sample;
    }
}
} // namespace omega

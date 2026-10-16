#pragma once
#include <array>
#include <cstddef>
#include <type_traits>
namespace adlib93 {
enum class Param : std::size_t {
 InputGain, GateEnabled, GateThreshold, GateAttenuation, GateAttack, GateHold, GateRelease,
 DeessEnabled, DeessFrequency, DeessThreshold, DeessMaxReduction, DeessListen,
 CharacterEnabled, CharacterMode, CharacterHpEnabled, CharacterHp, CharacterLpEnabled, CharacterLp, CharacterDrive, CharacterTrim,
 DirectLevel, DoubleEnabled, DoubleDelayL, DoubleDelayR, DoubleDepthL, DoubleDepthR, DoubleRateL, DoubleRateR, DoubleLevel,
 ChorusEnabled, ChorusDelay, ChorusDepth, ChorusRate, ChorusLevel, StereoPan, StereoWidth,
 DelayEnabled, DelaySync, DelayTime, DelayDivision, DelayModifier, DelayManualBpm, DelayFeedback, DelayPingpong, DelayHp, DelayLp, DelayDiffusion, DelayLevel, DelayThrowMode,
 ThrowActive, ThrowLatch, ReverbEnabled, ReverbPredelay, ReverbDecay, ReverbDamping, ReverbLevel, ReverbDelaySend,
 DuckEnabled, DuckThreshold, DuckMaxReduction, DuckAttack, DuckRelease, FreezeActive, MixAmount, RoutingMode, BypassInternal, OutputGain, LimiterEnabled, LimiterCeiling, LimiterRelease, Count
};
inline constexpr std::size_t parameterCount=static_cast<std::size_t>(Param::Count);
enum class ParameterKind { continuous, boolean, choice, level };
struct Definition { const char* id; const char* name; const char* unit; float min,max,initial; ParameterKind kind; bool logarithmic=false, transient=false; };
struct ParameterSnapshot {
 std::array<float,parameterCount> values{};
 float operator[](Param p) const noexcept { return values[static_cast<std::size_t>(p)]; }
 float& operator[](Param p) noexcept { return values[static_cast<std::size_t>(p)]; }
};
static_assert(std::is_trivially_copyable_v<ParameterSnapshot>);
struct CalibrationLocks { bool input=true, gate=true, output=true; };
const std::array<Definition,parameterCount>& parameterDefinitions() noexcept;
ParameterSnapshot makeInitSnapshot() noexcept;
ParameterSnapshot sanitizeSnapshot(ParameterSnapshot,double sampleRate=48000) noexcept;
ParameterSnapshot persistentSnapshot(ParameterSnapshot) noexcept;
ParameterSnapshot applyCalibrationLocks(ParameterSnapshot incoming,const ParameterSnapshot& current,CalibrationLocks) noexcept;
float levelToGain(float) noexcept;
float levelFromDb(float) noexcept;
float levelToDb(float) noexcept;
float parameterToNormalized(Param,float) noexcept;
float parameterFromNormalized(Param,float) noexcept;
const Definition& parameterDefinition(Param) noexcept;
}

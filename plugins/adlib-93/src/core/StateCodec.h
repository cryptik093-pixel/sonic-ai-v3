#pragma once
#include "Parameters.h"
#include <cstdint>
#include <string>
#include <vector>
#if defined(ADLIB93_WITH_JUCE)
#include <juce_core/juce_core.h>
#endif
namespace adlib93 {
struct UiState { float scale=1; int page=0; std::string preset="Init"; bool modified=false; };
struct PersistedState {
 int schema=1; ParameterSnapshot parameters=makeInitSnapshot();
 std::array<ParameterSnapshot,2> slots{{makeInitSnapshot(),makeInitSnapshot()}};
 int activeSlot=0; CalibrationLocks locks{}; UiState ui{};
 // Optional schema-1 extension: original recipe survives modified project recall.
 // Absence in old state files falls back to active values/factory provenance.
 ParameterSnapshot presetBaseline=makeInitSnapshot();bool hasPresetBaseline=false;
};
struct DecodeResult { bool success=false; PersistedState state{}; std::string error; explicit operator bool()const noexcept{return success;} };
inline constexpr std::size_t maximumStateBytes=256*1024;
std::string encodeStateJson(const PersistedState&);
std::vector<uint8_t> encodeStateBytes(const PersistedState&);
DecodeResult decodeState(const void*,std::size_t);
#if defined(ADLIB93_WITH_JUCE)
inline juce::MemoryBlock encodeState(const PersistedState& state){auto s=encodeStateJson(state);return juce::MemoryBlock(s.data(),s.size());}
#else
inline std::vector<uint8_t> encodeState(const PersistedState& state){return encodeStateBytes(state);}
#endif
}

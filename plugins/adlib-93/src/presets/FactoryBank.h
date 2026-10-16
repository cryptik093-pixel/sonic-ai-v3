#pragma once
#include "core/Parameters.h"
#include <cstdint>
namespace adlib93 {
struct FactoryPreset { const char* id; const char* name; const char* family; ParameterSnapshot parameters; };
const std::array<FactoryPreset,24>& factoryPresets() noexcept;
ParameterSnapshot loadFactory(uint32_t,const ParameterSnapshot&,CalibrationLocks={}) noexcept;
}

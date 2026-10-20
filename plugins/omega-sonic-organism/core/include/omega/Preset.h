#pragma once
#include "State.h"
#include <string>
#include <string_view>
#include <vector>

namespace omega {
// Patch documents are parsed on the UI/tool thread, never in render().
struct Preset {
    std::string name="Untitled", author="Omega House Studio LLC", description;
    std::vector<std::string> tags;
    ParameterValues params=defaults();
};
bool parsePreset(std::string_view document, Preset& result, std::string& error);
std::string exportPreset(const Preset& preset);
}

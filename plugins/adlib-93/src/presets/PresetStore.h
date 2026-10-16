#pragma once
#include "core/StateCodec.h"
#include <filesystem>
namespace adlib93 {
struct UserPreset { std::string id; std::string name; ParameterSnapshot parameters=makeInitSnapshot(); };
struct SaveResult { bool success=false; std::filesystem::path file; std::string error; explicit operator bool()const noexcept{return success;} };
struct LoadResult { bool success=false; UserPreset preset; std::string error; explicit operator bool()const noexcept{return success;} };
class PresetStore {
 std::filesystem::path directory;
public:
 PresetStore();
 explicit PresetStore(std::filesystem::path root):directory(std::move(root)){}
 const std::filesystem::path& root()const noexcept{return directory;}
 SaveResult save(const UserPreset&)const;
 LoadResult load(const std::filesystem::path&)const;
#if defined(ADLIB93_WITH_JUCE)
 LoadResult load(const juce::File& file)const{return load(std::filesystem::path(file.getFullPathName().toWideCharPointer()));}
#endif
 static bool validDisplayName(const std::string&);
};
}

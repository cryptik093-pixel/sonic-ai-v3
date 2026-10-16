#include "PresetStore.h"
#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <random>
#include <system_error>
#if defined(_WIN32)
#define NOMINMAX
#include <windows.h>
#endif
namespace adlib93 {
namespace {
bool validId(const std::string& id){return id.size()==32&&std::all_of(id.begin(),id.end(),[](char c){return(c>='a'&&c<='f')||(c>='0'&&c<='9');});}
std::string newId(){std::random_device random;std::string out;constexpr char digits[]="0123456789abcdef";for(int i=0;i<32;++i)out+=digits[random()&15];return out;}
std::filesystem::path defaultDirectory(){
#if defined(_WIN32)
 const wchar_t* base=_wgetenv(L"APPDATA");if(!base||!*base)throw std::runtime_error("APPDATA is unavailable");return std::filesystem::path(base)/L"Omega House Studio"/L"ADLIB-93"/L"Presets";
#else
 const char* xdg=std::getenv("XDG_DATA_HOME");if(xdg&&*xdg)return std::filesystem::path(xdg)/"Omega House Studio"/"ADLIB-93"/"Presets";const char* home=std::getenv("HOME");if(!home||!*home)throw std::runtime_error("User data directory unavailable");return std::filesystem::path(home)/".local"/"share"/"Omega House Studio"/"ADLIB-93"/"Presets";
#endif
}
}
PresetStore::PresetStore():directory(defaultDirectory()){}
bool PresetStore::validDisplayName(const std::string& text){if(text.empty()||text.size()>128||text=="."||text.find("..")!=std::string::npos||text.front()==' '||text.back()==' '||text.back()=='.')return false;for(unsigned char c:text)if(c<32||c=='/'||c=='\\'||c==':'||c=='*'||c=='?'||c=='"'||c=='<'||c=='>'||c=='|')return false;auto base=text.substr(0,text.find('.'));std::transform(base.begin(),base.end(),base.begin(),[](unsigned char c){return char(std::toupper(c));});if(base=="CON"||base=="PRN"||base=="AUX"||base=="NUL"||base=="CLOCK$")return false;if(base.size()==4&&(base.substr(0,3)=="COM"||base.substr(0,3)=="LPT")&&base[3]>='1'&&base[3]<='9')return false;return true;}
SaveResult PresetStore::save(const UserPreset& preset)const{SaveResult result;std::filesystem::path temporary;try{
 if(!validDisplayName(preset.name))throw std::runtime_error("Choose a safe, non-reserved preset name");if(!preset.id.empty()&&!validId(preset.id))throw std::runtime_error("Invalid preset ID");
 for(std::size_t i=0;i<parameterCount;++i){auto v=preset.parameters.values[i];auto& d=parameterDefinitions()[i];if(!std::isfinite(v)||v<d.min||v>d.max||((d.kind==ParameterKind::boolean||d.kind==ParameterKind::choice)&&v!=std::floor(v)))throw std::runtime_error("Preset contains invalid parameter data");}
 std::filesystem::create_directories(directory);auto id=preset.id.empty()?newId():preset.id;result.file=directory/(id+".json");temporary=directory/(id+"."+newId()+".tmp");PersistedState state;state.parameters=persistentSnapshot(preset.parameters);state.slots={state.parameters,state.parameters};state.ui.preset=preset.name;const auto json=encodeStateJson(state);
 {std::ofstream stream(temporary,std::ios::binary|std::ios::trunc);if(!stream||!stream.write(json.data(),static_cast<std::streamsize>(json.size()))||!stream.flush())throw std::runtime_error("Could not write preset");}
#if defined(_WIN32)
 if(!MoveFileExW(temporary.c_str(),result.file.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH))throw std::runtime_error("Atomic preset replacement failed");
#else
 std::filesystem::rename(temporary,result.file);
#endif
 result.success=true;
 }catch(const std::exception& e){result.error=e.what();if(!temporary.empty()){std::error_code ec;std::filesystem::remove(temporary,ec);}}return result;}
LoadResult PresetStore::load(const std::filesystem::path& file)const{LoadResult result;try{if(!validId(file.stem().string())||file.extension()!=L".json")throw std::runtime_error("Invalid preset filename");const auto rootPath=std::filesystem::weakly_canonical(directory);const auto actual=std::filesystem::canonical(file);if(actual.parent_path()!=rootPath)throw std::runtime_error("Preset is outside the user preset directory");auto size=std::filesystem::file_size(actual);if(!size||size>maximumStateBytes)throw std::runtime_error("Preset exceeds 256 KiB or is empty");std::ifstream stream(actual,std::ios::binary);std::string json(static_cast<std::size_t>(size),'\0');if(!stream.read(json.data(),static_cast<std::streamsize>(size)))throw std::runtime_error("Could not read complete preset");auto state=decodeState(json.data(),json.size());if(!state)throw std::runtime_error(state.error);if(!validDisplayName(state.state.ui.preset))throw std::runtime_error("Invalid preset display name");result.preset={file.stem().string(),state.state.ui.preset,state.state.parameters};result.success=true;}catch(const std::exception& e){result.error=e.what();}return result;}
}

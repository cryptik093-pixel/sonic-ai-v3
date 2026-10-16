#include "TestSupport.h"
#include "presets/FactoryBank.h"
#include "presets/PresetStore.h"
#include <chrono>
#include <cmath>
#include <fstream>
#include <limits>
using namespace adlib93;
TEST_CASE("Presets.Bank"){
 const char* names[]={"Pocket Double","Short Slap","Tight Answer","Dry Bite","Left\xe2\x80\x93Right Reply","Quarter Bounce","Dotted Throw","Stereo Orbit","Ghost Room","Diffused Halo","Long Goodbye","Frozen Tail","Phone Booth","Radio Bite","Worn Tape","Broken Speaker","Chorus Crowd","Uneven Double","Slow Drift","Metallic Reply","Tunnel Call","Distorted Echo","Ducked Cathedral","Feedback Bloom"};
 auto& bank=factoryPresets();require(bank.size()==24,"24 full presets");for(std::size_t i=0;i<bank.size();++i){const auto&s=bank[i].parameters;require(bank[i].name==std::string(names[i]),"exact preset names and order");require(s.values==sanitizeSnapshot(s).values,"complete bounded preset snapshot");require(s[Param::LimiterEnabled]==1&&s[Param::LimiterCeiling]==-1&&s[Param::DeessEnabled]==1&&s[Param::DeessMaxReduction]==4,"factory safety base");require(s[Param::FreezeActive]==0&&s[Param::ThrowActive]==0&&s[Param::DeessListen]==0&&s[Param::BypassInternal]==0,"factory transients off");auto hostile=makeInitSnapshot();for(std::size_t j=0;j<parameterCount;++j)hostile.values[j]=parameterDefinitions()[j].max;require(loadFactory(uint32_t(i),hostile,{false,false,false}).values==s.values,"no previous-preset leakage");}
 struct Check{int index;Param parameter;float value;};const Check checks[]={
 {0,Param::DoubleDelayL,14},{0,Param::DoubleDelayR,22},{0,Param::StereoWidth,.7f},
 {1,Param::DelayTime,90},{1,Param::DelayFeedback,.08f},{1,Param::DelayLp,6000},
 {2,Param::DelayDivision,1},{2,Param::DelayFeedback,.18f},{2,Param::DuckMaxReduction,6},
 {3,Param::CharacterHp,120},{3,Param::CharacterLp,9000},{3,Param::CharacterDrive,6},{3,Param::CharacterTrim,-4},{3,Param::MixAmount,.65f},
 {4,Param::DelayDivision,2},{4,Param::DelayFeedback,.3f},{4,Param::DelayPingpong,1},
 {5,Param::DelayDivision,3},{5,Param::DelayFeedback,.38f},{5,Param::DelayPingpong,.75f},{5,Param::DuckMaxReduction,8},
 {6,Param::DelayDivision,2},{6,Param::DelayModifier,1},{6,Param::DelayFeedback,.35f},
 {7,Param::ChorusDelay,18},{7,Param::ChorusDepth,4},{7,Param::ChorusRate,.22f},{7,Param::DelayFeedback,.2f},
 {8,Param::ReverbPredelay,12},{8,Param::ReverbDecay,1.8f},{8,Param::CharacterHp,180},{8,Param::MixAmount,.85f},
 {9,Param::DelayFeedback,.35f},{9,Param::DelayDiffusion,.75f},{9,Param::ReverbDecay,3.5f},
 {10,Param::DelayDivision,3},{10,Param::DelayFeedback,.55f},{10,Param::ReverbDecay,6},{10,Param::DuckMaxReduction,10},
 {11,Param::DelayEnabled,1},{11,Param::DelayTime,250},{11,Param::DelayFeedback,0},{11,Param::DelayDiffusion,.85f},{11,Param::ReverbDecay,8},
 {12,Param::CharacterHp,450},{12,Param::CharacterLp,3200},{12,Param::CharacterDrive,4},{12,Param::CharacterTrim,-3},
 {13,Param::CharacterHp,250},{13,Param::CharacterLp,4500},{13,Param::CharacterMode,3},{13,Param::CharacterDrive,10},{13,Param::DelayTime,70},{13,Param::DelayFeedback,.05f},{13,Param::MixAmount,.9f},
 {14,Param::CharacterHp,100},{14,Param::CharacterLp,6500},{14,Param::CharacterDrive,7},{14,Param::ChorusDelay,12},{14,Param::ChorusDepth,.6f},{14,Param::ChorusRate,.35f},
 {15,Param::CharacterHp,350},{15,Param::CharacterLp,3800},{15,Param::CharacterMode,2},{15,Param::CharacterDrive,16},{15,Param::CharacterTrim,-12},{15,Param::MixAmount,.7f},
 {16,Param::DoubleDelayL,19},{16,Param::DoubleDelayR,31},{16,Param::ChorusDelay,15},{16,Param::ChorusDepth,3},{16,Param::ChorusRate,.8f},
 {17,Param::DoubleDelayL,11},{17,Param::DoubleDelayR,34},{17,Param::DoubleRateL,.27f},{17,Param::DoubleRateR,.41f},{17,Param::DoubleDepthL,.8f},{17,Param::DoubleDepthR,1.3f},
 {18,Param::ChorusDelay,20},{18,Param::ChorusDepth,4},{18,Param::ChorusRate,.08f},{18,Param::ReverbDecay,2},
 {19,Param::DelayTime,12},{19,Param::DelayFeedback,.65f},{19,Param::DelayDiffusion,0},{19,Param::DelayHp,500},{19,Param::MixAmount,.8f},
 {20,Param::CharacterHp,200},{20,Param::CharacterLp,5000},{20,Param::DelayTime,160},{20,Param::DelayFeedback,.42f},{20,Param::ReverbDecay,4},
 {21,Param::CharacterMode,3},{21,Param::CharacterDrive,12},{21,Param::CharacterTrim,-8},{21,Param::DirectLevel,0},{21,Param::DelayDivision,2},{21,Param::DelayFeedback,.4f},{21,Param::MixAmount,.45f},
 {22,Param::ReverbPredelay,45},{22,Param::ReverbDecay,9},{22,Param::DuckMaxReduction,12},{22,Param::DuckRelease,450},
 {23,Param::DelayDivision,3},{23,Param::DelayFeedback,.78f},{23,Param::DelayDiffusion,.6f},{23,Param::ReverbDecay,5},{23,Param::DuckMaxReduction,10}};
 for(auto c:checks)require(std::abs(bank[std::size_t(c.index)].parameters[c.parameter]-c.value)<1e-5f,"specified exact recipe controls");
 const float echoDb[]={-100,-12,-10,-100,-10,-12,-9,-18,-100,-14,-12,-18,-100,-16,-100,-100,-100,-100,-100,-12,-12,-6,-100,-14};
 for(std::size_t i=0;i<24;++i)require(std::abs(bank[i].parameters[Param::DelayLevel]-(echoDb[i]<-60?0:levelFromDb(echoDb[i])))<1e-6f,"all echo branch levels");
 require(std::abs(levelToDb(bank[11].parameters[Param::ReverbDelaySend])+6)<1e-4f,"Frozen Tail active diffusion send");
}
TEST_CASE("Presets.Locks"){
 auto current=makeInitSnapshot();current[Param::InputGain]=7;current[Param::OutputGain]=-4;current[Param::GateEnabled]=1;current[Param::GateThreshold]=-37;auto loaded=loadFactory(23,current);require(loaded[Param::InputGain]==7&&loaded[Param::OutputGain]==-4&&loaded[Param::GateEnabled]==1&&loaded[Param::GateThreshold]==-37,"default locks preserve full calibration");loaded=loadFactory(23,current,{false,false,false});require(loaded[Param::InputGain]==0&&loaded[Param::OutputGain]==0&&loaded[Param::GateEnabled]==0,"explicit full reset clears calibration");
}
TEST_CASE("Presets.Files"){
 auto path=std::filesystem::temp_directory_path()/("adlib93-preset-test-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));PresetStore store(path);struct Cleanup{std::filesystem::path p;~Cleanup(){std::error_code e;std::filesystem::remove_all(p,e);}}cleanup{path};
 for(const auto* name:{"../escape","..","CON","aux.json","COM1","LPT9","a/b","a\\b","bad:","trailing.",""})require(!PresetStore::validDisplayName(name),"unsafe and Windows reserved names rejected");
 UserPreset p{"","My Vocal & Space",factoryPresets()[11].parameters};auto saved=store.save(p);require(saved.success,"atomic user preset save");require(saved.file.parent_path()==path,"safe internal filename contained");auto loaded=store.load(saved.file);require(loaded.success&&loaded.preset.name==p.name&&loaded.preset.parameters.values==p.parameters.values,"user preset complete round trip");p.id=loaded.preset.id;p.parameters[Param::MixAmount]=.37f;saved=store.save(p);require(saved.success&&store.load(saved.file).preset.parameters[Param::MixAmount]==.37f,"atomic existing preset replacement");p.parameters[Param::DelayTime]=std::numeric_limits<float>::infinity();require(!store.save(p).success,"nonfinite save rejected");require(!store.load(path/"../outside.json").success,"outside load rejected");
 {std::ofstream stream(saved.file,std::ios::binary|std::ios::trunc);stream<<"{\"schema\":2}";}require(!store.load(saved.file).success,"incompatible file rejected");{std::ofstream stream(saved.file,std::ios::binary|std::ios::trunc);stream<<std::string(maximumStateBytes+1,'x');}require(!store.load(saved.file).success,"oversized file rejected");
}
TEST_CASE("Presets.Recall"){
 PersistedState state;state.parameters=factoryPresets()[21].parameters;state.parameters[Param::InputGain]=9;state.locks={true,true,true};auto bytes=encodeStateBytes(state);auto restored=decodeState(bytes.data(),bytes.size());require(restored.success&&restored.state.parameters[Param::InputGain]==9,"project recall ignores browsing locks");
}

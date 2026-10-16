#include "TestSupport.h"
#include "core/StateCodec.h"
#include "core/SnapshotMailbox.h"
#include <atomic>
#include <thread>
using namespace adlib93;
TEST_CASE("State.RoundTrip"){
 PersistedState a;a.parameters[Param::InputGain]=7;a.parameters[Param::FreezeActive]=1;a.parameters[Param::ThrowActive]=1;a.parameters[Param::DeessListen]=1;a.parameters[Param::BypassInternal]=1;a.slots[0][Param::DelayTime]=999;a.slots[1][Param::ReverbDecay]=8;a.activeSlot=1;a.locks={false,true,false};a.ui={1.5f,4,"Quoted \"name\"",true};auto data=encodeStateBytes(a);auto b=decodeState(data.data(),data.size());require(b.success,"state decode success");require(b.state.parameters.values==persistentSnapshot(a.parameters).values,"complete processing snapshot and transients off");require(b.state.slots[0].values==a.slots[0].values&&b.state.slots[1].values==a.slots[1].values,"A/B values restored");require(b.state.activeSlot==1&&!b.state.locks.input&&b.state.locks.gate&&!b.state.locks.output,"slot and locks restored");require(b.state.ui.scale==1.5f&&b.state.ui.page==4&&b.state.ui.preset==a.ui.preset&&b.state.ui.modified,"UI metadata restored");
}
TEST_CASE("State.Malformed"){
 auto decode=[](const std::string&s){return decodeState(s.data(),s.size());};
 for(const auto* s:{"{", "[]", "{\"schema\":2}","{\"schema\":1.2}","{\"parameters\":{\"delay.time\":\"250\"}}","{\"parameters\":{\"delay.time\":1e999}}","{\"parameters\":{\"delay.time\":-4}}","{\"schema\":1,\"schema\":1}","{\"locks\":{\"input\":0}}","{\"ui\":{\"page\":6}}"})require(!decode(s).success,"malformed state rejected");
 require(!decodeState(nullptr,0).success&&!decodeState("x",maximumStateBytes+1).success,"empty and oversize rejected before read");auto a=decode("{\"future\":[{},true],\"parameters\":{\"input.gain\":3}}");require(a.success&&a.state.parameters[Param::InputGain]==3&&a.state.parameters[Param::LimiterEnabled]==1,"unknown fields tolerated and missing defaults filled");
}
TEST_CASE("State.Concurrent"){
 SnapshotMailbox box;std::atomic<int> done{0};std::atomic<bool> mixed{false};
 auto producer=[&](int offset){for(int k=1;k<=15000;++k){ParameterSnapshot s;for(auto&v:s.values)v=float(k+offset);while(!box.tryPublish(s))std::this_thread::yield();}done.fetch_add(1);};
 std::thread a(producer,0),b(producer,20000);ParameterSnapshot s;unsigned reads=0;while(done.load()!=2){if(box.tryConsume(s)){++reads;for(float v:s.values)if(v!=s.values[0])mixed=true;}}
 a.join();b.join();require(reads>0&&!mixed.load(),"concurrent snapshots never mix generation markers");ParameterSnapshot latest;for(auto&v:latest.values)v=123;for(int i=0;i<100;++i)require(box.tryPublish(latest),"idle consumer permits coalescing");require(box.tryConsume(s)&&s.values==latest.values,"latest request delivered");
}
TEST_CASE("State.PresetBaseline"){
 const std::string json="{\"schema\":1,\"parameters\":{\"delay.time\":700},\"presetBaseline\":{\"delay.time\":321,\"freeze.active\":1},\"ui\":{\"preset\":\"Modified user recipe\",\"modified\":true}}";
 auto decoded=decodeState(json.data(),json.size());require(decoded.success,"Optional preset baseline is a valid schema1 addition");
 require(decoded.state.hasPresetBaseline&&decoded.state.presetBaseline[Param::DelayTime]==321,"Optional baseline presence and physical values retained");
 require(decoded.state.presetBaseline[Param::FreezeActive]==0,"Baseline does not persist captured performance state");
 auto encoded=encodeStateJson(decoded.state);require(encoded.find("\"presetBaseline\"")!=std::string::npos,"Loaded preset baseline survives project round trip separately from modified values");
 const auto baselineBegin=encoded.find("\"presetBaseline\"");require(encoded.find("321",baselineBegin)!=std::string::npos,"Original baseline delay retained");
 for(const auto* invalid:{"{\"presetBaseline\":{\"delay.time\":9000}}","{\"presetBaseline\":[]}","{\"presetBaseline\":{\"input.gain\":\"3\"}}"})require(!decodeState(invalid,std::char_traits<char>::length(invalid)).success,"Baseline validates through identical parameter schema");
 const std::string old="{\"schema\":1,\"parameters\":{\"delay.time\":456}}";auto legacy=decodeState(old.data(),old.size());
 require(legacy.success&&!legacy.state.hasPresetBaseline&&legacy.state.presetBaseline[Param::DelayTime]==456,"Old schema1 files retain active-snapshot baseline fallback");
}

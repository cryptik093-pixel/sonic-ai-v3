#include "TestSupport.h"
#include "core/Parameters.h"
#include <cmath>
#include <cstring>
#include <limits>
using namespace adlib93;
TEST_CASE("Parameters.Schema"){
 auto init=makeInitSnapshot();auto& defs=parameterDefinitions();require(defs.size()==70,"all 70 schema controls");
 for(std::size_t i=0;i<defs.size();++i){auto& d=defs[i];require(d.min<d.max,"nonempty range");require(init.values[i]>=d.min&&init.values[i]<=d.max,"default in range");for(std::size_t j=0;j<i;++j)require(std::strcmp(d.id,defs[j].id)!=0,"unique stable ID");for(float u:{0.f,.25f,.5f,.75f,1.f}){auto p=static_cast<Param>(i);if(d.kind==ParameterKind::continuous||d.kind==ParameterKind::level)require(std::abs(parameterToNormalized(p,parameterFromNormalized(p,u))-u)<2e-5f,"normalized physical round trip");}}
 require(init[Param::DeessFrequency]==6000&&init[Param::DelayLp]==8000&&init[Param::ReverbDamping]==6000,"frequency physical Hz");require(levelToGain(0)==0&&levelToGain(1)==1,"exact mute and unity");require(std::abs(levelToDb(levelFromDb(-12))+12)<1e-4f,"level dB round trip");
 const float minimumLevel=levelFromDb(-60);
 require(minimumLevel>0&&std::isnormal(minimumLevel),"-60 dB uses a normal positive value distinct from mute");
 require(std::abs(levelToGain(minimumLevel)-.001f)<=1e-7f,"-60 dB remains audible at its supported amplitude");
 float previousLevel=0;
 for(float db:{-60.f,-59.f,-24.f,-12.f,0.f}){
  const float normalized=levelFromDb(db);
  require(normalized>=previousLevel&&std::abs(levelToDb(normalized)-db)<1e-4f,"supported dB values map monotonically and round trip");
  previousLevel=normalized;
 }
 auto hostile=init;for(auto& v:hostile.values)v=std::numeric_limits<float>::quiet_NaN();require(sanitizeSnapshot(hostile).values==init.values,"nonfinite resets schema defaults");hostile=init;hostile[Param::CharacterMode]=2.6f;hostile[Param::DelayFeedback]=100;hostile=sanitizeSnapshot(hostile,-1);require(hostile[Param::CharacterMode]==3&&hostile[Param::DelayFeedback]==.9f,"enum rounding and safe clamp");
}

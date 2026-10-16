#include "TestSupport.h"
#include "dsp/Echo.h"
#include <cmath>
#include <limits>
using namespace adlib93;
TEST_CASE("Echo.Timing") {
 auto p=makeInitSnapshot();p[Param::DelaySync]=1;
 for(double bpm:{60.,90.,120.,180.})for(int signature=0;signature<3;++signature){
  HostTiming host{bpm,signature==0?3:signature==1?4:6,signature==2?8:4,true,true};
  for(int division=0;division<6;++division)for(int modifier=0;modifier<3;++modifier){
   p[Param::DelayDivision]=static_cast<float>(division);p[Param::DelayModifier]=static_cast<float>(modifier);
   const double quarters[]={.125,.25,.5,1,2,host.numerator*4./host.denominator};
   const double raw=60000/bpm*quarters[division]*(modifier==1?1.5:modifier==2?2./3:1.);
   const auto result=resolveDelayTime(p,host);
   require(std::abs(result.milliseconds-std::fmin(4000.,std::fmax(10.,raw)))<1.e-9,"physical musical delay timing");
   require(result.clamped==(raw<10||raw>4000),"delay clamp flag");require(!result.usingManual,"valid host tempo");
  }
 }
 p[Param::DelayDivision]=5;p[Param::DelayModifier]=0;
 HostTiming missing{};missing.bpm=std::numeric_limits<double>::quiet_NaN();missing.bpmValid=true;missing.numerator=0;missing.denominator=0;missing.signatureValid=true;
 auto result=resolveDelayTime(p,missing);require(result.usingManual&&result.milliseconds==2000,"invalid host fallback 120 BPM 4/4");
 for(const auto signature:{HostTiming{120,3,4,false,true},HostTiming{120,6,8,false,true}}){
  result=resolveDelayTime(p,signature);
  require(result.usingManual&&result.milliseconds==2000,"manual tempo fallback ignores host signature and assumes 4/4");
 }
 p[Param::DelayManualBpm]=90;result=resolveDelayTime(p,missing);require(std::abs(result.milliseconds-60000./90*4)<1.e-8,"displayed manual BPM respected");
 p[Param::DelayManualBpm]=std::numeric_limits<float>::infinity();result=resolveDelayTime(p,missing);require(result.milliseconds==2000,"nonfinite manual tempo fallback");
 p[Param::DelaySync]=0;p[Param::DelayTime]=37;require(resolveDelayTime(p,missing).milliseconds==37,"unsynced milliseconds");
}

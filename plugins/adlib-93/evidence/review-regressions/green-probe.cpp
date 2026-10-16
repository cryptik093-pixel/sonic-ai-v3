#include "core/Parameters.h"
#include "dsp/Echo.h"
#include "dsp/Freeze.h"
#include <cmath>
#include <cstdio>
int main() {
 using namespace adlib93;
 auto p=makeInitSnapshot(); p[Param::DelaySync]=1; p[Param::DelayDivision]=5;
 bool ok=true;
 for(const auto h:{HostTiming{120,3,4,false,true},HostTiming{120,6,8,false,true}}) {
  auto r=resolveDelayTime(p,h);
  std::printf("Manual fallback host %d/%d: %.9f ms; expected2000; %s\n",h.numerator,h.denominator,r.milliseconds,r.milliseconds==2000?"PASS":"FAIL");
  ok=ok&&r.usingManual&&r.milliseconds==2000;
 }
 for(int heldSamples:{5000,20000}) {
  Freeze f;f.prepare({});
  for(int i=0;i<12000;++i)f.process({float(.4*std::sin(i*.007)),0},false);
  StereoFrame previous{};
  for(int i=0;i<heldSamples;++i)previous=f.process({},true);
  auto release=f.process({},false);
  auto retrigger=f.process({},true);
  const float delta=std::abs(retrigger.left-release.left);
  std::printf("Freeze held %d samples, prior %.9f, release %.9f, retrigger %.9f; discontinuity %.9f; %s\n",heldSamples,previous.left,release.left,retrigger.left,delta,delta<.01?"PASS":"FAIL");
  ok=ok&&delta<.01;
 }
 const float minimum=levelFromDb(-60),minimumGain=levelToGain(minimum);
 std::printf("-60 dB representation %.9g; gain %.9g; %s\n",minimum,minimumGain,minimum>0&&std::abs(minimumGain-.001f)<=1e-7f?"PASS":"FAIL");
 ok=ok&&minimum>0&&std::abs(minimumGain-.001f)<=1e-7f;
 return ok?0:1;
}

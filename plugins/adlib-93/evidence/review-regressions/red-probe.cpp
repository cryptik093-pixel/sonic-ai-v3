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
 Freeze f;f.prepare({});
 for(int i=0;i<12000;++i)f.process({float(.4*std::sin(i*.007)),0},false);
 StereoFrame previous{};
 for(int i=0;i<5000;++i)previous=f.process({},true);
 auto release=f.process({},false);
 auto retrigger=f.process({},true);
 std::printf("Freeze held %.9f, release %.9f, retrigger %.9f; discontinuity %.9f\n",previous.left,release.left,retrigger.left,std::abs(retrigger.left-release.left));
 return ok?0:1;
}

#include "omega/v4/ExperimentalSectors.h"
#include <cstdlib>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
using namespace omega::v4;

// Acceptance checks must execute in Release (/DNDEBUG) as well as Debug.
#define CHECK(x) do { if (!(x)) { std::cerr << "FAIL " << __LINE__ << ": " << #x << '\n'; std::exit(1); } } while (false)

int main() {
    // MIDI/macro IDs and legacy host OSO1 state must not be changed by this R&D header.
    Motion16 a,b;
    a.prepare(48000.,120.,GenerativeState::Orbit,93021u);
    b.prepare(48000.,120.,GenerativeState::Orbit,93021u);
    for(int i=0;i<100000;++i) {CHECK(a.tick()==0.);CHECK(b.tick()==0.);}
    a.setDepth(.7);b.setDepth(.7);
    double sum=0.;
    for(int i=0;i<48000;++i){double x=a.tick(),y=b.tick();CHECK(x==y);CHECK(std::isfinite(x));CHECK(std::abs(x)<=.70000001);sum+=std::abs(x);}
    CHECK(sum>1.);
    Motion16 c;c.prepare(48000.,120.,GenerativeState::Rise,2);c.setDepth(1.);
    for(int i=0;i<160000;++i){const auto x=c.tick();CHECK(std::isfinite(x)&&x>=-1.000001&&x<=1.000001);}
    for (auto sr: {44100.,48000.,96000.}) {
        // Equal elapsed musical time must select the same step while muted.
        Motion16 clock;clock.prepare(sr,120.,GenerativeState::Pulse,1);
        for(int n=0;n<int(sr*.1875);++n)CHECK(clock.tick()==0.);
        CHECK(clock.stepIndex()==1);
        const double phase=clock.stepPhase();
        clock.setTempo(240.);CHECK(clock.stepIndex()==1);
        CHECK(std::abs(clock.stepPhase()-phase)<1e-12);
        clock.setTempo(std::numeric_limits<double>::quiet_NaN());
        CHECK(std::abs(clock.stepPhase()-phase)<1e-12);
        clock.setDepth(1.);CHECK(std::isfinite(clock.tick()));
        // The initial step's smoothing follows the same physical time constant.
        Motion16 slew;slew.prepare(sr,120.,GenerativeState::Pulse,1);slew.setDepth(1.);
        double last=0;const int samples=int(sr*.01);
        for(int n=0;n<samples;++n)last=slew.tick();
        CHECK(std::abs(last-(1.-std::pow(.996,48000.*samples/sr)))<1e-11);
        ModContour env;env.prepare(sr,10.,3.,50.,.45,40.);env.noteOn();
        bool sawSustain=false;
        for(int i=0;i<int(sr);++i){auto x=env.tick();CHECK(std::isfinite(x)&&x>=0.&&x<=1.);if(env.state()==ContourState::Sustain)sawSustain=true;}
        CHECK(sawSustain);env.noteOff();
        for(int i=0;i<int(sr);++i){auto x=env.tick();CHECK(std::isfinite(x)&&x>=0.&&x<=1.);}
        CHECK(env.state()==ContourState::Idle);
        env.noteOn();for(int i=0;i<int(sr*.001);++i)env.tick();
        env.noteOn();env.noteOff();for(int i=0;i<int(sr);++i)env.tick();CHECK(env.state()==ContourState::Idle);
        CoupledModes p,q;p.prepare(sr,32.76,32.79,.6,.8,.003);q.prepare(sr,32.76,32.79,.6,.8,.003);
        CHECK(p.tick()==0.);
        p.excite(.9);q.excite(.9);
        auto begin=p.energy();CHECK(begin>0.);
        for(int i=0;i<int(sr*2.);++i){auto x=p.tick(),y=q.tick();CHECK(x==y);CHECK(std::isfinite(x));CHECK(p.energy()<100.);}
        CHECK(p.energy()<begin);
        p.reset();CHECK(p.tick()==0.&&p.energy()==0.);
    }
    const double nan=std::numeric_limits<double>::quiet_NaN();
    Motion16 invalid;invalid.prepare(nan,nan,GenerativeState::Rise,1);invalid.setDepth(1.);
    ModContour invalidContour;invalidContour.prepare(nan,nan,nan,nan,nan,nan);invalidContour.noteOn();
    CoupledModes invalidModes;invalidModes.prepare(nan,nan,nan,nan,nan,nan);invalidModes.excite(1.);
    for(int n=0;n<48000;++n){CHECK(std::isfinite(invalid.tick()));CHECK(std::isfinite(invalidContour.tick()));CHECK(std::isfinite(invalidModes.tick()));}
    std::cout << "OSO V4 research primitives: deterministic modulation, contour and coupled modes PASS\n";
}

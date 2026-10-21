#include "omega/v4/ExperimentalSectors.h"
#include <cassert>
#include <cmath>
#include <cstdint>
#include <iostream>
using namespace omega::v4;

int main() {
    // MIDI/macro IDs and legacy host OSO1 state must not be changed by this R&D header.
    Motion16 a,b;
    a.prepare(48000.,120.,GenerativeState::Orbit,93021u);
    b.prepare(48000.,120.,GenerativeState::Orbit,93021u);
    for(int i=0;i<100000;++i) {assert(a.tick()==0.);assert(b.tick()==0.);}
    a.setDepth(.7);b.setDepth(.7);
    double sum=0.;
    for(int i=0;i<48000;++i){double x=a.tick(),y=b.tick();assert(x==y);assert(std::isfinite(x));assert(std::abs(x)<=.70000001);sum+=std::abs(x);}
    assert(sum>1.);
    Motion16 c;c.prepare(48000.,120.,GenerativeState::Rise,2);c.setDepth(1.);
    for(int i=0;i<160000;++i){const auto x=c.tick();assert(std::isfinite(x)&&x>=-1.000001&&x<=1.000001);}
    for (auto sr: {44100.,48000.,96000.}) {
        ModContour env;env.prepare(sr,10.,3.,50.,.45,40.);env.noteOn();
        bool sawSustain=false;
        for(int i=0;i<int(sr);++i){auto x=env.tick();assert(std::isfinite(x)&&x>=0.&&x<=1.);if(env.state()==ContourState::Sustain)sawSustain=true;}
        assert(sawSustain);env.noteOff();
        for(int i=0;i<int(sr);++i){auto x=env.tick();assert(std::isfinite(x)&&x>=0.&&x<=1.);}
        assert(env.state()==ContourState::Idle);
        env.noteOn();for(int i=0;i<int(sr*.001);++i)env.tick();
        env.noteOn();env.noteOff();for(int i=0;i<int(sr);++i)env.tick();assert(env.state()==ContourState::Idle);
        CoupledModes p,q;p.prepare(sr,32.76,32.79,.6,.8,.003);q.prepare(sr,32.76,32.79,.6,.8,.003);
        assert(p.tick()==0.);
        p.excite(.9);q.excite(.9);
        auto begin=p.energy();assert(begin>0.);
        for(int i=0;i<int(sr*2.);++i){auto x=p.tick(),y=q.tick();assert(x==y);assert(std::isfinite(x));assert(p.energy()<100.);}
        assert(p.energy()<begin);
        p.reset();assert(p.tick()==0.&&p.energy()==0.);
    }
    std::cout << "OSO V4 research primitives: deterministic modulation, contour and coupled modes PASS\n";
}

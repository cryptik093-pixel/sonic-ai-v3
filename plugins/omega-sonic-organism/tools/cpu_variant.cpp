#include "CpuVariant.h"
#include "omega/OrganismCore.h"
#ifdef OSO_BASELINE_VARIANT
CpuVariant makeBaseline(int quality) {
#else
CpuVariant makeCurrent(int quality) {
#endif
    using Engine=omega::OrganismCore;
    auto* e=new Engine;
    e->setParameter(110,quality);
    e->setParameter(101,.65);e->setParameter(102,.7);
    e->setParameter(103,.65);e->setParameter(104,.3);
    e->prepare(48000,16);
    for(int i=0;i<16;++i)e->noteOn(36+i,.65f,i);
    return {e,[](void* p){delete static_cast<Engine*>(p);},
        [](void* p,float m){static_cast<Engine*>(p)->setMorph(m);},
        [](void* p,float* l,float* r,int n){static_cast<Engine*>(p)->render(l,r,n);},
        [](void* p){return static_cast<Engine*>(p)->nonFiniteFaults();}};
}

#pragma once
#include "DspPrimitives.h"
namespace omega::dsp {
#if defined(_MSC_VER)
#define OSO_EXCITER_INLINE __forceinline
#else
#define OSO_EXCITER_INLINE inline
#endif
// The shared periodic EXCITE source. Phase/step/width are bounded by the
// instrument's voice/control path. No state, allocation or extra engine bank.
struct Exciter final {
    struct Periodic {double sine,saw,pulse,spectral;};
    static double blep(double phase,double step) noexcept {
        if(step<=0)return 0;
        if(phase<step){phase/=step;return phase+phase-phase*phase-1;}
        if(phase>1-step){phase=(phase-1)/step;return phase*phase+phase+phase+1;}return 0;
    }
    static OSO_EXCITER_INLINE Periodic periodic(double phase,double step,double width,double pulseDc,
                             const std::array<double,8>& weights,
                             const std::array<double,8>& fades,const Tables& table) noexcept {
        const double baseIndex=phase*2048;
        const auto harmonicSine=[&](int harmonic) noexcept {
            const double x=baseIndex*harmonic;const int whole=int(x),index=whole&2047;
            return table.sines[size_t(index)]+(table.sines[size_t(index+1)]-table.sines[size_t(index)])*(x-double(whole));
        };
        const double sine=harmonicSine(1),saw=2*phase-1-blep(phase,step);
        double shifted=phase-width;if(shifted<0)shifted+=1;
        const double pulse=(phase<width?1.:-1.)+blep(phase,step)-blep(shifted,step)-pulseDc;
        double spectral=weights[0]*sine*fades[0];
        for(size_t k=1;k<8;++k)spectral+=weights[k]*harmonicSine(int(k+1))*fades[k];
        return {sine,saw,pulse,spectral};
    }
};
#undef OSO_EXCITER_INLINE
}

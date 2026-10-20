#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <vector>

namespace omega::dsp {
inline constexpr double pi=3.1415926535897932384626433832795;
inline double zap(double x) noexcept { return std::abs(x)<1e-20?0.:x; }
inline bool finite(double x) noexcept {
    static_assert(sizeof(double)==sizeof(uint64_t)&&std::numeric_limits<double>::is_iec559);
    uint64_t bits=0;std::memcpy(&bits,&x,sizeof(bits));
    return (bits&UINT64_C(0x7ff0000000000000))!=UINT64_C(0x7ff0000000000000);
}
struct Tables {
    mutable uint64_t nonFiniteFaults=0;
    mutable uint32_t firstFaultSource=0;
    std::array<double,2049> sines{};
    std::array<double,4097> tanhs{};
    std::array<double,31> halfband{};
    void prepare() noexcept {
        nonFiniteFaults=0;
        firstFaultSource=0;
        for(size_t i=0;i<sines.size();++i)sines[i]=std::sin(2*pi*double(i)/2048);
        for(size_t i=0;i<tanhs.size();++i)tanhs[i]=std::tanh(8.*double(i)/4096);
        double sum=0;
        for(int i=0;i<31;++i){const int k=i-15;const double w=.42-.5*std::cos(2*pi*i/30.)+.08*std::cos(4*pi*i/30.);
            halfband[size_t(i)]=(k==0?.5:(k%2==0?0.:std::sin(.5*pi*k)/(pi*k)))*w;sum+=halfband[size_t(i)];}
        for(auto& h:halfband)h/=sum;
    }
    double sine(double phase) const noexcept {
        if(!finite(phase)){++nonFiniteFaults;if(!firstFaultSource)firstFaultSource=1;return 0;}
        // Every oscillator lookup lies in [0, 8). Integer truncation is exact
        // floor in that domain and uses a bounded integer conversion.
        // Keep the general path for callers outside the oscillator domain.
        phase-=phase>=0&&phase<8?double(int(phase)):std::floor(phase);
        const double x=phase*2048;const int i=int(x);
        return sines[i]+(sines[i+1]-sines[i])*(x-double(i));
    }
    double saturate(double x) const noexcept {
        if(!finite(x)){++nonFiniteFaults;if(!firstFaultSource)firstFaultSource=2;return 0;}
        const double a=std::abs(x);if(a>=8)return std::copysign(1.,x);
        const double p=a*512;const int i=int(p);
        return std::copysign(tanhs[i]+(tanhs[i+1]-tanhs[i])*(p-double(i)),x);
    }
};
// Symmetric half-band FIR: non-centre odd taps are exactly zero.
struct HalfBand31 {
    std::array<double,31> history{};int position=0;
    void reset() noexcept {history.fill(0);position=0;}
    double tick(double x,const std::array<double,31>& h) noexcept {
        history[size_t(position)]=x;
        auto delayed=[this](int offset) noexcept {int i=position-offset;if(i<0)i+=31;return history[size_t(i)];};
        double y=h[15]*delayed(15);
        for(int i=0;i<15;i+=2)y+=h[size_t(i)]*(delayed(i)+delayed(30-i));
        if(++position==31)position=0;return y;
    }
};
struct DriveStage {
    static constexpr int latency=15;
    // Polyphase equivalent of two 31-tap half-band filters. Odd upsampled
    // outputs contain only the centre tap; discarded downsample outputs
    // only advance state. Keep those phases without computing zero products.
    std::array<double,16> input{},even{},odd{};
    int hqPosition=0;
    std::array<double,latency> ecoDelay{};int position=0;
    void reset() noexcept {resetHQ();ecoDelay.fill(0);position=0;}
    void resetHQ() noexcept {input.fill(0);even.fill(0);odd.fill(0);hqPosition=0;}
    double tick(double x,double drive,double compensation,double hqMix,const Tables& table) noexcept {
        const double eco=ecoDelay[size_t(position)];ecoDelay[size_t(position)]=table.saturate(x*drive)*compensation;
        if(++position==latency)position=0;if(hqMix<=0)return eco;
        const auto at=[this](int delay) noexcept {return size_t((hqPosition-delay)&15);};
        input[size_t(hqPosition)]=2*x;
        double a=0;
        for(int j=0;j<8;++j)a+=table.halfband[size_t(2*j)]*(input[at(j)]+input[at(15-j)]);
        const double b=table.halfband[15]*input[at(7)];
        even[size_t(hqPosition)]=table.saturate(a*drive)*compensation;
        double hq=table.halfband[15]*odd[at(8)];
        for(int j=0;j<8;++j)hq+=table.halfband[size_t(2*j)]*(even[at(j)]+even[at(15-j)]);
        odd[size_t(hqPosition)]=table.saturate(b*drive)*compensation;
        hqPosition=(hqPosition+1)&15;
        return eco+(hq-eco)*hqMix;
    }
};
// Trapezoidal SVF bounded simultaneous form: Simper (2013), pp. 4-5.
struct LowPass {
    struct Coefficients {double a1=1,a2=0,a3=0;};double s1=0,s2=0;
    static Coefficients coefficients(double cutoff,double q,double sr) noexcept {
        const double g=std::tan(pi*std::clamp(cutoff,20.,sr*.42)/sr);
        const double a1=1/(1+g*(g+1/std::clamp(q,.5,2.)));return {a1,g*a1,g*g*a1};
    }
    double tick(double x,const Coefficients& c) noexcept {
        const double v3=x-s2,v1=c.a1*s1+c.a2*v3,v2=s2+c.a2*s1+c.a3*v3;
        s1=zap(2*v1-s1);s2=zap(2*v2-s2);return v2;
    }
};
// Four delays and an orthonormal Hadamard feedback mix. Only prepare allocates.
class Room {
public:
    void prepare(double sr) {
        constexpr double seconds[]={.0297,.0371,.0411,.0437};
        for(size_t i=0;i<4;++i){const size_t length=size_t(std::ceil(sr*seconds[i]))+1;buffers_[i].assign(length,0.);epochs_[i].assign(length,0);}reset();
    }
    void reset() noexcept {
        if(++epoch_==0){for(auto& e:epochs_)std::fill(e.begin(),e.end(),0);epoch_=1;}
        positions_.fill(0);damping_.fill(0);
    }
    std::array<double,2> tick(double left,double right,double amount) noexcept {
        if(buffers_[0].empty())return {left,right};std::array<double,4> v{};
        for(size_t i=0;i<4;++i){const double sample=epochs_[i][positions_[i]]==epoch_?buffers_[i][positions_[i]]:0;damping_[i]=zap(damping_[i]+.38*(sample-damping_[i]));v[i]=damping_[i];}
        const std::array<double,4> h{{(v[0]+v[1]+v[2]+v[3])*.5,(v[0]-v[1]+v[2]-v[3])*.5,(v[0]+v[1]-v[2]-v[3])*.5,(v[0]-v[1]-v[2]+v[3])*.5}};
        for(size_t i=0;i<4;++i){buffers_[i][positions_[i]]=zap((i%2?right:left)*amount*.22+(.65+.22*amount)*h[i]);epochs_[i][positions_[i]]=epoch_;if(++positions_[i]==buffers_[i].size())positions_[i]=0;}
        return {left+amount*(v[0]+v[2]-v[3])*.45,right+amount*(v[1]+v[3]-v[2])*.45};
    }
private:
    std::array<std::vector<double>,4> buffers_;std::array<std::vector<uint64_t>,4> epochs_;
    std::array<size_t,4> positions_{};std::array<double,4> damping_{};uint64_t epoch_=1;
};
}

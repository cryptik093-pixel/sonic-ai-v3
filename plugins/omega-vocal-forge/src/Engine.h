#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>

namespace ovf {
// Persistent catalogue v1. Never reuse these IDs for another purpose.
constexpr uint32_t inputId=100, outputId=101, bypassId=102;
inline double normalized(double n) noexcept { return std::isfinite(n)?std::clamp(n,0.,1.):.5; }
inline double db(double n) noexcept { return normalized(n)*48.-24.; }
inline double gain(double n) noexcept { return std::pow(10.,db(n)/20.); }
struct Targets { double input=.5, output=.5; bool bypass=false; };
// Independent of GUI/SDK; prepare only when stopped. Linear 10 ms ramps have
// finite duration and no block-size dependence. Bypass crossfades to unity dry.
class Ramp {
 double value=1.,target=1.,step=0.; int remaining=0,length=480;
public:
 void prepare(double rate,double initial) noexcept {length=std::max(1,int(rate*.010));value=target=initial;remaining=0;}
 void set(double next) noexcept {if(next!=target){target=next;remaining=length;step=(target-value)/length;}}
 double tick() noexcept {if(remaining>0){value+=step;if(--remaining==0)value=target;}return value;}
};
class Engine {
 Ramp in,out,wet;
public:
 void prepare(double rate,Targets t={}) noexcept {in.prepare(rate,gain(t.input));out.prepare(rate,gain(t.output));wet.prepare(rate,t.bypass?0.:1.);}
 void set(Targets t) noexcept {in.set(gain(t.input));out.set(gain(t.output));wet.set(t.bypass?0.:1.);}
 void sample(float l,float r,float& a,float& b) noexcept {
  const double g=in.tick()*out.tick(), w=wet.tick(), factor=1.+w*(g-1.);
  auto safe=[factor](float x){const double y=std::isfinite(x)?double(x)*factor:0.;return float(std::clamp(y,-double(3.402823466e38F),double(3.402823466e38F)));};
  a=safe(l);b=safe(r);
 }
};
}

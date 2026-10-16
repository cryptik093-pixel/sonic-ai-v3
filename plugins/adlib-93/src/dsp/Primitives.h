#pragma once
#include "core/Parameters.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
namespace adlib93 {
constexpr double pi=3.14159265358979323846;
inline double dbToGain(double db) noexcept { return std::pow(10.0,db/20.0); }
inline float effectiveCutoff(float hz,double rate) noexcept { return static_cast<float>(std::min(static_cast<double>(hz),rate*.45)); }
inline double timeConstantCoefficient(float ms,double rate) noexcept { return std::exp(-1.0/(.001*static_cast<double>(ms)*rate)); }
inline float cleanSample(float x) noexcept { return std::isfinite(x)?x:0.0f; }
class Smooth {
public:
    void prepare(double rate,float ms,double initial=0) noexcept { coefficient=timeConstantCoefficient(ms,rate);value=target=initial; }
    void reset(double v) noexcept { value=target=v; }
    void setTarget(double v) noexcept { target=v; }
    double next() noexcept { value=target+coefficient*(value-target);if(std::abs(value-target)<1e-12) value=target;return value; }
    double current() const noexcept { return value; }
private: double coefficient=0,value=0,target=0;
};
class LinearRamp {
public:
    void reset(double initial) noexcept { value=target=initial;remaining=0;step=0; }
    void setTarget(double v,uint32_t samples) noexcept { if(v==target) return;target=v;remaining=std::max(1u,samples);step=(target-value)/remaining; }
    double next() noexcept { if(remaining>0 && --remaining==0) value=target;else if(remaining>0) value+=step;return value; }
    double current() const noexcept { return value; }
    bool settled() const noexcept { return remaining==0; }
private: double value=0,target=0,step=0;uint32_t remaining=0;
};
}

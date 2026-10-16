#pragma once
#include "Primitives.h"
#include "core/Types.h"
namespace adlib93 {
struct OutputMeasurements { float outputPeak=0,limiterReductionDb=0;uint64_t diagnostics=0; };
class OutputStage {
public:
    void prepare(const PrepareSpec& spec) noexcept { rate=spec.sampleRate;gain.prepare(rate,20,1);reset(); }
    void reset() noexcept { limiterGain=1;reading={};gain.reset(dbToGain(parameters[Param::OutputGain])); }
    void setParameters(const ParameterSnapshot& value) noexcept {
        parameters=sanitizeSnapshot(value,rate);gain.setTarget(dbToGain(parameters[Param::OutputGain]));
        ceiling=dbToGain(parameters[Param::LimiterCeiling]);release=timeConstantCoefficient(parameters[Param::LimiterRelease],rate);
    }
    StereoFrame process(StereoFrame input) noexcept {
        if(!std::isfinite(input.left)) { input.left=0;++reading.diagnostics; }
        if(!std::isfinite(input.right)) { input.right=0;++reading.diagnostics; }
        const double g=gain.next();
        double left=static_cast<double>(input.left)*g,right=static_cast<double>(input.right)*g;
        if(parameters[Param::LimiterEnabled]>.5f) {
            const double peak=std::max(std::abs(left),std::abs(right));
            const double required=peak>0?std::min(1.0,ceiling/peak):1.0;
            limiterGain=std::min(required,1.0+release*(limiterGain-1.0));
            left*=limiterGain;right*=limiterGain;
            reading.limiterReductionDb=static_cast<float>(-20.0*std::log10(std::max(limiterGain,1e-100)));
        } else { limiterGain=1;reading.limiterReductionDb=0; }
        const double maximum=std::numeric_limits<float>::max();
        if(std::abs(left)>maximum || std::abs(right)>maximum) ++reading.diagnostics;
        left=std::clamp(left,-maximum,maximum);right=std::clamp(right,-maximum,maximum);
        reading.outputPeak=static_cast<float>(std::max(std::abs(left),std::abs(right)));
        return {static_cast<float>(left),static_cast<float>(right)};
    }
    OutputMeasurements meters() const noexcept { return reading; }
private:
    ParameterSnapshot parameters=makeInitSnapshot();Smooth gain;double rate=48000,limiterGain=1,ceiling=.891250938,release=.9998;OutputMeasurements reading;
};
}

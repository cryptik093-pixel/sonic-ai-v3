#pragma once
#include "../core/Parameters.h"
#include "../core/Types.h"
#include <array>
namespace adlib93 {
class Character {
public:
 void prepare(const PrepareSpec&); void reset() noexcept;
 void setParameters(const ParameterSnapshot&) noexcept;
 StereoFrame process(StereoFrame) noexcept;
private:
 struct Biquad { double b0{1},b1{},b2{},a1{},a2{},z1{},z2{}; double run(double) noexcept; void coefficients(double,double,bool) noexcept; };
 ParameterSnapshot parameters_{makeInitSnapshot()}; double rate_{48000},hp_{20},lp_{20000},drive_{},trim_{},wet_{},hpWet_{},lpWet_{},smoothCoefficient_{},dcCoefficient_{};
 std::array<double,4> weights_{{1,0,0,0}};
 std::array<Biquad,2> hpFilters_{},lpFilters_{};
 std::array<std::array<double,2>,3> dcIn_{},dcOut_{};
 unsigned coefficientCounter_{};
};
}

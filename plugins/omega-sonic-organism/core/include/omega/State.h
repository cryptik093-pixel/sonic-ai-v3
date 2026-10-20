#pragma once
#include "Parameters.h"
#include <algorithm>
#include <cstring>

namespace omega {
using ParameterValues = std::array<double, 15>;
inline ParameterValues defaults() noexcept {
    ParameterValues p{};
    for (size_t i=0;i<p.size();++i) p[i]=parameterDefinitions[i].initial;
    return p;
}
// OSO1, schema, count, payload length, IEEE754 little-endian values, FNV1a.
inline constexpr size_t stateSize = 140;
using StateBytes = std::array<uint8_t,stateSize>;
inline void put32(uint8_t* p,uint32_t n) noexcept { for(int i=0;i<4;++i) p[i]=static_cast<uint8_t>(n>>(i*8)); }
inline uint32_t get32(const uint8_t* p) noexcept { uint32_t n=0; for(int i=0;i<4;++i)n|=uint32_t(p[i])<<(i*8); return n; }
inline uint32_t checksum(const uint8_t* p,size_t n) noexcept { uint32_t h=2166136261u;for(size_t i=0;i<n;++i)h=(h^p[i])*16777619u;return h; }
inline StateBytes encodeState(const ParameterValues& values) noexcept {
    StateBytes b{}; std::memcpy(b.data(),"OSO1",4);put32(b.data()+4,1);put32(b.data()+8,15);put32(b.data()+12,120);
    for(size_t i=0;i<15;++i){uint64_t bits;std::memcpy(&bits,&values[i],8);for(int j=0;j<8;++j)b[16+i*8+j]=static_cast<uint8_t>(bits>>(8*j));}
    put32(b.data()+136,checksum(b.data(),136));return b;
}
inline bool decodeState(const uint8_t* b,size_t size,ParameterValues& result) noexcept {
    if(!b||size<20||std::memcmp(b,"OSO1",4)||get32(b+4)!=1)return false;
    const auto count=get32(b+8);if(count<6||count>15||get32(b+12)!=count*8||size!=20+count*8)return false;
    if(get32(b+size-4)!=checksum(b,size-4))return false;
    auto candidate=defaults();
    for(size_t i=0;i<count;++i){uint64_t bits=0;for(int j=0;j<8;++j)bits|=uint64_t(b[16+i*8+j])<<(8*j);double v;std::memcpy(&v,&bits,8);
        if(!std::isfinite(v)||v<0||v>1)return false;
        if(parameterDefinitions[i].steps && std::abs(v*parameterDefinitions[i].steps-std::round(v*parameterDefinitions[i].steps))>1e-9)return false;
        candidate[i]=v;
    }
    result=candidate;return true;
}
}

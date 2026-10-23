#pragma once
#include "Parameters.h"
#include <algorithm>
#include <cstring>

namespace omega {
using ParameterValues = std::array<double, 18>;
inline ParameterValues defaults() noexcept {
    ParameterValues p{};
    for (size_t i=0;i<p.size();++i) p[i]=parameterDefinitions[i].initial;
    return p;
}
// OSO1, schema, count, payload length, IEEE754 little-endian values, FNV1a.
inline constexpr size_t stateSize = 140;
// Fixed capacity, variable encoded length: legacy values retain exact OSO1 bytes.
struct StateBytes {
    std::array<uint8_t,164> storage{};
    size_t length=stateSize;
    uint8_t* data() noexcept {return storage.data();}
    const uint8_t* data() const noexcept {return storage.data();}
    size_t size() const noexcept {return length;}
    uint8_t& operator[](size_t i) noexcept {return storage[i];}
    const uint8_t& operator[](size_t i) const noexcept {return storage[i];}
};
inline void put32(uint8_t* p,uint32_t n) noexcept { for(int i=0;i<4;++i) p[i]=static_cast<uint8_t>(n>>(i*8)); }
inline uint32_t get32(const uint8_t* p) noexcept { uint32_t n=0; for(int i=0;i<4;++i)n|=uint32_t(p[i])<<(i*8); return n; }
inline uint32_t checksum(const uint8_t* p,size_t n) noexcept { uint32_t h=2166136261u;for(size_t i=0;i<n;++i)h=(h^p[i])*16777619u;return h; }
inline StateBytes encodeState(const ParameterValues& values) noexcept {
    const bool extended=values[15]!=0||values[16]!=0||values[17]!=0;
    const size_t count=extended?18:15;
    StateBytes b{};b.length=20+count*8;
    std::memcpy(b.data(),extended?"OSO2":"OSO1",4);put32(b.data()+4,extended?2:1);
    put32(b.data()+8,uint32_t(count));put32(b.data()+12,uint32_t(count*8));
    for(size_t i=0;i<count;++i){uint64_t bits;std::memcpy(&bits,&values[i],8);for(int j=0;j<8;++j)b[16+i*8+j]=static_cast<uint8_t>(bits>>(8*j));}
    put32(b.data()+b.size()-4,checksum(b.data(),b.size()-4));return b;
}
inline bool decodeState(const uint8_t* b,size_t size,ParameterValues& result) noexcept {
    if(!b||size<20)return false;
    const bool legacy=std::memcmp(b,"OSO1",4)==0&&get32(b+4)==1;
    const bool extended=std::memcmp(b,"OSO2",4)==0&&get32(b+4)==2;
    const auto count=get32(b+8);
    if(!(legacy&&count>=6&&count<=15)&&!(extended&&count==18))return false;
    if(get32(b+12)!=count*8||size!=20+count*8)return false;
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

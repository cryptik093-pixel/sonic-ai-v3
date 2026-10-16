#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <vector>
namespace adlib93::tools {
struct WaveFile { uint32_t sampleRate=48000; uint16_t channels=2; std::vector<float> samples; };
inline uint16_t u16(const uint8_t* p) { return uint16_t(p[0]|uint16_t(p[1])<<8); }
inline uint32_t u32(const uint8_t* p) { return uint32_t(p[0])|uint32_t(p[1])<<8|uint32_t(p[2])<<16|uint32_t(p[3])<<24; }
// File parsing is a command-line operation, never called by DSP.
inline WaveFile readWave(const std::filesystem::path& file) {
    std::ifstream stream(file,std::ios::binary|std::ios::ate);
    if(!stream) throw std::runtime_error("Cannot open input WAV");
    auto length=stream.tellg();
    if(length<44 || length>512*1024*1024) throw std::runtime_error("WAV size outside 44 bytes..512 MiB");
    std::vector<uint8_t> bytes(static_cast<size_t>(length));stream.seekg(0);
    if(!stream.read(reinterpret_cast<char*>(bytes.data()),length)) throw std::runtime_error("Short WAV read");
    if(std::memcmp(bytes.data(),"RIFF",4)||std::memcmp(bytes.data()+8,"WAVE",4)||uint64_t(u32(bytes.data()+4))+8>bytes.size())
        throw std::runtime_error("Expected bounded little-endian RIFF WAVE");
    uint16_t format=0,bits=0,align=0;uint32_t byteRate=0;WaveFile result;
    size_t dataOffset=0,dataSize=0;const size_t end=size_t(u32(bytes.data()+4))+8;
    for(size_t cursor=12;cursor+8<=end;) {
        const auto size=u32(bytes.data()+cursor+4);const auto next=uint64_t(cursor)+8+size;
        if(next>end) throw std::runtime_error("WAV chunk exceeds RIFF size");
        auto p=bytes.data()+cursor+8;
        if(!std::memcmp(bytes.data()+cursor,"fmt ",4)) {
            if(size<16) throw std::runtime_error("Short WAV format");
            format=u16(p);result.channels=u16(p+2);result.sampleRate=u32(p+4);byteRate=u32(p+8);align=u16(p+12);bits=u16(p+14);
        } else if(!std::memcmp(bytes.data()+cursor,"data",4)) {dataOffset=cursor+8;dataSize=size;}
        cursor=static_cast<size_t>(next+(size&1));
    }
    if((format!=1&&format!=3)||(result.channels!=1&&result.channels!=2)||result.sampleRate<8000||result.sampleRate>192000||
       (format==3?bits!=32:(bits!=8&&bits!=16&&bits!=24&&bits!=32))||align!=result.channels*(bits/8)||byteRate!=result.sampleRate*align||!dataOffset||dataSize%align)
        throw std::runtime_error("Supported WAV: mono/stereo PCM 8/16/24/32 or float32, 8..192 kHz; no extensible format");
    result.samples.resize(dataSize/(bits/8));
    for(size_t i=0;i<result.samples.size();++i) {
        const auto p=bytes.data()+dataOffset+i*(bits/8);float value=0;
        if(format==3) {uint32_t word=u32(p);std::memcpy(&value,&word,4);}
        else if(bits==8) value=(int(p[0])-128)/128.f;
        else if(bits==16) value=static_cast<int16_t>(u16(p))/32768.f;
        else if(bits==24) {int32_t word=int32_t(uint32_t(p[0])|uint32_t(p[1])<<8|uint32_t(p[2])<<16);if(word&0x800000)word-=0x1000000;value=word/8388608.f;}
        else value=static_cast<int32_t>(u32(p))/2147483648.f;
        result.samples[i]=std::isfinite(value)?value:0;
    }
    return result;
}
inline void writeWave(const std::filesystem::path& file,const WaveFile& value) {
    if(std::filesystem::exists(file)) throw std::runtime_error("Output already exists; preserving it");
    if((value.channels!=1&&value.channels!=2)||!value.sampleRate||value.samples.size()%value.channels||value.samples.size()>(UINT32_MAX-36)/4)
        throw std::runtime_error("Invalid output WAV dimensions");
    std::ofstream stream(file,std::ios::binary);if(!stream)throw std::runtime_error("Cannot create output WAV");
    auto word=[&](uint32_t n,int count){for(int i=0;i<count;++i)stream.put(static_cast<char>((n>>(i*8))&255));};
    auto size=static_cast<uint32_t>(value.samples.size()*4);
    stream.write("RIFF",4);word(36+size,4);stream.write("WAVEfmt ",8);word(16,4);word(3,2);word(value.channels,2);
    word(value.sampleRate,4);word(value.sampleRate*value.channels*4,4);word(value.channels*4,2);word(32,2);stream.write("data",4);word(size,4);
    for(float sample:value.samples){if(!std::isfinite(sample))throw std::runtime_error("Non-finite render output");uint32_t n;std::memcpy(&n,&sample,4);word(n,4);}
    if(!stream)throw std::runtime_error("Output WAV write failed");
}
}

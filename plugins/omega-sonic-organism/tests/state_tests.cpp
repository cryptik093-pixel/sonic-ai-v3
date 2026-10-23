#include "omega/State.h"
#include <iostream>
#include <limits>
#include <cstdlib>
#define CHECK(c) do {if(!(c)){std::cerr<<"FAIL line "<<__LINE__<<": "<<#c<<'\n';std::exit(1);}}while(false)
int main(){
    auto p=omega::defaults();p[0]=.723;p[5]=.88;
    auto b=omega::encodeState(p);auto out=omega::defaults();
    CHECK(omega::decodeState(b.data(),b.size(),out));CHECK(out==p);
    for(size_t n=0;n<b.size();++n){auto before=out;CHECK(!omega::decodeState(b.data(),n,out));CHECK(out==before);}
    for(size_t n=0;n<b.size();++n){auto broken=b;broken[n]^=0x80;CHECK(!omega::decodeState(broken.data(),broken.size(),out));CHECK(out==p);}
    p[0]=std::numeric_limits<double>::quiet_NaN();auto invalid=omega::encodeState(p);CHECK(!omega::decodeState(invalid.data(),invalid.size(),out));
    p=omega::defaults();p[9]=.5;invalid=omega::encodeState(p);CHECK(!omega::decodeState(invalid.data(),invalid.size(),out));
    // Earlier schema-1 document: six principal values, new fields defaulted.
    b=omega::encodeState(omega::defaults());omega::put32(b.data()+8,6);omega::put32(b.data()+12,48);omega::put32(b.data()+64,omega::checksum(b.data(),64));
    CHECK(omega::decodeState(b.data(),68,out));CHECK(out==omega::defaults());
    // Additive controls use OSO2. Default V4 controls still emit original OSO1.
    p=omega::defaults();b=omega::encodeState(p);CHECK(b.size()==140);CHECK(std::memcmp(b.data(),"OSO1",4)==0);
    p[15]=.75;p[16]=2./3;p[17]=.82;b=omega::encodeState(p);
    CHECK(b.size()==164);CHECK(std::memcmp(b.data(),"OSO2",4)==0);
    CHECK(omega::decodeState(b.data(),b.size(),out));CHECK(out==p);
    for(size_t n=0;n<b.size();++n){auto before=out;CHECK(!omega::decodeState(b.data(),n,out));CHECK(out==before);}
    for(size_t n=0;n<b.size();++n){auto broken=b;broken[n]^=0x80;CHECK(!omega::decodeState(broken.data(),broken.size(),out));CHECK(out==p);}
    auto legacy=omega::encodeState(omega::defaults());CHECK(omega::decodeState(legacy.data(),legacy.size(),out));CHECK(out[15]==0&&out[16]==0&&out[17]==0);
    CHECK(std::abs(omega::physical(omega::parameterDefinitions[5],.6)+6)<1e-12);
    CHECK(std::abs(omega::physical(omega::parameterDefinitions[6],.5)-1)<1e-12);
    std::cout<<"State round-trip, every truncated length, checksum corruption, NaN, discrete validation and migration passed.\n";
}

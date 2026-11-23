#include "Engine.h"
#include <iostream>
#include <limits>
#include <cstdlib>
void check(bool b,const char* msg){if(!b){std::cerr<<"FAIL "<<msg<<'\n';std::exit(1);}}
int main(){
 for(double rate:{44100.,48000.,96000.})for(int block:{1,64,128,512,1031}){
  ovf::Engine e;e.prepare(rate);float l,r;
  for(int s=0;s<block;++s){e.sample(.125f,-.25f,l,r);check(l==.125f&&r==-.25f,"unity passthrough");}
  e.set({.75,.5,false});for(int s=0;s<int(rate*.02);++s)e.sample(.125f,-.25f,l,r);
  check(std::abs(l-.125f*ovf::gain(.75))<1e-6,"input gain +12dB");
  e.set({.5,.25,false});for(int s=0;s<int(rate*.02);++s)e.sample(.125f,-.25f,l,r);
  check(std::abs(l-.125f*ovf::gain(.25))<1e-6,"output gain -12dB");
  float previous=l,maxStep=0;e.set({.5,.25,true});for(int s=0;s<int(rate*.02);++s){e.sample(.125f,-.25f,l,r);maxStep=std::max(maxStep,std::abs(l-previous));previous=l;}
  check(l==.125f&&r==-.25f,"unity bypass");check(maxStep<.0003f,"bounded bypass step");
  e.sample(std::numeric_limits<float>::quiet_NaN(),std::numeric_limits<float>::infinity(),l,r);check(l==0&&r==0,"nonfinite sanitation");
  e.prepare(rate,{1,1,false});e.sample(std::numeric_limits<float>::max(),-std::numeric_limits<float>::max(),l,r);check(std::isfinite(l)&&std::isfinite(r),"finite extreme output");
  e.sample(0,0,l,r);check(l==0&&r==0,"silence");
 }
 // Partition independence: callback boundaries cannot restart smoothing.
 ovf::Engine a,b;a.prepare(48000);b.prepare(48000);a.set({1,.25,true});b.set({1,.25,true});float al,ar,bl,br;
 for(int n=0;n<4096;++n){a.sample(.2f,-.3f,al,ar);if(n%37==0)b.set({1,.25,true});b.sample(.2f,-.3f,bl,br);check(al==bl&&ar==br,"partition independent ramps");}
 std::cout<<"PASS 3 rates x 5 blocks; unity/gains/bypass/silence/extremes/partition\n";
}

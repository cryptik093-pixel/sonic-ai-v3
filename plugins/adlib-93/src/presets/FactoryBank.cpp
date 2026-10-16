#include "FactoryBank.h"
namespace adlib93 {
namespace {
using P=Param;
ParameterSnapshot recipe(unsigned i){auto s=makeInitSnapshot();s[P::DeessEnabled]=1;s[P::DeessMaxReduction]=4;
 auto level=[&](P p,float db){s[p]=levelFromDb(db);};
 auto echo=[&](float ms,float feedback,float db){s[P::DelayEnabled]=1;s[P::DelayTime]=ms;s[P::DelayFeedback]=feedback;level(P::DelayLevel,db);};
 auto synced=[&](int division,float feedback,float db){echo(250,feedback,db);s[P::DelaySync]=1;s[P::DelayDivision]=float(division);};
 auto space=[&](float decay,float db){s[P::ReverbEnabled]=1;s[P::ReverbDecay]=decay;level(P::ReverbLevel,db);};
 auto duck=[&](float depth){s[P::DuckEnabled]=1;s[P::DuckMaxReduction]=depth;};
 auto filters=[&](float hp,float lp){s[P::CharacterEnabled]=1;s[P::CharacterHpEnabled]=1;s[P::CharacterHp]=hp;if(lp>0){s[P::CharacterLpEnabled]=1;s[P::CharacterLp]=lp;}};
 auto drive=[&](int mode,float amount,float trim){s[P::CharacterEnabled]=1;s[P::CharacterMode]=float(mode);s[P::CharacterDrive]=amount;s[P::CharacterTrim]=trim;};
 auto doubler=[&](float left,float right,float db){s[P::DoubleEnabled]=1;s[P::DoubleDelayL]=left;s[P::DoubleDelayR]=right;level(P::DoubleLevel,db);};
 auto chorus=[&](float delay,float depth,float rate,float db){s[P::ChorusEnabled]=1;s[P::ChorusDelay]=delay;s[P::ChorusDepth]=depth;s[P::ChorusRate]=rate;level(P::ChorusLevel,db);};
 switch(i){
 case 0:doubler(14,22,-12);s[P::StereoWidth]=.7f;break;
 case 1:echo(90,.08f,-12);s[P::DelayLp]=6000;break;
 case 2:synced(1,.18f,-10);duck(6);break;
 case 3:filters(120,9000);drive(1,6,-4);s[P::MixAmount]=.65f;break;
 case 4:synced(2,.30f,-10);s[P::DelayPingpong]=1;break;
 case 5:synced(3,.38f,-12);s[P::DelayPingpong]=.75f;duck(8);break;
 case 6:synced(2,.35f,-9);s[P::DelayModifier]=1;s[P::DelayPingpong]=1;break;
 case 7:chorus(18,4,.22f,-9);synced(2,.2f,-18);break;
 case 8:level(P::DirectLevel,-6);space(1.8f,-8);s[P::ReverbPredelay]=12;filters(180,0);s[P::MixAmount]=.85f;break;
 case 9:synced(2,.35f,-14);s[P::DelayDiffusion]=.75f;space(3.5f,-12);break;
 case 10:synced(3,.55f,-12);space(6,-14);duck(10);break;
 case 11:level(P::DirectLevel,-6);space(8,-8);echo(250,0,-18);s[P::DelayDiffusion]=.85f;level(P::ReverbDelaySend,-6);break;
 case 12:filters(450,3200);drive(1,4,-3);break;
 case 13:filters(250,4500);drive(3,10,-7);echo(70,.05f,-16);s[P::MixAmount]=.9f;break;
 case 14:filters(100,6500);drive(1,7,-5);chorus(12,.6f,.35f,-6);s[P::MixAmount]=.85f;break;
 case 15:filters(350,3800);drive(2,16,-12);s[P::MixAmount]=.7f;break;
 case 16:doubler(19,31,-9);chorus(15,3,.8f,-12);break;
 case 17:doubler(11,34,-8);s[P::DoubleRateL]=.27f;s[P::DoubleRateR]=.41f;s[P::DoubleDepthL]=.8f;s[P::DoubleDepthR]=1.3f;break;
 case 18:chorus(20,4,.08f,-6);space(2,-18);break;
 case 19:echo(12,.65f,-12);s[P::DelayHp]=500;s[P::MixAmount]=.8f;break;
 case 20:filters(200,5000);echo(160,.42f,-12);space(4,-10);break;
 case 21:drive(3,12,-8);s[P::DirectLevel]=0;synced(2,.4f,-6);s[P::MixAmount]=.45f;break;
 case 22:space(9,-6);s[P::ReverbPredelay]=45;duck(12);s[P::DuckRelease]=450;break;
 case 23:synced(3,.78f,-14);s[P::DelayDiffusion]=.6f;space(5,-16);duck(10);break;
 default:break;
 }return persistentSnapshot(s);
}
const std::array<FactoryPreset,24> bank{{
 {"01","Pocket Double","Tight",recipe(0)},{"02","Short Slap","Tight",recipe(1)},{"03","Tight Answer","Tight",recipe(2)},{"04","Dry Bite","Tight",recipe(3)},
 {"05","Left\xe2\x80\x93Right Reply","Moving",recipe(4)},{"06","Quarter Bounce","Moving",recipe(5)},{"07","Dotted Throw","Moving",recipe(6)},{"08","Stereo Orbit","Moving",recipe(7)},
 {"09","Ghost Room","Atmospheric",recipe(8)},{"10","Diffused Halo","Atmospheric",recipe(9)},{"11","Long Goodbye","Atmospheric",recipe(10)},{"12","Frozen Tail","Atmospheric",recipe(11)},
 {"13","Phone Booth","Textured",recipe(12)},{"14","Radio Bite","Textured",recipe(13)},{"15","Worn Tape","Textured",recipe(14)},{"16","Broken Speaker","Textured",recipe(15)},
 {"17","Chorus Crowd","Modulated",recipe(16)},{"18","Uneven Double","Modulated",recipe(17)},{"19","Slow Drift","Modulated",recipe(18)},{"20","Metallic Reply","Modulated",recipe(19)},
 {"21","Tunnel Call","Dramatic",recipe(20)},{"22","Distorted Echo","Dramatic",recipe(21)},{"23","Ducked Cathedral","Dramatic",recipe(22)},{"24","Feedback Bloom","Dramatic",recipe(23)}
}};
}
const std::array<FactoryPreset,24>& factoryPresets() noexcept{return bank;}
ParameterSnapshot loadFactory(uint32_t index,const ParameterSnapshot& current,CalibrationLocks locks) noexcept {return applyCalibrationLocks(index<bank.size()?bank[index].parameters:makeInitSnapshot(),current,locks);}
}

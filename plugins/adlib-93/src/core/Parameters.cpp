#include "Parameters.h"
#include <algorithm>
#include <cmath>
#include <limits>
namespace adlib93 {
namespace {
using K=ParameterKind;
const std::array<Definition,parameterCount> definitions{{
 {"input.gain","Input","dB",-24,24,0,K::continuous},
 {"gate.enabled","Gate","",0,1,0,K::boolean},{"gate.threshold","Gate threshold","dBFS",-80,-12,-50,K::continuous},{"gate.attenuation","Gate attenuation","dB",0,80,30,K::continuous},{"gate.attack","Gate attack","ms",.5f,20,2,K::continuous},{"gate.hold","Gate hold","ms",0,250,50,K::continuous},{"gate.release","Gate release","ms",20,500,120,K::continuous},
 {"deess.enabled","De-esser","",0,1,0,K::boolean},{"deess.frequency","De-ess frequency","Hz",3000,12000,6000,K::continuous,true},{"deess.threshold","De-ess threshold","dBFS",-60,0,-24,K::continuous},{"deess.maxReduction","De-ess","dB",0,12,6,K::continuous},{"deess.listen","Listen","",0,1,0,K::boolean,false,true},
 {"character.enabled","Character","",0,1,0,K::boolean},{"character.mode","Character mode","",0,3,0,K::choice},{"character.hpEnabled","High-pass enabled","",0,1,0,K::boolean},{"character.hp","High-pass","Hz",20,1000,20,K::continuous,true},{"character.lpEnabled","Low-pass enabled","",0,1,0,K::boolean},{"character.lp","Low-pass","Hz",1000,20000,20000,K::continuous,true},{"character.drive","Drive","dB",0,24,0,K::continuous},{"character.trim","Character trim","dB",-24,12,0,K::continuous},
 {"direct.level","Direct","dB",0,1,1,K::level},{"double.enabled","Double","",0,1,0,K::boolean},{"double.delayL","Double left","ms",8,40,14,K::continuous},{"double.delayR","Double right","ms",8,40,22,K::continuous},{"double.depthL","Double depth left","ms",0,6,.4f,K::continuous},{"double.depthR","Double depth right","ms",0,6,.4f,K::continuous},{"double.rateL","Double rate left","Hz",.05f,2,.3f,K::continuous},{"double.rateR","Double rate right","Hz",.05f,2,.3f,K::continuous},{"double.level","Double level","dB",0,1,0,K::level},
 {"chorus.enabled","Chorus","",0,1,0,K::boolean},{"chorus.delay","Chorus delay","ms",5,25,15,K::continuous},{"chorus.depth","Chorus depth","ms",0,5,3,K::continuous},{"chorus.rate","Chorus rate","Hz",.05f,5,.8f,K::continuous},{"chorus.level","Chorus level","dB",0,1,0,K::level},{"stereo.pan","Pan","fraction",-1,1,0,K::continuous},{"stereo.width","Width","fraction",0,1,1,K::continuous},
 {"delay.enabled","Echo","",0,1,0,K::boolean},{"delay.sync","Tempo sync","",0,1,0,K::boolean},{"delay.time","Echo time","ms",10,4000,250,K::continuous},{"delay.division","Division","",0,5,2,K::choice},{"delay.modifier","Modifier","",0,2,0,K::choice},{"delay.manualBpm","Manual tempo","BPM",30,300,120,K::continuous},{"delay.feedback","Feedback","fraction",0,.9f,0,K::continuous},{"delay.pingpong","Ping-pong","fraction",0,1,0,K::continuous},{"delay.hp","Echo high-pass","Hz",20,1000,100,K::continuous,true},{"delay.lp","Echo low-pass","Hz",1000,20000,8000,K::continuous,true},{"delay.diffusion","Diffuse","fraction",0,1,0,K::continuous},{"delay.level","Echo level","dB",0,1,0,K::level},{"delay.throwMode","Throw mode","",0,1,0,K::choice},
 {"throw.active","Throw","",0,1,0,K::boolean,false,true},{"throw.latch","Throw latch","",0,1,0,K::boolean},{"reverb.enabled","Space","",0,1,0,K::boolean},{"reverb.predelay","Predelay","ms",0,150,20,K::continuous},{"reverb.decay","Target decay","s",.2f,12,2,K::continuous},{"reverb.damping","Damping","Hz",1000,20000,6000,K::continuous,true},{"reverb.level","Space level","dB",0,1,0,K::level},{"reverb.delaySend","Echo to space","dB",0,1,0,K::level},
 {"duck.enabled","Ducking","",0,1,0,K::boolean},{"duck.threshold","Duck threshold","dBFS",-60,0,-30,K::continuous},{"duck.maxReduction","Duck","dB",0,18,6,K::continuous},{"duck.attack","Duck attack","ms",1,50,5,K::continuous},{"duck.release","Duck release","ms",50,1000,250,K::continuous},{"freeze.active","Freeze","",0,1,0,K::boolean,false,true},{"mix.amount","Mix","fraction",0,1,1,K::continuous},{"routing.mode","Routing","",0,1,0,K::choice},{"bypass.internal","Bypass","",0,1,0,K::boolean,false,true},{"output.gain","Output","dB",-24,12,0,K::continuous},{"limiter.enabled","Limiter","",0,1,1,K::boolean},{"limiter.ceiling","Ceiling","dBFS",-12,-.1f,-1,K::continuous},{"limiter.release","Limiter release","ms",20,500,100,K::continuous}
}};
}
const std::array<Definition,parameterCount>& parameterDefinitions() noexcept { return definitions; }
const Definition& parameterDefinition(Param p) noexcept { return definitions[static_cast<std::size_t>(p)]; }
ParameterSnapshot makeInitSnapshot() noexcept { ParameterSnapshot s; for(std::size_t i=0;i<parameterCount;++i)s.values[i]=definitions[i].initial;return s; }
ParameterSnapshot sanitizeSnapshot(ParameterSnapshot s,double sampleRate) noexcept {
 if(!std::isfinite(sampleRate)||sampleRate<=0)sampleRate=48000;
 for(std::size_t i=0;i<parameterCount;++i){const auto& d=definitions[i];auto& v=s.values[i];if(!std::isfinite(v))v=d.initial;v=std::clamp(v,d.min,d.max);if(d.kind==K::boolean||d.kind==K::choice)v=std::round(v);}
 return s; // Stored values retain requested cutoffs; DSP clamps effective cutoff at 0.45 Fs.
}
ParameterSnapshot persistentSnapshot(ParameterSnapshot s) noexcept { s=sanitizeSnapshot(s);for(std::size_t i=0;i<parameterCount;++i)if(definitions[i].transient)s.values[i]=0;return s; }
ParameterSnapshot applyCalibrationLocks(ParameterSnapshot s,const ParameterSnapshot& current,CalibrationLocks locks) noexcept {
 if(locks.input)s[Param::InputGain]=current[Param::InputGain];if(locks.output)s[Param::OutputGain]=current[Param::OutputGain];
 if(locks.gate)for(auto i=static_cast<std::size_t>(Param::GateEnabled);i<=static_cast<std::size_t>(Param::GateRelease);++i)s.values[i]=current.values[i];return persistentSnapshot(s);
}
float levelToDb(float v) noexcept { if(!std::isfinite(v)||v<=0)return -std::numeric_limits<float>::infinity();return -60+60*std::clamp(v,0.f,1.f); }
float levelToGain(float v) noexcept { return v>0&&std::isfinite(v)?std::pow(10.f,levelToDb(v)/20):0; }
float levelFromDb(float db) noexcept {
 // Zero is reserved for mute. A normal positive epsilon represents the -60 dB
 // endpoint under the existing positive-value law, without relying on denormals.
 return std::isfinite(db)?std::max(std::numeric_limits<float>::epsilon(),std::clamp((db+60)/60,0.f,1.f)):0;
}
float parameterToNormalized(Param p,float v) noexcept { const auto&d=parameterDefinition(p);if(!std::isfinite(v))v=d.initial;v=std::clamp(v,d.min,d.max);return d.logarithmic?std::log(v/d.min)/std::log(d.max/d.min):(v-d.min)/(d.max-d.min); }
float parameterFromNormalized(Param p,float v) noexcept { const auto&d=parameterDefinition(p);if(!std::isfinite(v))v=0;v=std::clamp(v,0.f,1.f);float result=d.logarithmic?d.min*std::pow(d.max/d.min,v):d.min+(d.max-d.min)*v;return d.kind==K::boolean||d.kind==K::choice?std::round(result):result; }
}

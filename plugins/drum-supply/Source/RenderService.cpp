#include "RenderService.h"
#include <juce_audio_basics/juce_audio_basics.h>
#include <stdexcept>
namespace {void demand(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}}
juce::String RenderService::safeName(const juce::String& text){auto name=text.replaceCharacter(' ','_').retainCharacters("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-").substring(0,60);return name.isEmpty()?"CustomKit":name;}
RenderService::Result RenderService::oneShot(const Settings& requested,const std::array<const ohsample::Sample*,8>& samples,int slot,const juce::File& destination,const std::atomic<bool>& cancel,bool overwrite){
 juce::ScopedNoDenormals noDenormals;
 demand(slot>=0&&slot<8,"Invalid export department.");demand(std::isfinite(requested.rate)&&std::floor(requested.rate)==requested.rate&&requested.rate>=8000&&requested.rate<=192000,"Invalid export sample rate.");
 demand(overwrite||!destination.exists(),"Export destination already exists.");demand(destination.getParentDirectory().isDirectory(),"Export directory does not exist.");
 auto settings=requested;for(auto& c:settings.controls){c.mute=0;c.solo=0;}
 ohdrum::Engine renderer;renderer.setSlotControls(settings.controls,settings.output);renderer.prepare(settings.rate,settings.macros);renderer.replace(samples);renderer.triggerSlot(slot,1.0f,ohdrum::defaultNotes[static_cast<size_t>(slot)]);
 const auto maximum=static_cast<int64_t>(settings.rate*128);const auto quietRequired=static_cast<int64_t>(settings.rate*.25);const auto fadeFrames=static_cast<int64_t>(settings.rate*.02);int64_t quiet=0,frames=0;double energy=0,signalEnergy=0,peak=0;
 uint32_t seed=0x5eed1234u+static_cast<uint32_t>(slot)*7919u;auto uniform=[&](){seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;return static_cast<double>(seed>>8)/16777216.0;};
 juce::TemporaryFile temporary(destination);{
  juce::FileOutputStream stream(temporary.getFile());demand(stream.openedOk(),"Cannot create WAV export.");
  demand(stream.write("RIFF",4)&&stream.writeInt(0)&&stream.write("WAVEfmt ",8)&&stream.writeInt(16)&&stream.writeShort(1)&&stream.writeShort(2)&&stream.writeInt(static_cast<int>(settings.rate))&&stream.writeInt(static_cast<int>(settings.rate)*6)&&stream.writeShort(6)&&stream.writeShort(24)&&stream.write("data",4)&&stream.writeInt(0),"Cannot write WAV header.");
  std::array<uint8_t,128*6> pcm{};size_t used=0;
  for(int64_t frame=0;frame<maximum;++frame){if(frame%128==0)demand(!cancel.load(),"Export cancelled.");auto out=renderer.tick();const float magnitude=std::max(std::abs(out[0]),std::abs(out[1]));quiet=magnitude<.0000316228f?quiet+1:0;
   const double fade=frame>=maximum-fadeFrames?static_cast<double>(maximum-1-frame)/static_cast<double>(fadeFrames):1.0;
   for(float x:out){demand(std::isfinite(x),"Non-finite rendered audio.");const double signal=std::clamp(static_cast<double>(x),-.98,.98)*fade;signalEnergy+=signal*signal;
    // Deterministic TPDF dither, one 24-bit LSB peak, applied before rounding.
    const auto value=static_cast<int32_t>(std::llround(signal*8388608.0+uniform()-uniform()));const double quantized=static_cast<double>(value)/8388608.0;energy+=quantized*quantized;peak=std::max(peak,std::abs(quantized));const auto bits=static_cast<uint32_t>(value);
    pcm[used++]=static_cast<uint8_t>(bits);pcm[used++]=static_cast<uint8_t>(bits>>8);pcm[used++]=static_cast<uint8_t>(bits>>16);
   }++frames;
   const bool done=frame>=static_cast<int64_t>(settings.rate*.1)&&quiet>=quietRequired;
   if(used==pcm.size()||done||frame+1==maximum){demand(stream.write(pcm.data(),used),"WAV audio write failed.");used=0;}
   if(done)break;
  }
  demand(signalEnergy>1.e-20,"Export is silent: check blend, gain or missing optional samples.");const auto bytes=static_cast<int>(frames*6);demand(stream.setPosition(4)&&stream.writeInt(36+bytes)&&stream.setPosition(40)&&stream.writeInt(bytes),"Cannot finalize WAV header.");stream.flush();demand(stream.getStatus().wasOk(),"WAV flush failed.");
 }
 {juce::FileInputStream check(temporary.getFile());char header[4]{};demand(check.openedOk()&&check.read(header,4)==4&&std::memcmp(header,"RIFF",4)==0,"Invalid export RIFF header.");demand(check.readInt()==36+frames*6&&check.getTotalLength()==44+frames*6,"Invalid WAV length.");check.setPosition(20);demand(check.readShort()==1&&check.readShort()==2&&check.readInt()==static_cast<int>(settings.rate),"Invalid export PCM format.");check.setPosition(34);demand(check.readShort()==24,"Export is not 24-bit PCM.");}
 demand(overwrite||!destination.exists(),"Export destination appeared during rendering.");demand(temporary.overwriteTargetFileWithTemporary(),"Cannot commit WAV export.");juce::FileInputStream input(destination);const auto hash=juce::SHA256(input).toHexString();return {destination,frames,static_cast<int>(settings.rate),peak,std::sqrt(energy/static_cast<double>(frames*2)),frames==maximum,hash};
}

// Load the delivered DLL, process actual audio buffers, save and restore into
// a second factory-created instance. This does not substitute for FL Studio.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <objbase.h>
#include "Plugin.h"
#include "base/source/fstreamer.h"
#include "public.sdk/source/common/memorystream.h"
#include "public.sdk/source/vst/hosting/hostclasses.h"
#include "public.sdk/source/vst/hosting/parameterchanges.h"
#include <filesystem>
#include <fstream>
#include <vector>
#include <array>
#include <cstdlib>
#include <iostream>
using namespace Steinberg;using namespace Steinberg::Vst;
void check(bool b,const char* msg){if(!b){std::cerr<<"FAIL "<<msg<<'\n';std::exit(1);}}
struct Session {
 IComponent* component=nullptr;IAudioProcessor* audio=nullptr;
 Session(IPluginFactory* factory,HostApplication& host,IBStream* state=nullptr){check(factory->createInstance(ovf::processorId.toTUID(),IComponent::iid,reinterpret_cast<void**>(&component))==kResultOk,"create");check(component->initialize(&host)==kResultOk,"initialize");check(component->queryInterface(IAudioProcessor::iid,reinterpret_cast<void**>(&audio))==kResultOk,"audio interface");ProcessSetup s{};s.sampleRate=48000;s.maxSamplesPerBlock=1024;s.symbolicSampleSize=kSample32;s.processMode=kOffline;check(audio->setupProcessing(s)==kResultOk,"setup");if(state)check(component->setState(state)==kResultOk,"restore state");check(component->activateBus(kAudio,kInput,0,true)==kResultOk&&component->activateBus(kAudio,kOutput,0,true)==kResultOk,"activate buses");check(component->setActive(true)==kResultOk&&audio->setProcessing(true)==kResultOk,"start");}
 ~Session(){audio->setProcessing(false);component->setActive(false);audio->release();component->terminate();component->release();}
 std::vector<float> render(bool automate){std::vector<float> result;result.reserve(96000*2);std::array<float,1024> l{},r{},a{},b{};float* src[]{l.data(),r.data()};float* dst[]{a.data(),b.data()};AudioBusBuffers in{},out{};in.numChannels=out.numChannels=2;in.channelBuffers32=src;out.channelBuffers32=dst;ProcessData d{};d.symbolicSampleSize=kSample32;d.numInputs=d.numOutputs=1;d.inputs=&in;d.outputs=&out;
  ParameterChanges changes(3);int32 qi=0,pi=0;if(automate){changes.addParameterData(ovf::inputId,qi)->addPoint(0,.75,pi);changes.addParameterData(ovf::outputId,qi)->addPoint(0,.625,pi);changes.addParameterData(ovf::bypassId,qi)->addPoint(0,1.,pi);}
  for(int offset=0;offset<96000;){int count=std::min(1+(offset*31%1024),96000-offset);d.numSamples=count;d.inputParameterChanges=automate&&offset==0?&changes:nullptr;in.silenceFlags=0;for(int n=0;n<count;++n){double t=double(offset+n)/48000;l[n]=float(.15*std::sin(2*3.141592653589793*220*t));r[n]=float(.12*std::sin(2*3.141592653589793*330*t));}check(audio->process(d)==kResultOk,"process");for(int n=0;n<count;++n){check(std::isfinite(a[n])&&std::isfinite(b[n]),"finite audio");result.push_back(a[n]);result.push_back(b[n]);}offset+=count;}return result;
 }
};
void word(std::ofstream& f,uint32_t x,int bytes=4){for(int i=0;i<bytes;++i)f.put(char(x>>(8*i)));}
int wmain(int argc,wchar_t** argv){check(argc==3,"DLL and evidence directory arguments");std::filesystem::path directory(argv[2]);std::filesystem::create_directories(directory);check(SUCCEEDED(CoInitializeEx(nullptr,COINIT_APARTMENTTHREADED)),"COM");auto module=LoadLibraryW(argv[1]);check(module!=nullptr,"load actual DLL");auto init=reinterpret_cast<bool(*)()>(GetProcAddress(module,"InitDll"));auto get=reinterpret_cast<IPluginFactory*(*)()>(GetProcAddress(module,"GetPluginFactory"));auto exit=reinterpret_cast<bool(*)()>(GetProcAddress(module,"ExitDll"));check(init&&get&&exit&&init(),"VST exports");auto* factory=get();HostApplication host;
 MemoryStream state;std::vector<float> first,second,gained;{Session a(factory,host);first=a.render(true);check(a.component->getState(&state)==kResultOk,"state save");}state.seek(0,IBStream::kIBSeekSet,nullptr);{Session b(factory,host,&state);second=b.render(false);}
 MemoryStream gainState;{IBStreamer w(&gainState,kLittleEndian);check(w.writeInt32(0x3146564f)&&w.writeInt32(1)&&w.writeDouble(.75)&&w.writeDouble(.625)&&w.writeInt32(0),"gain fixture state");}gainState.seek(0,IBStream::kIBSeekSet,nullptr);{Session c(factory,host,&gainState);gained=c.render(false);}
 // Unequal gains total +18 dB. A missing/restored-off bypass must fail unity.
 double maxRecall=0,unityError=0,peak=0,squares=0;for(size_t n=0;n<first.size();++n){maxRecall=std::max(maxRecall,std::abs(double(first[n])-second[n]));double t=double(n/2)/48000;double expected=n%2?.12*std::sin(2*3.141592653589793*330*t):.15*std::sin(2*3.141592653589793*220*t);unityError=std::max(unityError,std::abs(double(second[n])-float(expected)));peak=std::max(peak,std::abs(double(second[n])));squares+=double(second[n])*second[n];}
 check(unityError==0,"unity bypass after reload");
 double gainError=0;for(size_t n=0;n<gained.size();++n)gainError=std::max(gainError,std::abs(double(gained[n])-float(double(second[n])*ovf::gain(.75)*ovf::gain(.625))));check(gainError<1e-6,"actual DLL +18 dB gain path");
 // First render may contain nonzero transient from independently smoothed gains;
 // fresh-instance recall is compared after the finite 10 ms transition window.
 double settledRecall=0;for(size_t n=2048;n<first.size();++n)settledRecall=std::max(settledRecall,std::abs(double(first[n])-second[n]));check(settledRecall==0,"settled exact recall");
 std::ofstream wav(directory/"actual-dll-bypass.wav",std::ios::binary);wav.write("RIFF",4);word(wav,uint32_t(36+second.size()*4));wav.write("WAVEfmt ",8);word(wav,16);word(wav,3,2);word(wav,2,2);word(wav,48000);word(wav,48000*8);word(wav,8,2);word(wav,32,2);wav.write("data",4);word(wav,uint32_t(second.size()*4));wav.write(reinterpret_cast<const char*>(second.data()),std::streamsize(second.size()*4));check(bool(wav),"write WAV");
 std::ofstream report(directory/"artifact-audio.json");report<<"{\"status\":\"PASS\",\"actualDll\":true,\"sampleRate\":48000,\"framesPerCase\":96000,\"cases\":3,\"fixture\":\"synthetic stereo tones, not a vocal recording\",\"peak\":"<<peak<<",\"rms\":"<<std::sqrt(squares/second.size())<<",\"unityBypassError\":"<<unityError<<",\"gainDb\":18,\"gainError\":"<<gainError<<",\"settledFreshInstanceRecallError\":"<<settledRecall<<",\"initialTransitionDifference\":"<<maxRecall<<",\"FLStudio\":\"BLOCKED\",\"listening\":\"NOT_TESTED\"}\n";check(bool(report),"write report");factory->release();check(exit(),"module shutdown");FreeLibrary(module);CoUninitialize();std::cout<<"PASS exact DLL: 3 x 96000 stereo frames, finite audio, +18 dB gain, unity bypass, saved/restored fresh instance\n";
}

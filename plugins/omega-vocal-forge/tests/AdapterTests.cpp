#include "Plugin.h"
#include "base/source/fstreamer.h"
#include "public.sdk/source/common/memorystream.h"
#include "public.sdk/source/vst/hosting/parameterchanges.h"
#include <array>
#include <iostream>
#include <cstdlib>
#include <cstring>
#include <new>
#include <limits>
static thread_local bool measuring=false;static size_t allocations=0;
void* operator new(std::size_t n){if(measuring)++allocations;if(auto* p=std::malloc(n?n:1))return p;throw std::bad_alloc();}
void* operator new[](std::size_t n){return ::operator new(n);}void operator delete(void* p)noexcept{std::free(p);}void operator delete[](void* p)noexcept{std::free(p);}void operator delete(void* p,std::size_t)noexcept{std::free(p);}void operator delete[](void* p,std::size_t)noexcept{std::free(p);}
using namespace Steinberg;using namespace Steinberg::Vst;
void check(bool b,const char* msg){if(!b){std::cerr<<"FAIL "<<msg<<'\n';std::exit(1);}}
int main(){for(double rate:{44100.,48000.,96000.}){
 ovf::Processor p;check(p.initialize(nullptr)==kResultOk,"initialize");ProcessSetup setup{};setup.sampleRate=rate;setup.maxSamplesPerBlock=2048;setup.symbolicSampleSize=kSample32;check(p.setupProcessing(setup)==kResultOk,"prepare");
 SpeakerArrangement stereo=SpeakerArr::kStereo,mono=SpeakerArr::kMono;check(p.setBusArrangements(&mono,1,&stereo,1)==kResultOk,"mono in stereo out");check(p.setBusArrangements(&stereo,1,&mono,1)==kResultFalse,"reject mono output");check(p.setBusArrangements(&stereo,1,&stereo,1)==kResultOk,"stereo");
 check(p.setActive(true)==kResultOk&&p.setProcessing(true)==kResultOk,"start");check(p.canProcessSampleSize(kSample64)==kResultFalse,"explicit float32 contract");
 std::array<float,2048> l{},r{},a{},b{};l.fill(.125f);r.fill(-.25f);float* src[]{l.data(),r.data()};float* dst[]{a.data(),b.data()};AudioBusBuffers input{},output{};input.numChannels=output.numChannels=2;input.channelBuffers32=src;output.channelBuffers32=dst;
 ProcessData d{};d.symbolicSampleSize=kSample32;d.numInputs=d.numOutputs=1;d.inputs=&input;d.outputs=&output;
 auto render=[&](){measuring=true;auto status=p.process(d);measuring=false;check(status==kResultOk,"render");};
 for(int size:{0,1,7,64,128,512,1031,2048}){d.numSamples=size;render();for(int n=0;n<size;++n)check(a[n]==l[n]&&b[n]==r[n],"unity variable block");}
 ParameterChanges changes(3);int32 qi=0,pi=0;auto* q=changes.addParameterData(ovf::inputId,qi);q->addPoint(73,.75,pi);q->addPoint(900,.25,pi);auto* bypass=changes.addParameterData(ovf::bypassId,qi);bypass->addPoint(1400,1,pi);
 d.numSamples=2048;d.inputParameterChanges=&changes;render();ovf::Engine reference;reference.prepare(rate);ovf::Targets t;
 for(int n=0;n<2048;++n){if(n==73)t.input=.75;if(n==900)t.input=.25;if(n==1400)t.bypass=true;reference.set(t);float x,y;reference.sample(l[n],r[n],x,y);check(a[n]==x&&b[n]==y,"sample offset automation");}
 d.inputParameterChanges=nullptr;MemoryStream saved;check(p.getState(&saved)==kResultOk,"save after automation");
 ovf::Processor restored;check(restored.initialize(nullptr)==kResultOk,"new instance");saved.seek(0,IBStream::kIBSeekSet,nullptr);check(restored.setState(&saved)==kResultOk,"restore");MemoryStream again;check(restored.getState(&again)==kResultOk,"resave");check(saved.getSize()==again.getSize()&&std::memcmp(saved.getData(),again.getData(),size_t(saved.getSize()))==0,"exact state recall");
 ovf::Controller controller;check(controller.initialize(nullptr)==kResultOk,"controller");saved.seek(0,IBStream::kIBSeekSet,nullptr);check(controller.setComponentState(&saved)==kResultOk,"controller recall");check(controller.getParamNormalized(ovf::inputId)==.25&&controller.getParamNormalized(ovf::bypassId)==1.,"bypass and gain persist");
 check(controller.getParameterCount()==3,"catalogue count");for(int n=0;n<3;++n){ParameterInfo info{};check(controller.getParameterInfo(n,info)==kResultOk&&info.id==100+uint32(n),"stable IDs");}
 auto* view=controller.createView(ViewType::kEditor);check(view!=nullptr,"original editor created");ViewRect rect{};check(view->getSize(&rect)==kResultOk&&rect.getWidth()==480,"editor size");view->release();
 auto* bytes=static_cast<char*>(saved.getData());bytes[0]^=1;saved.seek(0,IBStream::kIBSeekSet,nullptr);check(restored.setState(&saved)==kResultFalse,"reject corrupt state");MemoryStream after;check(restored.getState(&after)==kResultOk&&after.getSize()==again.getSize()&&std::memcmp(after.getData(),again.getData(),size_t(after.getSize()))==0,"corruption atomic rejection");
 for(int size:{0,1,7,27}){MemoryStream truncated(again.getData(),size);check(restored.setState(&truncated)==kResultFalse,"reject truncated state");}
 for(double invalid:{-1.,2.,std::numeric_limits<double>::infinity(),std::numeric_limits<double>::quiet_NaN()}){MemoryStream invalidState;IBStreamer writer(&invalidState,kLittleEndian);writer.writeInt32(0x3146564f);writer.writeInt32(1);writer.writeDouble(invalid);writer.writeDouble(.5);writer.writeInt32(0);invalidState.seek(0,IBStream::kIBSeekSet,nullptr);check(restored.setState(&invalidState)==kResultFalse,"reject invalid numeric state");}
 check(restored.terminate()==kResultOk,"terminate restored");check(controller.terminate()==kResultOk,"terminate controller");
 // In-place render and mono duplication use captured inputs before output writes.
 input.numChannels=1;src[0]=l.data();dst[0]=l.data();d.numSamples=2048;render();for(int n=0;n<2048;++n)check(l[n]==b[n],"mono duplication in place");
 input.silenceFlags=1;render();for(int n=0;n<2048;++n)check(l[n]==0&&b[n]==0,"input silence flags");check(output.silenceFlags==3,"output silence flags");input.silenceFlags=0;
 src[0]=nullptr;render();for(int n=0;n<2048;++n)check(l[n]==0&&b[n]==0,"null input");dst[1]=nullptr;check(p.process(d)==kResultFalse,"null output rejection");
 check(p.getLatencySamples()==0,"zero latency");check(p.setProcessing(false)==kResultOk&&p.setActive(false)==kResultOk&&p.terminate()==kResultOk,"shutdown");
 }
 check(allocations==0,"no measured audio callback allocations");std::cout<<"PASS native adapter: 3 rates, 8 blocks, sample offsets, mono/stereo/in-place/null/silence, exact fresh-instance state, corruption, GUI creation, zero audio allocations\n";
}

// Deterministic synthetic regression through the exact built DLL, not a DSP copy.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <objbase.h>
#include "Plugin.h"
#include "public.sdk/source/vst/hosting/hostclasses.h"
#include "public.sdk/source/vst/hosting/parameterchanges.h"
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
using namespace Steinberg;
using namespace Steinberg::Vst;
void require(bool value, const char* message) { if (!value) throw std::runtime_error(message); }

int wmain(int argc, wchar_t** argv) {
 try {
  require(argc == 3, "module and new PCM output required");
  require(!std::filesystem::exists(argv[2]), "refuse output overwrite");
  require(SUCCEEDED(CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED)), "COM init");
  auto module = LoadLibraryW(argv[1]);
  require(module != nullptr, "load DLL");
  auto init = reinterpret_cast<bool(*)()>(GetProcAddress(module, "InitDll"));
  auto get = reinterpret_cast<IPluginFactory*(*)()>(GetProcAddress(module, "GetPluginFactory"));
  auto exit = reinterpret_cast<bool(*)()>(GetProcAddress(module, "ExitDll"));
  require(init && get && exit && init(), "DLL exports/init");
  auto* factory = get();
  HostApplication host;
  std::ofstream output(std::filesystem::path(argv[2]), std::ios::binary);
  require(bool(output), "open PCM output");
  int cases = 0;
  for (double rate : {44100., 48000., 96000.}) for (int block : {64, 511, 1024}) {
   IComponent* component = nullptr;
   IAudioProcessor* processor = nullptr;
   require(factory->createInstance(oeq::processorId.toTUID(), IComponent::iid,
           reinterpret_cast<void**>(&component)) == kResultOk, "create component");
   require(component->initialize(&host) == kResultOk, "initialize");
   require(component->queryInterface(IAudioProcessor::iid,
           reinterpret_cast<void**>(&processor)) == kResultOk, "audio interface");
   ProcessSetup setup{};
   setup.sampleRate = rate; setup.maxSamplesPerBlock = block;
   setup.symbolicSampleSize = kSample32; setup.processMode = kOffline;
   require(processor->setupProcessing(setup) == kResultOk, "setup");
   require(component->activateBus(kAudio, kInput, 0, true) == kResultOk, "input activation");
   require(component->activateBus(kAudio, kOutput, 0, true) == kResultOk, "output activation");
   require(component->setActive(true) == kResultOk && processor->setProcessing(true) == kResultOk, "start");
   std::array<float, 1024> left{}, right{}, outLeft{}, outRight{};
   float* source[]{left.data(), right.data()};
   float* destination[]{outLeft.data(), outRight.data()};
   AudioBusBuffers input{}, rendered{};
   input.numChannels = rendered.numChannels = 2;
   input.channelBuffers32 = source; rendered.channelBuffers32 = destination;
   ProcessData data{};
   data.symbolicSampleSize = kSample32; data.numInputs = data.numOutputs = 1;
   data.inputs = &input; data.outputs = &rendered;
   uint32_t random = 0x193a2c7u;
   const int frames = int(rate * 2);
   for (int start = 0; start < frames; start += block) {
    data.numSamples = std::min(block, frames - start);
    ParameterChanges changes(5);
    for (int control = 0; control < 5; ++control) {
     int32 index = 0, point = 0;
     auto* queue = changes.addParameterData(oeq::bassId + control, index);
     const double target = control == 4 ? double((start / 4096) % 2) : double((start / 8192 + control) % 5) / 4.;
     require(queue->addPoint(std::min(17, data.numSamples - 1), target, point) == kResultOk, "automation");
    }
    data.inputParameterChanges = &changes;
    for (int n = 0; n < data.numSamples; ++n) {
     random ^= random << 13; random ^= random >> 17; random ^= random << 5;
     float noise = float(double(random) / 4294967296. - .5) * .02f;
     left[n] = noise + float(.03 * std::sin(2 * oeq::pi * 137 * (start + n) / rate));
     right[n] = -noise + float(.02 * std::sin(2 * oeq::pi * 3001 * (start + n) / rate));
     if (start + n >= int(rate)) left[n] = right[n] = 0; // decay/silence segment
    }
    require(processor->process(data) == kResultOk, "offline process");
    for (int n = 0; n < data.numSamples; ++n) {
     require(std::isfinite(outLeft[n]) && std::isfinite(outRight[n]), "finite stereo");
     require(std::abs(outLeft[n]) < 100 && std::abs(outRight[n]) < 100, "bounded output");
     output.write(reinterpret_cast<char*>(&outLeft[n]), sizeof(float));
     output.write(reinterpret_cast<char*>(&outRight[n]), sizeof(float));
    }
   }
   require(processor->setProcessing(false) == kResultOk && component->setActive(false) == kResultOk, "stop");
   processor->release(); require(component->terminate() == kResultOk, "terminate"); component->release();
   ++cases;
  }
  output.close(); require(bool(output), "PCM write");
  factory->release(); require(exit(), "DLL exit"); FreeLibrary(module); CoUninitialize();
  std::cout << "PASS " << cases << " exact-DLL renders; 44.1/48/96k, 64/511/1024 blocks, independent stereo, automation, bypass, silence. PCM=f32le stereo concatenated in rate/block loop order. Host/listening NOT_TESTED.\n";
  return 0;
 } catch (const std::exception& error) { std::cerr << error.what() << '\n'; return 1; }
}

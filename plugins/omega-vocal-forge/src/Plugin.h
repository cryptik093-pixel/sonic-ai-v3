#pragma once
#include "Engine.h"
#include "public.sdk/source/vst/vstaudioeffect.h"
#include "public.sdk/source/vst/vsteditcontroller.h"
#include <atomic>
namespace ovf {
static_assert(std::atomic<double>::is_always_lock_free && std::atomic<bool>::is_always_lock_free,"Audio state requires lock-free atomics");
inline const Steinberg::FUID processorId(0xA423BE19,0xC7104CA6,0x8F1C546E,0xD45D9321);
inline const Steinberg::FUID controllerId(0x2D772BC5,0xE3B04ED7,0xA827B35A,0x6F6F27A9);
class Processor final: public Steinberg::Vst::AudioEffect {
 Engine engine;
 std::atomic<double> input{.5},output{.5};std::atomic<bool> bypass{false};
 Targets targets() const noexcept {return {input.load(),output.load(),bypass.load()};}
 void apply(Steinberg::Vst::ParamID,double) noexcept;
public:
 Processor(){setControllerClass(controllerId);}
 static Steinberg::FUnknown* create(void*){return static_cast<Steinberg::Vst::IAudioProcessor*>(new Processor);}
 Steinberg::tresult PLUGIN_API initialize(Steinberg::FUnknown*) override;
 Steinberg::tresult PLUGIN_API setupProcessing(Steinberg::Vst::ProcessSetup&) override;
 Steinberg::tresult PLUGIN_API setProcessing(Steinberg::TBool) override;
 Steinberg::tresult PLUGIN_API canProcessSampleSize(Steinberg::int32 n) override;
 Steinberg::tresult PLUGIN_API setBusArrangements(Steinberg::Vst::SpeakerArrangement*,Steinberg::int32,Steinberg::Vst::SpeakerArrangement*,Steinberg::int32) override;
 Steinberg::tresult PLUGIN_API process(Steinberg::Vst::ProcessData&) override;
 Steinberg::tresult PLUGIN_API getState(Steinberg::IBStream*) override;
 Steinberg::tresult PLUGIN_API setState(Steinberg::IBStream*) override;
};
class Controller final: public Steinberg::Vst::EditControllerEx1 {
public:
 static Steinberg::FUnknown* create(void*){return static_cast<Steinberg::Vst::IEditController*>(new Controller);}
 Steinberg::tresult PLUGIN_API initialize(Steinberg::FUnknown*) override;
 Steinberg::tresult PLUGIN_API setComponentState(Steinberg::IBStream*) override;
 Steinberg::IPlugView* PLUGIN_API createView(Steinberg::FIDString) override;
};
}

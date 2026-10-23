#pragma once
#include "omega/OrganismCore.h"
#include "omega/State.h"
#include "StateBridge.h"
#include "public.sdk/source/vst/vstaudioeffect.h"
#include "public.sdk/source/vst/vsteditcontroller.h"

#define OSO_PRODUCT_VERSION "1.0.0-dev.v4"

namespace oso {
inline const Steinberg::FUID processorID(0xB7FE82DB,0x13A64A8D,0xAF3A2CAA,0x5CCC4CB1);
inline const Steinberg::FUID controllerID(0xB8BD8AEC,0xF05F4A27,0xB0F6EE2B,0x15346516);
class Processor final : public Steinberg::Vst::AudioEffect {
public:
    Processor();
    static Steinberg::FUnknown* create(void*) { return static_cast<Steinberg::Vst::IAudioProcessor*>(new Processor); }
    Steinberg::tresult PLUGIN_API initialize(Steinberg::FUnknown*) override;
    Steinberg::tresult PLUGIN_API setupProcessing(Steinberg::Vst::ProcessSetup&) override;
    Steinberg::tresult PLUGIN_API setBusArrangements(Steinberg::Vst::SpeakerArrangement*,Steinberg::int32,Steinberg::Vst::SpeakerArrangement*,Steinberg::int32) override;
    Steinberg::tresult PLUGIN_API canProcessSampleSize(Steinberg::int32) override;
    Steinberg::tresult PLUGIN_API setProcessing(Steinberg::TBool) override;
    Steinberg::tresult PLUGIN_API process(Steinberg::Vst::ProcessData&) override;
    Steinberg::tresult PLUGIN_API getState(Steinberg::IBStream*) override;
    Steinberg::tresult PLUGIN_API setState(Steinberg::IBStream*) override;
    Steinberg::uint32 PLUGIN_API getLatencySamples() override {return omega::OrganismCore::latencySamples;}
    Steinberg::uint32 PLUGIN_API getTailSamples() override {
        const double rate = processSetup.sampleRate > 0 ? processSetup.sampleRate : 48000.;
        return static_cast<Steinberg::uint32>(std::ceil(rate * 20.));
    }
private:
    void apply(size_t,double) noexcept;
    void consumeHostState() noexcept;
    omega::OrganismCore core;
    omega::ParameterValues values=omega::defaults();
    StateBridge stateBridge;
    uint32_t consumedStateRevision=0;
    double meterPeak=0,lastVelocity=0;
    int lastNote=-1;
    double expectedBeat=0;
    bool transportInitialized=false,wasPlaying=false;
};
class Controller final : public Steinberg::Vst::EditControllerEx1, public Steinberg::Vst::IMidiMapping {
public:
    static Steinberg::FUnknown* create(void*) { return static_cast<Steinberg::Vst::IEditController*>(new Controller); }
    Steinberg::tresult PLUGIN_API initialize(Steinberg::FUnknown*) override;
    Steinberg::tresult PLUGIN_API setComponentState(Steinberg::IBStream*) override;
    Steinberg::IPlugView* PLUGIN_API createView(Steinberg::FIDString name) override;
    Steinberg::tresult PLUGIN_API getMidiControllerAssignment(Steinberg::int32,Steinberg::int16,Steinberg::Vst::CtrlNumber,Steinberg::Vst::ParamID&) override;
    Steinberg::tresult PLUGIN_API queryInterface(const Steinberg::TUID,void**) override;
    Steinberg::uint32 PLUGIN_API addRef() override {return EditControllerEx1::addRef();}
    Steinberg::uint32 PLUGIN_API release() override {return EditControllerEx1::release();}
};
}

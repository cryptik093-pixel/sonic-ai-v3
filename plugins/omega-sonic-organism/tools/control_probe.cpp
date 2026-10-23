// Discover the real DLL's host contract without starting audio or networking.
#define NOMINMAX
#include <windows.h>
#include "Plugin.h"
#include "pluginterfaces/base/ustring.h"
#include "public.sdk/source/vst/hosting/hostclasses.h"
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <cstdlib>
#define CHECK(x) do { if (!(x)) { std::cerr << "FAIL " << __LINE__ << ": " << #x << '\n'; return 1; } } while(false)
using namespace Steinberg;
using namespace Steinberg::Vst;
int wmain(int argc,wchar_t** argv) {
    CHECK(argc==3);
    HMODULE module=LoadLibraryW(argv[1]);CHECK(module);
    const auto init=reinterpret_cast<bool(*)()>(GetProcAddress(module,"InitDll"));CHECK(init&&init());
    const auto getFactory=reinterpret_cast<IPluginFactory*(*)()>(GetProcAddress(module,"GetPluginFactory"));CHECK(getFactory);
    auto* factory=getFactory();CHECK(factory);
    IPluginFactory2* factory2=nullptr;
    CHECK(factory->queryInterface(IPluginFactory2::iid,reinterpret_cast<void**>(&factory2))==kResultOk);
    PClassInfo2 instrument{};CHECK(factory2->getClassInfo2(0,&instrument)==kResultOk);
    CHECK(FUID::fromTUID(instrument.cid)==oso::processorID);
    HostApplication host;IEditController* controller=nullptr;
    CHECK(factory->createInstance(oso::controllerID.toTUID(),IEditController::iid,reinterpret_cast<void**>(&controller))==kResultOk);
    CHECK(controller->initialize(&host)==kResultOk);
    char processorCid[33]{},controllerCid[33]{};
    FUID::fromTUID(instrument.cid).toString(processorCid);oso::controllerID.toString(controllerCid);
    std::ofstream out{std::filesystem::path(argv[2])};CHECK(out);
    out << std::setprecision(17) << "{\"contract\":\"omega-sonic-organism.host-control\",\"contractVersion\":1,"
        << "\"discovery\":\"actual VST3 DLL factory and controller\",\"integrationState\":\"PREPARED; Sonic AI end-to-end NOT_TESTED\","
        << "\"instrumentVersion\":" << std::quoted(instrument.version) << ",\"instrumentName\":" << std::quoted(instrument.name)
        << ",\"processorCid\":" << std::quoted(processorCid) << ",\"controllerCid\":" << std::quoted(controllerCid)
        << ",\"nativeState\":{\"magic\":\"OSO1\",\"schema\":1,\"bytes\":140,\"parameterCount\":15},\"parameters\":[";
    CHECK(controller->getParameterCount()==23);
    for(int32 i=0;i<controller->getParameterCount();++i) {
        ParameterInfo info{};CHECK(controller->getParameterInfo(i,info)==kResultOk);
        char title[512]{},units[512]{};
        static_assert(sizeof(TChar)==sizeof(wchar_t));
        CHECK(WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,reinterpret_cast<const wchar_t*>(info.title),-1,title,512,nullptr,nullptr)>0);
        CHECK(WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,reinterpret_cast<const wchar_t*>(info.units),-1,units,512,nullptr,nullptr)>0);
        if(i<15){const auto& expected=omega::parameterDefinitions[size_t(i)];
            CHECK(info.id==expected.id&&info.stepCount==expected.steps&&info.defaultNormalizedValue==expected.initial);}
        if(i)out << ',';
        out << "{\"id\":" << info.id << ",\"title\":" << std::quoted(title) << ",\"units\":" << std::quoted(units)
            << ",\"defaultNormalized\":" << info.defaultNormalizedValue << ",\"steps\":" << info.stepCount
            << ",\"flags\":" << info.flags << ",\"nativeStateMember\":" << (i<15?"true":"false")
            << ",\"minimumPlain\":" << controller->normalizedParamToPlain(info.id,0)
            << ",\"maximumPlain\":" << controller->normalizedParamToPlain(info.id,1) << '}';
    }
    out << "],\"macroIds\":[100,101,102,103,104,105],\"presetSelection\":\"parse validated factory/imported JSON; send its 15 normalized values through VST3 edit gestures\","
        << "\"offlineRenderMetadataFields\":[\"contractVersion\",\"moduleSha256\",\"nativeStateSha256\",\"presetId\",\"sampleRate\",\"frames\",\"tempo\",\"eventStreamSha256\",\"audioSha256\"],"
        << "\"realtimePolicy\":\"host automation only; no network or file operations in audio callbacks\"}\n";
    CHECK(out);
    CHECK(controller->terminate()==kResultOk);controller->release();factory2->release();factory->release();
    const auto exitModule=reinterpret_cast<bool(*)()>(GetProcAddress(module,"ExitDll"));CHECK(exitModule&&exitModule());
    FreeLibrary(module);
    std::cout << "PASS actual DLL control discovery: stable 15-value state contract and 23 controller parameters. Sonic AI orchestration NOT_TESTED.\n";
}

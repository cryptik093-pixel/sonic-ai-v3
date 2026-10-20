// Native integration test host. Calls the actual DLL's IPlugView API. This
// owns its window and does not automate or alter any existing DAW session.
#define NOMINMAX
#include <windows.h>
#include "Plugin.h"
#include "public.sdk/source/vst/hosting/hostclasses.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <vector>
#include <cstdlib>
#define CHECK(x) do{if(!(x)){std::cerr<<"FAIL "<<__LINE__<<": "<<#x<<'\n';std::exit(1);}}while(false)
using namespace Steinberg;
using namespace Steinberg::Vst;
// Avoid silently clamping a 150% capture to a smaller development monitor.
LRESULT CALLBACK probeWindow(HWND window,UINT message,WPARAM w,LPARAM l){if(message==WM_GETMINMAXINFO){auto* limits=reinterpret_cast<MINMAXINFO*>(l);limits->ptMaxTrackSize={4096,4096};return 0;}return DefWindowProcW(window,message,w,l);}
void pump(int milliseconds){const auto end=GetTickCount64()+milliseconds;MSG m{};do{while(PeekMessageW(&m,nullptr,0,0,PM_REMOVE)){TranslateMessage(&m);DispatchMessageW(&m);}Sleep(10);}while(GetTickCount64()<end);}
void capture(HWND window,const std::filesystem::path& path){RECT r{};CHECK(GetClientRect(window,&r));int width=r.right,height=r.bottom;HDC dc=GetDC(window),memory=CreateCompatibleDC(dc);BITMAPINFO info{};info.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);info.bmiHeader.biWidth=width;info.bmiHeader.biHeight=-height;info.bmiHeader.biPlanes=1;info.bmiHeader.biBitCount=32;info.bmiHeader.biCompression=BI_RGB;void* pixels=nullptr;HBITMAP bitmap=CreateDIBSection(dc,&info,DIB_RGB_COLORS,&pixels,nullptr,0);CHECK(bitmap&&pixels);auto previous=SelectObject(memory,bitmap);BOOL printed=PrintWindow(window,memory,PW_CLIENTONLY|2);CHECK(printed);BITMAPFILEHEADER header{};header.bfType=0x4d42;header.bfOffBits=sizeof(header)+sizeof(BITMAPINFOHEADER);header.bfSize=header.bfOffBits+width*height*4;std::ofstream out(path,std::ios::binary);CHECK(out);out.write(reinterpret_cast<const char*>(&header),sizeof(header));out.write(reinterpret_cast<const char*>(&info.bmiHeader),sizeof(BITMAPINFOHEADER));out.write(static_cast<const char*>(pixels),width*height*4);CHECK(out);SelectObject(memory,previous);DeleteObject(bitmap);DeleteDC(memory);ReleaseDC(window,dc);}
int wmain(int argc,wchar_t** argv){CHECK(argc==3);CHECK(SUCCEEDED(CoInitializeEx(nullptr,COINIT_APARTMENTTHREADED)));std::filesystem::path output(argv[2]);std::filesystem::create_directories(output);
    HMODULE module=LoadLibraryW(argv[1]);CHECK(module);auto init=reinterpret_cast<bool(*)()>(GetProcAddress(module,"InitDll"));CHECK(init&&init());auto getFactory=reinterpret_cast<IPluginFactory*(*)()>(GetProcAddress(module,"GetPluginFactory"));CHECK(getFactory);auto* factory=getFactory();CHECK(factory);
    HostApplication host;IEditController* controller=nullptr;CHECK(factory->createInstance(oso::controllerID.toTUID(),IEditController::iid,reinterpret_cast<void**>(&controller))==kResultOk);CHECK(controller->initialize(&host)==kResultOk);
    WNDCLASSW wc{};wc.lpfnWndProc=probeWindow;wc.hInstance=GetModuleHandleW(nullptr);wc.lpszClassName=L"OmegaOrganismEditorProbe";CHECK(RegisterClassW(&wc));HWND window=CreateWindowW(wc.lpszClassName,L"OMEGA SONIC ORGANISM - native editor test",WS_OVERLAPPEDWINDOW,20,20,1080,680,nullptr,nullptr,wc.hInstance,nullptr);CHECK(window);ShowWindow(window,SW_SHOWNOACTIVATE);
    for(int iteration=0;iteration<3;++iteration){auto* view=controller->createView(ViewType::kEditor);CHECK(view);CHECK(view->isPlatformTypeSupported(kPlatformTypeHWND)==kResultTrue);CHECK(view->attached(window,kPlatformTypeHWND)==kResultOk);CHECK(view->canResize()==kResultTrue);
        ViewRect size(0,0,int32(1040*(1+iteration*.25)),int32(620*(1+iteration*.25)));CHECK(view->checkSizeConstraint(&size)==kResultTrue);RECT outer{0,0,size.right,size.bottom};AdjustWindowRect(&outer,WS_OVERLAPPEDWINDOW,false);SetWindowPos(window,nullptr,0,0,outer.right-outer.left,outer.bottom-outer.top,SWP_NOMOVE|SWP_NOZORDER|SWP_NOACTIVATE);RECT actual{};CHECK(GetClientRect(window,&actual));CHECK(actual.right==size.right&&actual.bottom==size.bottom);CHECK(view->onSize(&size)==kResultOk);
        CHECK(controller->setParamNormalized(100,iteration*.5)==kResultOk);CHECK(controller->setParamNormalized(101,.3+iteration*.3)==kResultOk);CHECK(controller->setParamNormalized(1010,.25+iteration*.2)==kResultOk);CHECK(controller->setParamNormalized(1011,1./32)==kResultOk);CHECK(controller->setParamNormalized(1012,61./128)==kResultOk);CHECK(controller->setParamNormalized(1013,.85)==kResultOk);pump(700);capture(window,output/("editor-"+std::to_string(100+25*iteration)+".bmp"));
        CHECK(view->removed()==kResultOk);view->release();pump(100);}
    DestroyWindow(window);UnregisterClassW(wc.lpszClassName,wc.hInstance);CHECK(controller->terminate()==kResultOk);controller->release();factory->release();auto exitModule=reinterpret_cast<bool(*)()>(GetProcAddress(module,"ExitDll"));CHECK(exitModule&&exitModule());FreeLibrary(module);CoUninitialize();std::cout<<"PASS actual DLL editor attach/remove/reopen; host parameter refresh; 100/125/150 percent resize API. Captures require visual inspection. This is not an FL Studio test.\n";
}

#include "Plugin.h"
#include "public.sdk/source/common/pluginview.h"
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <commctrl.h>
#include <cstdio>
#include <cstring>
namespace ovf {
class Editor final:public Steinberg::CPluginView {
 Controller* controller;HWND window=nullptr,sliders[2]{},button=nullptr;
 static constexpr wchar_t className[]=L"OmegaVocalForgeEditorV1";
 static HINSTANCE instance(){HINSTANCE h=nullptr;GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,reinterpret_cast<LPCWSTR>(&proc),&h);return h;}
 void sync(){for(int i=0;i<2;++i)SendMessageW(sliders[i],TBM_SETPOS,TRUE,LPARAM(std::lround(controller->getParamNormalized(inputId+i)*480)));SetWindowTextW(button,controller->getParamNormalized(bypassId)>=.5?L"BYPASS : ON":L"BYPASS : OFF");InvalidateRect(window,nullptr,FALSE);}
 void edit(Steinberg::Vst::ParamID id,double value){controller->beginEdit(id);controller->setParamNormalized(id,value);controller->performEdit(id,value);controller->endEdit(id);sync();}
 static LRESULT CALLBACK proc(HWND h,UINT msg,WPARAM wp,LPARAM lp){
  auto* self=reinterpret_cast<Editor*>(GetWindowLongPtrW(h,GWLP_USERDATA));
  if(msg==WM_NCCREATE){self=static_cast<Editor*>(reinterpret_cast<CREATESTRUCTW*>(lp)->lpCreateParams);SetWindowLongPtrW(h,GWLP_USERDATA,reinterpret_cast<LONG_PTR>(self));}
  if(!self)return DefWindowProcW(h,msg,wp,lp);
  if(msg==WM_HSCROLL){for(int i=0;i<2;++i)if(reinterpret_cast<HWND>(lp)==self->sliders[i])self->edit(inputId+i,double(SendMessageW(self->sliders[i],TBM_GETPOS,0,0))/480.);return 0;}
  if(msg==WM_COMMAND&&LOWORD(wp)==12){self->edit(bypassId,self->controller->getParamNormalized(bypassId)>=.5?0.:1.);return 0;}
  if(msg==WM_TIMER){self->sync();return 0;}
  if(msg==WM_ERASEBKGND)return 1;
  if(msg==WM_PAINT){PAINTSTRUCT ps;auto dc=BeginPaint(h,&ps);RECT r;GetClientRect(h,&r);auto brush=CreateSolidBrush(RGB(23,20,31));FillRect(dc,&r,brush);DeleteObject(brush);SetBkMode(dc,TRANSPARENT);SetTextColor(dc,RGB(232,192,112));
   auto text=[dc](int x,int y,const wchar_t* t){TextOutW(dc,x,y,t,int(wcslen(t)));};
   text(26,22,L"OMEGA HOUSE / VOCAL FORGE");SetTextColor(dc,RGB(232,230,237));text(26,53,L"Vocal channel     /     Input > Gain > Output");
   wchar_t label[80];for(int i=0;i<2;++i){swprintf_s(label,L"%s   %+.2f dB",i==0?L"INPUT":L"OUTPUT",db(self->controller->getParamNormalized(inputId+i)));text(26,92+i*76,label);}
   SetTextColor(dc,RGB(177,166,194));text(26,286,L"Unity bypass  /  10 ms transitions  /  Gate 1");EndPaint(h,&ps);return 0;}
  return DefWindowProcW(h,msg,wp,lp);
 }
public:
 explicit Editor(Controller* c):controller(c){controller->addRef();rect={0,0,480,326};}
 ~Editor() override {removed();controller->release();}
 Steinberg::tresult PLUGIN_API isPlatformTypeSupported(Steinberg::FIDString t) override{return t&&std::strcmp(t,Steinberg::kPlatformTypeHWND)==0?Steinberg::kResultTrue:Steinberg::kResultFalse;}
 Steinberg::tresult PLUGIN_API attached(void* parent,Steinberg::FIDString type) override {
  if(!parent||window||isPlatformTypeSupported(type)!=Steinberg::kResultTrue)return Steinberg::kResultFalse;
  INITCOMMONCONTROLSEX common{sizeof(common),ICC_BAR_CLASSES};InitCommonControlsEx(&common);
  WNDCLASSW wc{};wc.lpfnWndProc=proc;wc.hInstance=instance();wc.lpszClassName=className;wc.hCursor=LoadCursor(nullptr,IDC_ARROW);RegisterClassW(&wc);
  window=CreateWindowExW(0,className,L"Omega Vocal Forge",WS_CHILD|WS_VISIBLE|WS_CLIPCHILDREN,0,0,480,326,static_cast<HWND>(parent),nullptr,instance(),this);if(!window)return Steinberg::kResultFalse;
  for(int i=0;i<2;++i){sliders[i]=CreateWindowExW(0,TRACKBAR_CLASSW,L"",WS_CHILD|WS_VISIBLE|WS_TABSTOP|TBS_HORZ|TBS_NOTICKS,24,118+i*76,426,30,window,nullptr,instance(),nullptr);SendMessageW(sliders[i],TBM_SETRANGE,TRUE,MAKELPARAM(0,480));}
  button=CreateWindowExW(0,L"BUTTON",L"",WS_CHILD|WS_VISIBLE|WS_TABSTOP|BS_PUSHBUTTON,26,236,170,32,window,reinterpret_cast<HMENU>(12),instance(),nullptr);
  sync();SetTimer(window,1,100,nullptr);return CPluginView::attached(parent,type);
 }
 Steinberg::tresult PLUGIN_API removed() override{if(window){KillTimer(window,1);DestroyWindow(window);window=nullptr;UnregisterClassW(className,instance());}return CPluginView::removed();}
};
Steinberg::IPlugView* makeEditor(Controller* c){return new Editor(c);}
}

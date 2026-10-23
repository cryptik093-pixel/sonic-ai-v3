#include "Editor.h"
#include "omega/Preset.h"
#include "omega/FactoryBank.h"
#include "public.sdk/source/vst/vstguieditor.h"
#include "pluginterfaces/base/ustring.h"
#include "vstgui/lib/controls/cbuttons.h"
#include "vstgui/lib/controls/cknob.h"
#include "vstgui/lib/controls/cslider.h"
#include "vstgui/lib/controls/coptionmenu.h"
#include "vstgui/lib/controls/ctextedit.h"
#include "vstgui/lib/controls/ctextlabel.h"
#include "vstgui/lib/cfileselector.h"
#include "vstgui/lib/cvstguitimer.h"
#include <algorithm>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iterator>

namespace oso {
using namespace VSTGUI;
using namespace Steinberg;
namespace {
const CColor ink{12,11,18,255},panel{23,21,32,255},line{56,48,70,255},gold{222,185,119,255},purple{150,108,220,255},white{236,231,241,255},muted{162,151,177,255};
void tooltip(CView* v,const char* text){v->setAttribute(kCViewTooltipAttribute,uint32_t(std::strlen(text)+1),text);}
void font(CParamDisplay* v,double size=13){auto* f=new CFontDesc("Segoe UI",size);v->setFont(f);f->forget();v->setBackColor(panel);v->setFontColor(white);v->setFrameColor(line);}
class Field final: public CView {
public:
    explicit Field(const CRect& r):CView(r){setMouseEnabled(false);}
    double morph=0,energy=.5,motion=.25,peak=0;int voices=0,note=-1;double velocity=0;
    void draw(CDrawContext* c) override {
        const auto r=getViewSize();const double cx=r.getCenter().x,cy=r.getCenter().y;
        c->setDrawMode(kAntiAliasing);c->setFillColor(ink);c->drawRect(r,kDrawFilled);
        for(int ring=0;ring<3;++ring){c->setFrameColor(ring==1?purple:line);c->setLineWidth(ring==1?1.5:1);
            CPoint previous;for(int n=0;n<=96;++n){const double t=2*omega::dsp::pi*n/96.;const double radius=33+ring*20+9*energy*std::sin(t*(3+morph*4))+peak*18;CPoint point(cx+radius*std::cos(t),cy+radius*.60*std::sin(t));if(n)c->drawLine(previous,point);previous=point;}}
        c->setFrameColor(gold);c->setLineWidth(2);c->drawLine({r.left+16,r.bottom-14},{r.left+16+std::clamp(peak,0.,1.)*(r.getWidth()-32),r.bottom-14});
        setDirty(false);
    }
};
class Editor final: public Steinberg::Vst::VSTGUIEditor, public IControlListener {
    Controller* model;
    std::array<CControl*,15> controls{};
    std::array<CTextEdit*,15> textValues{};
    std::array<bool,15> gestures{};
    std::vector<CView*> advanced;
    std::vector<omega::Preset> bank;
    COptionMenu* patches=nullptr;
    CTextEdit* patchName=nullptr;
    CTextLabel* status=nullptr;
    CTextLabel* monitor=nullptr;
    CTextLabel* identity=nullptr;
    Field* field=nullptr;
    bool advancedVisible=false;
    bool refreshing=false;
    omega::Preset currentPatch;
    void showAdvanced(bool visible){
        advancedVisible=visible;
        for(auto* v:advanced)v->setVisible(visible);
        for(size_t i=1;i<=5;++i){controls[i]->setVisible(!visible);textValues[i]->setVisible(!visible);}
        for(int32_t k=0;k<frame->getNbViews();++k){auto* v=frame->getView(k);const auto r=v->getViewSize();
            if(r.top>=313&&r.bottom<=505&&std::find(advanced.begin(),advanced.end(),v)==advanced.end())v->setVisible(!visible);}
        frame->invalid();
    }
    void selectSector(int sector){
        static constexpr size_t focus[]={0,1,3,6,1,13,4};
        static constexpr const char* descriptions[]={
            "DNA / Morph changes the structure of one voice across five identities.",
            "EXCITE / Energy shapes harmonic brightness, drive and strike intensity.",
            "BODY / Material shapes inharmonic modes and noise excitation.",
            "LIFE / Attack, release, glide, voices and legato control note articulation.",
            "CONTOUR / Energy shapes the stable lowpass and calibrated Eco/HQ drive.",
            "MOTION / Tempo Sync and Motion Rate control shared rhythmic modulation.",
            "SPACE / Space controls the single global stereo room; Output sets final gain."
        };
        if(sector<0||sector>6)return;
        showAdvanced(sector==3||sector==5);
        frame->setFocusView(controls[focus[sector]]);
        status->setText(descriptions[sector]);
    }
    CTextLabel* label(CRect r,const char* text,double size=13,CColor color=muted){auto* v=new CTextLabel(r,text);font(v,size);v->setBackColor(ink);v->setFrameColor(ink);v->setFontColor(color);v->setHoriAlign(kLeftText);v->setMouseEnabled(false);frame->addView(v);return v;}
    CTextButton* button(CRect r,const char* text,int tag){auto* b=new CTextButton(r,this,tag,text);b->setTextColor(white);b->setTextColorHighlighted(gold);b->setFrameColor(line);b->setRoundRadius(5);auto g=VSTGUI::owned(CGradient::create(0,1,panel,panel));b->setGradient(g);auto h=VSTGUI::owned(CGradient::create(0,1,line,panel));b->setGradientHighlighted(h);tooltip(b,text);frame->addView(b);return b;}
    void textValue(size_t i,CRect r){auto* v=new CTextEdit(r,this,int32_t(200+i),"");font(v,12);tooltip(v,"Type an exact physical value, then press Enter. Escape cancels.");frame->addView(v);textValues[i]=v;}
    void addParameter(size_t i,CRect r,bool knob=false){const auto& def=omega::parameterDefinitions[i];
        CControl* control=nullptr;
        if(def.steps){auto* menu=new COptionMenu(r,this,int32_t(def.id));font(menu);for(int n=0;n<=def.steps;++n){char text[64]{};UString(const_cast<char16*>(def.choices[n]),64).toAscii(text,64);menu->addEntry(text);}control=menu;}
        else if(knob){auto* k=new CKnob(r,this,int32_t(def.id),nullptr,nullptr);k->setDrawStyle(CKnob::kCoronaDrawing|CKnob::kCoronaOutline);k->setCoronaColor(purple);k->setColorHandle(gold);k->setColorShadowHandle(panel);k->setCoronaInset(4);k->setHandleLineWidth(3);k->setZoomFactor(12);control=k;}
        else{auto* s=new CSlider(r,this,int32_t(def.id),0,int32_t(r.getWidth()),nullptr,nullptr);s->setDrawStyle(CSlider::kDrawBack|CSlider::kDrawFrame|CSlider::kDrawValue);s->setBackColor(panel);s->setFrameColor(line);s->setValueColor(i==0?gold:purple);s->setZoomFactor(12);control=s;}
        control->setDefaultValue(float(def.initial));control->setValueNormalized(float(model->getParamNormalized(def.id)));control->setWantsFocus(true);tooltip(control,def.key);frame->addView(control);controls[i]=control;
    }
    void edit(size_t i,double value){const auto id=omega::parameterDefinitions[i].id;const bool transient=!gestures[i];if(transient)model->beginEdit(id);model->setParamNormalized(id,value);model->performEdit(id,value);if(transient)model->endEdit(id);}
    omega::ParameterValues values() const {auto result=omega::defaults();for(size_t i=0;i<result.size();++i)result[i]=model->getParamNormalized(omega::parameterDefinitions[i].id);return result;}
    void load(const omega::Preset& p){for(size_t i=0;i<p.params.size();++i)edit(i,p.params[i]);currentPatch=p;patchName->setText(p.name.c_str());status->setText("Patch loaded. Host automation retains control during playback.");refresh();}
    void refresh(){if(!frame)return;refreshing=true;
        const auto params=values();for(size_t i=0;i<params.size();++i){if(!gestures[i]&&controls[i]&&std::abs(controls[i]->getValueNormalized()-params[i])>1e-6){controls[i]->setValueNormalized(float(params[i]));controls[i]->invalid();}
            if(textValues[i]&&frame->getFocusView()!=textValues[i]){Steinberg::Vst::String128 text{};model->getParamStringByValue(omega::parameterDefinitions[i].id,params[i],text);char ascii[128]{};UString(text,128).toAscii(ascii,128);textValues[i]->setText(ascii);}}
        int match=-1;for(size_t k=0;k<bank.size();++k){bool equal=true;for(size_t i=0;i<params.size();++i)equal=equal&&std::abs(params[i]-bank[k].params[i])<1e-7;if(equal){match=int(k);break;}}
        patches->setValue(float(match+1));patches->invalid();
        field->morph=params[0];field->energy=params[1];field->motion=params[2];field->peak=model->getParamNormalized(1010);field->voices=int(std::round(model->getParamNormalized(1011)*32));field->note=int(std::round(model->getParamNormalized(1012)*128))-1;field->velocity=model->getParamNormalized(1013);field->invalid();
        char meter[180]{};std::snprintf(meter,sizeof(meter),"OUTPUT %.1f dBFS    /    %d VOICES    /    LAST NOTE %d    /    VELOCITY %.0f%%",20*std::log10(std::max(1e-6,field->peak)),field->voices,field->note,field->velocity*100);monitor->setText(meter);
        const char* names[]={"BASS / fundamental body","BELLS / struck inharmonic modes","LEAD / harmonic edge","SYNTH / evolving spectrum","PERC / tuned noise and impact"};identity->setText(names[std::min(4,int(std::round(params[0]*4)))]);refreshing=false;
    }
    void file(bool save){Steinberg::IPtr<Steinberg::IPlugView> keepAlive(static_cast<Steinberg::IPlugView*>(this));auto selector=VSTGUI::owned(CNewFileSelector::create(frame,save?CNewFileSelector::kSelectSaveFile:CNewFileSelector::kSelectFile));if(!selector){status->setText("File dialog unavailable in this host.");return;}
        selector->setTitle(save?"Save Organism JSON Patch":"Load Organism JSON Patch");selector->setDefaultExtension(CFileExtension("Organism JSON Patch","json","application/json"));selector->setDefaultSaveName("Organism-Patch.json");
        if(!selector->runModal()||!selector->getNumSelectedFiles()||!frame||!status||!patchName)return;
        const auto path=std::filesystem::u8path(selector->getSelectedFile(0));
        try{if(save){auto patch=currentPatch;patch.params=values();patch.name=patchName->getText().getString();if(patch.name.empty())patch.name="Untitled";std::string error;omega::Preset checked;auto document=omega::exportPreset(patch);if(!omega::parsePreset(document,checked,error)){status->setText(error.c_str());return;}std::ofstream out(path,std::ios::binary);out<<document;out.close();status->setText(out?"JSON patch saved.":"Patch could not be written.");}
            else{if(std::filesystem::file_size(path)>65536){status->setText("Patch exceeds 64 KiB.");return;}std::ifstream in(path,std::ios::binary);if(!in){status->setText("Patch could not be read.");return;}const std::string document((std::istreambuf_iterator<char>(in)),{});omega::Preset patch;std::string error;if(!omega::parsePreset(document,patch,error)){status->setText(error.c_str());return;}load(patch);}}
        catch(const std::exception&){status->setText("File operation failed. Current sound is preserved.");}
    }
public:
    explicit Editor(Controller* c):VSTGUIEditor(c),model(c){ViewRect r(0,0,1040,620);setRect(r);setIdleRate(50);for(auto* doc:omega::factoryDocuments){omega::Preset p;std::string error;if(omega::parsePreset(doc,p,error))bank.push_back(std::move(p));}}
    ~Editor() override {close();}
    bool PLUGIN_API open(void* parent,const PlatformType& type) override {
        if(frame)return false;frame=new CFrame(CRect(0,0,1040,620),this);frame->setBackgroundColor(ink);frame->enableTooltips(true);frame->setFocusDrawingEnabled(true);frame->setFocusColor(gold);
        label({32,17,520,35},"OMEGA HOUSE  /  OFFLINE INSTRUMENT",11,gold);
        label({30,36,530,76},"SONIC ORGANISM",29,white);
        patchName=new CTextEdit({560,22,822,48},this,320,"Session Patch");font(patchName);tooltip(patchName,"Name used when exporting your JSON patch.");frame->addView(patchName);
        patches=new COptionMenu({560,54,822,83},this,300);font(patches);patches->addEntry("Session / Modified");for(const auto& p:bank)patches->addEntry(p.name.c_str());tooltip(patches,"30 factory patches. Selection edits the existing host parameters.");frame->addView(patches);
        button({837,22,914,49},"LOAD",301);button({925,22,1006,49},"SAVE",302);button({837,55,1006,83},"ADVANCED",303);
        const char* sectors[]={"01 DNA","02 EXCITE","03 BODY","04 LIFE","05 CONTOUR","06 MOTION","07 SPACE"};
        for(int i=0;i<7;++i)button({32.+i*140,98,164.+i*140,126},sectors[i],400+i);
        field=new Field({670,129,1006,290});frame->addView(field);
        const char* anchors[]={"BASS","BELLS","LEAD","SYNTH","PERC"};for(int i=0;i<5;++i)button({32.+i*126,140,141.+i*126,171},anchors[i],310+i);
        addParameter(0,{32,193,642,220});textValue(0,{545,237,642,262});
        identity=label({32,235,530,261},"BASS / fundamental body",17,white);
        label({32,272,640,293},"Drag to evolve a held note. Shift-drag for fine control. Ctrl-click resets.",12,muted);
        const char* macroNames[]={"ENERGY","MOTION","MATERIAL","SPACE"};const char* hints[]={"Drive / brightness / impact","Profile-specific modulation","Body / inharmonicity / noise","Dry to stereo ambience"};
        for(int i=0;i<4;++i){const double x=32+i*164;label({x,313,x+150,337},macroNames[i],14,gold);addParameter(size_t(i+1),{x+24,347,x+124,447},true);textValue(size_t(i+1),{x+24,452,x+124,476});label({x,482,x+158,505},hints[i],11,muted);}
        label({710,316,1006,339},"OUTPUT / HEADROOM",14,gold);addParameter(5,{710,355,1006,379});textValue(5,{838,389,1006,415});label({710,438,1006,461},"15 samples latency / Eco + HQ",12,muted);label({710,464,1006,487},"No samples. No login. No network.",12,muted);
        const char* advNames[]={"ATTACK SCALE","RELEASE SCALE","GLIDE ms","VOICES","QUALITY","BEND RANGE","TEMPO SYNC","MOTION RATE","MONO LEGATO"};
        // Advanced controls occupy a separate page; macro controls stay available through the host.
        for(size_t i=6;i<15;++i){const size_t n=i-6;double x=32+double(n%3)*326,y=316+double(n/3)*65;const auto before=frame->getNbViews();label({x,y,x+150,y+20},advNames[n],11,gold);addParameter(i,{x+155,y,x+300,y+23});if(!omega::parameterDefinitions[i].steps)textValue(i,{x+155,y+26,x+300,y+49});for(int32_t k=before;k<frame->getNbViews();++k){auto* v=frame->getView(k);v->setVisible(false);advanced.push_back(v);}}
        monitor=label({32,526,1006,550},"Waiting for host output meters",12,gold);status=label({32,557,1006,580},"Ready. Play MIDI notes in your host. All sound generation stays local.",12,muted);label({32,589,1006,610},"OMEGA SONIC ORGANISM  " OSO_PRODUCT_VERSION "     /     WINDOWS x64 VST3     /     TAB: FOCUS   ARROWS: ADJUST",10,muted);
        refresh();if(!frame->open(parent,type)){close();return false;}return true;
    }
    void PLUGIN_API close() override {for(size_t i=0;i<gestures.size();++i)if(gestures[i]){model->endEdit(omega::parameterDefinitions[i].id);gestures[i]=false;}if(frame){frame->close();frame=nullptr;}controls.fill(nullptr);textValues.fill(nullptr);advanced.clear();patches=nullptr;patchName=nullptr;field=nullptr;status=nullptr;monitor=nullptr;identity=nullptr;advancedVisible=false;gestures.fill(false);}
    VSTGUI_INT32 getKnobMode() const override {return kLinearMode;}
    tresult PLUGIN_API canResize() override {return kResultTrue;}
    tresult PLUGIN_API checkSizeConstraint(ViewRect* r) override {if(!r)return kInvalidArgument;const double scale=std::clamp(double(r->right-r->left)/1040.,.8,1.5);r->right=r->left+int32(std::round(1040*scale));r->bottom=r->top+int32(std::round(620*scale));return kResultTrue;}
    tresult PLUGIN_API onSize(ViewRect* r) override {if(!r)return kInvalidArgument;if(frame)frame->setZoom(double(r->right-r->left)/1040.);return Steinberg::Vst::EditorView::onSize(r);}
    CMessageResult notify(VSTGUI::CBaseObject* sender,const char* message) override {if(message==CVSTGUITimer::kMsgTimer)refresh();return VSTGUIEditor::notify(sender,message);}
    void valueChanged(CControl* c) override {if(refreshing)return;int tag=c->getTag();if(tag>=100&&tag<=114){edit(size_t(tag-100),c->getValueNormalized());return;}
        if(tag>=200&&tag<=214){size_t i=size_t(tag-200);Steinberg::Vst::String128 text{};UString(text,128).fromAscii(textValues[i]->getText().getString().c_str());double n=0;if(model->getParamValueByString(omega::parameterDefinitions[i].id,text,n)==kResultTrue&&std::isfinite(n)&&n>=0&&n<=1)edit(i,n);else status->setText("Invalid value. Use the displayed physical units and range.");refresh();return;}
        if(tag==300){const int index=int(std::round(c->getValue()))-1;if(index>=0&&size_t(index)<bank.size())load(bank[size_t(index)]);return;}if(c->getValue()<.5)return;
        if(tag==301||tag==302){file(tag==302);return;}if(tag>=310&&tag<=314){edit(0,(tag-310)*.25);refresh();return;}
        if(tag==303){showAdvanced(!advancedVisible);return;}
        if(tag>=400&&tag<=406){selectSector(tag-400);return;}
    }
    void controlBeginEdit(CControl* c) override {const int i=omega::parameterIndex(uint32_t(c->getTag()));if(i>=0){gestures[size_t(i)]=true;model->beginEdit(c->getTag());}}
    void controlEndEdit(CControl* c) override {const int i=omega::parameterIndex(uint32_t(c->getTag()));if(i>=0&&gestures[size_t(i)]){model->endEdit(c->getTag());gestures[size_t(i)]=false;}}
};
}
Steinberg::IPlugView* createOrganismEditor(Controller* c){return new Editor(c);}
}

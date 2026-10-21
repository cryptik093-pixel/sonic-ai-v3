#include "PluginProcessor.h"
#include "PluginEditor.h"
#include <set>
#include <stdexcept>
static_assert(std::atomic<const DrumProcessor::Snapshot*>::is_always_lock_free);
namespace {
constexpr size_t slotFields=11;
void require(bool condition,const char* message){if(!condition)throw std::runtime_error(message);}
juce::var object(){return juce::var(new juce::DynamicObject);}
void put(juce::var& v,const char* key,const juce::var& value){v.getDynamicObject()->setProperty(key,value);}
bool number(const juce::var& v){return v.isInt()||v.isInt64()||v.isDouble();}
juce::var document(const void* bytes,size_t length){
    require(bytes&&length>0&&length<=65536,"Kit JSON exceeds the 64 KiB limit.");const auto* data=static_cast<const char*>(bytes);int depth=0;bool quoted=false,escaped=false;
    for(size_t i=0;i<length;++i){const char c=data[i];require(c!=0,"Embedded NUL in kit JSON.");if(quoted){if(escaped)escaped=false;else if(c=='\\')escaped=true;else if(c=='\"')quoted=false;}else if(c=='\"')quoted=true;else if(c=='{'||c=='['){require(++depth<=12,"Kit JSON nesting limit exceeded.");}else if(c=='}'||c==']')require(--depth>=0,"Invalid kit JSON brackets.");}
    require(!quoted&&depth==0,"Incomplete kit JSON.");return juce::JSON::parse(juce::String::fromUTF8(data,static_cast<int>(length)));
}
juce::MemoryBlock boundedKit(const juce::File& file){
    constexpr int64_t maximum=256ll*1024*1024;juce::FileInputStream stream(file);require(stream.openedOk()&&stream.getTotalLength()>0&&stream.getTotalLength()<=maximum,"Kit is missing, empty or too large.");juce::MemoryBlock block;stream.readIntoMemoryBlock(block,maximum+1);require(block.getSize()<=static_cast<size_t>(maximum),"Kit grew beyond its input limit.");return block;
}
}
juce::String DrumProcessor::slotId(int slot,const char* field){return "s"+juce::String(slot)+"_"+field;}
const std::vector<DrumProcessor::Spec>& DrumProcessor::specs(){
    static const auto result=[] {
        std::vector<Spec> r{{"department","Drum",0,6,0,true},{"body","BODY",0,1,.5f},{"character","CHARACTER",0,1,.5f},{"space","SPACE",0,1,.25f}};
        const std::array<Spec,slotFields> fields{{{"tune","Tune (st)",-24,24,0},{"gain","Gain (dB)",-60,12,-6},{"pan","Pan",-1,1,0},{"start","Start",0,.999f,0},{"end","End",.001f,1,1},{"attack","Attack (ms)",0,500,0},{"release","Release (ms)",0,3000,30},{"filter","Low-pass (Hz)",40,20000,20000},{"reverse","Reverse",0,1,0,true},{"mute","Mute",0,1,0,true},{"solo","Solo",0,1,0,true}}};
        for(int s=0;s<7;++s)for(auto f:fields){f.id=slotId(s,f.id.toRawUTF8());f.name=juce::String(ohdrum::slotNames[static_cast<size_t>(s)])+" "+f.name;r.push_back(f);}
        r.push_back({"output","Output (dB)",-36,6,-6});
        for(auto f:fields){f.id=slotId(7,f.id.toRawUTF8());f.name="Open Hat "+f.name;r.push_back(f);}
        const std::array<Spec,11> synthesis{{{"punch","Punch",0,1,.5f},{"tone","Tone",0,1,.5f},{"texture","Character",0,1,.5f},{"decay","Decay scale",.1f,3,1},{"pitchdepth","Pitch envelope depth",0,2,1},{"pitchtime","Pitch envelope (ms)",2,200,28.5f},{"blend","Sample blend",0,1,0},{"samplelevel","Sample level (dB)",-60,12,0},{"note","MIDI note",0,127,36,true},{"choke","Choke group",0,8,0,true},{"veltone","Velocity tone",0,1,0}}};
        for(int slot=0;slot<8;++slot)for(auto f:synthesis){const auto field=f.id;if(field=="note")f.value=static_cast<float>(ohdrum::defaultNotes[static_cast<size_t>(slot)]);if(field=="choke"&&(slot==2||slot==7))f.value=1;f.id=slotId(slot,field.toRawUTF8());f.name=juce::String(ohdrum::slotNames[static_cast<size_t>(slot)])+" "+f.name;r.push_back(f);}
        r[0].max=7;return r;
    }();return result;
}
juce::AudioProcessorValueTreeState::ParameterLayout DrumProcessor::layout(){
    juce::AudioProcessorValueTreeState::ParameterLayout r;
    r.add(std::make_unique<juce::AudioParameterChoice>(juce::ParameterID{"department",1},"Department",juce::StringArray{"Kick","Snare","Closed Hat","Cymbal","Tom","Percussion","Clap","Open Hat"},0));
    const auto& definitions=specs();for(size_t i=1;i<definitions.size();++i){const auto& s=definitions[i];juce::NormalisableRange<float> range(s.min,s.max,s.discrete?1.0f:0.0f);
        if(s.id.endsWith("filter"))range.setSkewForCentre(2500);
        r.add(std::make_unique<juce::AudioParameterFloat>(juce::ParameterID{s.id,1},s.name,range,s.value));}return r;
}
DrumProcessor::DrumProcessor(const juce::File& storageOverride):AudioProcessor(BusesProperties().withOutput("Drums",juce::AudioChannelSet::stereo(),true)),parameters(*this,nullptr,"DrumSupply",layout()),library(storageOverride){
    raw.resize(specs().size());for(size_t i=0;i<raw.size();++i)raw[i]=parameters.getRawParameterValue(specs()[i].id);
    constexpr std::array<const char*,22> fields{"tune","gain","pan","start","end","attack","release","filter","reverse","mute","solo","punch","tone","texture","decay","pitchdepth","pitchtime","blend","samplelevel","note","choke","veltone"};
    for(int slot=0;slot<8;++slot)for(size_t i=0;i<fields.size();++i)slotRaw[static_cast<size_t>(slot)][i]=parameters.getRawParameterValue(slotId(slot,fields[i]));
    savedValues=capture();worker=std::thread([this]{work();});resetKit();waitIdle();setLatencySamples(0);
}
DrumProcessor::~DrumProcessor(){cancelRender.store(true); {std::lock_guard lock(control);stopping=true;jobs.clear();}wake.notify_one();if(worker.joinable())worker.join();}
bool DrumProcessor::submit(std::function<void()> job,bool stateRequest){
    {std::lock_guard lock(control);if(stopping||(!stateRequest&&running)||!jobs.empty()){status="Busy: wait for the current operation";return false;}jobs.push_back(std::move(job));status="Working...";}
    wake.notify_one();return true;
}
void DrumProcessor::work(){
    for(;;){std::function<void()> job;{std::unique_lock lock(control);wake.wait(lock,[this]{return stopping||!jobs.empty();});if(stopping)return;running=true;job=std::move(jobs.front());jobs.pop_front();}
        try{collect();job();}catch(const std::exception& error){std::lock_guard lock(control);status=juce::String("Failed: ")+error.what();}
        {std::lock_guard lock(control);running=false;}idle.notify_all();}
}
bool DrumProcessor::waitIdle(int milliseconds){std::unique_lock lock(control);return idle.wait_for(lock,std::chrono::milliseconds(milliseconds),[this]{return !running&&jobs.empty();});}
std::vector<float> DrumProcessor::capture() const {std::vector<float> values;values.reserve(raw.size());for(auto* r:raw)values.push_back(r->load());return values;}
void DrumProcessor::apply(const std::vector<float>& values){for(size_t i=0;i<raw.size();++i){auto* p=parameters.getParameter(specs()[i].id);p->setValueNotifyingHost(p->convertTo0to1(values[i]));}}
void DrumProcessor::collect(){std::lock_guard lock(control);const auto* protectedPointer=hazard.load();const auto* currentPointer=published.load();
    retained.erase(std::remove_if(retained.begin(),retained.end(),[&](const auto& p){return p.get()!=protectedPointer&&p.get()!=currentPointer;}),retained.end());}
void DrumProcessor::publish(std::shared_ptr<Snapshot> snapshot){retained.push_back(snapshot);published.store(snapshot.get());}
bool DrumProcessor::resetKit(const juce::String& name){return submit([this,name]{rawComparison.store(false);auto snapshot=std::make_shared<Snapshot>();for(int s=0;s<8;++s)snapshot->assets[static_cast<size_t>(s)]=library.factory(s==7?2:s);
    std::vector<float> values;for(const auto& s:specs())values.push_back(s.value);apply(values);
    std::lock_guard lock(control);banks={Bank{snapshot,values,name},Bank{snapshot,values,name}};active=0;savedValues=values;edited=false;status="Starter kit loaded | Synthesis kit | optional samples muted";publish(snapshot);});}
bool DrumProcessor::loadSample(int slot,const juce::File& file){if(slot<0||slot>7)return false;return submit([this,slot,file]{const auto started=std::chrono::steady_clock::now();{std::lock_guard lock(control);status="Loading "+juce::String(ohdrum::slotNames[static_cast<size_t>(slot)])+"...";}auto asset=library.load(file);
    std::lock_guard lock(control);auto snapshot=std::make_shared<Snapshot>(*banks[static_cast<size_t>(active)].snapshot);snapshot->assets[static_cast<size_t>(slot)]=std::move(asset);
    banks[static_cast<size_t>(active)].snapshot=snapshot;edited=true;++editRevision;status="Loaded "+file.getFileName()+" / "+juce::String(std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-started).count(),1)+" ms";publish(snapshot);});}
bool DrumProcessor::switchAB(){return submit([this]{rawComparison.store(false);Bank next;{std::lock_guard lock(control);banks[static_cast<size_t>(active)].values=capture();active=1-active;next=banks[static_cast<size_t>(active)];}
    apply(next.values);std::lock_guard lock(control);edited=true;++editRevision;status=active==0?"Comparison A":"Comparison B";publish(next.snapshot);});}
void DrumProcessor::renameKit(const juce::String& text){std::lock_guard lock(control);const auto name=text.trim().substring(0,80);if(name.isEmpty()){status="Kit name cannot be empty";return;}banks[static_cast<size_t>(active)].name=name;edited=true;++editRevision;}
DrumProcessor::View DrumProcessor::view() const {std::lock_guard lock(control);const auto& bank=banks[static_cast<size_t>(active)];return {bank.snapshot,bank.name,status,running||!jobs.empty(),edited||capture()!=savedValues,active,library.memoryUsed()};}
bool DrumProcessor::isBusesLayoutSupported(const BusesLayout& b) const {return b.inputBuses.isEmpty()&&b.outputBuses.size()==1&&(b.getMainOutputChannelSet()==juce::AudioChannelSet::mono()||b.getMainOutputChannelSet()==juce::AudioChannelSet::stereo());}
void DrumProcessor::syncControls() noexcept {
    std::array<ohdrum::SlotControls,8> controls{};
    for(size_t s=0;s<8;++s){const auto& p=slotRaw[s];controls[s]={p[0]->load(),p[1]->load(),p[2]->load(),p[3]->load(),p[4]->load(),p[5]->load(),p[6]->load(),p[7]->load(),p[8]->load(),p[9]->load(),p[10]->load(),p[11]->load(),p[12]->load(),p[13]->load(),p[14]->load(),p[15]->load(),p[16]->load(),p[17]->load(),p[18]->load(),p[19]->load(),p[20]->load(),p[21]->load()};}
    const bool rawMode=rawComparison.load();if(rawMode)controls=ohdrum::factoryControls(0);
    engine.setSlotControls(controls,raw[81]->load());engine.setMacros(rawMode?ohdrum::Macros{.5f,.5f,.25f}:ohdrum::Macros{raw[1]->load(),raw[2]->load(),raw[3]->load()});
    if(rawMode!=lastRaw){engine.snapControls();lastRaw=rawMode;}
}
void DrumProcessor::prepareToPlay(double rate,int){lastRaw=rawComparison.load();syncControls();engine.prepare(rate,lastRaw?ohdrum::Macros{.5f,.5f,.25f}:ohdrum::Macros{raw[1]->load(),raw[2]->load(),raw[3]->load()});reset();}
void DrumProcessor::reset(){engine.reset();preview.store(-1);panic.store(false);peak.store(0);clipped.store(false);meterFrame.fetch_add(1);}
void DrumProcessor::processBlock(juce::AudioBuffer<float>& audio,juce::MidiBuffer& midi){
    juce::ScopedNoDenormals noDenormals;audio.clear();
    const Snapshot* next=nullptr;bool reacquired=false;
    // Bounded hazard-pointer acquisition. Reclamation and buffer destruction run only on the worker.
    for(int attempt=0;attempt<3;++attempt){next=published.load();hazard.store(next);if(next==published.load())break;next=nullptr;reacquired=true;}
    if(!next){hazard.store(nullptr);if(audioSnapshot){engine.replace({});audioSnapshot=nullptr;}}
    else if(reacquired||next!=audioSnapshot){std::array<const ohsample::Sample*,8> samples{};for(size_t s=0;s<8;++s)samples[s]=next->assets[s].sample.get();engine.replace(samples);audioSnapshot=next;}
    syncControls();
    if(panic.exchange(false))engine.panic();
    const float department=raw[0]->load();const int category=std::isfinite(department)?static_cast<int>(std::clamp(department,0.0f,7.0f)):0;const int clicked=preview.exchange(-1);if(clicked>=0&&clicked<8){engine.triggerSlot(clicked,.8f);activity[static_cast<size_t>(clicked)].fetch_add(1);}
    auto event=midi.cbegin();const auto end=midi.cend();float level=0;
    for(int i=0;i<audio.getNumSamples();++i){while(event!=end&&(*event).samplePosition<=i){const auto message=*event;const auto* bytes=message.data;
        if(message.numBytes==3&&(bytes[0]&0xf0)==0x90&&bytes[1]<128&&bytes[2]>0&&bytes[2]<128){bool assigned=false;for(size_t slot=0;slot<8;++slot)if(slotRaw[slot][19]->load()==static_cast<float>(bytes[1])){engine.triggerSlot(static_cast<int>(slot),static_cast<float>(bytes[2])/127,bytes[1]);activity[slot].fetch_add(1);assigned=true;}if(!assigned&&bytes[1]==60){engine.triggerSlot(category,static_cast<float>(bytes[2])/127,bytes[1]);activity[static_cast<size_t>(category)].fetch_add(1);}}
        else if(message.numBytes==3&&(bytes[0]&0xf0)==0xb0&&(bytes[1]==120||bytes[1]==123))engine.panic(bytes[1]==120);
        ++event;}
        const auto out=engine.tick();if(engine.clipped())clipped.store(true);const float left=audio.getNumChannels()==1?(out[0]+out[1])*.5f:out[0];
        if(audio.getNumChannels()>0)audio.setSample(0,i,left);if(audio.getNumChannels()>1)audio.setSample(1,i,out[1]);
        level=std::max(level,std::abs(left));if(audio.getNumChannels()>1)level=std::max(level,std::abs(out[1]));}
    midi.clear();peak.store(std::max(level,peak.load(std::memory_order_relaxed)),std::memory_order_relaxed);if(level>=1)clipped.store(true);meterFrame.fetch_add(1,std::memory_order_release);
}
juce::var DrumProcessor::stateObject() const {
    std::lock_guard lock(control);auto state=object();put(state,"version",3);put(state,"active",active);juce::Array<juce::var> comparisons;
    for(int b=0;b<2;++b){const auto& bank=banks[static_cast<size_t>(b)];auto item=object();put(item,"name",bank.name);
        auto values=object();const auto numbers=b==active?capture():bank.values;for(size_t i=0;i<specs().size();++i)values.getDynamicObject()->setProperty(specs()[i].id,numbers[i]);put(item,"parameters",values);
        juce::Array<juce::var> assets;for(const auto& a:bank.snapshot->assets){auto entry=object();put(entry,"ref",a.reference);put(entry,"name",a.name);assets.add(entry);}put(item,"samples",assets);comparisons.add(item);}
    put(state,"banks",comparisons);return state;
}
void DrumProcessor::getStateInformation(juce::MemoryBlock& dest){const auto text=juce::JSON::toString(stateObject(),true);dest.replaceAll(text.toRawUTF8(),static_cast<size_t>(text.getNumBytesAsUTF8()));}
bool DrumProcessor::decodeState(const juce::var& state,std::array<Bank,2>& result,int& selected,juce::String& message){
    require(state.isObject()&&number(state["version"]),"Invalid kit state.");const double versionNumber=state["version"];require(std::isfinite(versionNumber)&&versionNumber>=1&&versionNumber<=3&&std::floor(versionNumber)==versionNumber,"Invalid state version.");const int version=static_cast<int>(versionNumber);
    if(version==1){require(state.getDynamicObject()->getProperties().size()==5,"Invalid legacy state.");std::vector<float> values;for(const auto& s:specs())values.push_back(s.value);
        for(size_t i=0;i<4;++i){const auto v=state[juce::Identifier(specs()[i].id)];require(number(v),"Invalid legacy parameter.");const double n=v;require(std::isfinite(n)&&n>=specs()[i].min&&n<=specs()[i].max&&(!specs()[i].discrete||std::floor(n)==n),"Legacy parameter out of range.");values[i]=static_cast<float>(n);}
        auto snapshot=std::make_shared<Snapshot>();for(int s=0;s<8;++s)snapshot->assets[static_cast<size_t>(s)]=library.factory(s==7?2:s);
        result={Bank{snapshot,values,"Migrated legacy kit"},Bank{snapshot,values,"Migrated legacy kit"}};selected=0;message="Legacy global controls migrated; per-slot defaults use original synthesis maps. Exact 0.1.0 sessions require the preserved legacy build";return true;}
    require(version==3&&state.getDynamicObject()->getProperties().size()==3,"Unsupported or malformed state version.");
    require(number(state["active"])&&(static_cast<double>(state["active"])==0||static_cast<double>(state["active"])==1),"Invalid A/B selection.");selected=state["active"];
    auto* array=state["banks"].getArray();require(array&&array->size()==2,"Two comparison banks are required.");
    // Validate both banks completely before any decode, parameter change or publication.
    for(int b=0;b<2;++b){const auto& item=(*array)[b];require(item.isObject()&&item.getDynamicObject()->getProperties().size()==3&&item["name"].isString()&&item["name"].toString().length()<=80,"Invalid kit name/schema.");
        const auto params=item["parameters"];require(params.isObject()&&params.getDynamicObject()->getProperties().size()==static_cast<int>(specs().size()),"Invalid parameter count.");auto& bank=result[static_cast<size_t>(b)];bank.name=item["name"].toString();
        for(const auto& s:specs()){const auto v=params[juce::Identifier(s.id)];require(number(v),"Invalid parameter type.");const double n=v;require(std::isfinite(n)&&n>=s.min-1.e-6&&n<=s.max+1.e-6&&(!s.discrete||std::floor(n)==n),"Parameter outside supported range.");bank.values.push_back(static_cast<float>(n));}
        const auto* assets=item["samples"].getArray();require(assets&&assets->size()==8,"Eight sample assignments required.");bank.snapshot=std::make_shared<Snapshot>();
        for(int s=0;s<8;++s){const auto& a=(*assets)[s];require(a.isObject()&&a.getDynamicObject()->getProperties().size()==2&&a["ref"].isString()&&a["name"].isString()&&a["name"].toString().length()<=255&&SampleLibrary::validReference(a["ref"].toString()),"Invalid sample reference/name.");
            bank.snapshot->assets[static_cast<size_t>(s)]={nullptr,a["ref"].toString(),a["name"].toString(),false};}}
    bool missing=false;
    for(auto& bank:result)for(auto& asset:bank.snapshot->assets){asset=library.resolve(asset.reference,asset.name);missing=missing||asset.missing;}
    message=missing?"Missing samples: select each missing slot and Load / Relink Sample":"Kit recalled";return true;
}
bool DrumProcessor::restoreState(const void* data,int size){
    if(!data||size<=0||size>65536)return false;
    juce::var state;try{state=document(data,static_cast<size_t>(size));}catch(const std::exception& e){std::lock_guard lock(control);status=juce::String("Failed: ")+e.what();return false;}
    auto success=std::make_shared<std::atomic<bool>>(false);
    cancelRender.store(true);
    if(!submit([this,state,success]{std::array<Bank,2> next;int selected=0;juce::String message;decodeState(state,next,selected,message);apply(next[static_cast<size_t>(selected)].values);
        rawComparison.store(false);std::lock_guard lock(control);banks=std::move(next);active=selected;savedValues=capture();edited=false;status=message;publish(banks[static_cast<size_t>(active)].snapshot);success->store(true);},true))return false;
    // JUCE host state callbacks are non-realtime control operations. All file/decode work stays on our worker.
    return waitIdle(30000)&&success->load();
}
void DrumProcessor::setStateInformation(const void* data,int size){(void)restoreState(data,size);}
bool DrumProcessor::saveKit(const juce::File& file,bool portable,bool rightsConfirmed){
    if(portable&&!rightsConfirmed){std::lock_guard lock(control);status="Confirm permission to redistribute every referenced sample before portable export";return false;}
    return submit([this,file,portable]{uint64_t revision=0;{std::lock_guard lock(control);revision=editRevision;}auto state=stateObject();const auto text=juce::JSON::toString(state,true);juce::MemoryOutputStream output;
        if(!portable)output.write(text.toRawUTF8(),static_cast<size_t>(text.getNumBytesAsUTF8()));
        else {output.write("DHKIT2\r\n",8);output.writeInt(static_cast<int>(text.getNumBytesAsUTF8()));output.write(text.toRawUTF8(),static_cast<size_t>(text.getNumBytesAsUTF8()));std::map<juce::String,SampleLibrary::Asset> assets;
            {std::lock_guard lock(control);for(const auto& bank:banks)for(const auto& a:bank.snapshot->assets)if(a.reference.length()==64)assets[a.reference]=a;}
            output.writeInt(static_cast<int>(assets.size()));for(const auto& [ref,asset]:assets){auto data=library.bytes(asset);require(output.getDataSize()+data.getSize()<256ull*1024*1024,"Portable kit exceeds 256 MiB.");output.write(ref.toRawUTF8(),64);output.writeInt64(static_cast<int64_t>(data.getSize()));output.write(data.getData(),data.getSize());}}
        juce::TemporaryFile temporary(file);require(temporary.getFile().replaceWithData(output.getData(),output.getDataSize())&&temporary.overwriteTargetFileWithTemporary(),"Could not save kit.");
        std::vector<float> writtenValues;const auto written=state["banks"][static_cast<int>(state["active"])]["parameters"];for(const auto& s:specs())writtenValues.push_back(static_cast<float>(written[juce::Identifier(s.id)]));
        std::lock_guard lock(control);savedValues=std::move(writtenValues);edited=editRevision!=revision;status=portable?"Portable kit exported":"Kit saved; managed samples must stay in local storage";});
}
bool DrumProcessor::loadKit(const juce::File& file){return submit([this,file]{
    auto block=boundedKit(file);
    juce::var state;
    if(block.getSize()>=8&&std::memcmp(block.getData(),"DHKIT2\r\n",8)==0){juce::MemoryInputStream stream(block,false);stream.skipNextBytes(8);const int length=stream.readInt();require(length>0&&length<=65536&&stream.getNumBytesRemaining()>=length+4,"Invalid portable manifest length.");
        juce::MemoryBlock json;require(stream.readIntoMemoryBlock(json,length)==static_cast<int64_t>(length),"Truncated manifest.");state=document(json.getData(),json.getSize());
        const int count=stream.readInt();require(count>=0&&count<=16,"Invalid asset count.");std::set<juce::String> seen;std::vector<std::pair<juce::String,juce::MemoryBlock>> blobs;
        for(int i=0;i<count;++i){require(stream.getNumBytesRemaining()>=72,"Truncated asset header.");char key[65]{};require(stream.read(key,64)==64,"Invalid asset key.");const juce::String ref=juce::String::fromUTF8(key,64);require(SampleLibrary::validReference(ref)&&ref.length()==64&&seen.insert(ref).second,"Invalid or duplicate asset key.");
            const auto bytes=stream.readInt64();require(bytes>0&&bytes<=static_cast<int64_t>(SampleLibrary::fileLimit)&&stream.getNumBytesRemaining()>=bytes,"Invalid asset size.");juce::MemoryBlock blob;require(stream.readIntoMemoryBlock(blob,static_cast<int64_t>(bytes))==bytes&&juce::SHA256(blob).toHexString()==ref,"Truncated asset or hash mismatch.");blobs.emplace_back(ref,std::move(blob));}
        require(stream.isExhausted(),"Unexpected trailing archive data.");
        // This format contains hash keys only: no filenames, links, paths, compression or extraction targets.
        // Cache writes are additive; current kit publication occurs only after every asset and state validates.
        for(const auto& [ref,blob]:blobs){juce::TemporaryFile temp(".wav");require(temp.getFile().replaceWithData(blob.getData(),blob.getSize()),"Cannot stage imported sample.");auto asset=library.load(temp.getFile());require(asset.reference==ref,"Imported sample changed.");}
    }else {require(block.getSize()<=65536,"Invalid kit format; ZIP imports are not supported.");state=document(block.getData(),block.getSize());}
    std::array<Bank,2> next;int selected=0;juce::String message;decodeState(state,next,selected,message);apply(next[static_cast<size_t>(selected)].values);
    rawComparison.store(false);std::lock_guard lock(control);banks=std::move(next);active=selected;savedValues=capture();edited=false;status=message;publish(banks[static_cast<size_t>(active)].snapshot);});}

namespace {
constexpr std::array<const char*,22> designFields{"tune","gain","pan","start","end","attack","release","filter","reverse","mute","solo","punch","tone","texture","decay","pitchdepth","pitchtime","blend","samplelevel","note","choke","veltone"};
std::array<float,22> designNumbers(const ohdrum::SlotControls& c){return {c.tune,c.gain,c.pan,c.start,c.end,c.attack,c.release,c.filter,c.reverse,c.mute,c.solo,c.punch,c.tone,c.texture,c.decay,c.pitchDepth,c.pitchTime,c.blend,c.sampleLevel,c.note,c.choke,c.velocityTone};}
size_t parameterIndex(const juce::String& id){const auto& specs=DrumProcessor::specs();const auto found=std::find_if(specs.begin(),specs.end(),[&](const auto& spec){return spec.id==id;});require(found!=specs.end(),"Unknown synthesis parameter.");return static_cast<size_t>(found-specs.begin());}
juce::var renderRecord(const RenderService::Result& rendered){auto item=object();put(item,"file",rendered.file.getFileName());put(item,"frames",static_cast<juce::int64>(rendered.frames));put(item,"sample_rate",rendered.rate);put(item,"channels",2);put(item,"bit_depth",24);put(item,"format","PCM");put(item,"peak",rendered.peak);put(item,"rms",rendered.rms);put(item,"tail_capped",rendered.truncated);put(item,"sha256",rendered.sha256);return item;}
}
std::vector<float> DrumProcessor::factoryValues(int profile){
 require(profile>=0&&profile<static_cast<int>(ohdrum::factoryNames.size()),"Unknown factory profile.");std::vector<float> values;for(const auto& spec:specs())values.push_back(spec.value);const auto controls=ohdrum::factoryControls(profile);
 for(int slot=0;slot<8;++slot){const auto numbers=designNumbers(controls[static_cast<size_t>(slot)]);for(size_t i=0;i<designFields.size();++i)values[parameterIndex(slotId(slot,designFields[i]))]=numbers[i];}
 values[parameterIndex("space")]=ohdrum::factorySpace(profile);values[parameterIndex("output")]=profile==5?-8.0f:-6.0f;return values;
}
bool DrumProcessor::loadFactoryKit(int profile){if(profile<0||profile>=static_cast<int>(ohdrum::factoryNames.size()))return false;return submit([this,profile]{auto snapshot=std::make_shared<Snapshot>();for(int slot=0;slot<8;++slot)snapshot->assets[static_cast<size_t>(slot)]=library.factory(slot==7?2:slot);auto values=factoryValues(profile);rawComparison.store(false);apply(values);const juce::String name(ohdrum::factoryNames[static_cast<size_t>(profile)]);
 std::lock_guard lock(control);banks={Bank{snapshot,values,name},Bank{snapshot,values,name}};active=0;savedValues=capture();edited=false;status="Factory kit loaded: "+name;publish(snapshot);});}
RenderService::Settings DrumProcessor::renderSettings(const std::vector<float>& values,double rate){
 require(values.size()==specs().size(),"Invalid export parameter snapshot.");for(size_t i=0;i<values.size();++i)require(std::isfinite(values[i])&&values[i]>=specs()[i].min-.00001f&&values[i]<=specs()[i].max+.00001f,"Invalid export parameter value.");RenderService::Settings settings;settings.rate=rate;
 for(int slot=0;slot<8;++slot){std::array<float,22> f{};for(size_t i=0;i<f.size();++i)f[i]=values[parameterIndex(slotId(slot,designFields[i]))];settings.controls[static_cast<size_t>(slot)]={f[0],f[1],f[2],f[3],f[4],f[5],f[6],f[7],f[8],f[9],f[10],f[11],f[12],f[13],f[14],f[15],f[16],f[17],f[18],f[19],f[20],f[21]};}
 settings.macros={values[1],values[2],values[3]};settings.output=values[parameterIndex("output")];return settings;
}
bool DrumProcessor::exportShot(int slot,const juce::File& file,double rate,bool overwrite){
 if(slot<0||slot>7)return false;if(rawComparison.load()){std::lock_guard lock(control);status="Return to EDITED mode before exporting";return false;}const auto values=capture();const auto current=view();cancelRender.store(false);
 return submit([this,slot,file,rate,overwrite,values,snapshot=current.snapshot]{require(snapshot!=nullptr,"No kit loaded.");std::array<const ohsample::Sample*,8> samples{};for(size_t i=0;i<8;++i)samples[i]=snapshot->assets[i].sample.get();const auto rendered=RenderService::oneShot(renderSettings(values,rate),samples,slot,file,cancelRender,overwrite);std::lock_guard lock(control);status="Exported PCM24 WAV: "+rendered.file.getFileName()+" / "+juce::String(static_cast<double>(rendered.frames)/rendered.rate,2)+" s";});
}
bool DrumProcessor::exportKitAudio(const juce::File& directory,double rate){
 if(rawComparison.load()){std::lock_guard lock(control);status="Return to EDITED mode before exporting";return false;}const auto values=capture();const auto current=view();const auto kitState=stateObject();cancelRender.store(false);
 return submit([this,directory,rate,values,current,kitState]{require(directory.isDirectory(),"Select an existing export directory.");require(current.snapshot!=nullptr,"No kit loaded.");const auto settings=renderSettings(values,rate);std::array<const ohsample::Sample*,8> samples{};for(size_t i=0;i<8;++i)samples[i]=current.snapshot->assets[i].sample.get();
  const auto prefix="DrumShotSupplyCo_"+RenderService::safeName(current.name);juce::File destination,staging;int index=1;
  for(;index<10000;++index){const auto suffix=juce::String(index).paddedLeft('0',2);destination=directory.getChildFile(prefix+"_"+suffix);staging=directory.getChildFile(prefix+"_"+suffix+".rendering");if(!destination.exists()&&!staging.exists())break;}
  require(index<10000&&staging.createDirectory().wasOk(),"Cannot create export staging directory.");auto manifest=object();put(manifest,"schema",1);put(manifest,"product","Drum Shot Supply Co.");put(manifest,"version","0.3.0");put(manifest,"kit",current.name);put(manifest,"state","RENDERING");put(manifest,"kit_state",kitState);put(manifest,"velocity",127);put(manifest,"dither","Deterministic TPDF, 24-bit quantization");juce::Array<juce::var> files;
  const auto statusFile=staging.getChildFile("ExportManifest.json");require(statusFile.replaceWithText(juce::JSON::toString(manifest,true)),"Cannot write export status.");
  try{for(int slot=0;slot<8;++slot){{std::lock_guard lock(control);status="Rendering "+juce::String(ohdrum::slotNames[static_cast<size_t>(slot)])+" / "+juce::String(slot+1)+" of 8";}
    const auto filename=prefix+"_"+RenderService::safeName(ohdrum::slotNames[static_cast<size_t>(slot)])+"_"+juce::String(index).paddedLeft('0',2)+".wav";files.add(renderRecord(RenderService::oneShot(settings,samples,slot,staging.getChildFile(filename),cancelRender)));}
   put(manifest,"state","COMPLETE");put(manifest,"files",files);require(statusFile.replaceWithText(juce::JSON::toString(manifest,true)),"Cannot finalize export manifest.");require(!destination.exists()&&staging.moveFileTo(destination),"Cannot commit complete kit export.");
  }catch(...){put(manifest,"state","FAILED");put(manifest,"files",files);statusFile.replaceWithText(juce::JSON::toString(manifest,true));throw;}
  std::lock_guard lock(control);status="Exported eight PCM24 sounds: "+destination.getFileName();
 });
}
juce::AudioProcessorEditor* DrumProcessor::createEditor(){return new DrumEditor(*this);}
juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter(){return new DrumProcessor();}

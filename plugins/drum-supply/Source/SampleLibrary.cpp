#include "SampleLibrary.h"
#include "BinaryData.h"
#include <stdexcept>
namespace {
juce::String factoryFile(int slot){return "starter"+juce::String(slot)+"_wav";}
std::pair<const char*,int> factoryData(int slot){int size=0;auto* data=BinaryData::getNamedResource(factoryFile(slot).toRawUTF8(),size);return {data,size};}
void fail(const char* text){throw std::runtime_error(text);}
juce::MemoryBlock boundedFile(const juce::File& file,uint64_t maximum) {
    juce::FileInputStream stream(file);if(!stream.openedOk()||stream.getTotalLength()<=0||static_cast<uint64_t>(stream.getTotalLength())>maximum)fail("File is empty, unavailable or too large.");
    juce::MemoryBlock block;stream.readIntoMemoryBlock(block,static_cast<int64_t>(maximum+1));if(block.getSize()==0||block.getSize()>maximum)fail("File exceeded the input limit while reading.");return block;
}
void container(const juce::MemoryBlock& block) {
    const auto* p=static_cast<const uint8_t*>(block.getData());const size_t size=block.getSize();
    if(size<12)fail("Truncated audio container.");const bool wav=std::memcmp(p,"RIFF",4)==0&&std::memcmp(p+8,"WAVE",4)==0;
    const bool aiff=std::memcmp(p,"FORM",4)==0&&(std::memcmp(p+8,"AIFF",4)==0||std::memcmp(p+8,"AIFC",4)==0);
    if(!wav&&!aiff)fail("Expected a standard RIFF WAV or AIFF/AIFC container.");
    auto word=[&](size_t offset){uint64_t v=0;for(int i=0;i<4;++i)v|=static_cast<uint64_t>(p[offset+static_cast<size_t>(i)])<<(8*(wav?i:3-i));return v;};
    const auto end=word(4)+8;if(end>size||end<12)fail("Truncated audio container length.");size_t offset=12;bool sound=false;int chunks=0;
    while(offset+8<=end){if(++chunks>4096)fail("Too many audio container chunks.");const auto length=word(offset+4);if(length>end-offset-8)fail("Truncated audio data chunk.");
        if((wav&&std::memcmp(p+offset,"data",4)==0)||(aiff&&std::memcmp(p+offset,"SSND",4)==0))sound=length>0;
        offset+=8+static_cast<size_t>(length)+(static_cast<size_t>(length)&1);}
    if(!sound)fail("Audio container has no sample data.");
}
}
SampleLibrary::SampleLibrary(const juce::File& storageOverride) {
    formats.registerFormat(new juce::WavAudioFormat(),true);formats.registerFormat(new juce::AiffAudioFormat(),false);
    root=storageOverride==juce::File{}?juce::File::getSpecialLocation(juce::File::userApplicationDataDirectory).getChildFile("OmegaHouse/DrumSupply/Samples"):storageOverride;
}
bool SampleLibrary::validReference(const juce::String& ref) {
    if(ref.length()==2&&ref[0]=='f'&&ref[1]>='0'&&ref[1]<='6')return true;
    return ref.length()==64&&ref.containsOnly("0123456789abcdef");
}
SampleLibrary::Asset SampleLibrary::decode(std::unique_ptr<juce::InputStream> stream,const juce::String& ref,const juce::String& name) {
    for(auto it=cache.begin();it!=cache.end();)if(it->second.expired())it=cache.erase(it);else ++it;
    if(auto existing=cache[ref].lock())return {existing,ref,name,false};
    std::unique_ptr<juce::AudioFormatReader> reader(formats.createReaderFor(std::move(stream)));
    if(!reader)fail("Cannot decode this WAV/AIFF. The previous sound is unchanged.");
    if(!std::isfinite(reader->sampleRate)||reader->sampleRate<8000||reader->sampleRate>384000||reader->numChannels<1||reader->numChannels>2||reader->lengthInSamples<2||reader->lengthInSamples>reader->sampleRate*30)
        fail("Use a mono/stereo WAV or AIFF, 8-384 kHz, between 2 frames and 30 seconds.");
    const auto frames=static_cast<size_t>(reader->lengthInSamples);const auto bytes=frames*2*sizeof(float);
    if(bytes>memoryLimit||*allocated>memoryLimit-bytes)fail("256 MiB instance sample budget reached. Reset the kit or shorten the sample.");
    auto budget=allocated;auto* raw=new ohsample::Sample;
    *allocated+=bytes;
    std::shared_ptr<ohsample::Sample> data(raw,[budget,bytes](ohsample::Sample* p){delete p;*budget-=bytes;});
    data->rate=reader->sampleRate;
    for(auto& channel:data->audio)channel.resize(frames);
    float* channels[]{data->audio[0].data(),data->audio[1].data()};
    if(!reader->read(channels,2,0,static_cast<int>(frames)))fail("Sample data is truncated or unreadable.");
    if(reader->numChannels==1)data->audio[1]=data->audio[0];
    for(size_t i=0;i<frames;++i)for(size_t ch=0;ch<2;++ch){const float x=data->audio[ch][i];if(!std::isfinite(x)||std::abs(x)>16)fail("Sample contains non-finite or excessive floating-point values.");
        auto& bucket=data->waveform[std::min<size_t>(255,i*256/frames)];bucket=std::max(bucket,std::abs(x));}
    cache[ref]=data;return {data,ref,name,false};
}
SampleLibrary::Asset SampleLibrary::factory(int slot) {
    if(slot<0||slot>6)fail("Unknown factory slot.");auto& cached=factoryCache[static_cast<size_t>(slot)];if(cached.sample)return cached;
    const auto [data,size]=factoryData(slot);if(!data||size<=0)fail("Embedded factory sample missing.");
    cached=decode(std::make_unique<juce::MemoryInputStream>(data,static_cast<size_t>(size),false),"f"+juce::String(slot),juce::String(ohsample::names[static_cast<size_t>(slot)])+" / Starter");return cached;
}
SampleLibrary::Asset SampleLibrary::load(const juce::File& file) {
    if(!file.existsAsFile())fail("Sample is unavailable. Choose another file to relink this slot.");
    if(!file.hasFileExtension("wav;aif;aiff"))fail("Supported sample formats: WAV and AIFF.");
    if(file.getSize()<=0||static_cast<uint64_t>(file.getSize())>fileLimit)fail("Sample file is empty or exceeds the 64 MiB input limit.");
    // Read one bounded immutable file snapshot: hash, decode and managed copy agree even if source changes.
    auto block=boundedFile(file,fileLimit);container(block);
    const auto ref=juce::SHA256(block).toHexString();
    auto asset=decode(std::make_unique<juce::MemoryInputStream>(block,true),ref,file.getFileName());
    if(!root.createDirectory())fail("Cannot create managed sample storage.");
    const auto destination=root.getChildFile(ref+".sample");
    if(!destination.existsAsFile()) {
        juce::TemporaryFile temp(destination);if(!temp.getFile().replaceWithData(block.getData(),block.getSize())||!temp.overwriteTargetFileWithTemporary())fail("Cannot store sample for session recall.");
    } else {juce::FileInputStream stream(destination);if(juce::SHA256(stream).toHexString()!=ref)fail("Managed sample hash mismatch. Relink after recovering the corrupt cache file.");}
    return asset;
}
SampleLibrary::Asset SampleLibrary::resolve(const juce::String& ref,const juce::String& name) {
    if(!validReference(ref))fail("Invalid sample reference.");
    if(ref.startsWithChar('f')&&ref.length()==2){auto asset=factory(ref.substring(1).getIntValue());asset.name=name;return asset;}
    const auto file=root.getChildFile(ref+".sample");
    if(!file.existsAsFile())return {nullptr,ref,name,true};
    if(file.getSize()<=0||static_cast<uint64_t>(file.getSize())>fileLimit)fail("Managed sample size is invalid.");
    auto block=boundedFile(file,fileLimit);if(juce::SHA256(block).toHexString()!=ref)fail("Managed sample is corrupt: hash mismatch.");container(block);
    return decode(std::make_unique<juce::MemoryInputStream>(block,true),ref,name);
}
juce::MemoryBlock SampleLibrary::bytes(const Asset& asset) const {
    if(asset.reference.length()==2){auto [data,size]=factoryData(asset.reference.substring(1).getIntValue());return juce::MemoryBlock(data,static_cast<size_t>(size));}
    const auto file=root.getChildFile(asset.reference+".sample");auto result=boundedFile(file,fileLimit);
    if(juce::SHA256(result).toHexString()!=asset.reference)fail("Cannot export a missing or corrupt sample. Relink it first.");
    return result;
}

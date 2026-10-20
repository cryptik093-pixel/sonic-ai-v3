#pragma once
#include "SampleEngine.h"
#include <juce_audio_formats/juce_audio_formats.h>
#include <juce_cryptography/juce_cryptography.h>
#include <memory>
#include <map>
#include <atomic>

class SampleLibrary {
public:
    static constexpr uint64_t memoryLimit=256ull*1024*1024, fileLimit=64ull*1024*1024;
    struct Asset {std::shared_ptr<const ohsample::Sample> sample;juce::String reference,name;bool missing=false;};
    explicit SampleLibrary(const juce::File& storageOverride={});
    Asset factory(int);
    Asset load(const juce::File&);
    Asset resolve(const juce::String&,const juce::String&);
    juce::MemoryBlock bytes(const Asset&) const;
    static bool validReference(const juce::String&);
    juce::File storage() const {return root;}
    uint64_t memoryUsed() const {return allocated->load();}
private:
    Asset decode(std::unique_ptr<juce::InputStream>,const juce::String&,const juce::String&);
    juce::AudioFormatManager formats;
    juce::File root;
    std::shared_ptr<std::atomic<uint64_t>> allocated=std::make_shared<std::atomic<uint64_t>>(0);
    std::map<juce::String,std::weak_ptr<const ohsample::Sample>> cache;
    std::array<Asset,7> factoryCache;
};

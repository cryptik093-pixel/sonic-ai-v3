#pragma once
#include <juce_audio_processors/juce_audio_processors.h>
#include "SampleLibrary.h"
#include "DrumEngine.h"
#include <atomic>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <deque>
#include <functional>

class DrumProcessor final : public juce::AudioProcessor {
public:
    struct Spec {juce::String id,name;float min,max,value;bool discrete=false;};
    struct Snapshot {std::array<SampleLibrary::Asset,8> assets;};
    struct Bank {std::shared_ptr<Snapshot> snapshot;std::vector<float> values;juce::String name="Starter Kit";};
    struct View {std::shared_ptr<const Snapshot> snapshot;juce::String name,status;bool busy=false,dirty=false;int ab=0;uint64_t memory=0;};
    static const std::vector<Spec>& specs();
    static juce::String slotId(int,const char*);
    explicit DrumProcessor(const juce::File& storageOverride={});
    ~DrumProcessor() override;
    const juce::String getName() const override { return "Drum Shot Supply Co."; }
    void prepareToPlay(double,int) override;
    void reset() override;
    void releaseResources() override {}
    bool isBusesLayoutSupported(const BusesLayout&) const override;
    void processBlock(juce::AudioBuffer<float>&,juce::MidiBuffer&) override;
    using juce::AudioProcessor::processBlock;
    bool acceptsMidi() const override { return true; }
    bool producesMidi() const override { return false; }
    double getTailLengthSeconds() const override { return 128; }
    bool hasEditor() const override { return true; }
    juce::AudioProcessorEditor* createEditor() override;
    int getNumPrograms() override { return 1; }
    int getCurrentProgram() override { return 0; }
    void setCurrentProgram(int) override {}
    const juce::String getProgramName(int) override { return "Current Kit"; }
    void changeProgramName(int,const juce::String&) override {}
    void getStateInformation(juce::MemoryBlock&) override;
    void setStateInformation(const void*,int) override;
    bool restoreState(const void*,int);
    bool loadSample(int,const juce::File&);
    bool saveKit(const juce::File&,bool portable,bool rightsConfirmed=false);
    bool loadKit(const juce::File&);
    bool switchAB();
    bool resetKit();
    void renameKit(const juce::String&);
    View view() const;
    bool waitIdle(int milliseconds=10000);
    juce::File sampleStorage() const {return library.storage();}
    juce::AudioProcessorValueTreeState parameters;
    std::array<std::atomic<uint32_t>,8> activity{};
    std::atomic<int> preview{-1}; // One bounded UI -> audio trigger mailbox.
    std::atomic<bool> panic{false};
    std::atomic<float> peak{0};
    std::atomic<bool> clipped{false};
    std::atomic<uint32_t> meterFrame{0};
private:
    static juce::AudioProcessorValueTreeState::ParameterLayout layout();
    std::vector<float> capture() const;
    void apply(const std::vector<float>&);
    void syncControls() noexcept;
    void publish(std::shared_ptr<Snapshot>);
    void collect();
    bool submit(std::function<void()>,bool stateRequest=false);
    void work();
    juce::var stateObject() const;
    bool decodeState(const juce::var&,std::array<Bank,2>&,int&,juce::String&);
    std::vector<std::atomic<float>*> raw;
    std::array<std::array<std::atomic<float>*,22>,8> slotRaw{};
    ohdrum::Engine engine;
    SampleLibrary library;
    mutable std::mutex control;
    std::condition_variable wake,idle;
    std::deque<std::function<void()>> jobs;
    bool stopping=false,running=false;
    std::thread worker;
    std::array<Bank,2> banks;
    int active=0;
    juce::String status="Loading starter kit";
    std::vector<float> savedValues;
    bool edited=false;
    uint64_t editRevision=0;
    std::atomic<const Snapshot*> published{nullptr},hazard{nullptr};
    const Snapshot* audioSnapshot=nullptr;
    std::vector<std::shared_ptr<Snapshot>> retained;
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(DrumProcessor)
};

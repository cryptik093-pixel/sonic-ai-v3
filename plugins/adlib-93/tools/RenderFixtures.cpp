#include "WaveFile.h"
#include "dsp/Transitions.h"
#include "presets/FactoryBank.h"
#include <iostream>
#include <map>
#include <string>
int main(int argc,char** argv) {
    try {
        std::map<std::string,std::string> args;
        if(argc==2&&std::string(argv[1])=="--help") {
            std::cout<<"adlib93_render --preset <1..24> --input <wav> --output <new.wav> --sample-rate <hz> --block-size <n> [--tail-seconds <0..180>]\nInput rate must match: no implicit resampling. Outputs stereo float32 WAV.\n";return 0;
        }
        for(int i=1;i<argc;i+=2) {if(i+1==argc||!args.emplace(argv[i],argv[i+1]).second)throw std::runtime_error("Expected unique argument/value pairs");}
        for(const auto& a:args) if(a.first!="--preset"&&a.first!="--input"&&a.first!="--output"&&a.first!="--sample-rate"&&a.first!="--block-size"&&a.first!="--tail-seconds")throw std::runtime_error("Unknown render argument");
        auto integer=[&](const char* key){size_t n=0;auto value=std::stoul(args.at(key),&n);if(n!=args.at(key).size())throw std::runtime_error("Invalid integer");return value;};
        const auto preset=integer("--preset"),rate=integer("--sample-rate"),block=integer("--block-size");
        const auto tail=args.count("--tail-seconds")?integer("--tail-seconds"):0;
        if(preset<1||preset>24||rate<8000||rate>192000||block<1||block>1048576||tail>180)throw std::runtime_error("Render argument outside bounds");
        auto input=adlib93::tools::readWave(args.at("--input"));if(input.sampleRate!=rate)throw std::runtime_error("Input sample rate differs; resample explicitly outside this tool");
        const auto frames=input.samples.size()/input.channels;
        adlib93::tools::WaveFile output;output.sampleRate=static_cast<uint32_t>(rate);output.channels=2;output.samples.resize((frames+tail*rate)*2);
        adlib93::Transitions engine;auto p=adlib93::factoryPresets()[preset-1].parameters;
        engine.prepare({double(rate),static_cast<uint32_t>(std::min(block,128ul)),input.channels==1?adlib93::ChannelLayout::monoStereo:adlib93::ChannelLayout::stereoStereo},p);
        engine.setTiming({120,4,4,false,false});
        // The same sample-based production path is used for every callback partition.
        for(size_t start=0;start<output.samples.size()/2;start+=block) {
            const auto end=std::min(start+block,output.samples.size()/2);
            for(size_t i=start;i<end;++i){adlib93::StereoFrame x{};if(i<frames){x.left=input.samples[i*input.channels];x.right=input.channels==2?input.samples[i*2+1]:x.left;}auto y=engine.process(x);output.samples[i*2]=y.left;output.samples[i*2+1]=y.right;}
        }
        adlib93::tools::writeWave(args.at("--output"),output);
        std::cout<<"Rendered preset "<<preset<<" ("<<adlib93::factoryPresets()[preset-1].name<<"), "<<output.samples.size()/2<<" stereo frames at "<<rate<<" Hz; requested callback partition "<<block<<". Listening PENDING.\n";
        return 0;
    } catch(const std::exception& e){std::cerr<<"Render failed: "<<e.what()<<'\n';return 1;}
}

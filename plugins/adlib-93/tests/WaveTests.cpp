#include "TestSupport.h"
#include "../tools/WaveFile.h"
#include <chrono>
TEST_CASE("Tools.WaveRoundTrip") {
    auto root=std::filesystem::temp_directory_path()/("adlib93-wave-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count()));
    std::filesystem::create_directory(root);auto file=root/"generated.wav";
    adlib93::tools::WaveFile in;in.sampleRate=44100;in.samples={0,.25f,-.5f,1,-1,.001f};
    adlib93::tools::writeWave(file,in);auto out=adlib93::tools::readWave(file);
    require(out.sampleRate==in.sampleRate&&out.channels==in.channels&&out.samples==in.samples,"float WAV exact round trip");
    bool rejected=false;try{adlib93::tools::writeWave(file,in);}catch(const std::exception&){rejected=true;}require(rejected,"existing WAV preserved");
    std::filesystem::remove(file);std::filesystem::remove(root);
}
TEST_CASE("Tools.WaveMalformed") {
    auto file=std::filesystem::temp_directory_path()/("adlib93-invalid-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+".wav");
    {std::ofstream out(file,std::ios::binary);out<<"RIFFxxxxWAVEfmt ";}
    bool rejected=false;try{(void)adlib93::tools::readWave(file);}catch(const std::exception&){rejected=true;}require(rejected,"truncated WAV rejected");std::filesystem::remove(file);
}

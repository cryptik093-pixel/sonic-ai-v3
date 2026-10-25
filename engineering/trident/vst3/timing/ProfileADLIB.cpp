#define NOMINMAX
#include <windows.h>
#include "dsp/Transitions.h"
#include "presets/FactoryBank.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

using Clock = std::chrono::steady_clock;
struct Row { double wallMs; uint64_t cycles; double startLagMs; };
struct Result {
    std::string mode;
    std::vector<Row> rows;
    uint64_t fingerprint = 14695981039346656037ULL;
    double elapsed = 0, threadCpuMs = 0;
    bool finite = true;
};
class ExclusiveFile {
    HANDLE handle;
public:
    explicit ExclusiveFile(const std::filesystem::path& path) {
        handle = CreateFileW(path.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_NEW,
                             FILE_ATTRIBUTE_NORMAL, nullptr);
        if (handle == INVALID_HANDLE_VALUE) throw std::runtime_error("Cannot reserve new output; existing files are preserved");
    }
    ~ExclusiveFile() { CloseHandle(handle); }
    ExclusiveFile(const ExclusiveFile&) = delete;
    ExclusiveFile& operator=(const ExclusiveFile&) = delete;
    void write(const std::string& text) {
        size_t position = 0;
        while (position < text.size()) {
            DWORD written = 0;
            const DWORD count = static_cast<DWORD>(std::min<size_t>(text.size()-position, 1048576));
            if (!WriteFile(handle, text.data()+position, count, &written, nullptr) || written == 0)
                throw std::runtime_error("Output write failed; partial evidence retained");
            position += written;
        }
        if (!FlushFileBuffers(handle)) throw std::runtime_error("Evidence flush failed");
    }
};
uint64_t cycles() {
    ULONG64 value = 0;
    if (!QueryThreadCycleTime(GetCurrentThread(), &value)) throw std::runtime_error("QueryThreadCycleTime unavailable");
    return value;
}
uint64_t fileTicks(FILETIME f) { return (uint64_t(f.dwHighDateTime)<<32) | f.dwLowDateTime; }
uint64_t threadTicks() {
    FILETIME created{}, exited{}, kernel{}, user{};
    if (!GetThreadTimes(GetCurrentThread(), &created, &exited, &kernel, &user))
        throw std::runtime_error("GetThreadTimes unavailable");
    return fileTicks(kernel) + fileTicks(user);
}
template<class T> double quantile(std::vector<T> values, double q) {
    if (values.empty() || !(q > 0 && q <= 1)) throw std::runtime_error("Invalid quantile input");
    std::sort(values.begin(), values.end());
    return static_cast<double>(values[static_cast<size_t>(std::ceil(values.size()*q))-1]);
}
void hashFloat(uint64_t& hash, float value) {
    uint32_t bits = 0; std::memcpy(&bits, &value, sizeof(bits));
    for (unsigned shift=0; shift<32; shift+=8) { hash ^= (bits>>shift)&255; hash *= 1099511628211ULL; }
}
Result measure(unsigned rate, unsigned block, unsigned seconds, unsigned warmup,
               bool transitions, bool paced, bool captureCycles) {
    adlib93::Transitions engine;
    engine.prepare({double(rate), block, adlib93::ChannelLayout::stereoStereo}, adlib93::factoryPresets()[23].parameters);
    engine.setTiming({120,4,4,true,true});
    std::vector<adlib93::StereoFrame> input(block), output(block);
    const uint64_t count = (uint64_t(seconds)*rate+block-1)/block;
    const uint64_t warmCount = (uint64_t(warmup)*rate+block-1)/block;
    Result result; result.mode = transitions ? "transitions" : "steady";
    result.rows.resize(static_cast<size_t>(count));
    uint64_t cursor = 0;
    auto fill = [&] {
        for (unsigned i=0; i<block; ++i) {
            const double t = double(cursor+i)/rate;
            input[i] = {float(.18*std::sin(6.283185307179586*137*t)), float(.17*std::sin(6.283185307179586*191*t))};
        }
    };
    for (uint64_t b=0; b<warmCount; ++b) {
        fill(); for(unsigned i=0;i<block;++i) engine.process(input[i]); cursor += block;
    }
    unsigned selected = 23;
    const auto cpuStart = threadTicks();
    const auto start = Clock::now();
    for (uint64_t b=0; b<count; ++b) {
        fill();
        const bool change = transitions && b%std::max<uint64_t>(1, uint64_t(double(rate)*.075/block))==0;
        if (change) selected = (selected+1)%24;
        const auto cycleStart = captureCycles ? cycles() : 0;
        const auto begin = Clock::now();
        if (change) engine.request(adlib93::factoryPresets()[selected].parameters);
        for (unsigned i=0; i<block; ++i) output[i] = engine.process(input[i]);
        const auto end = Clock::now();
        const auto cycleEnd = captureCycles ? cycles() : 0;
        if (cycleEnd < cycleStart) throw std::runtime_error("Non-monotonic thread cycle counter");
        const double dueMs = 1000.*double(b)*block/rate;
        result.rows[static_cast<size_t>(b)] = {
            std::chrono::duration<double,std::milli>(end-begin).count(), cycleEnd-cycleStart,
            paced ? std::max(0., std::chrono::duration<double,std::milli>(begin-start).count()-dueMs) : 0.
        };
        for (const auto frame : output) {
            result.finite = result.finite && std::isfinite(frame.left) && std::isfinite(frame.right);
            hashFloat(result.fingerprint, frame.left); hashFloat(result.fingerprint, frame.right);
        }
        cursor += block;
        if (paced) std::this_thread::sleep_until(start + std::chrono::duration_cast<Clock::duration>(
            std::chrono::duration<double>(double(b+1)*block/rate)));
    }
    result.elapsed = std::chrono::duration<double>(Clock::now()-start).count();
    result.threadCpuMs = double(threadTicks()-cpuStart)/10000.;
    return result;
}
int main(int argc, char** argv) {
    try {
        if(argc==2 && std::string(argv[1])=="--self-test") {
            if(quantile(std::vector<double>{4,1,2,3},.5)!=2 || quantile(std::vector<double>{4,1,2,3},.99)!=4)
                throw std::runtime_error("Quantile self-test failed");
            const auto first=cycles(); const auto second=cycles();
            if(second<first) throw std::runtime_error("Windows cycle self-test failed");
            (void)threadTicks();
            std::cout << "Self-test passed\n"; return 0;
        }
        if(argc==2 && std::string(argv[1])=="--help") {
            std::cout << "profile_adlib --report <new.json> --csv <new.csv> [--seconds 30] [--warmup 3] [--sample-rate 48000] [--block-size 128] [--paced true|false] [--cycles true|false]\n";
            return 0;
        }
        std::map<std::string,std::string> args;
        for(int i=1;i<argc;i+=2) {
            if(i+1>=argc || !args.emplace(argv[i],argv[i+1]).second) throw std::runtime_error("Expected unique option/value pairs");
        }
        for(const auto& pair:args) {
            if(pair.first!="--report" && pair.first!="--csv" && pair.first!="--seconds" && pair.first!="--warmup" && pair.first!="--sample-rate" && pair.first!="--block-size" && pair.first!="--paced" && pair.first!="--cycles")
                throw std::runtime_error("Unknown option");
        }
        auto number = [&](const char* key, unsigned fallback) {
            if(!args.count(key)) return fallback;
            const std::string value=args.at(key);
            if(value.empty() || value.find_first_not_of("0123456789")!=std::string::npos) throw std::runtime_error("Invalid unsigned option");
            const auto n=std::stoull(value); if(n>192000) throw std::runtime_error("Numeric option too large"); return unsigned(n);
        };
        auto boolean = [&](const char* key, bool fallback) {
            if(!args.count(key)) return fallback;
            if(args.at(key)!="true" && args.at(key)!="false") throw std::runtime_error("Invalid boolean option");
            return args.at(key)=="true";
        };
        const unsigned rate=number("--sample-rate",48000),block=number("--block-size",128),seconds=number("--seconds",30),warmup=number("--warmup",3);
        const bool paced=boolean("--paced",true), captureCycles=boolean("--cycles",true);
        if(rate<8000 || rate>192000 || block<1 || block>8192 || seconds<1 || seconds>120 || warmup>10 || (uint64_t(seconds)*rate+block-1)/block>250000)
            throw std::runtime_error("Diagnostic configuration outside bounds");
        ExclusiveFile report(args.at("--report")), csv(args.at("--csv"));
        std::vector<Result> results;
        results.push_back(measure(rate,block,seconds,warmup,false,paced,captureCycles));
        results.push_back(measure(rate,block,seconds,warmup,true,paced,captureCycles));
        std::ostringstream json, raw; json << std::setprecision(12); raw << std::setprecision(12);
        const double deadline=1000.*block/rate;
        json << "{\"schema\":1,\"diagnostic_only\":true,\"release_qualified\":false,\"sample_rate\":" << rate
             << ",\"block_size\":" << block << ",\"seconds_per_mode\":" << seconds << ",\"warmup_audio_seconds\":" << warmup
             << ",\"paced\":" << (paced?"true":"false") << ",\"cycles_enabled\":" << (captureCycles?"true":"false")
             << ",\"deadline_ms\":" << deadline << ",\"cpu_budget\":\"PENDING\",\"modes\":[";
        raw << "mode,block,wall_ms,thread_cycles,start_lag_ms\n";
        bool finite=true;
        for(size_t i=0;i<results.size();++i) {
            const auto& result=results[i]; std::vector<double> wall,lag; std::vector<uint64_t> cycle;
            wall.reserve(result.rows.size()); lag.reserve(result.rows.size()); cycle.reserve(result.rows.size());
            for(const auto& row:result.rows) { wall.push_back(row.wallMs); lag.push_back(row.startLagMs); cycle.push_back(row.cycles); }
            const double medianWall=quantile(wall,.5), medianCycle=quantile(cycle,.5);
            uint64_t wallOutliers=0,lowCycleOutliers=0,misses=0;
            for(size_t b=0;b<result.rows.size();++b) {
                const auto& row=result.rows[b]; misses += row.wallMs>deadline;
                if(row.wallMs>2*medianWall) { ++wallOutliers; if(captureCycles && medianCycle>0 && row.cycles<=1.5*medianCycle) ++lowCycleOutliers; }
                raw << result.mode << ',' << b << ',' << row.wallMs << ',' << row.cycles << ',' << row.startLagMs << '\n';
            }
            finite = finite && result.finite;
            if(i) json << ',';
            json << "{\"mode\":\"" << result.mode << "\",\"blocks\":" << result.rows.size()
                 << ",\"wall_seconds\":" << result.elapsed << ",\"whole_loop_thread_cpu_ms\":" << result.threadCpuMs
                 << ",\"wall_p50_ms\":" << medianWall << ",\"wall_p95_ms\":" << quantile(wall,.95)
                 << ",\"wall_p99_ms\":" << quantile(wall,.99) << ",\"wall_max_ms\":" << quantile(wall,1.)
                 << ",\"cycle_p50\":" << medianCycle << ",\"cycle_p95\":" << quantile(cycle,.95)
                 << ",\"cycle_p99\":" << quantile(cycle,.99) << ",\"cycle_max\":" << quantile(cycle,1.)
                 << ",\"start_lag_p99_ms\":" << quantile(lag,.99) << ",\"deadline_misses\":" << misses
                 << ",\"wall_outliers_gt_2x_median\":" << wallOutliers << ",\"low_cycle_wall_outliers_le_1_5x_median\":" << lowCycleOutliers
                 << ",\"finite\":" << (result.finite?"true":"false") << ",\"output_fnv1a64\":\"" << std::hex << result.fingerprint << std::dec << "\"}";
        }
        json << "],\"limitations\":[\"Core-only custom loop, not a native VST3 or FL Studio callback.\",\"Raw thread cycles must not be converted to time; CPU frequency may vary.\",\"Low-cycle wall outliers are diagnostic clues, not proof of scheduling causation.\",\"Whole-loop thread CPU includes generator, checks, hashing, instrumentation and pacing overhead.\",\"Per-block cycle intervals include clock/counter overhead; no overhead subtraction.\",\"Output fingerprint is non-cryptographic; source/library/executable SHA256 belongs in the runner manifest.\"]}\n";
        csv.write(raw.str()); report.write(json.str());
        std::cout << "Timing diagnostic collected; release qualification remains false\n";
        return finite?0:2;
    } catch(const std::exception& error) { std::cerr << "Timing diagnostic failed: " << error.what() << '\n'; return 1; }
}

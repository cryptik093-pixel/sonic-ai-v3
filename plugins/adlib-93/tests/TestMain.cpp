#include "TestSupport.h"
#include <iostream>
int main(int argc,char** argv) {
    std::string selected;
    if(argc==3 && std::string(argv[1])=="--case") selected=argv[2];
    else if(argc!=1) { std::cerr<<"Usage: adlib93_tests [--case name]\n";return 2; }
    int executed=0,failed=0;
    for(const auto& test:adlib93::test::cases()) {
        if(!selected.empty() && selected!=test.name) continue;
        ++executed;
        try { test.run();std::cout<<"PASS "<<test.name<<'\n'; }
        catch(const std::exception& e) { ++failed;std::cerr<<"FAIL "<<test.name<<": "<<e.what()<<'\n'; }
    }
    if(executed==0) { std::cerr<<"Unknown case: "<<selected<<'\n';return 2; }
    std::cout<<executed<<" cases, "<<failed<<" failures\n";return failed?1:0;
}

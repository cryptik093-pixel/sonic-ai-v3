#include "TestSupport.h"
namespace adlib93 { long buildLanguageStandard() noexcept; }
TEST_CASE("Build.Configuration") {
    require(sizeof(void*)==8,"x64 required");
    require(__cplusplus>=201703L,"C++17 required");
    require(adlib93::buildLanguageStandard()>=201703L,"production library uses C++17");
}

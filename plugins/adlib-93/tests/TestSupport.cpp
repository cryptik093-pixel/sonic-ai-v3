#include "TestSupport.h"
#include <stdexcept>
namespace adlib93::test {
std::vector<Case>& cases() { static std::vector<Case> value;return value; }
Register::Register(const char* name,void (*run)()) { cases().push_back({name,run}); }
void require(bool condition,const char* message) { if(!condition) throw std::runtime_error(message); }
}

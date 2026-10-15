#pragma once
#include <functional>
#include <string>
#include <vector>
namespace adlib93::test {
struct Case { std::string name; void (*run)(); };
std::vector<Case>& cases();
struct Register { Register(const char*,void (*)()); };
void require(bool,const char*);
}
#define ADLIB_JOIN_IMPL(a,b) a##b
#define ADLIB_JOIN(a,b) ADLIB_JOIN_IMPL(a,b)
#define TEST_CASE(name) static void ADLIB_JOIN(test_,__LINE__)(); static ::adlib93::test::Register ADLIB_JOIN(reg_,__LINE__)(name,&ADLIB_JOIN(test_,__LINE__)); static void ADLIB_JOIN(test_,__LINE__)()
using adlib93::test::require;

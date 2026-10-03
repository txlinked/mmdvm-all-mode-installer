// Exercise the actual patched converter, replacing only external command execution.
#include <string>
#include <vector>
#include <sstream>
#include <fstream>
#include <iostream>
#include <map>
#include <list>
#include <functional>
#include <algorithm>
#include <cstdlib>
#include <cstdio>
#include <cassert>
#define private public
#include "DMR2YSF.h"
#undef private

static std::vector<std::string> commands;
static bool commandFails = false;
int mmod_test_system(const char* command) {
    commands.push_back(command);
    return commandFails ? 1 : 0;
}
#define system mmod_test_system
#define main converter_main
#include "DMR2YSF.cpp"
#undef main
#undef system

int main() {
    CDMR2YSF converter("/unused-test.ini");
    converter.connectYSF(100334U);
    assert(commands.size() == 1U);
    assert(commands.back().find("LinkFCS 00334") != std::string::npos);
    assert(converter.m_lastTG == 100334U);
    converter.connectYSF(100334U);
    assert(commands.size() == 1U);
    converter.connectYSF(4000U);
    assert(commands.back().find("-m Unlink") != std::string::npos);
    assert(converter.m_lastTG == 0U);
    converter.connectYSF(100334U);
    assert(commands.size() == 3U);
    converter.connectYSF(200123U);
    assert(commands.back().find("LinkYSF 00123") != std::string::npos);
    commandFails = true;
    converter.connectYSF(100335U);
    assert(converter.m_lastTG == 200123U);
    commandFails = false;
    converter.connectYSF(100335U);
    assert(converter.m_lastTG == 100335U);
    CTimer timer(1000U, 600U);
    timer.start();
    timer.clock(599999U);
    assert(!timer.hasExpired());
    timer.clock(1U);
    assert(timer.hasExpired());
    std::puts("Native FCS/YSF controls, unlink/relink, command failure and 10-minute timer passed");
    return 0;
}

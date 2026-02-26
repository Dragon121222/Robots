#include <map>
#include <cstdint>
#include <iostream>

#include "crtp/crtp.h"
#include "plex/plex.h"
#include "dispatch/dispatch.h"

size_t func_0(size_t v) { std::cout << "func_0\n"; return 0; }
size_t func_1(size_t v) { std::cout << "func_1\n"; return 0; }
size_t func_2(size_t v) { std::cout << "func_2\n"; return 0; }

int main() {

    using Input_t = size_t;
    using Output_t = size_t;
    using FunctionPtr_t = Output_t (*)(Input_t x);

    using Key_t = uint8_t;
    using Value_t = FunctionPtr_t;
    using Map_t = std::map<uint8_t,FunctionPtr_t>;

    Map_t testMap = {
        {0,&func_0},
        {1,&func_1},
        {2,&func_2}
    };

    using testPlex = plex::plex<
        Input_t,
        Output_t,
        Key_t,
        Value_t,
        Map_t
    >;

    testPlex mPlex = testPlex(testMap);

    mPlex.run(0,0);
    mPlex.run(1,0);
    mPlex.run(2,0);

    return 0;
}
#pragma once

namespace plex {

template<
    typename Input_t,
    typename Output_t,
    typename Key_t,
    typename Value_t,
    typename Map_t
>
class plex {
    public:

        plex(
            const Map_t& m
        ) : map_(m) {

        }

        Output_t run(Key_t k, Input_t x) {
            auto f = map_.at(k);
            return f(x);
        }

    private:
        const Map_t& map_;
};

};


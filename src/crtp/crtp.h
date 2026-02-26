#pragma once

namespace crtp {

    class base {
        public:
        base() {

        }

    };

    template<typename Base>
    class derived : public Base {
        public:
        derived() : Base() {

        }

    };

}


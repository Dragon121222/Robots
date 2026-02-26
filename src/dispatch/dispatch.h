#include <thread>
#include <vector>

namespace {

class dispatch {
public:
    dispatch() = default;

    ~dispatch() {
        for (auto& t : threads_) {
            if (t.joinable()) {
                t.join();
            }
        }
    }

    void run(void(*func)()) {
        threads_.emplace_back(func);
    }

private:
    std::vector<std::thread> threads_;
};

};


cmake_minimum_required(VERSION 3.21)
project(Robots)

add_executable(
    App.exe 
    src/main.cpp
)

target_link_libraries(App.exe)
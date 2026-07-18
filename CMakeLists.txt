cmake_minimum_required(VERSION 3.20)
project(JarvisAssistant VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(Qt6 REQUIRED COMPONENTS Widgets Network Sql Core)

add_subdirectory(src/jarvis)

if(BUILD_TESTING)
    enable_testing()
    add_subdirectory(tests/CppTests)
endif()

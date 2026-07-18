find_package(Qt6 REQUIRED COMPONENTS Test)

add_executable(TestJarvis
    test_agent.cpp
    test_tools.cpp
    test_memory.cpp
)

target_include_directories(TestJarvis PRIVATE
    ${CMAKE_SOURCE_DIR}/src/jarvis
)

target_link_libraries(TestJarvis PRIVATE
    Qt6::Test
    Qt6::Core
)

add_test(NAME JarvisTests COMMAND TestJarvis)

set(JARVIS_SOURCES
    main.cpp
    core/Config.cpp
    core/AgentOrchestrator.cpp
    core/ReActLoop.cpp
    core/ToolRegistry.cpp
    ai/AIEngine.cpp
    ai/OpenRouterClient.cpp
    ui/MainWindow.cpp
    ui/ChatPanel.cpp
    ui/SettingsDialog.cpp
    ui/TrayManager.cpp
    tools/WebSearchTool.cpp
    tools/FileIOTool.cpp
    tools/SystemControlTool.cpp
    tools/CalculatorTool.cpp
    memory/MemoryStore.cpp
    security/Governance.cpp
    security/CredentialManager.cpp
    plugins/PluginLoader.cpp
    voice/VoicePipeline.cpp
)

set(JARVIS_HEADERS
    core/Config.h
    core/AgentOrchestrator.h
    core/ReActLoop.h
    core/ToolRegistry.h
    ai/AIEngine.h
    ai/OpenRouterClient.h
    ui/MainWindow.h
    ui/ChatPanel.h
    ui/SettingsDialog.h
    ui/TrayManager.h
    tools/BaseTool.h
    tools/WebSearchTool.h
    tools/FileIOTool.h
    tools/SystemControlTool.h
    tools/CalculatorTool.h
    memory/MemoryStore.h
    security/Governance.h
    security/CredentialManager.h
    plugins/PluginLoader.h
    voice/VoicePipeline.h
)

add_executable(Jarvis WIN32 ${JARVIS_SOURCES} ${JARVIS_HEADERS}
    ${CMAKE_SOURCE_DIR}/resources/resources.qrc
)

target_include_directories(Jarvis PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})

target_link_libraries(Jarvis PRIVATE
    Qt6::Widgets
    Qt6::Network
    Qt6::Sql
    Qt6::Core
)

set_target_properties(Jarvis PROPERTIES
    WIN32_EXECUTABLE TRUE
    OUTPUT_NAME "Jarvis"
)

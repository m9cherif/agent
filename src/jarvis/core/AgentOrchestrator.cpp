#include "AgentOrchestrator.h"
#include "../tools/WebSearchTool.h"
#include "../tools/FileIOTool.h"
#include "../tools/SystemControlTool.h"
#include "../tools/CalculatorTool.h"

AgentOrchestrator::AgentOrchestrator(QObject* parent)
    : QObject(parent)
{
    m_aiEngine = new AIEngine(this);
    m_toolRegistry = new ToolRegistry(this);
    m_memoryStore = new MemoryStore(this);
    m_governance = new Governance(this);
    m_reactLoop = new ReActLoop(m_aiEngine, m_toolRegistry, m_governance, this);

    m_toolRegistry->registerTool("web_search", new WebSearchTool(this));
    m_toolRegistry->registerTool("file_read", new FileIOTool(this));
    m_toolRegistry->registerTool("file_write", new FileIOTool(this));
    m_toolRegistry->registerTool("run_command", new SystemControlTool(this));
    m_toolRegistry->registerTool("calculator", new CalculatorTool(this));

    connect(m_reactLoop, &ReActLoop::stepComplete, this, [this](const QString& thought) {
        emit agentThinking(thought);
    });
    connect(m_reactLoop, &ReActLoop::toolCalled, this, [this](const QString& tool, const QString& result) {
        emit toolExecuted(tool, result);
    });
    connect(m_reactLoop, &ReActLoop::finalResponse, this, [this](const QString& response) {
        emit agentResponse(response);
    });
    connect(m_reactLoop, &ReActLoop::error, this, [this](const QString& error) {
        emit agentError(error);
    });
}

void AgentOrchestrator::processUserInput(const QString& input) {
    m_memoryStore->addConversationEntry("user", input);
    m_reactLoop->execute(input);
}

void AgentOrchestrator::setGovernanceLevel(int level) {
    m_governance->setLevel(level);
}

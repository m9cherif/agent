#pragma once
#include <QObject>
#include <QString>
#include <functional>
#include "ReActLoop.h"
#include "ToolRegistry.h"
#include "../ai/AIEngine.h"
#include "../memory/MemoryStore.h"
#include "../security/Governance.h"

class AgentOrchestrator : public QObject {
    Q_OBJECT
public:
    explicit AgentOrchestrator(QObject* parent = nullptr);

    void processUserInput(const QString& input);

    void setGovernanceLevel(int level);
    AIEngine* aiEngine() { return m_aiEngine; }
    ToolRegistry* toolRegistry() { return m_toolRegistry; }
    MemoryStore* memoryStore() { return m_memoryStore; }
    Governance* governance() { return m_governance; }

signals:
    void agentResponse(const QString& response);
    void agentThinking(const QString& thought);
    void agentError(const QString& error);
    void toolExecuted(const QString& tool, const QString& result);

private:
    void handleReActResult(const ReActLoop::Result& result);

    AIEngine* m_aiEngine;
    ToolRegistry* m_toolRegistry;
    MemoryStore* m_memoryStore;
    Governance* m_governance;
    ReActLoop* m_reactLoop;
};

#pragma once
#include <QObject>
#include <QString>
#include <QJsonObject>

class AIEngine;
class ToolRegistry;
class Governance;

class ReActLoop : public QObject {
    Q_OBJECT
public:
    struct Result {
        bool success;
        QString response;
    };

    ReActLoop(AIEngine* engine, ToolRegistry* tools, Governance* gov, QObject* parent = nullptr);

    void execute(const QString& userInput);
    void setMaxIterations(int max) { m_maxIterations = max; }

signals:
    void stepComplete(const QString& thought);
    void toolCalled(const QString& tool, const QString& result);
    void finalResponse(const QString& response);
    void error(const QString& error);

private:
    void processUserMessage(const QString& userInput);
    Result executeToolAction(const QJsonObject& action);
    bool isToolAction(const QString& text, QJsonObject& outAction);

    AIEngine* m_engine;
    ToolRegistry* m_tools;
    Governance* m_governance;
    int m_maxIterations = 10;
    int m_currentIteration = 0;
    QStringList m_conversationHistory;
};

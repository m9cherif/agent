#include "ReActLoop.h"
#include "ToolRegistry.h"
#include "tools/BaseTool.h"
#include "../ai/AIEngine.h"
#include "../security/Governance.h"
#include <QJsonDocument>
#include <QJsonParseError>
#include <QRegularExpression>

ReActLoop::ReActLoop(AIEngine* engine, ToolRegistry* tools, Governance* gov, QObject* parent)
    : QObject(parent), m_engine(engine), m_tools(tools), m_governance(gov)
{
}

void ReActLoop::execute(const QString& userInput) {
    m_currentIteration = 0;
    m_conversationHistory.clear();
    processUserMessage(userInput);
}

void ReActLoop::processUserMessage(const QString& userInput) {
    if (m_currentIteration >= m_maxIterations) {
        emit error("Max iterations reached without final answer");
        return;
    }
    m_currentIteration++;

    QString systemPrompt = "You are JARVIS. Follow this ReAct format:\n"
        "THOUGHT: (reason about what to do)\n"
        "ACTION: {\"tool\":\"tool_name\",\"params\":{...}}\n"
        "or if done:\n"
        "FINAL: (your final answer to the user)\n\n"
        "Available tools: web_search, file_read, file_write, run_command, calculator.";

    m_conversationHistory.append("User: " + userInput);

    QString fullPrompt = systemPrompt + "\n\n" + m_conversationHistory.join("\n") + "\n\nAssistant:";

    m_engine->sendMessage(fullPrompt,
        [this](const QString& chunk) {
            QJsonObject action;
            if (isToolAction(chunk, action)) {
                emit stepComplete("Executing tool: " + action["tool"].toString());
                Result r = executeToolAction(action);
                emit toolCalled(action["tool"].toString(), r.response);
                m_conversationHistory.append("Tool result: " + r.response);
                processUserMessage("Continue based on tool result: " + r.response);
            } else if (chunk.contains("FINAL:")) {
                QString finalResp = chunk;
                finalResp.replace("FINAL:", "").trimmed();
                emit finalResponse(finalResp);
            } else {
                emit stepComplete(chunk);
            }
        },
        [this](bool success) {
            if (!success) emit error("LLM call failed");
        }
    );
}

bool ReActLoop::isToolAction(const QString& text, QJsonObject& outAction) {
    QRegularExpression re(R"(\{"tool"\s*:\s*"[^"]+"\s*,\s*"params"\s*:\s*\{[^}]*\}\})");
    QRegularExpressionMatch match = re.match(text);
    if (match.hasMatch()) {
        QJsonParseError err;
        QJsonDocument doc = QJsonDocument::fromJson(match.captured().toUtf8(), &err);
        if (err.error == QJsonParseError::NoError && doc.isObject()) {
            outAction = doc.object();
            return true;
        }
    }
    return false;
}

ReActLoop::Result ReActLoop::executeToolAction(const QJsonObject& action) {
    QString toolName = action["tool"].toString();
    QJsonObject params = action["params"].toObject();

    if (!m_governance->isActionAllowed(toolName, params)) {
        return {false, "Action blocked by governance policy"};
    }

    BaseTool* tool = m_tools->getTool(toolName);
    if (!tool) {
        return {false, "Unknown tool: " + toolName};
    }

    return tool->execute(params);
}

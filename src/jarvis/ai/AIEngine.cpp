#include "AIEngine.h"
#include "OpenRouterClient.h"
#include "../core/Config.h"
#include <QJsonArray>
#include <QJsonObject>
#include <QJsonDocument>

AIEngine::AIEngine(QObject* parent) : QObject(parent) {
    auto& cfg = Config::instance();
    m_apiKey = cfg.openRouterKey();
    m_baseUrl = cfg.openRouterBaseUrl();
    m_model = cfg.model();
}

void AIEngine::setApiKey(const QString& key) { m_apiKey = key; }
void AIEngine::setBaseUrl(const QString& url) { m_baseUrl = url; }
void AIEngine::setModel(const QString& model) { m_model = model; }

bool AIEngine::isConfigured() const {
    return !m_apiKey.isEmpty() && !m_baseUrl.isEmpty();
}

void AIEngine::sendMessage(const QString& userMessage,
                           std::function<void(const QString&)> onChunk,
                           std::function<void(bool)> onComplete)
{
    OpenRouterClient* client = new OpenRouterClient(this);
    client->setApiKey(m_apiKey);
    client->setBaseUrl(m_baseUrl);
    client->setModel(m_model);

    QJsonArray messages;
    QJsonObject systemMsg;
    systemMsg["role"] = "system";
    systemMsg["content"] = "You are JARVIS, an AI desktop assistant. "
        "You have access to tools for file operations, web search, "
        "system control, and calculations. Respond conversationally. "
        "When you need to use a tool, output JSON in the format: "
        "{\"tool\":\"tool_name\",\"params\":{...}}. "
        "Available tools: web_search, file_read, file_write, "
        "run_command, calculator, clipboard_get, clipboard_set.";
    messages.append(systemMsg);

    QJsonObject userMsg;
    userMsg["role"] = "user";
    userMsg["content"] = userMessage;
    messages.append(userMsg);

    connect(client, &OpenRouterClient::streamChunk, this, [onChunk](const QString& chunk) {
        if (onChunk) onChunk(chunk);
    });

    connect(client, &OpenRouterClient::finished, this, [this, client, onComplete](bool success) {
        if (success) emit responseReceived(client->fullResponse());
        else emit errorOccurred(client->errorString());
        if (onComplete) onComplete(success);
        client->deleteLater();
    });

    client->sendChatCompletion(messages);
}

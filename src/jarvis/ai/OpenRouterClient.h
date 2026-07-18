#pragma once
#include <QObject>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QJsonArray>
#include <QJsonObject>
#include <QString>

class OpenRouterClient : public QObject {
    Q_OBJECT
public:
    explicit OpenRouterClient(QObject* parent = nullptr);

    void setApiKey(const QString& key) { m_apiKey = key; }
    void setBaseUrl(const QString& url) { m_baseUrl = url; }
    void setModel(const QString& model) { m_model = model; }

    void sendChatCompletion(const QJsonArray& messages);

    QString fullResponse() const { return m_fullResponse; }
    QString errorString() const { return m_errorString; }

signals:
    void streamChunk(const QString& text);
    void finished(bool success);

private:
    void handleReply(QNetworkReply* reply);

    QNetworkAccessManager* m_manager;
    QString m_apiKey;
    QString m_baseUrl = "https://openrouter.ai/api/v1";
    QString m_model = "openrouter/free";
    QString m_fullResponse;
    QString m_errorString;
};

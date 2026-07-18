#pragma once
#include <QObject>
#include <QString>
#include <functional>

class AIEngine : public QObject {
    Q_OBJECT
public:
    explicit AIEngine(QObject* parent = nullptr);

    void sendMessage(const QString& userMessage,
                     std::function<void(const QString&)> onChunk,
                     std::function<void(bool)> onComplete);

    void setApiKey(const QString& key);
    void setBaseUrl(const QString& url);
    void setModel(const QString& model);

    bool isConfigured() const;

signals:
    void responseReceived(const QString& text);
    void errorOccurred(const QString& error);

private:
    QString m_apiKey;
    QString m_baseUrl = "https://openrouter.ai/api/v1";
    QString m_model = "openrouter/free";
};

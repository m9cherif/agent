#include "OpenRouterClient.h"
#include <QJsonDocument>
#include <QUrl>
#include <QUrlQuery>

OpenRouterClient::OpenRouterClient(QObject* parent)
    : QObject(parent), m_manager(new QNetworkAccessManager(this))
{
}

void OpenRouterClient::sendChatCompletion(const QJsonArray& messages) {
    m_fullResponse.clear();
    m_errorString.clear();

    QUrl url(m_baseUrl + "/chat/completions");
    QNetworkRequest request(url);
    request.setRawHeader("Authorization", ("Bearer " + m_apiKey).toUtf8());
    request.setRawHeader("Content-Type", "application/json");
    request.setRawHeader("HTTP-Referer", "https://github.com/jarvis-assistant");
    request.setRawHeader("X-Title", "JARVIS Desktop Assistant");

    QJsonObject payload;
    payload["model"] = m_model;
    payload["messages"] = messages;
    payload["stream"] = false;
    payload["max_tokens"] = 4096;

    QNetworkReply* reply = m_manager->post(request, QJsonDocument(payload).toJson());
    connect(reply, &QNetworkReply::finished, this, [this, reply]() {
        handleReply(reply);
    });
}

void OpenRouterClient::handleReply(QNetworkReply* reply) {
    reply->deleteLater();

    if (reply->error() != QNetworkReply::NoError) {
        m_errorString = reply->errorString();
        emit finished(false);
        return;
    }

    QJsonDocument doc = QJsonDocument::fromJson(reply->readAll());
    QJsonObject obj = doc.object();

    if (obj.contains("error")) {
        m_errorString = obj["error"].toObject()["message"].toString();
        emit finished(false);
        return;
    }

    QJsonArray choices = obj["choices"].toArray();
    if (choices.isEmpty()) {
        m_errorString = "No response choices returned";
        emit finished(false);
        return;
    }

    m_fullResponse = choices[0].toObject()["message"].toObject()["content"].toString();
    emit streamChunk(m_fullResponse);
    emit finished(true);
}

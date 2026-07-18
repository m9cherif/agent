#include "WebSearchTool.h"
#include <QJsonDocument>
#include <QJsonArray>
#include <QUrl>
#include <QUrlQuery>

WebSearchTool::WebSearchTool(QObject* parent)
    : BaseTool(parent), m_manager(new QNetworkAccessManager(this))
{
}

ReActLoop::Result WebSearchTool::execute(const QJsonObject& params) {
    QString query = params["query"].toString();
    if (query.isEmpty()) {
        return {false, "No search query provided"};
    }

    QUrl url("https://api.duckduckgo.com");
    QUrlQuery queryParams;
    queryParams.addQueryItem("q", query);
    queryParams.addQueryItem("format", "json");
    queryParams.addQueryItem("no_html", "1");
    url.setQuery(queryParams);

    QNetworkRequest request(url);
    request.setRawHeader("User-Agent", "JarvisAssistant/1.0");

    QNetworkReply* reply = m_manager->get(request);

    QEventLoop loop;
    connect(reply, &QNetworkReply::finished, &loop, &QEventLoop::quit);
    loop.exec();

    if (reply->error() != QNetworkReply::NoError) {
        reply->deleteLater();
        return {false, "Search failed: " + reply->errorString()};
    }

    QJsonDocument doc = QJsonDocument::fromJson(reply->readAll());
    reply->deleteLater();

    QJsonObject root = doc.object();
    QString abstract = root["Abstract"].toString();
    if (abstract.isEmpty()) {
        abstract = root["AbstractText"].toString();
    }

    return {true, abstract.isEmpty() ? "No results found" : abstract};
}

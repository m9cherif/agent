#pragma once
#include "BaseTool.h"
#include <QNetworkAccessManager>

class WebSearchTool : public BaseTool {
    Q_OBJECT
public:
    explicit WebSearchTool(QObject* parent = nullptr);

    QString name() const override { return "web_search"; }
    QString description() const override { return "Search the web for information"; }
    ReActLoop::Result execute(const QJsonObject& params) override;

private:
    QNetworkAccessManager* m_manager;
};

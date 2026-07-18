#pragma once
#include "BaseTool.h"
#include <QProcess>

class SystemControlTool : public BaseTool {
    Q_OBJECT
public:
    explicit SystemControlTool(QObject* parent = nullptr);

    QString name() const override { return "system_control"; }
    QString description() const override { return "Execute system commands and control desktop"; }
    ReActLoop::Result execute(const QJsonObject& params) override;
};

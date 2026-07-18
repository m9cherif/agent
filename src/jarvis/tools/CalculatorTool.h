#pragma once
#include "BaseTool.h"
#include <QScriptEngine>

class CalculatorTool : public BaseTool {
    Q_OBJECT
public:
    explicit CalculatorTool(QObject* parent = nullptr);

    QString name() const override { return "calculator"; }
    QString description() const override { return "Evaluate mathematical expressions"; }
    ReActLoop::Result execute(const QJsonObject& params) override;
};

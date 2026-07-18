#include "CalculatorTool.h"
#include <QJSEngine>
#include <QRegularExpression>

CalculatorTool::CalculatorTool(QObject* parent) : BaseTool(parent) {}

ReActLoop::Result CalculatorTool::execute(const QJsonObject& params) {
    QString expression = params["expression"].toString();
    if (expression.isEmpty()) {
        expression = params["expr"].toString();
    }
    if (expression.isEmpty()) {
        return {false, "No expression provided"};
    }

    expression.replace(QRegularExpression("[^0-9+\\-*/.()% ]"), "");

    QJSEngine engine;
    QJSValue result = engine.evaluate(expression);

    if (result.isError()) {
        return {false, "Calculation error: " + result.toString()};
    }

    return {true, QString("= %1").arg(result.toNumber(), 0, 'f', 10)};
}

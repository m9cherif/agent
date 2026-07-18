#pragma once
#include <QObject>
#include <QJsonObject>
#include <QString>
#include "../core/ReActLoop.h"

class BaseTool : public QObject {
    Q_OBJECT
public:
    explicit BaseTool(QObject* parent = nullptr) : QObject(parent) {}
    virtual ~BaseTool() = default;

    virtual QString name() const = 0;
    virtual QString description() const = 0;
    virtual ReActLoop::Result execute(const QJsonObject& params) = 0;
};

#pragma once
#include <QObject>
#include <QHash>
#include <QString>

class BaseTool;

class ToolRegistry : public QObject {
    Q_OBJECT
public:
    explicit ToolRegistry(QObject* parent = nullptr);

    void registerTool(const QString& name, BaseTool* tool);
    BaseTool* getTool(const QString& name) const;
    QStringList availableTools() const;

private:
    QHash<QString, BaseTool*> m_tools;
};

#include "ToolRegistry.h"
#include "../tools/BaseTool.h"

ToolRegistry::ToolRegistry(QObject* parent) : QObject(parent) {}

void ToolRegistry::registerTool(const QString& name, BaseTool* tool) {
    m_tools.insert(name, tool);
    tool->setParent(this);
}

BaseTool* ToolRegistry::getTool(const QString& name) const {
    return m_tools.value(name, nullptr);
}

QStringList ToolRegistry::availableTools() const {
    return m_tools.keys();
}

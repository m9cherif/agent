#include "Governance.h"

Governance::Governance(QObject* parent) : QObject(parent) {}

void Governance::setLevel(int level) {
    m_level = qBound(0, level, 2);
}

bool Governance::isActionAllowed(const QString& toolName, const QJsonObject& params) {
    if (m_alwaysBlocked.contains(toolName)) {
        emit actionBlocked(toolName, "Tool is always blocked for security");
        return false;
    }

    if (m_level >= High) {
        QString action = params["action"].toString();
        QString path = params["path"].toString();

        if (toolName == "file_write" || toolName == "file_io") {
            if (path.contains(":\\Windows", Qt::CaseInsensitive) ||
                path.contains(":\\System32", Qt::CaseInsensitive)) {
                emit actionBlocked(toolName, "Writing to system directories is blocked");
                return false;
            }
        }

        if (toolName == "run_command") {
            if (action == "run") {
                emit actionBlocked(toolName, "Running arbitrary commands requires confirmation");
                return false;
            }
        }
    }

    if (m_level >= Medium) {
        QString action = params["action"].toString();
        if (toolName == "file_io" && action == "delete") {
            emit actionBlocked(toolName, "File deletion requires explicit user confirmation");
            return false;
        }
        if (toolName == "run_command") {
            if (action == "shutdown" || action == "restart") {
                emit actionBlocked(toolName, "System power actions blocked");
                return false;
            }
        }
    }

    return true;
}

QStringList Governance::allowedTools() const {
    if (m_level >= High) {
        return {"web_search", "calculator", "file_read", "clipboard_get"};
    }
    if (m_level >= Medium) {
        return {"web_search", "calculator", "file_read", "file_write",
                "clipboard_get", "clipboard_set", "file_io"};
    }
    return {};
}

QStringList Governance::blockedTools() const {
    return m_alwaysBlocked;
}

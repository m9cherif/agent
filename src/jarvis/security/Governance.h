#pragma once
#include <QObject>
#include <QJsonObject>
#include <QString>
#include <QStringList>

class Governance : public QObject {
    Q_OBJECT
public:
    explicit Governance(QObject* parent = nullptr);

    enum Level {
        Low = 0,
        Medium = 1,
        High = 2
    };

    void setLevel(int level);
    int level() const { return m_level; }

    bool isActionAllowed(const QString& toolName, const QJsonObject& params);

    QStringList allowedTools() const;
    QStringList blockedTools() const;

signals:
    void actionBlocked(const QString& tool, const QString& reason);
    void actionRequiresConfirmation(const QString& tool, const QString& details);

private:
    int m_level = Medium;
    QStringList m_alwaysBlocked = {
        "rmdir_force", "format_drive", "shutdown_force",
        "delete_system_file", "modify_registry"
    };
};

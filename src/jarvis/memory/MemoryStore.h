#pragma once
#include <QObject>
#include <QSqlDatabase>
#include <QString>
#include <QJsonArray>
#include <QDateTime>

class MemoryStore : public QObject {
    Q_OBJECT
public:
    explicit MemoryStore(QObject* parent = nullptr);
    ~MemoryStore();

    bool initialize(const QString& dbPath = QString());

    void addConversationEntry(const QString& role, const QString& content);
    QJsonArray getConversationHistory(int limit = 50);
    void clearConversation();

    void saveUserPreference(const QString& key, const QString& value);
    QString getUserPreference(const QString& key);

    void saveContext(const QString& key, const QString& value);
    QString getContext(const QString& key);

    int totalConversations() const;

private:
    void createTables();
    QSqlDatabase m_db;
    int m_sessionId;
};

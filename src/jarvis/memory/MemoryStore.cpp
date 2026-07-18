#include "MemoryStore.h"
#include <QSqlQuery>
#include <QSqlError>
#include <QStandardPaths>
#include <QDir>
#include <QDebug>

MemoryStore::MemoryStore(QObject* parent) : QObject(parent), m_sessionId(0) {}

MemoryStore::~MemoryStore() {
    if (m_db.isOpen()) m_db.close();
}

bool MemoryStore::initialize(const QString& dbPath) {
    QString path = dbPath;
    if (path.isEmpty()) {
        path = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation)
               + "/memory.db";
    }

    QDir().mkpath(QFileInfo(path).absolutePath());

    m_db = QSqlDatabase::addDatabase("QSQLITE", "jarvis_memory");
    m_db.setDatabaseName(path);

    if (!m_db.open()) {
        qWarning() << "Failed to open memory DB:" << m_db.lastError().text();
        return false;
    }

    createTables();

    QSqlQuery query(m_db);
    query.exec("INSERT INTO sessions (started_at) VALUES (datetime('now'))");
    m_sessionId = query.lastInsertId().toInt();

    return true;
}

void MemoryStore::createTables() {
    QSqlQuery query(m_db);

    query.exec(
        "CREATE TABLE IF NOT EXISTS conversations ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  session_id INTEGER,"
        "  role TEXT NOT NULL,"
        "  content TEXT NOT NULL,"
        "  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP"
        ")"
    );

    query.exec(
        "CREATE TABLE IF NOT EXISTS preferences ("
        "  key TEXT PRIMARY KEY,"
        "  value TEXT"
        ")"
    );

    query.exec(
        "CREATE TABLE IF NOT EXISTS context ("
        "  key TEXT PRIMARY KEY,"
        "  value TEXT,"
        "  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
        ")"
    );

    query.exec(
        "CREATE TABLE IF NOT EXISTS sessions ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  started_at DATETIME DEFAULT CURRENT_TIMESTAMP"
        ")"
    );
}

void MemoryStore::addConversationEntry(const QString& role, const QString& content) {
    QSqlQuery query(m_db);
    query.prepare("INSERT INTO conversations (session_id, role, content) VALUES (?, ?, ?)");
    query.addBindValue(m_sessionId);
    query.addBindValue(role);
    query.addBindValue(content);
    query.exec();
}

QJsonArray MemoryStore::getConversationHistory(int limit) {
    QJsonArray history;
    QSqlQuery query(m_db);
    query.prepare(
        "SELECT role, content FROM conversations WHERE session_id = ? "
        "ORDER BY id DESC LIMIT ?"
    );
    query.addBindValue(m_sessionId);
    query.addBindValue(limit);
    query.exec();

    while (query.next()) {
        QJsonObject entry;
        entry["role"] = query.value(0).toString();
        entry["content"] = query.value(1).toString();
        history.prepend(entry);
    }
    return history;
}

void MemoryStore::clearConversation() {
    QSqlQuery query(m_db);
    query.prepare("DELETE FROM conversations WHERE session_id = ?");
    query.addBindValue(m_sessionId);
    query.exec();
}

void MemoryStore::saveUserPreference(const QString& key, const QString& value) {
    QSqlQuery query(m_db);
    query.prepare("INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)");
    query.addBindValue(key);
    query.addBindValue(value);
    query.exec();
}

QString MemoryStore::getUserPreference(const QString& key) {
    QSqlQuery query(m_db);
    query.prepare("SELECT value FROM preferences WHERE key = ?");
    query.addBindValue(key);
    if (query.exec() && query.next()) {
        return query.value(0).toString();
    }
    return {};
}

void MemoryStore::saveContext(const QString& key, const QString& value) {
    QSqlQuery query(m_db);
    query.prepare("INSERT OR REPLACE INTO context (key, value, updated_at) VALUES (?, ?, datetime('now'))");
    query.addBindValue(key);
    query.addBindValue(value);
    query.exec();
}

QString MemoryStore::getContext(const QString& key) {
    QSqlQuery query(m_db);
    query.prepare("SELECT value FROM context WHERE key = ?");
    query.addBindValue(key);
    if (query.exec() && query.next()) {
        return query.value(0).toString();
    }
    return {};
}

int MemoryStore::totalConversations() const {
    QSqlQuery query(m_db);
    query.exec("SELECT COUNT(*) FROM conversations");
    if (query.next()) return query.value(0).toInt();
    return 0;
}

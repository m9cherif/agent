#include <QTest>
#include <QJsonObject>
#include <QJsonArray>
#include <QJsonDocument>
#include <QSqlDatabase>
#include <QSqlQuery>
#include <QTemporaryDir>

class TestMemory : public QObject {
    Q_OBJECT

private slots:
    void testInMemoryDatabase() {
        QTemporaryDir tempDir;
        QVERIFY(tempDir.isValid());

        QString dbPath = tempDir.path() + "/test_memory.db";
        {
            QSqlDatabase db = QSqlDatabase::addDatabase("QSQLITE", "test_connection");
            db.setDatabaseName(dbPath);
            QVERIFY(db.open());

            QSqlQuery query(db);
            QVERIFY(query.exec(
                "CREATE TABLE IF NOT EXISTS conversations ("
                "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "  session_id INTEGER,"
                "  role TEXT NOT NULL,"
                "  content TEXT NOT NULL,"
                "  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP"
                ")"
            ));

            QVERIFY(query.exec(
                "INSERT INTO conversations (session_id, role, content) "
                "VALUES (1, 'user', 'Hello'), (1, 'assistant', 'Hi there')"
            ));

            QVERIFY(query.exec("SELECT COUNT(*) FROM conversations"));
            QVERIFY(query.next());
            QCOMPARE(query.value(0).toInt(), 2);

            QVERIFY(query.exec("SELECT role, content FROM conversations WHERE session_id = 1"));
            int count = 0;
            while (query.next()) {
                count++;
                QVERIFY(!query.value(0).toString().isEmpty());
                QVERIFY(!query.value(1).toString().isEmpty());
            }
            QCOMPARE(count, 2);

            db.close();
        }
        QSqlDatabase::removeDatabase("test_connection");
    }

    void testPreferencesStorage() {
        QTemporaryDir tempDir;
        QVERIFY(tempDir.isValid());

        QString dbPath = tempDir.path() + "/test_prefs.db";
        {
            QSqlDatabase db = QSqlDatabase::addDatabase("QSQLITE", "prefs_connection");
            db.setDatabaseName(dbPath);
            QVERIFY(db.open());

            QSqlQuery query(db);
            QVERIFY(query.exec(
                "CREATE TABLE IF NOT EXISTS preferences ("
                "  key TEXT PRIMARY KEY,"
                "  value TEXT"
                ")"
            ));

            QVERIFY(query.exec(
                "INSERT OR REPLACE INTO preferences (key, value) "
                "VALUES ('theme', 'dark'), ('language', 'en')"
            ));

            QVERIFY(query.exec("SELECT value FROM preferences WHERE key = 'theme'"));
            QVERIFY(query.next());
            QCOMPARE(query.value(0).toString(), QString("dark"));

            db.close();
        }
        QSqlDatabase::removeDatabase("prefs_connection");
    }
};

QTEST_MAIN(TestMemory)
#include "test_memory.moc"

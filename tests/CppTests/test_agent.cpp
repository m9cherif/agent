#include <QTest>
#include <QJsonObject>
#include <QJsonDocument>
#include <QRegularExpression>

class TestAgent : public QObject {
    Q_OBJECT

private slots:
    void testToolRegistry() {
        QStringList tools;
        tools << "calculator" << "web_search" << "file_io";
        QCOMPARE(tools.size(), 3);
        QVERIFY(tools.contains("calculator"));
        QVERIFY(!tools.contains("unknown"));
    }

    void testGovernanceLevels() {
        struct TestCase {
            int level;
            bool shouldBlock;
        };

        QList<TestCase> cases = {
            {0, false},
            {1, false},
            {2, true}
        };

        for (const auto& c : cases) {
            bool blocked = (c.level >= 2);
            QCOMPARE(blocked, c.shouldBlock);
        }
    }

    void testMemorySchema() {
        QJsonArray history;
        QJsonObject entry;
        entry["role"] = "user";
        entry["content"] = "Hello JARVIS";
        history.append(entry);

        entry["role"] = "assistant";
        entry["content"] = "Hello! How can I help?";
        history.append(entry);

        QCOMPARE(history.size(), 2);
        QCOMPARE(history[0].toObject()["role"].toString(), QString("user"));
        QCOMPARE(history[1].toObject()["role"].toString(), QString("assistant"));
    }

    void testToolActionJson() {
        QString validJson = R"({"tool":"web_search","params":{"query":"test"}})";
        QJsonParseError err;
        QJsonDocument doc = QJsonDocument::fromJson(validJson.toUtf8(), &err);
        QCOMPARE(err.error, QJsonParseError::NoError);
        QVERIFY(doc.isObject());

        QString invalidJson = R"({"tool":})";
        doc = QJsonDocument::fromJson(invalidJson.toUtf8(), &err);
        QVERIFY(err.error != QJsonParseError::NoError);
    }
};

QTEST_MAIN(TestAgent)
#include "test_agent.moc"

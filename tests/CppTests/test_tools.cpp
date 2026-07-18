#include <QTest>
#include <QJsonObject>
#include <QJsonDocument>
#include <QRegularExpression>

class TestTools : public QObject {
    Q_OBJECT

private slots:
    void testReActActionParsing() {
        QString text = "THOUGHT: I need to search for something\n"
                       "ACTION: {\"tool\":\"web_search\",\"params\":{\"query\":\"weather\"}}\n"
                       "FINAL: Done";

        QRegularExpression re(R"(\{"tool"\s*:\s*"[^"]+"\s*,\s*"params"\s*:\s*\{[^}]*\}\})");
        QRegularExpressionMatch match = re.match(text);
        QVERIFY(match.hasMatch());

        QJsonParseError err;
        QJsonDocument doc = QJsonDocument::fromJson(match.captured().toUtf8(), &err);
        QCOMPARE(err.error, QJsonParseError::NoError);
        QVERIFY(doc.isObject());

        QJsonObject obj = doc.object();
        QCOMPARE(obj["tool"].toString(), QString("web_search"));
        QVERIFY(obj["params"].isObject());
        QCOMPARE(obj["params"].toObject()["query"].toString(), QString("weather"));
    }

    void testNoActionInPlainText() {
        QString text = "Hello, how are you today?";
        QRegularExpression re(R"(\{"tool"\s*:\s*"[^"]+"\s*,\s*"params"\s*:\s*\{[^}]*\}\})");
        QRegularExpressionMatch match = re.match(text);
        QVERIFY(!match.hasMatch());
    }

    void testConfigJsonParsing() {
        QJsonObject config;
        config["openrouter_key"] = "test-key";
        config["model"] = "openrouter/free";
        config["governance_level"] = 1;

        QCOMPARE(config["openrouter_key"].toString(), QString("test-key"));
        QCOMPARE(config["model"].toString(), QString("openrouter/free"));
        QCOMPARE(config["governance_level"].toInt(), 1);
    }
};

QTEST_MAIN(TestTools)
#include "test_tools.moc"

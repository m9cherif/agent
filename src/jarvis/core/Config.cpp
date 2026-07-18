#include "Config.h"
#include <QFile>
#include <QJsonDocument>
#include <QJsonArray>
#include <QStandardPaths>
#include <QDir>

Config& Config::instance() {
    static Config cfg;
    return cfg;
}

void Config::load(const QString& path) {
    QString configPath = path;
    if (!QFile::exists(configPath)) {
        configPath = QStandardPaths::writableLocation(QStandardPaths::AppConfigLocation)
                     + "/JarvisConfig.json";
    }

    QFile file(configPath);
    if (!file.open(QIODevice::ReadOnly)) return;

    QJsonObject obj = QJsonDocument::fromJson(file.readAll()).object();
    file.close();

    m_openRouterKey = obj["openrouter_key"].toString();
    m_openRouterBaseUrl = obj["openrouter_base_url"].toString("https://openrouter.ai/api/v1");
    m_model = obj["model"].toString("openrouter/free");
    m_governanceLevel = obj["governance_level"].toInt(1);
    m_wakeWordEnabled = obj["wake_word_enabled"].toBool(true);
    m_ttsEnabled = obj["tts_enabled"].toBool(true);
    m_pythonPath = obj["python_path"].toString("python");

    QJsonArray arr = obj["recent_conversations"].toArray();
    for (const auto& v : arr) m_recentConversations.append(v.toString());
}

void Config::save() {
    QString configPath = QStandardPaths::writableLocation(QStandardPaths::AppConfigLocation);
    QDir().mkpath(configPath);
    configPath += "/JarvisConfig.json";

    QJsonObject obj;
    obj["openrouter_key"] = m_openRouterKey;
    obj["openrouter_base_url"] = m_openRouterBaseUrl;
    obj["model"] = m_model;
    obj["governance_level"] = m_governanceLevel;
    obj["wake_word_enabled"] = m_wakeWordEnabled;
    obj["tts_enabled"] = m_ttsEnabled;
    obj["python_path"] = m_pythonPath;

    QJsonArray arr;
    for (const auto& c : m_recentConversations) arr.append(c);
    obj["recent_conversations"] = arr;

    QFile file(configPath);
    if (file.open(QIODevice::WriteOnly)) {
        file.write(QJsonDocument(obj).toJson());
        file.close();
    }
}

void Config::setOpenRouterKey(const QString& key) { m_openRouterKey = key; save(); }
void Config::setOpenRouterBaseUrl(const QString& url) { m_openRouterBaseUrl = url; save(); }
void Config::setModel(const QString& model) { m_model = model; save(); }
void Config::setGovernanceLevel(int level) { m_governanceLevel = level; save(); }
void Config::setWakeWordEnabled(bool enabled) { m_wakeWordEnabled = enabled; save(); }
void Config::setTtsEnabled(bool enabled) { m_ttsEnabled = enabled; save(); }
void Config::setPythonPath(const QString& path) { m_pythonPath = path; save(); }

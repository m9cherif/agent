#pragma once
#include <QString>
#include <QJsonObject>
#include <QSettings>

class Config {
public:
    static Config& instance();

    void load(const QString& path = "JarvisConfig.json");
    void save();

    QString openRouterKey() const { return m_openRouterKey; }
    void setOpenRouterKey(const QString& key);

    QString openRouterBaseUrl() const { return m_openRouterBaseUrl; }
    void setOpenRouterBaseUrl(const QString& url);

    QString model() const { return m_model; }
    void setModel(const QString& model);

    int governanceLevel() const { return m_governanceLevel; }
    void setGovernanceLevel(int level);

    bool wakeWordEnabled() const { return m_wakeWordEnabled; }
    void setWakeWordEnabled(bool enabled);

    bool ttsEnabled() const { return m_ttsEnabled; }
    void setTtsEnabled(bool enabled);

    QString pythonPath() const { return m_pythonPath; }
    void setPythonPath(const QString& path);

    QStringList recentConversations() const { return m_recentConversations; }

private:
    Config() = default;

    QString m_openRouterKey;
    QString m_openRouterBaseUrl = "https://openrouter.ai/api/v1";
    QString m_model = "openrouter/free";
    int m_governanceLevel = 1;
    bool m_wakeWordEnabled = true;
    bool m_ttsEnabled = true;
    QString m_pythonPath = "python";
    QStringList m_recentConversations;
};

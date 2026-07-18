#pragma once
#include <QObject>
#include <QString>
#include <QJsonObject>
#include <QHash>
#include <QProcess>
#include <QLibrary>

class PluginLoader : public QObject {
    Q_OBJECT
public:
    explicit PluginLoader(QObject* parent = nullptr);

    bool loadPlugin(const QString& pluginPath);
    bool loadFromDirectory(const QString& dirPath);
    void unloadPlugin(const QString& pluginName);

    QStringList loadedPlugins() const { return m_plugins.keys(); }
    QJsonObject pluginManifest(const QString& name) const;

signals:
    void pluginLoaded(const QString& name, const QString& version);
    void pluginError(const QString& name, const QString& error);

private:
    QJsonObject loadManifest(const QString& manifestPath);

    struct PluginInfo {
        QString name;
        QString version;
        QString entryPoint;
        QString type;
        QString path;
        QProcess* process = nullptr;
    };

    QHash<QString, PluginInfo> m_plugins;
};

#include "PluginLoader.h"
#include <QDir>
#include <QFile>
#include <QJsonDocument>
#include <QJsonArray>

PluginLoader::PluginLoader(QObject* parent) : QObject(parent) {}

bool PluginLoader::loadPlugin(const QString& pluginPath) {
    QDir dir(pluginPath);
    if (!dir.exists()) {
        emit pluginError(dir.dirName(), "Plugin directory not found");
        return false;
    }

    QJsonObject manifest = loadManifest(dir.filePath("manifest.json"));
    if (manifest.isEmpty()) {
        emit pluginError(dir.dirName(), "Invalid or missing manifest.json");
        return false;
    }

    PluginInfo info;
    info.name = manifest["name"].toString(dir.dirName());
    info.version = manifest["version"].toString("0.0.1");
    info.entryPoint = manifest["entry_point"].toString("plugin.py");
    info.type = manifest["type"].toString("python");
    info.path = pluginPath;
    info.process = nullptr;

    if (info.type == "python") {
        QString scriptPath = dir.filePath(info.entryPoint);
        if (!QFile::exists(scriptPath)) {
            emit pluginError(info.name, "Entry point not found: " + info.entryPoint);
            return false;
        }

        info.process = new QProcess(this);
        info.process->setWorkingDirectory(pluginPath);
        info.process->start("python", {scriptPath});
    }

    m_plugins[info.name] = info;
    emit pluginLoaded(info.name, info.version);
    return true;
}

bool PluginLoader::loadFromDirectory(const QString& dirPath) {
    QDir dir(dirPath);
    if (!dir.exists()) return false;

    bool anyLoaded = false;
    for (const QString& subDir : dir.entryList(QDir::Dirs | QDir::NoDotAndDotDot)) {
        if (loadPlugin(dir.filePath(subDir))) {
            anyLoaded = true;
        }
    }
    return anyLoaded;
}

void PluginLoader::unloadPlugin(const QString& pluginName) {
    if (!m_plugins.contains(pluginName)) return;

    PluginInfo& info = m_plugins[pluginName];
    if (info.process) {
        info.process->kill();
        info.process->waitForFinished(3000);
        info.process->deleteLater();
    }
    m_plugins.remove(pluginName);
}

QJsonObject PluginLoader::pluginManifest(const QString& name) const {
    if (!m_plugins.contains(name)) return {};
    QJsonObject manifest;
    manifest["name"] = m_plugins[name].name;
    manifest["version"] = m_plugins[name].version;
    manifest["type"] = m_plugins[name].type;
    return manifest;
}

QJsonObject PluginLoader::loadManifest(const QString& manifestPath) {
    QFile file(manifestPath);
    if (!file.open(QIODevice::ReadOnly)) return {};

    QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
    file.close();

    if (!doc.isObject()) return {};
    return doc.object();
}

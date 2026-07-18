#include "FileIOTool.h"
#include <QFile>
#include <QFileInfo>
#include <QDir>

FileIOTool::FileIOTool(QObject* parent) : BaseTool(parent) {}

ReActLoop::Result FileIOTool::execute(const QJsonObject& params) {
    QString action = params["action"].toString();
    QString path = params["path"].toString();
    QString content = params["content"].toString();

    if (path.isEmpty()) {
        return {false, "No file path provided"};
    }

    if (action == "read") {
        QFile file(path);
        if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
            return {false, "Cannot open file: " + path};
        }
        QString data = file.readAll();
        file.close();
        return {true, data};
    }
    else if (action == "write") {
        QDir().mkpath(QFileInfo(path).absolutePath());
        QFile file(path);
        if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) {
            return {false, "Cannot write to file: " + path};
        }
        file.write(content.toUtf8());
        file.close();
        return {true, "File written successfully: " + path};
    }
    else if (action == "list") {
        QDir dir(path);
        if (!dir.exists()) return {false, "Directory not found: " + path};
        QStringList entries = dir.entryList(QDir::Files | QDir::Dirs | QDir::NoDotAndDotDot);
        return {true, "Files: " + entries.join(", ")};
    }
    else if (action == "info") {
        QFileInfo info(path);
        if (!info.exists()) return {false, "Path not found: " + path};
        QString result = QString("Size: %1 bytes, Modified: %2, IsDir: %3")
            .arg(info.size())
            .arg(info.lastModified().toString(Qt::ISODate))
            .arg(info.isDir() ? "yes" : "no");
        return {true, result};
    }

    return {false, "Unknown action: " + action};
}

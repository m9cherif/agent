#include "SystemControlTool.h"
#include <QProcess>
#include <QDir>

SystemControlTool::SystemControlTool(QObject* parent) : BaseTool(parent) {}

ReActLoop::Result SystemControlTool::execute(const QJsonObject& params) {
    QString action = params["action"].toString();
    QString target = params["target"].toString();

    if (action == "run") {
        QString cmd = params["command"].toString();
        if (cmd.isEmpty()) return {false, "No command specified"};

        QProcess process;
        process.start("cmd.exe", QStringList() << "/c" << cmd);
        process.waitForFinished(30000);
        QString output = process.readAllStandardOutput();
        QString error = process.readAllStandardError();
        if (!error.isEmpty()) output += "\nSTDERR: " + error;
        return {true, output.isEmpty() ? "Command executed (no output)" : output};
    }
    else if (action == "open") {
        QProcess::startDetached("cmd.exe", QStringList() << "/c" << "start" << target);
        return {true, "Opened: " + target};
    }
    else if (action == "volume") {
        int level = params["level"].toInt(-1);
        if (level >= 0 && level <= 100) {
            QProcess::startDetached("cmd.exe", QStringList() << "/c"
                << "nircmd.exe setsysvolume " + QString::number(level * 655.35));
            return {true, "Volume set to " + QString::number(level) + "%"};
        }
        return {false, "Volume level must be 0-100"};
    }

    return {false, "Unknown action: " + action};
}

#include <QApplication>
#include <QIcon>
#include <QFile>
#include <QTextStream>
#include "ui/MainWindow.h"
#include "core/Config.h"

static void loadEnvFile(const QString& path = ".env") {
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) return;
    QTextStream in(&file);
    while (!in.atEnd()) {
        QString line = in.readLine().trimmed();
        if (line.isEmpty() || line.startsWith('#')) continue;
        int eq = line.indexOf('=');
        if (eq < 0) continue;
        QString key = line.left(eq).trimmed();
        QString val = line.mid(eq + 1).trimmed();
        if (!key.isEmpty() && !val.isEmpty()) {
            qputenv(key.toUtf8(), val.toUtf8());
        }
    }
    file.close();
}

int main(int argc, char* argv[]) {
    QApplication app(argc, argv);
    app.setApplicationName("JARVIS");
    app.setApplicationVersion("1.0.0");
    app.setOrganizationName("JarvisAssistant");
    app.setOrganizationDomain("jarvis.ai");
    app.setQuitOnLastWindowClosed(false);

    app.setWindowIcon(QIcon(":/icons/jarvis.svg"));

    loadEnvFile(".env");

    QFile styleFile(":/styles/main.qss");
    if (styleFile.open(QIODevice::ReadOnly)) {
        app.setStyleSheet(styleFile.readAll());
        styleFile.close();
    }

    Config::instance().load();

    MainWindow window;
    window.initialize();
    window.show();

    return app.exec();
}

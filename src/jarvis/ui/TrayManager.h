#pragma once
#include <QObject>
#include <QSystemTrayIcon>
#include <QMenu>
#include <QAction>

class MainWindow;

class TrayManager : public QObject {
    Q_OBJECT
public:
    explicit TrayManager(QObject* parent = nullptr);
    ~TrayManager();

    void initialize();
    void showNotification(const QString& title, const QString& message);

signals:
    void showWindowRequested();
    void quitRequested();
    void toggleListeningRequested();
    void openSettingsRequested();

private:
    void createTrayIcon();
    void createMenu();

    QSystemTrayIcon* m_trayIcon;
    QMenu* m_trayMenu;
    QAction* m_showAction;
    QAction* m_listenAction;
    QAction* m_settingsAction;
    QAction* m_quitAction;
};

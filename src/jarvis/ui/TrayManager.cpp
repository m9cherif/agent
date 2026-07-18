#include "TrayManager.h"
#include <QApplication>
#include <QIcon>

TrayManager::TrayManager(QObject* parent) : QObject(parent) {
    m_trayIcon = nullptr;
    m_trayMenu = nullptr;
}

TrayManager::~TrayManager() {
    delete m_trayMenu;
}

void TrayManager::initialize() {
    createTrayIcon();
    createMenu();
    m_trayIcon->show();
}

void TrayManager::createTrayIcon() {
    m_trayIcon = new QSystemTrayIcon(this);
    m_trayIcon->setIcon(QIcon(":/icons/jarvis.svg"));
    m_trayIcon->setToolTip("JARVIS Assistant");
    m_trayIcon->setContextMenu(m_trayMenu);
}

void TrayManager::createMenu() {
    m_trayMenu = new QMenu();

    m_showAction = m_trayMenu->addAction("Show JARVIS");
    m_listenAction = m_trayMenu->addAction("Start Listening");
    m_listenAction->setCheckable(true);
    m_settingsAction = m_trayMenu->addAction("Settings...");
    m_trayMenu->addSeparator();
    m_quitAction = m_trayMenu->addAction("Quit");

    connect(m_showAction, &QAction::triggered, this, &TrayManager::showWindowRequested);
    connect(m_listenAction, &QAction::triggered, this, [this](bool checked) {
        m_listenAction->setText(checked ? "Stop Listening" : "Start Listening");
        emit toggleListeningRequested();
    });
    connect(m_settingsAction, &QAction::triggered, this, &TrayManager::openSettingsRequested);
    connect(m_quitAction, &QAction::triggered, this, &TrayManager::quitRequested);

    m_trayIcon->setContextMenu(m_trayMenu);

    connect(m_trayIcon, &QSystemTrayIcon::activated, this, [this](QSystemTrayIcon::ActivationReason reason) {
        if (reason == QSystemTrayIcon::DoubleClick) {
            emit showWindowRequested();
        }
    });
}

void TrayManager::showNotification(const QString& title, const QString& message) {
    m_trayIcon->showMessage(title, message, QSystemTrayIcon::Information, 5000);
}

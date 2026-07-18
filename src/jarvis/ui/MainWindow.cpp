#include "MainWindow.h"
#include "ChatPanel.h"
#include "TrayManager.h"
#include "SettingsDialog.h"
#include "../core/AgentOrchestrator.h"
#include "../core/Config.h"
#include "../voice/VoicePipeline.h"
#include <QApplication>
#include <QCloseEvent>
#include <QMessageBox>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QStatusBar>
#include <QMenuBar>

MainWindow::MainWindow(QWidget* parent) : QMainWindow(parent) {
    m_orchestrator = new AgentOrchestrator(this);
    m_trayManager = new TrayManager(this);
    m_minimizeToTray = true;

    setupUI();
    setupConnections();
}

MainWindow::~MainWindow() {}

void MainWindow::initialize() {
    auto& cfg = Config::instance();
    cfg.load();

    m_orchestrator->setGovernanceLevel(cfg.governanceLevel());
    m_trayManager->initialize();

    if (!cfg.openRouterKey().isEmpty()) {
        m_orchestrator->aiEngine()->setApiKey(cfg.openRouterKey());
    } else {
        QString envKey = qEnvironmentVariable("OPENROUTER_API_KEY");
        if (!envKey.isEmpty()) {
            m_orchestrator->aiEngine()->setApiKey(envKey);
            cfg.setOpenRouterKey(envKey);
        }
    }

    m_orchestrator->aiEngine()->setBaseUrl(cfg.openRouterBaseUrl());
    m_orchestrator->aiEngine()->setModel(cfg.model());
    m_orchestrator->memoryStore()->initialize();

    m_chatPanel->appendSystemMessage("JARVIS initialized. Ready.");
    updateStatus("Ready");

    if (!m_orchestrator->aiEngine()->isConfigured()) {
        m_chatPanel->appendSystemMessage(
            "OpenRouter API key not configured. Press Ctrl+Shift+S or "
            "click Settings in tray menu to configure."
        );
    }
}

void MainWindow::setupUI() {
    setWindowTitle("JARVIS - Desktop Assistant");
    setMinimumSize(800, 600);
    resize(1000, 700);

    setStyleSheet(
        "QMainWindow { background-color: #1a1a2e; }"
        "QStatusBar { background-color: #16213e; color: #888; border-top: 1px solid #0f3460; }"
    );

    auto* centralWidget = new QWidget(this);
    auto* mainLayout = new QVBoxLayout(centralWidget);
    mainLayout->setContentsMargins(8, 8, 8, 8);

    auto* splitter = new QSplitter(Qt::Vertical, this);

    m_chatPanel = new ChatPanel(this);
    splitter->addWidget(m_chatPanel);

    m_toolLog = new QListWidget(this);
    m_toolLog->setMaximumHeight(150);
    m_toolLog->setStyleSheet(
        "QListWidget { background-color: #16213e; color: #888; "
        "border: 1px solid #0f3460; border-radius: 4px; font-size: 11px; "
        "font-family: 'Consolas'; }"
        "QListWidget::item { padding: 2px 4px; }"
    );
    m_toolLog->setAlternatingRowColors(true);
    splitter->addWidget(m_toolLog);

    mainLayout->addWidget(splitter);
    setCentralWidget(centralWidget);

    m_statusLabel = new QLabel("Initializing...", this);
    statusBar()->addWidget(m_statusLabel);
}

void MainWindow::setupConnections() {
    connect(m_chatPanel, &ChatPanel::messageSent, this, [this](const QString& text) {
        m_chatPanel->appendSystemMessage("JARVIS is thinking...");
        m_orchestrator->processUserInput(text);
    });

    connect(m_orchestrator, &AgentOrchestrator::agentResponse, this, [this](const QString& response) {
        m_chatPanel->appendMessage("JARVIS", response);
        updateStatus("Ready");
    });

    connect(m_orchestrator, &AgentOrchestrator::agentThinking, this, [this](const QString& thought) {
        updateStatus("Thinking: " + thought.left(50) + "...");
    });

    connect(m_orchestrator, &AgentOrchestrator::agentError, this, [this](const QString& error) {
        m_chatPanel->appendSystemMessage("Error: " + error);
        updateStatus("Error");
    });

    connect(m_orchestrator, &AgentOrchestrator::toolExecuted, this, [this](const QString& tool, const QString& result) {
        m_toolLog->insertItem(0, QString("[%1] %2").arg(tool, result.left(80)));
        if (m_toolLog->count() > 100) m_toolLog->takeItem(m_toolLog->count() - 1);
    });

    connect(m_trayManager, &TrayManager::showWindowRequested, this, [this]() {
        show();
        raise();
        activateWindow();
    });

    connect(m_trayManager, &TrayManager::quitRequested, qApp, &QApplication::quit);
    connect(m_trayManager, &TrayManager::openSettingsRequested, this, &MainWindow::openSettings);
    connect(m_trayManager, &TrayManager::toggleListeningRequested, this, &MainWindow::toggleListening);
}

void MainWindow::openSettings() {
    SettingsDialog dialog(this);
    connect(&dialog, &SettingsDialog::settingsChanged, this, [this]() {
        auto& cfg = Config::instance();
        m_orchestrator->aiEngine()->setApiKey(cfg.openRouterKey());
        m_orchestrator->aiEngine()->setBaseUrl(cfg.openRouterBaseUrl());
        m_orchestrator->aiEngine()->setModel(cfg.model());
        m_orchestrator->setGovernanceLevel(cfg.governanceLevel());
        m_chatPanel->appendSystemMessage("Settings updated.");
    });
    dialog.exec();
}

void MainWindow::toggleListening() {
    m_chatPanel->appendSystemMessage("Voice toggle not yet available (requires Python voice pipeline)");
}

void MainWindow::updateStatus(const QString& status) {
    m_statusLabel->setText("Status: " + status);
}

void MainWindow::closeEvent(QCloseEvent* event) {
    if (m_minimizeToTray && isVisible()) {
        hide();
        m_trayManager->showNotification("JARVIS", "Still running in system tray");
        event->ignore();
    } else {
        event->accept();
    }
}

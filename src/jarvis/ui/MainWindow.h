#pragma once
#include <QMainWindow>
#include <QSplitter>
#include <QTextEdit>
#include <QListWidget>
#include <QLabel>

class ChatPanel;
class TrayManager;
class AgentOrchestrator;

class MainWindow : public QMainWindow {
    Q_OBJECT
public:
    explicit MainWindow(QWidget* parent = nullptr);
    ~MainWindow();

    void initialize();

protected:
    void closeEvent(QCloseEvent* event) override;

private:
    void setupUI();
    void setupConnections();
    void openSettings();
    void toggleListening();
    void updateStatus(const QString& status);

    ChatPanel* m_chatPanel;
    TrayManager* m_trayManager;
    AgentOrchestrator* m_orchestrator;
    QListWidget* m_toolLog;
    QLabel* m_statusLabel;
    bool m_minimizeToTray = true;
};

#pragma once
#include <QWidget>
#include <QTextEdit>
#include <QLineEdit>
#include <QPushButton>
#include <QVBoxLayout>
#include <QScrollArea>

class ChatPanel : public QWidget {
    Q_OBJECT
public:
    explicit ChatPanel(QWidget* parent = nullptr);

    void appendMessage(const QString& role, const QString& message);
    void appendSystemMessage(const QString& message);
    void clearChat();
    void setInputEnabled(bool enabled);

signals:
    void messageSent(const QString& text);

private:
    QTextEdit* m_chatDisplay;
    QLineEdit* m_inputField;
    QPushButton* m_sendButton;
    QPushButton* m_voiceButton;
    QScrollArea* m_scrollArea;
};

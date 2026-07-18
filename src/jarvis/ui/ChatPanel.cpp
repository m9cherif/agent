#include "ChatPanel.h"
#include <QDateTime>
#include <QScrollBar>

ChatPanel::ChatPanel(QWidget* parent) : QWidget(parent) {
    auto* layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);
    layout->setSpacing(4);

    m_chatDisplay = new QTextEdit(this);
    m_chatDisplay->setReadOnly(true);
    m_chatDisplay->setStyleSheet(
        "QTextEdit { background-color: #1a1a2e; color: #e0e0e0; "
        "border: none; font-family: 'Consolas'; font-size: 13px; }"
    );

    auto* inputLayout = new QHBoxLayout();
    m_voiceButton = new QPushButton("🎤", this);
    m_voiceButton->setFixedSize(36, 36);
    m_voiceButton->setToolTip("Voice input");
    m_voiceButton->setStyleSheet(
        "QPushButton { background: #16213e; color: #0f3460; border: 1px solid #0f3460; "
        "border-radius: 18px; font-size: 16px; }"
        "QPushButton:hover { background: #0f3460; color: #e94560; }"
    );

    m_inputField = new QLineEdit(this);
    m_inputField->setPlaceholderText("Ask JARVIS anything...");
    m_inputField->setStyleSheet(
        "QLineEdit { background-color: #16213e; color: #e0e0e0; "
        "border: 1px solid #0f3460; border-radius: 8px; padding: 8px 12px; "
        "font-family: 'Consolas'; font-size: 13px; }"
        "QLineEdit:focus { border-color: #e94560; }"
    );

    m_sendButton = new QPushButton("Send", this);
    m_sendButton->setFixedWidth(80);
    m_sendButton->setStyleSheet(
        "QPushButton { background-color: #e94560; color: white; border: none; "
        "border-radius: 8px; padding: 8px 16px; font-weight: bold; }"
        "QPushButton:hover { background-color: #c73652; }"
        "QPushButton:disabled { background-color: #555; }"
    );

    inputLayout->addWidget(m_voiceButton);
    inputLayout->addWidget(m_inputField);
    inputLayout->addWidget(m_sendButton);

    layout->addWidget(m_chatDisplay, 1);
    layout->addLayout(inputLayout);

    connect(m_sendButton, &QPushButton::clicked, this, [this]() {
        QString text = m_inputField->text().trimmed();
        if (!text.isEmpty()) {
            appendMessage("You", text);
            emit messageSent(text);
            m_inputField->clear();
        }
    });

    connect(m_inputField, &QLineEdit::returnPressed, m_sendButton, &QPushButton::click);
}

void ChatPanel::appendMessage(const QString& role, const QString& message) {
    QString timestamp = QDateTime::currentDateTime().toString("HH:mm:ss");
    QString html;
    if (role == "You") {
        html = QString("<div style='margin: 4px 0;'>"
            "<span style='color: #e94560; font-weight: bold;'>[%1] %2:</span> "
            "<span style='color: #ffffff;'>%3</span></div>")
            .arg(timestamp, role, message.toHtmlEscaped());
    } else {
        html = QString("<div style='margin: 4px 0;'>"
            "<span style='color: #0f3460; font-weight: bold;'>[%1] %2:</span> "
            "<span style='color: #00ff88;'>%3</span></div>")
            .arg(timestamp, role, message.toHtmlEscaped());
    }

    m_chatDisplay->append(html);
    QScrollBar* sb = m_chatDisplay->verticalScrollBar();
    sb->setValue(sb->maximum());
}

void ChatPanel::appendSystemMessage(const QString& message) {
    QString timestamp = QDateTime::currentDateTime().toString("HH:mm:ss");
    QString html = QString("<div style='margin: 2px 0; color: #888; font-style: italic;'>"
        "[%1] %2</div>").arg(timestamp, message.toHtmlEscaped());
    m_chatDisplay->append(html);
}

void ChatPanel::clearChat() {
    m_chatDisplay->clear();
}

void ChatPanel::setInputEnabled(bool enabled) {
    m_inputField->setEnabled(enabled);
    m_sendButton->setEnabled(enabled);
}

#include "SettingsDialog.h"
#include "../core/Config.h"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFormLayout>
#include <QGroupBox>
#include <QMessageBox>

SettingsDialog::SettingsDialog(QWidget* parent) : QDialog(parent) {
    setWindowTitle("JARVIS Settings");
    setFixedSize(500, 500);
    setStyleSheet(
        "QDialog { background-color: #1a1a2e; color: #e0e0e0; }"
        "QGroupBox { border: 1px solid #0f3460; border-radius: 8px; "
        "margin-top: 12px; padding-top: 12px; color: #e94560; font-weight: bold; }"
        "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }"
        "QLineEdit, QComboBox, QSpinBox { "
        "background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; "
        "border-radius: 4px; padding: 6px; }"
        "QCheckBox { color: #e0e0e0; }"
    );

    auto* mainLayout = new QVBoxLayout(this);

    auto* aiGroup = new QGroupBox("AI Configuration");
    auto* aiForm = new QFormLayout(aiGroup);

    m_apiKeyEdit = new QLineEdit(this);
    m_apiKeyEdit->setEchoMode(QLineEdit::Password);
    m_apiKeyEdit->setPlaceholderText("OpenRouter API Key (from env or manual)");
    aiForm->addRow("API Key:", m_apiKeyEdit);

    m_baseUrlEdit = new QLineEdit(this);
    m_baseUrlEdit->setPlaceholderText("https://openrouter.ai/api/v1");
    aiForm->addRow("Base URL:", m_baseUrlEdit);

    m_modelCombo = new QComboBox(this);
    m_modelCombo->setEditable(true);
    m_modelCombo->addItems({
        "openrouter/free",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "anthropic/claude-3.5-sonnet",
        "google/gemini-2.0-flash",
        "meta-llama/llama-3.3-70b-instruct",
        "mistralai/mistral-7b-instruct"
    });
    aiForm->addRow("Model:", m_modelCombo);

    auto* voiceGroup = new QGroupBox("Voice Settings");
    auto* voiceForm = new QFormLayout(voiceGroup);

    m_wakeWordCheck = new QCheckBox("Enable wake word ('Hey Jarvis')", this);
    voiceForm->addRow(m_wakeWordCheck);

    m_ttsCheck = new QCheckBox("Enable text-to-speech", this);
    voiceForm->addRow(m_ttsCheck);

    m_pythonPathEdit = new QLineEdit(this);
    m_pythonPathEdit->setPlaceholderText("python");
    voiceForm->addRow("Python Path:", m_pythonPathEdit);

    auto* secGroup = new QGroupBox("Security & Governance");
    auto* secForm = new QFormLayout(secGroup);

    m_governanceLevel = new QSpinBox(this);
    m_governanceLevel->setRange(0, 2);
    m_governanceLevel->setToolTip("0=Low, 1=Medium, 2=High");
    secForm->addRow("Governance Level:", m_governanceLevel);

    auto* btnLayout = new QHBoxLayout();
    btnLayout->addStretch();

    m_saveButton = new QPushButton("Save", this);
    m_saveButton->setStyleSheet(
        "QPushButton { background: #e94560; color: white; border: none; "
        "border-radius: 6px; padding: 8px 24px; font-weight: bold; }"
        "QPushButton:hover { background: #c73652; }"
    );

    m_cancelButton = new QPushButton("Cancel", this);
    m_cancelButton->setStyleSheet(
        "QPushButton { background: #16213e; color: #e0e0e0; border: 1px solid #0f3460; "
        "border-radius: 6px; padding: 8px 24px; }"
        "QPushButton:hover { background: #0f3460; }"
    );

    btnLayout->addWidget(m_saveButton);
    btnLayout->addWidget(m_cancelButton);

    mainLayout->addWidget(aiGroup);
    mainLayout->addWidget(voiceGroup);
    mainLayout->addWidget(secGroup);
    mainLayout->addLayout(btnLayout);

    connect(m_saveButton, &QPushButton::clicked, this, [this]() {
        QString key = m_apiKeyEdit->text().trimmed();
        if (key.isEmpty()) {
            key = qEnvironmentVariable("OPENROUTER_API_KEY");
        }
        if (key.isEmpty()) {
            QMessageBox::warning(this, "API Key",
                "OpenRouter API key is required. Set it in settings or as OPENROUTER_API_KEY env var.");
            return;
        }
        saveSettings();
        emit settingsChanged();
        accept();
    });

    connect(m_cancelButton, &QPushButton::clicked, this, &QDialog::reject);

    loadSettings();
}

void SettingsDialog::loadSettings() {
    auto& cfg = Config::instance();
    m_apiKeyEdit->setText(cfg.openRouterKey());
    m_baseUrlEdit->setText(cfg.openRouterBaseUrl());
    m_modelCombo->setCurrentText(cfg.model());
    m_governanceLevel->setValue(cfg.governanceLevel());
    m_wakeWordCheck->setChecked(cfg.wakeWordEnabled());
    m_ttsCheck->setChecked(cfg.ttsEnabled());
    m_pythonPathEdit->setText(cfg.pythonPath());
}

void SettingsDialog::saveSettings() {
    auto& cfg = Config::instance();
    QString key = m_apiKeyEdit->text().trimmed();
    if (key.isEmpty()) key = qEnvironmentVariable("OPENROUTER_API_KEY");
    if (!key.isEmpty()) cfg.setOpenRouterKey(key);
    cfg.setOpenRouterBaseUrl(m_baseUrlEdit->text().trimmed());
    cfg.setModel(m_modelCombo->currentText());
    cfg.setGovernanceLevel(m_governanceLevel->value());
    cfg.setWakeWordEnabled(m_wakeWordCheck->isChecked());
    cfg.setTtsEnabled(m_ttsCheck->isChecked());
    cfg.setPythonPath(m_pythonPathEdit->text().trimmed());
}

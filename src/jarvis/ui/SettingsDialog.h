#pragma once
#include <QDialog>
#include <QLineEdit>
#include <QComboBox>
#include <QCheckBox>
#include <QSpinBox>
#include <QPushButton>
#include <QLabel>

class SettingsDialog : public QDialog {
    Q_OBJECT
public:
    explicit SettingsDialog(QWidget* parent = nullptr);

signals:
    void settingsChanged();

private:
    void loadSettings();
    void saveSettings();

    QLineEdit* m_apiKeyEdit;
    QLineEdit* m_baseUrlEdit;
    QComboBox* m_modelCombo;
    QSpinBox* m_governanceLevel;
    QCheckBox* m_wakeWordCheck;
    QCheckBox* m_ttsCheck;
    QLineEdit* m_pythonPathEdit;
    QPushButton* m_saveButton;
    QPushButton* m_cancelButton;
};

#pragma once
#include <QObject>
#include <QProcess>
#include <QString>

class VoicePipeline : public QObject {
    Q_OBJECT
public:
    explicit VoicePipeline(QObject* parent = nullptr);

    bool initialize(const QString& pythonPath = "python");
    void startWakeWordDetection();
    void stopWakeWordDetection();
    void startListening();
    void stopListening();
    void speak(const QString& text);

    bool isListening() const { return m_isListening; }
    bool isWakeWordActive() const { return m_wakeActive; }

signals:
    void wakeWordDetected();
    void speechRecognized(const QString& text);
    void speechSynthesized();
    void voiceError(const QString& error);
    void listeningStateChanged(bool listening);

private:
    bool startPythonWorker(const QString& script, const QStringList& args);

    QProcess* m_voiceProcess = nullptr;
    QString m_pythonPath;
    bool m_isListening = false;
    bool m_wakeActive = false;
    QString m_scriptsDir;
};

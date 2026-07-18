#include "VoicePipeline.h"
#include <QDir>
#include <QCoreApplication>
#include <QDebug>

VoicePipeline::VoicePipeline(QObject* parent) : QObject(parent) {
    m_scriptsDir = QCoreApplication::applicationDirPath() + "/../src/python/jarvis_voice";
}

bool VoicePipeline::initialize(const QString& pythonPath) {
    m_pythonPath = pythonPath;

    if (!QDir(m_scriptsDir).exists()) {
        m_scriptsDir = QCoreApplication::applicationDirPath() + "/python/jarvis_voice";
    }

    return QDir(m_scriptsDir).exists();
}

void VoicePipeline::startWakeWordDetection() {
    if (m_wakeActive) return;
    m_wakeActive = true;

    QStringList args;
    args << QDir(m_scriptsDir).filePath("wake_word.py");

    if (startPythonWorker(args.first(), args.mid(1))) {
        qDebug() << "Wake word detection started";
    } else {
        emit voiceError("Failed to start wake word detection");
    }
}

void VoicePipeline::stopWakeWordDetection() {
    m_wakeActive = false;
    if (m_voiceProcess && m_voiceProcess->state() == QProcess::Running) {
        m_voiceProcess->terminate();
        m_voiceProcess->waitForFinished(3000);
    }
}

void VoicePipeline::startListening() {
    if (m_isListening) return;
    m_isListening = true;
    emit listeningStateChanged(true);
}

void VoicePipeline::stopListening() {
    m_isListening = false;
    emit listeningStateChanged(false);
}

void VoicePipeline::speak(const QString& text) {
    QStringList args;
    args << QDir(m_scriptsDir).filePath("tts_engine.py") << text;

    if (!startPythonWorker(args.first(), args.mid(1))) {
        emit voiceError("TTS failed");
    } else {
        emit speechSynthesized();
    }
}

bool VoicePipeline::startPythonWorker(const QString& script, const QStringList& args) {
    if (m_voiceProcess) {
        m_voiceProcess->deleteLater();
    }

    m_voiceProcess = new QProcess(this);
    m_voiceProcess->setProcessChannelMode(QProcess::MergedChannels);

    connect(m_voiceProcess, &QProcess::readyReadStandardOutput, this, [this]() {
        QByteArray data = m_voiceProcess->readAllStandardOutput();
        QString line = QString::fromUtf8(data).trimmed();

        if (line.startsWith("WAKE:")) {
            emit wakeWordDetected();
        } else if (line.startsWith("STT:")) {
            emit speechRecognized(line.mid(4).trimmed());
        } else if (line.startsWith("ERROR:")) {
            emit voiceError(line.mid(6).trimmed());
        }
    });

    m_voiceProcess->start(m_pythonPath, QStringList() << script << args);

    if (!m_voiceProcess->waitForStarted(5000)) {
        return false;
    }

    return true;
}

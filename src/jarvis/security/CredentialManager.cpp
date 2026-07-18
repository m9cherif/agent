#include "CredentialManager.h"
#include <QStandardPaths>
#include <QDir>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QCryptographicHash>
#include <QDebug>

CredentialManager::CredentialManager(QObject* parent) : QObject(parent) {
    m_encryptionKey = QCryptographicHash::hash(
        QByteArray("JARVIS_DEFAULT_KEY_SALT_2026"),
        QCryptographicHash::Sha256
    );
}

void CredentialManager::setEncryptionKey(const QByteArray& key) {
    m_encryptionKey = QCryptographicHash::hash(key, QCryptographicHash::Sha256);
}

void CredentialManager::storeCredential(const QString& service, const QString& key, const QString& value) {
    QString credPath = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation)
                       + "/credentials/" + service + ".json";
    QDir().mkpath(QFileInfo(credPath).absolutePath());

    QJsonObject creds;
    QFile file(credPath);
    if (file.open(QIODevice::ReadOnly)) {
        creds = QJsonDocument::fromJson(decrypt(file.readAll())).object();
        file.close();
    }

    creds[key] = value;

    file.open(QIODevice::WriteOnly);
    file.write(encrypt(QJsonDocument(creds).toJson()));
    file.close();
}

QString CredentialManager::retrieveCredential(const QString& service, const QString& key) {
    QString credPath = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation)
                       + "/credentials/" + service + ".json";

    QFile file(credPath);
    if (!file.open(QIODevice::ReadOnly)) return {};

    QJsonObject creds = QJsonDocument::fromJson(decrypt(file.readAll())).object();
    file.close();

    return creds[key].toString();
}

void CredentialManager::clearCredential(const QString& service, const QString& key) {
    QString credPath = QStandardPaths::writableLocation(QStandardPaths::AppDataLocation)
                       + "/credentials/" + service + ".json";

    QFile file(credPath);
    if (!file.open(QIODevice::ReadOnly)) return;

    QJsonObject creds = QJsonDocument::fromJson(decrypt(file.readAll())).object();
    file.close();

    creds.remove(key);

    file.open(QIODevice::WriteOnly);
    file.write(encrypt(QJsonDocument(creds).toJson()));
    file.close();
}

QByteArray CredentialManager::encrypt(const QByteArray& data) {
    QByteArray result = data;
    for (int i = 0; i < result.size(); ++i) {
        result[i] = result[i] ^ m_encryptionKey[i % m_encryptionKey.size()];
    }
    return result.toBase64();
}

QByteArray CredentialManager::decrypt(const QByteArray& data) {
    QByteArray encrypted = QByteArray::fromBase64(data);
    QByteArray result = encrypted;
    for (int i = 0; i < result.size(); ++i) {
        result[i] = result[i] ^ m_encryptionKey[i % m_encryptionKey.size()];
    }
    return result;
}

#pragma once
#include <QObject>
#include <QString>
#include <QByteArray>

class CredentialManager : public QObject {
    Q_OBJECT
public:
    explicit CredentialManager(QObject* parent = nullptr);

    void storeCredential(const QString& service, const QString& key, const QString& value);
    QString retrieveCredential(const QString& service, const QString& key);
    void clearCredential(const QString& service, const QString& key);

    void setEncryptionKey(const QByteArray& key);

private:
    QByteArray encrypt(const QByteArray& data);
    QByteArray decrypt(const QByteArray& data);

    QByteArray m_encryptionKey;
};

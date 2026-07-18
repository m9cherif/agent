#pragma once
#include "BaseTool.h"

class FileIOTool : public BaseTool {
    Q_OBJECT
public:
    explicit FileIOTool(QObject* parent = nullptr);

    QString name() const override { return "file_io"; }
    QString description() const override { return "Read from or write to files on the filesystem"; }
    ReActLoop::Result execute(const QJsonObject& params) override;
};

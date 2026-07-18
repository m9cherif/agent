@echo off
REM JARVIS - Download Voice Models
REM Downloads Sherpa-ONNX wake word and Piper TTS models

echo ========================================
echo    Downloading JARVIS Voice Models
echo ========================================
echo.

if not exist "..\models" mkdir ..\models
if not exist "..\models\sherpa" mkdir ..\models\sherpa
if not exist "..\models\piper" mkdir ..\models\piper

echo [1/3] Downloading Sherpa-ONNX wake word model...
echo NOTE: Sherpa models require manual download from:
echo https://github.com/k2-fsa/sherpa-onnx/releases
echo.
echo Place these files in models\sherpa\:
echo   - encoder.onnx
echo   - decoder.onnx  
echo   - joiner.onnx
echo   - tokens.txt
echo.

echo [2/3] Downloading Whisper model...
echo Downloading ggml-base.en.bin (~50MB)...
powershell -Command "& {Invoke-WebRequest -Uri 'https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin' -OutFile '..\models\ggml-base.en.bin'}"
if %ERRORLEVEL% EQU 0 (
    echo Whisper model downloaded ✓
) else (
    echo WARNING: Whisper download failed. Try manually from:
    echo https://huggingface.co/ggerganov/whisper.cpp
)

echo [3/3] Downloading Piper TTS model...
echo Downloading en_US-lessac-medium (~20MB)...
powershell -Command "& {Invoke-WebRequest -Uri 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx' -OutFile '..\models\piper\en_US-lessac-medium.onnx'}"
if %ERRORLEVEL% EQU 0 (
    powershell -Command "& {Invoke-WebRequest -Uri 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json' -OutFile '..\models\piper\en_US-lessac-medium.onnx.json'}"
    echo Piper model downloaded ✓
) else (
    echo WARNING: Piper download failed. Try manually from:
    echo https://huggingface.co/rhasspy/piper-voices
)

echo.
echo ========================================
echo    Model download complete!
echo    Place Sherpa models manually from:
echo    https://github.com/k2-fsa/sherpa-onnx/releases
echo ========================================
pause

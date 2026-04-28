# Ollama Installation Script for Windows
# This script downloads and installs Ollama on Windows
# Run this script as Administrator

$ErrorActionPreference = 'Stop'

Write-Host "Downloading Ollama installer..."
$installerUrl = "https://ollama.com/download/OllamaSetup.exe"
$installerPath = "$env:TEMP\OllamaSetup.exe"

Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath

Write-Host "Running Ollama installer... (You may need to accept the UAC prompt)"
Start-Process -FilePath $installerPath -ArgumentList "/S" -Wait

Write-Host "Ollama installation completed."
Write-Host "You may need to restart your terminal or log out and back in for PATH changes to take effect."

# Optional: Verify installation
Write-Host "Verifying Ollama installation..."
try {
    $version = ollama --version
    Write-Host "Ollama version: $version"
} catch {
    Write-Host "Ollama not found in PATH. Please check installation or restart your system."
}

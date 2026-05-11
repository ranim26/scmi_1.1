#!/bin/bash
# ================================================================
# install_linux.sh - Installe SysMonAgent sur Linux
# Compatible : Ubuntu, Debian, CentOS, Fedora, Mint...
# Executer avec : sudo bash install_linux.sh
# ================================================================

echo "================================================"
echo " SysMon Agent - Installation Linux"
echo "================================================"

# Verifier root
if [ "$EUID" -ne 0 ]; then
    echo "[ERREUR] Executer en tant que root :"
    echo "  sudo bash install_linux.sh"
    exit 1
fi

INSTALL_DIR="/opt/SysMonAgent"
AGENT_SRC="$(dirname "$0")/sysmon_agent.py"
SERVICE_FILE="/etc/systemd/system/sysmonagent.service"

# Verifier que l'agent existe
if [ ! -f "$AGENT_SRC" ]; then
    echo "[ERREUR] sysmon_agent.py introuvable."
    exit 1
fi

# Installer Python et pip si necessaire
echo "[1/4] Verification de Python..."
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "      Installation de Python..."
    apt-get install -y python3 python3-pip 2>/dev/null || \
    yum install -y python3 python3-pip 2>/dev/null || \
    dnf install -y python3 python3-pip 2>/dev/null
fi

# Detecter python
PYTHON=$(command -v python3 || command -v python)
echo "      Python : $PYTHON"

# Installer psutil
echo "[2/4] Installation de psutil..."
$PYTHON -m pip install psutil --quiet 2>/dev/null || \
pip3 install psutil --quiet 2>/dev/null || \
pip install psutil --quiet 2>/dev/null

# Copier l'agent
echo "[3/4] Copie de l'agent..."
mkdir -p "$INSTALL_DIR"
cp "$AGENT_SRC" "$INSTALL_DIR/sysmon_agent.py"
chmod +x "$INSTALL_DIR/sysmon_agent.py"

# Creer le service systemd
echo "[4/4] Creation du service systemd..."
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=SysMon Agent - Surveillance systeme
After=network.target

[Service]
Type=simple
ExecStart=$PYTHON $INSTALL_DIR/sysmon_agent.py
Restart=always
RestartSec=30
User=root

[Install]
WantedBy=multi-user.target
EOF

# Activer et demarrer le service
systemctl daemon-reload
systemctl enable sysmonagent
systemctl start sysmonagent

echo ""
echo "================================================"
echo " INSTALLATION REUSSIE !"
echo "================================================"
echo " Service : sysmonagent"
echo " Statut  : $(systemctl is-active sysmonagent)"
echo " Logs    : journalctl -u sysmonagent -f"
echo " Stop    : systemctl stop sysmonagent"
echo "================================================"

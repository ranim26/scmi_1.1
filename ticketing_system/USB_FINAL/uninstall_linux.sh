#!/bin/bash
# Desinstalle SysMonAgent sur Linux
if [ "$EUID" -ne 0 ]; then echo "Executer avec sudo"; exit 1; fi
systemctl stop sysmonagent 2>/dev/null
systemctl disable sysmonagent 2>/dev/null
rm -f /etc/systemd/system/sysmonagent.service
systemctl daemon-reload
rm -rf /opt/SysMonAgent
echo "SysMonAgent desinstalle."

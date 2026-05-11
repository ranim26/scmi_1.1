"""
╔══════════════════════════════════════════════════════════════════╗
║         SysMon Agent Universel v2.0                             ║
║  Compatible : Windows XP / 7 / 10 / 11 / Linux                 ║
║  Python     : 2.7 et 3.x                                        ║
╚══════════════════════════════════════════════════════════════════╝
"""
from __future__ import print_function, unicode_literals

import platform
import socket
import time
import uuid
import json
import sys
import os
from datetime import datetime

# ─── CONFIGURATION ─────────────────────────────────────────────────────────────
SERVER_URL   = "http://10.22.30.149:8888"
INTERVAL_SEC = 30
AGENT_NAME   = socket.gethostname()
VERSION      = "2.0.0"
PROTOCOL     = "SYSMON_V1"
# ───────────────────────────────────────────────────────────────────────────────

IS_WINDOWS = sys.platform == "win32"
IS_LINUX   = sys.platform.startswith("linux")
PY2        = sys.version_info[0] == 2

if PY2:
    import urllib2
    def http_post(url, data, headers):
        req = urllib2.Request(url, data.encode("utf-8"), headers)
        resp = urllib2.urlopen(req, timeout=10)
        return resp.read()
else:
    import urllib.request
    def http_post(url, data, headers):
        req = urllib.request.Request(url, data.encode("utf-8"), headers)
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.read()

if IS_WINDOWS:
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass

try:
    import psutil
    PSUTIL = True
except ImportError:
    PSUTIL = False

AGENT_ID = str(uuid.uuid4())

SYSTEM_PROCS_WIN = {
    "svchost.exe","csrss.exe","winlogon.exe","services.exe","lsass.exe",
    "smss.exe","wininit.exe","dwm.exe","conhost.exe","taskhost.exe",
    "taskhostw.exe","sihost.exe","fontdrvhost.exe","spoolsv.exe",
    "searchindexer.exe","wsmprovhost.exe","dllhost.exe","system","registry",
    "memory compression","idle","system idle process","rundll32.exe",
    "msiexec.exe","wuauclt.exe","audiodg.exe","ntoskrnl.exe","lsm.exe",
    "runtimebroker.exe","wmiprvse.exe","searchprotocolhost.exe",
}

SYSTEM_PROCS_LINUX = {
    "kthreadd","ksoftirqd","kworker","rcu_sched","migration","watchdog",
    "kdevtmpfs","netns","kblockd","kswapd","systemd-journal","systemd-udevd",
    "dbus-daemon","networkmanager","polkitd","rsyslogd","cron","atd","sshd","agetty",
}

def get_system_info():
    info = {
        "os":           platform.system(),
        "os_version":   platform.version(),
        "os_release":   platform.release(),
        "architecture": platform.machine(),
        "processor":    platform.processor(),
        "hostname":     socket.gethostname(),
        "python_ver":   platform.python_version(),
        "platform":     "Windows" if IS_WINDOWS else ("Linux" if IS_LINUX else "Other"),
    }
    if PSUTIL:
        try:
            info["boot_time"] = datetime.fromtimestamp(psutil.boot_time()).isoformat()
            delta = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
            h = int(delta.total_seconds() // 3600)
            m = int((delta.total_seconds() % 3600) // 60)
            info["uptime"] = "{0}h {1}m".format(h, m)
        except Exception:
            pass
    if IS_LINUX:
        try:
            import subprocess
            dist = subprocess.check_output(["cat", "/etc/os-release"], stderr=subprocess.STDOUT).decode("utf-8", errors="ignore")
            for line in dist.splitlines():
                if line.startswith("PRETTY_NAME="):
                    info["linux_distro"] = line.split("=", 1)[1].strip().strip('"')
                    break
        except Exception:
            pass
    return info

def get_cpu_info():
    if not PSUTIL:
        return {"usage_percent": None, "core_count": None}
    try:
        cpu_freq = psutil.cpu_freq()
        return {
            "usage_percent":    psutil.cpu_percent(interval=1),
            "core_count":       psutil.cpu_count(logical=False),
            "thread_count":     psutil.cpu_count(logical=True),
            "frequency_mhz":    round(cpu_freq.current, 1) if cpu_freq else None,
            "per_core_percent": psutil.cpu_percent(percpu=True),
        }
    except Exception as e:
        return {"error": str(e)}

def get_memory_info():
    if not PSUTIL:
        return {"ram_total_gb": None, "ram_percent": None}
    try:
        vm = psutil.virtual_memory()
        sw = psutil.swap_memory()
        return {
            "ram_total_gb":  round(vm.total    / 1e9, 2),
            "ram_used_gb":   round(vm.used     / 1e9, 2),
            "ram_free_gb":   round(vm.available/ 1e9, 2),
            "ram_percent":   vm.percent,
            "swap_total_gb": round(sw.total    / 1e9, 2),
            "swap_used_gb":  round(sw.used     / 1e9, 2),
            "swap_percent":  sw.percent,
        }
    except Exception as e:
        return {"error": str(e)}

def get_disk_info():
    if not PSUTIL:
        return []
    disks = []
    try:
        for part in psutil.disk_partitions(all=False):
            try:
                if IS_LINUX and part.fstype in ("tmpfs","devtmpfs","squashfs","overlay","proc","sysfs","cgroup"):
                    continue
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "device":     part.device,
                    "mountpoint": part.mountpoint,
                    "fstype":     part.fstype,
                    "total_gb":   round(usage.total / 1e9, 2),
                    "used_gb":    round(usage.used  / 1e9, 2),
                    "free_gb":    round(usage.free  / 1e9, 2),
                    "percent":    usage.percent,
                })
            except Exception:
                continue
    except Exception as e:
        disks.append({"error": str(e)})
    return disks

def get_network_info():
    if not PSUTIL:
        return {"bytes_sent_mb": None, "bytes_recv_mb": None}
    try:
        net_io = psutil.net_io_counters()
        interfaces = []
        for name, addrs in psutil.net_if_addrs().items():
            if name.lower() in ("lo", "loopback"):
                continue
            iface = {"name": name, "addresses": []}
            for addr in addrs:
                iface["addresses"].append({
                    "family":  str(addr.family),
                    "address": addr.address,
                    "netmask": addr.netmask,
                })
            interfaces.append(iface)
        return {
            "bytes_sent_mb": round(net_io.bytes_sent / 1e6, 2),
            "bytes_recv_mb": round(net_io.bytes_recv / 1e6, 2),
            "packets_sent":  net_io.packets_sent,
            "packets_recv":  net_io.packets_recv,
            "errors_in":     net_io.errin,
            "errors_out":    net_io.errout,
            "interfaces":    interfaces,
        }
    except Exception as e:
        return {"error": str(e)}

def get_temperature_info():
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return {}
        result = {}
        for name, entries in temps.items():
            result[name] = [{"label": e.label or name, "current": e.current, "high": e.high, "critical": e.critical} for e in entries]
        return result
    except Exception:
        return {}

def get_process_info(top_n=5):
    if not PSUTIL:
        return []
    procs = []
    try:
        for p in sorted(
            psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]),
            key=lambda x: x.info.get("cpu_percent") or 0,
            reverse=True
        )[:top_n]:
            procs.append({
                "pid":     p.info["pid"],
                "name":    p.info["name"],
                "cpu_pct": round(p.info["cpu_percent"] or 0, 1),
                "mem_pct": round(p.info["memory_percent"] or 0, 2),
            })
    except Exception:
        pass
    return procs

def get_active_applications():
    apps = []
    if not PSUTIL:
        return apps
    IGNORE = SYSTEM_PROCS_WIN if IS_WINDOWS else SYSTEM_PROCS_LINUX
    seen = set()
    try:
        for p in psutil.process_iter(["pid", "name", "exe", "status", "create_time", "memory_percent", "username"]):
            try:
                name = p.info["name"] or ""
                name_lower = name.lower()
                if not name or name_lower in IGNORE:
                    continue
                if p.info["status"] not in ["running", "sleeping"]:
                    continue
                if IS_LINUX:
                    exe = p.info.get("exe") or ""
                    if not exe and name_lower.startswith("k"):
                        continue
                if name_lower in seen:
                    continue
                seen.add(name_lower)
                try:
                    create_time = datetime.fromtimestamp(p.info["create_time"])
                    delta = datetime.now() - create_time
                    h = int(delta.total_seconds() // 3600)
                    m = int((delta.total_seconds() % 3600) // 60)
                    uptime = "{0}h {1}m".format(h, m)
                except Exception:
                    uptime = "—"
                apps.append({
                    "pid":     p.info["pid"],
                    "name":    name,
                    "exe":     p.info.get("exe") or "—",
                    "status":  p.info["status"],
                    "uptime":  uptime,
                    "mem_pct": round(p.info["memory_percent"] or 0, 2),
                    "user":    p.info.get("username") or "—",
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        apps.sort(key=lambda x: x["name"].lower())
    except Exception:
        pass
    return apps

def build_packet(seq):
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "protocol":   PROTOCOL,
        "version":    VERSION,
        "agent_id":   AGENT_ID,
        "agent_name": AGENT_NAME,
        "timestamp":  now,
        "sequence":   seq,
        "payload": {
            "system":       get_system_info(),
            "cpu":          get_cpu_info(),
            "memory":       get_memory_info(),
            "disks":        get_disk_info(),
            "network":      get_network_info(),
            "temps":        get_temperature_info(),
            "processes":    get_process_info(),
            "applications": get_active_applications(),
        }
    }

def send_packet(packet):
    url  = SERVER_URL.rstrip("/") + "/api/report"
    data = json.dumps(packet, default=str)
    headers = {
        "Content-Type": "application/json",
        "X-Protocol":   PROTOCOL,
        "X-Agent-ID":   AGENT_ID,
        "X-Agent-Name": AGENT_NAME,
    }
    http_post(url, data, headers)

def do_handshake():
    url  = SERVER_URL.rstrip("/") + "/api/handshake"
    now  = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    data = json.dumps({
        "protocol":   PROTOCOL,
        "version":    VERSION,
        "agent_id":   AGENT_ID,
        "agent_name": AGENT_NAME,
        "timestamp":  now,
        "action":     "HELLO",
        "os":         platform.system(),
    })
    headers = {"Content-Type": "application/json"}
    http_post(url, data, headers)

def get_log_path():
    try:
        if IS_WINDOWS:
            base = os.environ.get("APPDATA", os.path.expanduser("~"))
        else:
            base = os.path.expanduser("~")
        log_dir = os.path.join(base, "SysMonAgent")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        return os.path.join(log_dir, "agent.log")
    except Exception:
        return os.path.join(os.path.dirname(sys.executable), "agent.log")

LOG_PATH = get_log_path()

def log(msg):
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[{0}] {1}\n".format(ts, msg)
    try:
        with open(LOG_PATH, "a") as f:
            f.write(line)
        if os.path.getsize(LOG_PATH) > 2 * 1024 * 1024:
            with open(LOG_PATH, "r") as f:
                lines = f.readlines()
            with open(LOG_PATH, "w") as f:
                f.writelines(lines[-500:])
    except Exception:
        pass

def main():
    log("=== SysMon Agent v{0} | OS: {1} {2} | ID: {3} ===".format(
        VERSION, platform.system(), platform.release(), AGENT_ID[:8]))
    log("Serveur: {0} | Intervalle: {1}s | psutil: {2}".format(
        SERVER_URL, INTERVAL_SEC, "OK" if PSUTIL else "MANQUANT"))

    for attempt in range(1, 6):
        try:
            do_handshake()
            log("Handshake reussi")
            break
        except Exception as e:
            log("Handshake tentative {0}/5: {1}".format(attempt, e))
            time.sleep(10)

    seq = 0
    while True:
        try:
            packet = build_packet(seq)
            send_packet(packet)
            cpu  = packet["payload"]["cpu"].get("usage_percent", "?")
            ram  = packet["payload"]["memory"].get("ram_percent", "?")
            apps = len(packet["payload"]["applications"])
            log("Paquet #{0:04d} | CPU:{1}% | RAM:{2}% | Apps:{3}".format(seq, cpu, ram, apps))
            seq += 1
        except Exception as e:
            log("Erreur paquet #{0}: {1}".format(seq, e))
        time.sleep(INTERVAL_SEC)

if __name__ == "__main__":
    main()

import subprocess, time, urllib.request, socket, sys

WEB = r"D:\Dev\projects\flowers\web"

def probe(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status == 200
    except Exception:
        return False

def port_free(port):
    s = socket.socket()
    free = s.connect_ex(("127.0.0.1", port)) != 0
    s.close()
    return free

def listener_pid(port):
    out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if "LISTENING" in line and f":{port}" in line:
            return line.split()[-1]
    return None

def wait_up(seconds=20):
    ok_api = ok_web = False
    for _ in range(seconds):
        time.sleep(1)
        ok_api = ok_api or probe("http://localhost:8000/api/v1/gardens/1")
        ok_web = ok_web or probe("http://localhost:5173/")
        if ok_api and ok_web:
            break
    return ok_api, ok_web

def start():
    return subprocess.Popen(["node", "scripts/dev.mjs"], cwd=WEB,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

fails = []

# 场景 1：正常启动
p1 = start()
ok_api, ok_web = wait_up()
print("s1 normal start: backend", "OK" if ok_api else "FAIL", "/ frontend", "OK" if ok_web else "FAIL")
if not (ok_api and ok_web): fails.append("s1")

# 场景 2：强杀 dev.mjs（Windows 上任何停止本质都是强杀，可能留孤儿）→ 下次启动自愈
subprocess.run(["taskkill", "/PID", str(p1.pid), "/F"], capture_output=True)
time.sleep(3)
print("s2 after force-kill: 8000", "free" if port_free(8000) else "orphaned -> self-heal next")
p2 = start()
ok_api, ok_web = wait_up()
print("s2 self-heal restart: backend", "OK" if ok_api else "FAIL", "/ frontend", "OK" if ok_web else "FAIL")
if not (ok_api and ok_web): fails.append("s2")

# 场景 3：uvicorn 异常退出 → dev.mjs 级联关闭全部并释放端口
pid8000 = listener_pid(8000)
subprocess.run(["taskkill", "/PID", pid8000, "/T", "/F"], capture_output=True)
for _ in range(10):
    time.sleep(1)
    if p2.poll() is not None:
        break
time.sleep(2)
f8000, f5173 = port_free(8000), port_free(5173)
print("s3 cascade shutdown: dev.mjs exited =", p2.poll() is not None,
      "/ 8000", "free" if f8000 else "OCCUPIED", "/ 5173", "free" if f5173 else "OCCUPIED")
if not (f8000 and f5173): fails.append("s3")

# 兜底清理
for port in (8000, 5173):
    pid = listener_pid(port)
    if pid:
        subprocess.run(["taskkill", "/PID", pid, "/T", "/F"], capture_output=True)
time.sleep(2)
ok_final = port_free(8000) and port_free(5173)
print("final ports:", "free" if ok_final else "STILL OCCUPIED")
if not ok_final: fails.append("final")
print("RESULT:", "ALL PASS" if not fails else f"FAILED: {fails}")
sys.exit(0 if not fails else 1)

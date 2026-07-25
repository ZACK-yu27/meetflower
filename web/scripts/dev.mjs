// 一键拉起前后端：uvicorn(:8000) + vite（CLI 参数原样转发给 vite，如 --host/--port）
// 设计要点（针对本机 venv python 为 shim 启动器、强杀父进程会留下孙辈孤儿的特点）：
// 1. 启动前自清：占用 8000 / vite 端口的残留进程（上次异常退出的孤儿）直接 taskkill 掉；
// 2. 正常退出（SIGINT/SIGTERM 或任一方退出）时用 taskkill /T 整树杀净；
// 3. 强杀 dev.mjs 的极端情况会留孤儿，但下次启动会被步骤 1 自愈清理。
import { spawn, execSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const webDir = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
const serverDir = path.join(webDir, '..', 'server')
const py = path.join(serverDir, '.venv', 'Scripts', 'python.exe')
const viteBin = path.join(webDir, 'node_modules', 'vite', 'bin', 'vite.js')
const viteArgs = process.argv.slice(2)

function vitePort() {
  for (let i = 0; i < viteArgs.length; i++) {
    if (viteArgs[i] === '--port' && viteArgs[i + 1]) return Number(viteArgs[i + 1])
    const m = /^--port=(\d+)$/.exec(viteArgs[i])
    if (m) return Number(m[1])
  }
  return 5173
}

function freePort(port) {
  try {
    const out = execSync('netstat -ano', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] })
    const pids = new Set()
    for (const line of out.splitlines()) {
      if (line.includes('LISTENING') && line.includes(`:${port}`)) {
        pids.add(line.trim().split(/\s+/).pop())
      }
    }
    for (const pid of pids) {
      console.log(`[dev] port ${port} occupied by PID ${pid} (leftover), killing...`)
      execSync(`taskkill /PID ${pid} /T /F`, { stdio: 'ignore' })
    }
  } catch { /* netstat/taskkill 失败不阻塞启动 */ }
}

const children = []
let shuttingDown = false

function killTree(child) {
  try { execSync(`taskkill /PID ${child.pid} /T /F`, { stdio: 'ignore' }) } catch { /* already dead */ }
}

function shutdown(code = 0) {
  if (shuttingDown) return
  shuttingDown = true
  for (const c of children) killTree(c)
  // venv python 是 shim 启动器，真实 uvicorn/vite 可能不在 taskkill /T 的树上，按端口兜底杀净
  setTimeout(() => {
    freePort(8000)
    freePort(vitePort())
    process.exit(code)
  }, 500)
}

function start(cmd, args, cwd, name) {
  const c = spawn(cmd, args, { cwd, stdio: 'inherit' })
  c.on('exit', (code) => {
    if (!shuttingDown) {
      console.log(`[dev] ${name} exited (code ${code}), shutting down...`)
      shutdown(code ?? 0)
    }
  })
  c.on('error', (err) => {
    console.error(`[dev] failed to start ${name}: ${err.message}`)
    shutdown(1)
  })
  children.push(c)
}

process.on('SIGINT', () => shutdown(0))
process.on('SIGTERM', () => shutdown(0))

freePort(8000)
freePort(vitePort())

start(py, ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'], serverDir, 'uvicorn')
start(process.execPath, [viteBin, ...viteArgs], webDir, 'vite')

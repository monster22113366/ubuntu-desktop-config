#!/usr/bin/env python3
"""Super+T: reuse an identifiable attached Ghostty, or attach a sole session."""
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

class LaunchError(Exception):
    pass

def run(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.PIPE, timeout=5).strip()

def ancestors(pid):
    seen = set()
    while pid > 1 and pid not in seen:
        seen.add(pid)
        try:
            fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
            pid = int(fields[1])
        except (OSError, ValueError, IndexError):
            break
    return seen

def choose(clients, windows, active):
    matches = []
    for client in clients:
        parents = ancestors(int(client['pid']))
        candidates = [w for w in windows if w.get('mapped') and 'ghostty' in w.get('class', '').lower()
                      and w.get('workspace', {}).get('id', 0) > 0 and w['pid'] in parents]
        if len(candidates) == 1:
            matches.append((client, candidates[0]))
    focused = [m for m in matches if m[1]['address'] == active]
    if len(focused) == 1:
        return focused[0]
    if not matches or len({c['session'] for c, _ in matches}) != 1:
        raise LaunchError('无法唯一确定已附着的 Ghostty / tmux Session；请先聚焦目标终端。')
    # Same session: most recently active client, PID as deterministic tie-break.
    return max(matches, key=lambda m: (int(m[0]['activity']), int(m[0]['pid'])))

def snapshot():
    result = subprocess.run(['tmux', 'list-sessions', '-F', '#{session_id}'], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
    if result.returncode:
        if 'no server running' in result.stderr or ('error connecting to' in result.stderr and 'No such file' in result.stderr):
            return [], []
        raise LaunchError('tmux 服务查询失败：' + result.stderr.strip())
    sessions = result.stdout.splitlines()
    raw = run('tmux', 'list-clients', '-F', '#{client_pid}\t#{session_id}\t#{client_activity}')
    clients = [dict(zip(('pid', 'session', 'activity'), line.split('\t'))) for line in raw.splitlines()]
    return sessions, clients

def launch():
    sessions, clients = snapshot()
    if clients:
        windows = json.loads(run('hyprctl', '-j', 'clients'))
        active = json.loads(run('hyprctl', '-j', 'activewindow')).get('address')
        client, window = choose(clients, windows, active)
        address = window['address']
        if not re.fullmatch(r'0x[0-9a-fA-F]+', address):
            raise LaunchError('窗口地址无效')
        # Focus and verify before mutating the session.
        run('hyprctl', 'eval', f'hl.dispatch(hl.dsp.focus({{window="address:{address}"}}))')
        if json.loads(run('hyprctl', '-j', 'activewindow')).get('address') != address:
            raise LaunchError('Ghostty 聚焦失败，未创建 tmux Window')
        current = run('tmux', 'list-clients', '-F', '#{client_pid}\t#{session_id}')
        if f"{client['pid']}\t{client['session']}" not in current.splitlines():
            raise LaunchError('tmux 客户端已变化，请重试')
        run('tmux', 'new-window', '-t', client['session'] + ':')
        return
    if len(sessions) > 1:
        raise LaunchError('存在多个未附着 Session；请先手动附着目标 Session。')
    command = ['tmux', 'attach-session', '-t', sessions[0]] if sessions else ['tmux', 'new-session', '-s', 'main']
    env = dict(os.environ, LC_CTYPE='C.UTF-8')
    process = subprocess.Popen(['/usr/bin/ghostty', '-e', *command], env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    # Keep the lock until attachment completes so rapid presses cannot duplicate.
    for _ in range(100):
        time.sleep(.1)
        _, attached = snapshot()
        if attached:
            return
        if process.poll() is not None:
            raise LaunchError('Ghostty 启动后未附着 tmux，请检查终端启动环境。')
    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    raise LaunchError('等待 tmux 附着超时，已关闭本次未附着的终端。')

def main():
    try:
        with (Path(os.environ['XDG_RUNTIME_DIR']) / 'udc-tmux-launch.lock').open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return
            launch()
    except (LaunchError, OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        message = str(error)
        print(message, file=sys.stderr)
        subprocess.run(['notify-send', 'Super+T 启动失败', message], check=False)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

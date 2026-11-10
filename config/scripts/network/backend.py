"""NetworkManager operations. No shell interpolation or credential logging."""
import os
import subprocess
import uuid
from dataclasses import dataclass


class NetworkError(RuntimeError):
    pass


def split_terse(line):
    """nmcli -t escapes colons and backslashes, including BSSIDs and SSIDs."""
    fields, buf, escaped = [], [], False
    for char in line:
        if escaped:
            buf.append(char)
            escaped = False
        elif char == '\\':
            escaped = True
        elif char == ':':
            fields.append(''.join(buf))
            buf = []
        else:
            buf.append(char)
    if escaped:
        buf.append('\\')
    return fields + [''.join(buf)]


@dataclass
class Device:
    name: str
    kind: str
    state: str
    connection: str


@dataclass
class Profile:
    uuid: str
    name: str
    kind: str
    ssid: str = ''


@dataclass
class AccessPoint:
    active: bool
    ssid: str
    signal: str
    security: str
    bssid: str


class NetworkManager:
    def run(self, *args, secret=None, wait=15):
        command = ['nmcli', '--colors', 'no', '--wait', str(wait), *args]
        fd = None
        try:
            if secret is not None:
                if any(c in secret for c in '\r\n\0'):
                    raise NetworkError('密码不能包含换行或 NUL。')
                # Anonymous RAM-backed file: never appears in argv, env or disk files.
                fd = os.memfd_create('nm-secret', os.MFD_CLOEXEC)
                os.fchmod(fd, 0o600)
                os.write(fd, ('802-11-wireless-security.psk:' + secret + '\n').encode())
                os.lseek(fd, 0, os.SEEK_SET)
                command += ['passwd-file', f'/proc/self/fd/{fd}']
            result = subprocess.run(command, text=True, capture_output=True,
                                    timeout=wait + 5, env=dict(os.environ, LC_ALL='C'),
                                    pass_fds=() if fd is None else (fd,))
        except FileNotFoundError:
            raise NetworkError('未安装 nmcli，或 NetworkManager 不可用。') from None
        except subprocess.TimeoutExpired:
            raise NetworkError('NetworkManager 操作超时；请刷新状态后重试。') from None
        finally:
            if fd is not None:
                os.close(fd)
        if result.returncode:
            # Never relay raw stderr: it may contain user-supplied data or secrets.
            reasons = {3: '操作超时', 4: '连接激活失败，请检查密码、信号或网线',
                       5: '连接停用失败', 7: '连接配置操作失败',
                       8: 'NetworkManager 未运行', 10: '设备或连接已不存在'}
            raise NetworkError(reasons.get(result.returncode,
                               '操作失败，请检查 NetworkManager 权限与设备状态')
                               + f'（nmcli 状态 {result.returncode}）')
        return result.stdout.rstrip('\n')

    def rows(self, fields, *args):
        raw = self.run('-t', '-e', 'yes', '-f', fields, *args)
        count = len(fields.split(','))
        rows = [split_terse(line) for line in raw.splitlines() if line]
        if any(len(row) != count for row in rows):
            raise NetworkError('网络名称含不支持的换行或数据格式异常，未执行操作。')
        return rows

    def devices(self):
        return [Device(*row) for row in self.rows('DEVICE,TYPE,STATE,CONNECTION', 'device', 'status')
                if row[1] in ('wifi', 'ethernet')]

    def profiles(self, kind):
        profiles = []
        for uid, name, ptype in self.rows('UUID,NAME,TYPE', 'connection', 'show'):
            if ptype != kind:
                continue
            ssid = ''
            if kind == '802-11-wireless':
                raw = self.run('-g', '802-11-wireless.ssid', 'connection', 'show', 'uuid', uid)
                if '\n' in raw or '\r' in raw:
                    continue
                ssid = ':'.join(split_terse(raw))
            profiles.append(Profile(uid, name, kind, ssid))
        return profiles

    def wifi_enabled(self):
        return self.run('radio', 'wifi') == 'enabled'

    def scan(self, device):
        return [AccessPoint(row[0] == '*', *row[1:]) for row in
                self.rows('IN-USE,SSID,SIGNAL,SECURITY,BSSID', 'device', 'wifi', 'list',
                          'ifname', device, '--rescan', 'yes')]

    def activate(self, profile, device):
        self.run('connection', 'up', 'uuid', profile.uuid, 'ifname', device, wait=30)

    def disconnect(self, device):
        self.run('device', 'disconnect', device)

    def radio(self, enabled):
        self.run('radio', 'wifi', 'on' if enabled else 'off')

    def connect_new(self, ssid, device, security, password=None, hidden=False):
        if not ssid or len(ssid.encode()) > 32 or any(c in ssid for c in '\r\n\0'):
            raise NetworkError('SSID 必须为 1～32 字节，不能含换行或 NUL。')
        if security not in ('open', 'wpa-psk', 'sae', 'owe'):
            raise NetworkError('此安全类型需要预先配置 NetworkManager 连接。')
        if security in ('wpa-psk', 'sae') and not password:
            raise NetworkError('请输入 Wi-Fi 密码。')
        uid = str(uuid.uuid4())
        args = ['connection', 'add', 'type', 'wifi', 'ifname', device,
                'con-name', 'Wi-Fi ' + ssid, 'connection.uuid', uid, 'ssid', ssid,
                'connection.autoconnect', 'no', '802-11-wireless.hidden', 'yes' if hidden else 'no']
        if security != 'open':
            args += ['wifi-sec.key-mgmt', security]
        if password is not None:
            args += ['wifi-sec.psk-flags', '0']
        self.run(*args)
        try:
            self.run('connection', 'up', 'uuid', uid, 'ifname', device, secret=password, wait=30)
        except NetworkError as error:
            # Only remove the UUID generated by THIS operation, never a saved profile.
            try:
                self.run('connection', 'delete', 'uuid', uid)
            except NetworkError:
                raise NetworkError(str(error) + '；临时连接配置清理失败，可在已保存列表中重试。') from None
            raise
        try:
            self.run('connection', 'modify', 'uuid', uid, 'connection.autoconnect', 'yes')
        except NetworkError:
            raise NetworkError('连接已建立，但自动连接设置失败；请检查已保存连接。') from None

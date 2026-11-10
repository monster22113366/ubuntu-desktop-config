"""Wofi network controller. Run through ../network-control.sh."""
import os
from pathlib import Path
import subprocess
import sys
from backend import NetworkError, NetworkManager

WOFI = Path(__file__).resolve().parents[2] / 'wofi'


def notify(message, error=False):
    try:
        subprocess.run(['notify-send', '-u', 'critical' if error else 'normal',
                        '网络控制', message], timeout=3, capture_output=True)
    except (OSError, subprocess.TimeoutExpired):
        pass


def display(value):
    return ''.join(c if c.isprintable() else ' ' for c in value)


def state_text(state):
    for key, label in [('connected', '已连接'), ('disconnected', '未连接'),
                       ('unavailable', '不可用'), ('unmanaged', '未托管'),
                       ('connecting', '连接中'), ('deactivating', '断开中')]:
        if state.startswith(key):
            return label
    return state


def wofi(prompt, labels=(), password=False, entry=False, error=False):
    style_fd = None
    style = str(WOFI / 'style.css')
    if error:
        style_fd = os.memfd_create('wofi-style', os.MFD_CLOEXEC)
        os.write(style_fd, (WOFI / 'style.css').read_bytes() + (WOFI / 'network-error.css').read_bytes())
        os.lseek(style_fd, 0, os.SEEK_SET)
        style = f'/proc/self/fd/{style_fd}'
    command = ['wofi', '--conf', str(WOFI / 'config'), '--style', style,
               '--dmenu', '--prompt', prompt, '--width', '760', '--height', '440' if labels else '160',
               '--cache-file', '/dev/null', '--sort-order', 'default',
               '--define', 'allow_markup=false', '--define', 'allow_images=false',
               '--define', 'exec_search=' + ('true' if entry else 'false'),
               '--define', 'dmenu-print_line_num=' + ('false' if entry else 'true')]
    if password:
        command += ['--password']
    try:
        result = subprocess.run(command, input='\n'.join(display(s) for s in labels),
                                text=True, capture_output=True,
                                pass_fds=() if style_fd is None else (style_fd,))
    except OSError:
        raise NetworkError('无法启动 Wofi。') from None
    finally:
        if style_fd is not None:
            os.close(style_fd)
    if result.returncode == 1:
        return None
    if result.returncode:
        raise NetworkError('Wofi 菜单异常退出。')
    value = result.stdout.removesuffix('\n')
    if entry:
        return value if value else None
    if not value.isascii() or not value.isdecimal() or int(value) >= len(labels):
        return None
    return int(value)


def choose(prompt, options, error=False):
    """Keep identity separate from SSID/name display; use UUID/device objects."""
    index = wofi(prompt, [label for label, _ in options], error=error)
    return options[index][1] if index is not None else None



class Controller:
    def __init__(self, nm=None):
        self.nm = nm or NetworkManager()

    def device(self, kind):
        devices = [d for d in self.nm.devices() if d.kind == kind]
        if not devices:
            raise NetworkError('未检测到无线网卡。' if kind == 'wifi' else '未检测到有线网卡。')
        if len(devices) == 1:
            return devices[0]
        return choose('选择网络设备', [(f'{d.name}｜{state_text(d.state)}', d) for d in devices])

    def saved(self, kind, device=None, profiles=None):
        device = device or self.device('wifi' if kind == '802-11-wireless' else 'ethernet')
        if device is None:
            return
        profiles = self.nm.profiles(kind) if profiles is None else profiles
        if not profiles:
            raise NetworkError('没有已保存的连接配置。')
        profile = choose('选择已保存连接', [(f'{p.name}｜{p.uuid[:8]}', p) for p in profiles])
        if profile:
            self.nm.activate(profile, device.name)
            notify('连接已建立。')

    def new(self, device, ssid=None, security=None, hidden=False):
        if ssid is None:
            ssid = wofi('输入 Wi-Fi 名称（SSID）', entry=True)
        if not ssid:
            return
        if security is None:
            security = choose('选择安全类型', [('WPA / WPA2 个人网络', 'wpa-psk'),
                              ('WPA3 个人网络', 'sae'), ('开放网络（无密码）', 'open')])
        if security is None:
            return
        password = None
        if security in ('wpa-psk', 'sae'):
            password = wofi('输入 Wi-Fi 密码（Esc 取消）', password=True, entry=True)
            if password is None:
                return
        self.nm.connect_new(ssid, device.name, security, password, hidden)
        notify('连接已建立，配置由 NetworkManager 管理。')

    def scan(self):
        device = self.device('wifi')
        if device is None:
            return
        if not self.nm.wifi_enabled():
            raise NetworkError('Wi-Fi 已关闭，请先在主菜单开启。')
        aps = self.nm.scan(device.name)
        profiles = self.nm.profiles('802-11-wireless')
        saved = {p.ssid for p in profiles}
        if not aps:
            raise NetworkError('未发现附近 Wi-Fi，可重试扫描或手动输入隐藏 SSID。')
        options = []
        for ap in aps:
            flags = ('当前连接 · ' if ap.active else '') + ('已保存' if ap.ssid in saved and ap.ssid else '未保存')
            options.append((f'{ap.ssid or "隐藏网络（需输入 SSID）"}｜{ap.signal}%｜{ap.security or "开放"}｜{flags}｜{ap.bssid}', ap))
        ap = choose('附近 Wi-Fi（选择后连接）', options)
        if ap is None or ap.active:
            return
        matches = [p for p in profiles if ap.ssid and p.ssid == ap.ssid]
        if matches:
            if len(matches) == 1:
                self.nm.activate(matches[0], device.name)
                notify('已连接保存的 Wi-Fi。')
            else:
                self.saved('802-11-wireless', device, matches)
            return
        if '802.1X' in ap.security or 'EAP' in ap.security or 'WEP' in ap.security:
            raise NetworkError('企业认证 / WEP 请先配置 NetworkManager，再使用“已保存的 Wi-Fi”。')
        security = ('owe' if 'OWE' in ap.security else 'wpa-psk' if 'WPA2' in ap.security or 'WPA1' in ap.security
                    else 'sae' if 'WPA3' in ap.security else 'open')
        self.new(device, ap.ssid or None, security if ap.ssid else None, not bool(ap.ssid))

    def ethernet(self):
        device = self.device('ethernet')
        if device is None:
            return
        action = choose(f'有线网络：{device.name}', [
            (f'状态：{state_text(device.state)}｜{device.connection or "未连接"}', 'status'),
            ('连接已配置的有线网络', 'connect'), ('断开此有线设备', 'disconnect')])
        if action == 'connect':
            self.saved('802-3-ethernet', device)
        elif action == 'disconnect':
            self.nm.disconnect(device.name)
            notify('有线设备已断开，配置保留。')

    def main(self):
        while True:
            try:
                devices = self.nm.devices()
                enabled = self.nm.wifi_enabled()
                summary = '；'.join(f'{d.name} {state_text(d.state)} {d.connection}' for d in devices) or '没有可用网络设备'
                action = choose('网络控制中心', [(f'当前状态：{summary}', 'status'),
                    ('扫描附近 Wi-Fi', 'scan'), ('已保存的 Wi-Fi', 'saved'),
                    ('连接新 Wi-Fi / 隐藏 SSID', 'new'), ('断开当前网络（保留配置）', 'disconnect'),
                    ('关闭 Wi-Fi' if enabled else '开启 Wi-Fi', 'radio'), ('有线网络管理', 'ethernet')])
                if action is None:
                    return
                if action == 'scan':
                    self.scan()
                elif action == 'saved':
                    self.saved('802-11-wireless')
                elif action == 'new':
                    device = self.device('wifi')
                    if device:
                        self.new(device, hidden=True)
                elif action == 'disconnect':
                    connected = [d for d in devices if d.state.startswith('connected')]
                    if not connected:
                        raise NetworkError('当前没有已连接的 Wi-Fi 或有线设备。')
                    device = choose('选择要断开的设备', [(f'{d.name}｜{d.connection}', d) for d in connected])
                    if device:
                        self.nm.disconnect(device.name)
                        notify('设备已断开，已保存配置保留。')
                elif action == 'radio':
                    self.nm.radio(not enabled)
                elif action == 'ethernet':
                    self.ethernet()
                # Waybar network listens to netlink/rfkill; 5 s polling is a fallback.
            except NetworkError as error:
                notify(str(error), error=True)
                # Also visible when no notification daemon is running.
                choice = choose('网络操作未完成', [(str(error), 'back'), ('返回主菜单', 'back')], error=True)
                if choice is None:
                    return


if __name__ == '__main__':
    try:
        Controller().main()
    except NetworkError as error:
        notify(str(error), error=True)
        sys.exit(1)

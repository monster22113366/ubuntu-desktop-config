#!/usr/bin/env python3
"""CPU/RAM with cached independent Intel/NVIDIA samples."""
from pathlib import Path
import subprocess
import time
import os
import json
import fcntl
import re
import sys


def cpu_sample(path=Path('/proc/stat')):
    fields = path.read_text().splitlines()[0].split()
    if fields[0] != 'cpu' or len(fields) < 9:
        raise ValueError('invalid CPU counters')
    values = [int(value) for value in fields[1:9]]  # guest time already included
    return sum(values), values[3] + values[4]


def cpu_percent(before, after):
    total, idle = after[0] - before[0], after[1] - before[1]
    if total <= 0 or idle < 0 or idle > total:
        return 'N/A'
    return f'{round(100 * (total - idle) / total)}%'


def memory_percent(path=Path('/proc/meminfo')):
    values = {line.split(':')[0]: int(line.split()[1]) for line in path.read_text().splitlines()}
    total, available = values['MemTotal'], values['MemAvailable']
    if total <= 0 or not 0 <= available <= total:
        return 'N/A'
    return f'{round(100 * (total - available) / total)}%'


def gpu_percent():
    """Never query a runtime-suspended or unbound NVIDIA PCI device."""
    for device in Path('/sys/bus/pci/devices').glob('*'):
        try:
            if device.joinpath('vendor').read_text().strip() != '0x10de':
                continue
            if not device.joinpath('class').read_text().strip().startswith('0x03'):
                continue
            if not device.joinpath('driver').exists():
                return 'N/A'
            if device.joinpath('power/runtime_status').read_text().strip() != 'active':
                return 'N/A'
            # Only monitor a GPU already held active by a display/client. Avoid
            # extending runtime-PM idle timers by querying an otherwise idle GPU.
            if int(device.joinpath('power/runtime_usage').read_text()) <= 0:
                return 'N/A'
            result = subprocess.run(
                ['nvidia-smi', '--id=' + device.name, '--query-gpu=utilization.gpu',
                 '--format=csv,noheader,nounits'], stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, text=True, check=True, timeout=1)
            value = int(result.stdout.strip())
            return f'{value}%' if 0 <= value <= 100 else 'N/A'
        except (OSError, ValueError, subprocess.SubprocessError):
            return 'N/A'
    return 'N/A'


def intel_device(root=Path('/sys/class/drm')):
    """Resolve the unique Intel DRM card by PCI vendor, never card numbering."""
    candidates = []
    for card in root.glob('card*'):
        if not re.fullmatch(r'card[0-9]+', card.name):
            continue
        try:
            if (card / 'device/vendor').read_text().strip() == '0x8086':
                candidates.append('/dev/dri/' + card.name)
        except OSError:
            continue
    return candidates[0] if len(candidates) == 1 else None


def intel_percent():
    """Bounded Intel Render/3D sample; never invoke sudo or change permissions."""
    device = intel_device()
    if device is None:
        return 'N/A'
    import tempfile
    import signal
    import resource
    def no_core():
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    try:
        with tempfile.TemporaryFile(mode='w+') as output:
            process = subprocess.Popen(
                ['intel_gpu_top', '-d', 'drm:' + device, '-J', '-s', '500', '-o', '-'],
                stdout=output, stderr=subprocess.DEVNULL, preexec_fn=no_core)
            try:
                process.wait(timeout=1.6)
                return 'N/A'  # Early termination is a failed collector.
            except subprocess.TimeoutExpired:
                process.send_signal(signal.SIGINT)
                try:
                    process.wait(timeout=.5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    return 'N/A'
                if process.returncode not in (0, -signal.SIGINT):
                    return 'N/A'
            output.seek(0)
            return parse_intel(output.read())
    except (OSError, ValueError, subprocess.SubprocessError):
        return 'N/A'


def parse_intel(raw):
    # intel_gpu_top emits an array incrementally; tolerate an unfinished tail.
    decoder = json.JSONDecoder()
    records = []
    remaining = raw.lstrip().lstrip('[').lstrip()
    while remaining:
        try:
            record, end = decoder.raw_decode(remaining)
        except ValueError:
            break
        records.append(record)
        remaining = remaining[end:].lstrip().lstrip(',').lstrip()
    if len(records) < 2:
        return 'N/A'  # First frame has no valid sampling interval.
    try:
        value = records[-1]['engines']['Render/3D']['busy']
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not 0 <= value <= 100:
            return 'N/A'
        return f'{round(value)}%'
    except (KeyError, TypeError):
        return 'N/A'


REFRESH_SECONDS = 4  # Trigger on the next five-second tmux refresh.
MAX_AGE_SECONDS = 15  # Never keep displaying an indefinitely stale success.


def cache_directory():
    directory = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'udc-gpu'
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    return directory


def read_gpu_cache(directory):
    try:
        data = json.loads((directory / 'status-v2.json').read_text())
        age = time.monotonic() - data['time']
        boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        if data['boot'] != boot or not 0 <= age <= MAX_AGE_SECONDS:
            raise ValueError('expired cache')
        values = data['intel'], data['nvidia']
        if not all(isinstance(v, str) and (v == 'N/A' or re.fullmatch(r'(?:100|[0-9]{1,2})%', v)) for v in values):
            raise ValueError('invalid sample')
        return values, age
    except (OSError, ValueError, KeyError, TypeError):
        return ('N/A', 'N/A'), float('inf')


def refresh_gpu_cache(directory):
    values = {}
    for name, collector in [('intel', intel_percent), ('nvidia', gpu_percent)]:
        try:
            values[name] = collector()
        except Exception:
            values[name] = 'N/A'
    values.update(time=time.monotonic(), boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
    temporary = directory / ('status-' + str(os.getpid()) + '.tmp')
    try:
        temporary.write_text(json.dumps(values))
        temporary.replace(directory / 'status-v2.json')
    finally:
        temporary.unlink(missing_ok=True)


def gpu_status():
    """Return immediately; one detached worker refreshes all clients' cache."""
    try:
        directory = cache_directory()
        values, age = read_gpu_cache(directory)
        if age < REFRESH_SECONDS:
            return values
        with (directory / 'refresh.lock').open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return values
            values, age = read_gpu_cache(directory)
            if age >= REFRESH_SECONDS:
                # flock stays held by the inherited descriptor until worker exit.
                subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                  '--refresh-gpu', str(lock.fileno())],
                                 pass_fds=(lock.fileno(),), stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 start_new_session=True)
        return values
    except OSError:
        return 'N/A', 'N/A'


def main():
    cpu = memory = 'N/A'
    try:
        before = cpu_sample()
        time.sleep(0.2)
        cpu = cpu_percent(before, cpu_sample())
    except (OSError, ValueError, IndexError):
        pass
    try:
        memory = memory_percent()
    except (OSError, ValueError, KeyError, IndexError):
        pass
    intel, nvidia = gpu_status()
    if '--tmux' in sys.argv:
        segments = [('CPU', cpu, '#293b50', '#7dcfff'),
                    ('RAM', memory, '#35334d', '#bb9af7'),
                    ('Intel', intel, '#293e40', '#9ece6a'),
                    ('NVIDIA', nvidia, '#293e40', '#9ece6a')]
        print(' '.join(
            f'#[fg={bg},bg=default,nobold]#[fg={fg},bg={bg}]'
            f'{label} {value}#[fg={bg},bg=default]#[default]'
            for label, value, bg, fg in segments))
    else:
        print(f'CPU {cpu} | RAM {memory} | Intel GPU {intel} | NVIDIA GPU {nvidia}')


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--refresh-gpu':
        with os.fdopen(int(sys.argv[2]), 'a'):
            refresh_gpu_cache(cache_directory())
    else:
        main()

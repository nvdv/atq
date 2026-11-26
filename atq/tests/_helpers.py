"""Shared helpers for end-to-end tests."""
import os
import signal
import socket
import subprocess
import sys
import time


def build_test_env():
    """Returns an environment with tests dir and repo root on PYTHONPATH."""
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(tests_dir))
    env = os.environ.copy()
    existing = env.get('PYTHONPATH')
    paths = [tests_dir, repo_root]
    if existing:
        paths.append(existing)
    env['PYTHONPATH'] = os.pathsep.join(paths)
    return env


def find_free_ports(count, host='localhost'):
    """Returns `count` distinct currently unused TCP ports on `host`."""
    sockets = []
    ports = []
    try:
        for _ in range(count):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind((host, 0))
            ports.append(sock.getsockname()[1])
            sockets.append(sock)
    finally:
        for sock in sockets:
            sock.close()
    return ports


def wait_for_server(proc, host, port, timeout=5.0):
    """Waits until `host:port` accepts TCP connections or `proc` exits."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(
                'atq server exited prematurely with code %s' % proc.returncode)
        try:
            with socket.create_connection((host, port), timeout=0.1):
                return
        except OSError:
            time.sleep(0.05)
    raise TimeoutError(
        'Timed out waiting for atq server on %s:%s' % (host, port))


def start_server(host, port, num_workers, startup_timeout=5.0):
    """Starts an atq server subprocess and waits until it is listening."""
    proc = subprocess.Popen(
        [sys.executable, '-m', 'atq', '-H', host, '-p', str(port),
         '-w', str(num_workers)],
        env=build_test_env(),
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_for_server(proc, host, port, timeout=startup_timeout)
    except Exception:
        stop_server(proc)
        raise
    return proc


def start_servers(host, ports, num_workers, startup_timeout=5.0):
    """Starts multiple atq servers, stopping any already started on failure."""
    procs = []
    try:
        for port in ports:
            procs.append(
                start_server(
                    host, port, num_workers, startup_timeout=startup_timeout))
    except Exception:
        for proc in procs:
            stop_server(proc)
        raise
    return procs


def stop_server(proc, timeout=5.0):
    """Stops a server subprocess with SIGINT and falls back to terminate/kill."""
    if proc.poll() is not None:
        proc.communicate()
        return
    proc.send_signal(signal.SIGINT)
    try:
        proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.terminate()
        try:
            proc.communicate(timeout=2.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import main


PRODUCTS = [
    ("teclado", 200.0, 10),
    ("mouse", 100.0, 5),
    ("camiseta", 50.0, 0),
]

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8001")
SERVER_PROCESS = None
SERVER_DB_PATH = Path(__file__).with_name("geekstore_pytest_server.db")


def server_is_ready(base_url: str, timeout: float = 0.5) -> bool:
    try:
        with urllib.request.urlopen(f"{base_url}/api/produtos", timeout=timeout) as response:
            return response.status == 200
    except OSError:
        return False


def pytest_sessionstart(session):
    global SERVER_PROCESS

    if server_is_ready(BASE_URL):
        return

    env = os.environ.copy()
    env.setdefault("DB_PATH", str(SERVER_DB_PATH))
    SERVER_PROCESS = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8001",
        ],
        cwd=Path(__file__).parent,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    deadline = time.time() + 20
    while time.time() < deadline:
        if SERVER_PROCESS.poll() is not None:
            pytest.exit("Servidor FastAPI encerrou antes dos testes iniciarem.", returncode=1)
        if server_is_ready(BASE_URL):
            return
        time.sleep(0.5)

    pytest.exit("Nao foi possivel iniciar o servidor FastAPI em http://127.0.0.1:8001.", returncode=1)


def pytest_sessionfinish(session, exitstatus):
    if SERVER_PROCESS and SERVER_PROCESS.poll() is None:
        SERVER_PROCESS.terminate()
        try:
            SERVER_PROCESS.wait(timeout=5)
        except subprocess.TimeoutExpired:
            SERVER_PROCESS.kill()

    for suffix in ("", "-wal", "-shm"):
        SERVER_DB_PATH.with_name(f"{SERVER_DB_PATH.name}{suffix}").unlink(missing_ok=True)


@pytest.fixture
def db_connection(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    main.init_db(str(db_path))

    conn = main.get_db_connection(str(db_path))
    conn.execute("DELETE FROM produtos")
    conn.executemany(
        "INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)",
        PRODUCTS,
    )
    conn.commit()

    yield conn

    conn.close()
    for suffix in ("", "-wal", "-shm"):
        Path(f"{db_path}{suffix}").unlink(missing_ok=True)


@pytest.fixture
def client(db_connection):
    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()


@pytest.fixture
def mock_gateway():
    gateway = Mock(spec=main.GatewayPagamento)
    gateway.cobrar.return_value = True
    main.app.dependency_overrides[main.get_gateway] = lambda: gateway

    yield gateway

    main.app.dependency_overrides.pop(main.get_gateway, None)


@pytest.fixture(scope="session")
def live_server_url():
    return BASE_URL
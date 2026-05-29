import os
import sqlite3
import time
import urllib.request

import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


pytestmark = pytest.mark.e2e


def wait_for_server(base_url, timeout=15):
    deadline = time.time() + timeout
    last_error = None

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/api/produtos", timeout=1) as response:
                if response.status == 200:
                    return
        except OSError as exc:
            last_error = exc
        time.sleep(0.5)

    pytest.fail(f"Servidor nao respondeu em {base_url}: {last_error}")


def reset_live_database():
    db_path = os.getenv("DB_PATH", "geekstore.db")
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS produtos "
        "(nome TEXT PRIMARY KEY, preco REAL, estoque INTEGER)"
    )
    conn.executemany(
        "INSERT OR REPLACE INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)",
        [("teclado", 200.0, 10), ("mouse", 100.0, 5)],
    )
    conn.commit()
    conn.close()


def build_headless_chrome():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,720")
    return webdriver.Chrome(options=options)


def test_fluxo_de_compra_com_selenium_headless(live_server_url):
    wait_for_server(live_server_url)
    reset_live_database()

    try:
        driver = build_headless_chrome()
    except WebDriverException as exc:
        if os.getenv("CI"):
            raise
        pytest.skip(f"Navegador Chrome/driver indisponivel neste ambiente: {exc.msg}")

    try:
        wait = WebDriverWait(driver, 10)
        driver.get(live_server_url)

        wait.until(EC.visibility_of_element_located((By.ID, "input-produto"))).send_keys("teclado")
        driver.find_element(By.ID, "input-cartao").send_keys("4111111111111111")
        driver.find_element(By.ID, "input-cupom").send_keys("GEEK20")
        wait.until(EC.element_to_be_clickable((By.ID, "btn-comprar"))).click()

        wait.until(
            EC.text_to_be_present_in_element(
                (By.ID, "mensagem"),
                "Compra aprovada com sucesso!",
            )
        )
        mensagem = driver.find_element(By.ID, "mensagem").text

        assert "Valor pago: R$ 160.00" in mensagem
    finally:
        driver.quit()
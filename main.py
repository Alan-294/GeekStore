import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Permite sobrescrever o banco via variavel de ambiente nos testes/CI.
DB_PATH = os.getenv("DB_PATH", "geekstore.db")


def get_db_path() -> str:
    return os.getenv("DB_PATH", DB_PATH)


def get_db_connection(db_path: Optional[str] = None):
    conn = sqlite3.connect(db_path or get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None):
    """Cria a tabela e insere os produtos iniciais quando o banco esta vazio."""
    conn = get_db_connection(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS produtos "
        "(nome TEXT PRIMARY KEY, preco REAL, estoque INTEGER)"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM produtos")
    if cursor.fetchone()[0] == 0:
        conn.execute("INSERT INTO produtos (nome, preco, estoque) VALUES ('teclado', 200.0, 10)")
        conn.execute("INSERT INTO produtos (nome, preco, estoque) VALUES ('mouse', 100.0, 5)")
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


# --- Dependencias Externas ---
class GatewayPagamento:
    """Simula uma API externa de cartao de credito."""

    def cobrar(self, cartao: str, valor: float):
        # Na vida real faria request HTTP
        return True


def get_gateway():
    return GatewayPagamento()


# --- Regras de Negocio ---
def calcular_desconto(valor: float, cupom: str) -> float:
    if cupom and cupom.upper() == "GEEK20":
        return valor * 0.8
    return valor


def processar_pedido(valor: float, cartao: str, gateway: GatewayPagamento):
    if valor <= 0:
        raise ValueError("O valor deve ser maior que zero.")
    sucesso = gateway.cobrar(cartao, valor)
    if not sucesso:
        raise ValueError("Pagamento recusado pelo Gateway.")
    return "Compra aprovada!"


# --- Rotas da API ---
class CompraRequest(BaseModel):
    produto: str
    cartao: str
    cupom: Optional[str] = ""


@app.get("/api/produtos")
def listar_produtos():
    conn = get_db_connection()
    produtos = conn.execute("SELECT * FROM produtos ORDER BY nome").fetchall()
    conn.close()
    return [dict(p) for p in produtos]


@app.post("/api/comprar")
def comprar(req: CompraRequest, gateway: GatewayPagamento = Depends(get_gateway)):
    conn = get_db_connection()
    nome_produto = req.produto.lower()
    produto = conn.execute("SELECT * FROM produtos WHERE nome = ?", (nome_produto,)).fetchone()

    if not produto:
        conn.close()
        raise HTTPException(status_code=404, detail="Produto nao encontrado")

    if produto["estoque"] <= 0:
        conn.close()
        raise HTTPException(status_code=400, detail="Sem estoque")

    valor_final = calcular_desconto(produto["preco"], req.cupom)

    try:
        mensagem = processar_pedido(valor_final, req.cartao, gateway)
        conn.execute("UPDATE produtos SET estoque = estoque - 1 WHERE nome = ?", (nome_produto,))
        conn.commit()
        conn.close()
        return {"status": "sucesso", "mensagem": mensagem, "valor_pago": valor_final}
    except ValueError as e:
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/", response_class=HTMLResponse)
def frontend():
    html_path = Path(__file__).with_name("index.html")
    with html_path.open("r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000)
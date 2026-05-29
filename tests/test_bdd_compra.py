from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when


scenarios(str(Path(__file__).parent.parent / "features" / "compra_sucesso.feature"))


@given(parsers.parse('que existe o produto "{nome}" com preço {preco:f} e estoque {estoque:d}'))
def produto_existe(db_connection, nome, preco, estoque):
    db_connection.execute(
        "INSERT OR REPLACE INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)",
        (nome, preco, estoque),
    )
    db_connection.commit()


@when(parsers.parse('o cliente compra "{produto}" com o cupom "{cupom}"'), target_fixture="resposta_compra")
def cliente_compra(client, mock_gateway, produto, cupom):
    return client.post(
        "/api/comprar",
        json={"produto": produto, "cartao": "4111111111111111", "cupom": cupom},
    )


@then(parsers.parse("a compra é aprovada pelo valor {valor:f}"))
def compra_aprovada(resposta_compra, valor):
    assert resposta_compra.status_code == 200
    assert resposta_compra.json()["valor_pago"] == pytest.approx(valor)


@then(parsers.parse('o estoque de "{produto}" passa a ser {estoque:d}'))
def estoque_atualizado(db_connection, produto, estoque):
    row = db_connection.execute(
        "SELECT estoque FROM produtos WHERE nome = ?",
        (produto,),
    ).fetchone()
    assert row["estoque"] == estoque
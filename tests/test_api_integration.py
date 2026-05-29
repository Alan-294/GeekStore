import pytest


def estoque_atual(db_connection, produto):
    row = db_connection.execute(
        "SELECT estoque FROM produtos WHERE nome = ?",
        (produto,),
    ).fetchone()
    return row["estoque"]


def test_listar_produtos_retorna_itens_do_banco(client):
    response = client.get("/api/produtos")

    assert response.status_code == 200
    assert response.json() == [
        {"nome": "camiseta", "preco": 50.0, "estoque": 0},
        {"nome": "mouse", "preco": 100.0, "estoque": 5},
        {"nome": "teclado", "preco": 200.0, "estoque": 10},
    ]


def test_frontend_retorna_html_da_loja(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "GeekStore" in response.text
    assert "input-produto" in response.text


def test_comprar_com_sucesso_aplica_desconto_e_baixa_estoque(client, mock_gateway, db_connection):
    response = client.post(
        "/api/comprar",
        json={"produto": "teclado", "cartao": "4111111111111111", "cupom": "GEEK20"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sucesso"
    assert data["mensagem"] == "Compra aprovada!"
    assert data["valor_pago"] == pytest.approx(160.0)
    mock_gateway.cobrar.assert_called_once_with("4111111111111111", 160.0)
    assert estoque_atual(db_connection, "teclado") == 9


def test_comprar_produto_inexistente_retorna_404(client, mock_gateway):
    response = client.post(
        "/api/comprar",
        json={"produto": "monitor", "cartao": "4111111111111111"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Produto nao encontrado"
    mock_gateway.cobrar.assert_not_called()


def test_comprar_produto_sem_estoque_retorna_400(client, mock_gateway):
    response = client.post(
        "/api/comprar",
        json={"produto": "camiseta", "cartao": "4111111111111111"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Sem estoque"
    mock_gateway.cobrar.assert_not_called()


def test_comprar_com_gateway_recusando_nao_baixa_estoque(client, mock_gateway, db_connection):
    mock_gateway.cobrar.return_value = False

    response = client.post(
        "/api/comprar",
        json={"produto": "mouse", "cartao": "4000000000000002"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Pagamento recusado pelo Gateway."
    mock_gateway.cobrar.assert_called_once_with("4000000000000002", 100.0)
    assert estoque_atual(db_connection, "mouse") == 5
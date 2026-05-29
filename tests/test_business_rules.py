from unittest.mock import Mock

import pytest

import main


def test_calcular_desconto_com_cupom_geek20():
    assert main.calcular_desconto(200.0, "GEEK20") == 160.0


def test_calcular_desconto_sem_cupom():
    assert main.calcular_desconto(200.0, "") == 200.0


def test_gateway_padrao_aprova_cobranca():
    assert main.GatewayPagamento().cobrar("4111111111111111", 100.0) is True


def test_get_gateway_retorna_gateway_de_pagamento():
    assert isinstance(main.get_gateway(), main.GatewayPagamento)


def test_processar_pedido_chama_gateway_e_aprova():
    gateway = Mock(spec=main.GatewayPagamento)
    gateway.cobrar.return_value = True

    resultado = main.processar_pedido(160.0, "4111111111111111", gateway)

    assert resultado == "Compra aprovada!"
    gateway.cobrar.assert_called_once_with("4111111111111111", 160.0)


def test_processar_pedido_rejeita_valor_invalido():
    gateway = Mock(spec=main.GatewayPagamento)

    with pytest.raises(ValueError, match="maior que zero"):
        main.processar_pedido(0, "4111111111111111", gateway)

    gateway.cobrar.assert_not_called()


def test_processar_pedido_repassa_recusa_do_gateway():
    gateway = Mock(spec=main.GatewayPagamento)
    gateway.cobrar.return_value = False

    with pytest.raises(ValueError, match="Pagamento recusado"):
        main.processar_pedido(50.0, "4000000000000002", gateway)

    gateway.cobrar.assert_called_once_with("4000000000000002", 50.0)
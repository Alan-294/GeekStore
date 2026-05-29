# language: pt
Funcionalidade: Compra com sucesso
  Como cliente da GeekStore
  Quero finalizar uma compra com cupom válido
  Para receber a confirmação e pagar o valor com desconto

  Cenário: Compra aprovada com desconto
    Dado que existe o produto "teclado" com preço 200.0 e estoque 10
    Quando o cliente compra "teclado" com o cupom "GEEK20"
    Então a compra é aprovada pelo valor 160.0
    E o estoque de "teclado" passa a ser 9
# GeekStore

Projeto FastAPI com SQLite e testes automatizados para a AP2.

## Criar o ambiente

No PowerShell, execute os comandos abaixo na pasta do projeto:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
## Rodar a aplicacao manualmente

Para abrir o sistema no navegador:

```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

- Frontend: <http://localhost:8001>
- Documentacao da API: <http://localhost:8001/docs>

## Rodar os testes

Com o ambiente virtual ativado, rode:

```powershell
python -m pytest
```

Para executar a validacao oficial da atividade, com cobertura minima de 90%:

```powershell
python -m pytest --cov=. --cov-fail-under=90
```

Os testes de API com Tavern e E2E com Selenium precisam da aplicacao em
`http://127.0.0.1:8001`. A configuracao de testes ja tenta subir o servidor
automaticamente se ele nao estiver rodando.

## Entrega

A pipeline em `.github/workflows/ci.yml` instala as dependencias, sobe a
aplicacao em background, executa testes unitarios, integracao/DB, mocks, BDD,
Tavern e Selenium headless, e bloqueia a build se a cobertura ficar abaixo de
90%.

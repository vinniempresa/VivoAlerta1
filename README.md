# Vivo Regularização de Linha

Aplicação web para simulação de regularização cadastral de linhas telefônicas Vivo.

## Descrição

Este projeto simula uma interface de regularização da Vivo, onde o usuário pode:
- Visualizar informações sobre pendências cadastrais
- Realizar verificação de identidade com captura de selfie
- Efetuar pagamento da taxa de regularização via PIX

## Tecnologias

- Python 3.11
- Flask
- Bootstrap 5
- For4Payments API (para geração de pagamentos PIX)

## Deploy no Heroku

### Pré-requisitos

- Conta no [Heroku](https://heroku.com)
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) instalada
- Git instalado

### Passos para Deploy

1. Clone este repositório:
   ```
   git clone <URL_DO_REPOSITORIO>
   cd vivo-reativacao
   ```

2. Faça login no Heroku:
   ```
   heroku login
   ```

3. Crie uma aplicação no Heroku:
   ```
   heroku create
   ```

4. Renomeie o arquivo para que o Heroku possa reconhecê-lo:
   ```
   mv requirements-heroku.txt requirements.txt
   ```

5. Configure as variáveis de ambiente:
   ```
   heroku config:set FOR4PAYMENTS_SECRET_KEY=sua_chave_aqui
   heroku config:set SESSION_SECRET=$(python -c 'import secrets; print(secrets.token_hex(16))')
   ```

6. Faça o deploy:
   ```
   git add .
   git commit -m "Deploy para Heroku"
   git push heroku main
   ```

7. Abra a aplicação:
   ```
   heroku open
   ```

## Variáveis de Ambiente

- `FOR4PAYMENTS_SECRET_KEY`: Chave da API For4Payments (obrigatória)
- `SESSION_SECRET`: Chave secreta para o Flask (opcional, gerada automaticamente se não fornecida)
- `HEROKU_APP_NAME`: Nome da aplicação no Heroku (configurada automaticamente)
- `PORT`: Porta para o servidor web (configurada automaticamente pelo Heroku)

## Desenvolvimento Local

Para executar localmente:

```
python app.py
```

A aplicação estará disponível em `http://localhost:5000`.
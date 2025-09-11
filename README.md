# Aerodicionário

Aplicação de demonstração que combina dois ambientes:

- **Express/Node.js** responsável por autenticação de usuários e rotas protegidas.
- **Django** com um pequeno glossário de termos de aviação e painel administrativo.

## Requisitos

- [Node.js](https://nodejs.org/) 20+
- [Python](https://www.python.org/) 3.11+
- `npm` e `pip`
- (Opcional) [VS Code](https://code.visualstudio.com/) com as extensões *Python* e *JavaScript/TypeScript*.

## Executando o servidor Express

```bash
npm install
npm start
```

Usuários padrão:

- `admin` / `adminpass` (administrador)
- `user` / `userpass` (usuário comum)

Testes do Express:

```bash
npm test
```

## Executando o projeto Django (Local)

Crie um ambiente virtual (recomendado) e instale as dependências:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Inicialize o banco de dados e rode o servidor de desenvolvimento:

```bash
python manage.py migrate
python manage.py runserver
```

Para acessar o painel administrativo vá em `http://localhost:8000/admin/`.
Crie um superusuário com:

```bash
python manage.py createsuperuser
```

Testes do Django (nenhum teste ainda, mas o comando verifica a configuração):

```bash
python manage.py test
```

## Produção — Guia rápido

1) Variáveis de ambiente

- Copie `.env.example` para `.env` e ajuste:
  - `SECRET_KEY` (valor forte/único)
  - `DEBUG=False`
  - `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS`
  - `DATABASE_URL` (recomendado Postgres)

2) Requisitos

- Python 3.11+ e Postgres (com extensão `pg_trgm`; nossa migration cria quando permitido)
- Servidor de aplicação (gunicorn/uvicorn) atrás de Nginx/Proxy

3) Build estáticos + migrações

```bash
python manage.py collectstatic --noinput
python manage.py migrate
```

4) Servindo a aplicação

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
# ou (ASGI)
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers 3
```

5) Arquivos estáticos e mídia

- Em produção, use S3/CloudFront (django-storages) ou Nginx com cache e gzip/br.
- Configure Cache-Control e headers de segurança no proxy/CDN.

6) Segurança

- HSTS, CSP, Referrer-Policy, X-Content-Type-Options no proxy
- `SECRET_KEY` seguro e `DEBUG=False`
- Rate-limit em `/api/autocomplete/` e POST `/sugerir/` (já incluído)

7) Observabilidade

- Sentry (erros) e Uptime para healthcheck.


## Dicas para VS Code

1. Abra a pasta do projeto no VS Code.
2. Use o terminal integrado para executar os comandos acima.
3. Para depurar, utilize as configurações padrão de *Node.js* ou *Django* disponíveis no VS Code.

## Licença

Projeto de demonstração para fins educacionais.

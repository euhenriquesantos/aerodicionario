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

## Executando o projeto Django

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

## Dicas para VS Code

1. Abra a pasta do projeto no VS Code.
2. Use o terminal integrado para executar os comandos acima.
3. Para depurar, utilize as configurações padrão de *Node.js* ou *Django* disponíveis no VS Code.

## Licença

Projeto de demonstração para fins educacionais.

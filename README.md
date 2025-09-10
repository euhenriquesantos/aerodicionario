# aerodicionario
Dicionário da Aviação

## Autenticação e autorização
A aplicação usa sessões do Express para controlar o acesso. O login cria uma sessão que guarda o usuário autenticado e seu perfil.

Usuários padrão:
- `admin` / `adminpass` (administrador)
- `user` / `userpass` (usuário comum)

### Login
`POST /login` com JSON `{ "username": "...", "password": "..." }` inicia a sessão.

### Logout
`POST /logout` encerra a sessão atual.

### Reset de senha
Usuários autenticados podem enviar `POST /reset-password` com `{ "newPassword": "..." }` para alterar a própria senha.

### Rotas restritas
As rotas de criação e edição de itens são protegidas e só podem ser acessadas por administradores:
- `POST /items`
- `PUT /items/:id`

Requisições de usuários sem permissão resultam em `403 Forbidden`.

### Execução
Instale as dependências e inicie o servidor:

```bash
npm install
npm start
```

Execute os testes:

```bash
npm test
```

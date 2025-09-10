const express = require('express');
const session = require('express-session');
const { requireAuth, requireAdmin } = require('./middleware/auth');
const { findUser, resetPassword } = require('./users');

const app = express();
app.use(express.json());
app.use(session({
  secret: 'change_this_secret',
  resave: false,
  saveUninitialized: false,
}));

app.post('/login', (req, res) => {
  const { username, password } = req.body;
  const user = findUser(username);
  if (user && user.password === password) {
    req.session.user = { username: user.username, role: user.role };
    return res.json({ message: 'Logged in' });
  }
  res.status(401).json({ message: 'Invalid credentials' });
});

app.post('/logout', requireAuth, (req, res) => {
  req.session.destroy(err => {
    if (err) return res.status(500).json({ message: 'Logout failed' });
    res.json({ message: 'Logged out' });
  });
});

app.post('/reset-password', requireAuth, (req, res) => {
  const { newPassword } = req.body;
  const { username } = req.session.user;
  resetPassword(username, newPassword);
  res.json({ message: 'Password updated' });
});

let items = [];
let nextId = 1;

app.post('/items', requireAuth, requireAdmin, (req, res) => {
  const item = { id: nextId++, ...req.body };
  items.push(item);
  res.status(201).json(item);
});

app.put('/items/:id', requireAuth, requireAdmin, (req, res) => {
  const id = parseInt(req.params.id, 10);
  const idx = items.findIndex(i => i.id === id);
  if (idx === -1) return res.status(404).json({ message: 'Not found' });
  items[idx] = { ...items[idx], ...req.body };
  res.json(items[idx]);
});

app.get('/items', (req, res) => {
  res.json(items);
});

module.exports = app;

if (require.main === module) {
  const port = process.env.PORT || 3000;
  app.listen(port, () => console.log(`Server running on port ${port}`));
}

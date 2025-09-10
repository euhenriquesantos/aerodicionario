const users = [
  { id: 1, username: 'admin', password: 'adminpass', role: 'admin' },
  { id: 2, username: 'user', password: 'userpass', role: 'user' }
];

function findUser(username) {
  return users.find(u => u.username === username);
}

function resetPassword(username, newPassword) {
  const user = findUser(username);
  if (user) {
    user.password = newPassword;
    return true;
  }
  return false;
}

module.exports = { users, findUser, resetPassword };

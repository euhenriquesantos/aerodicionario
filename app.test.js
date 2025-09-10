const test = require('node:test');
const assert = require('node:assert');
const request = require('supertest');
const app = require('./server');

test('non-admin cannot create item', async () => {
  const agent = request.agent(app);
  await agent.post('/login').send({ username: 'user', password: 'userpass' }).expect(200);
  await agent.post('/items').send({ name: 'test' }).expect(403);
});

test('admin can create item', async () => {
  const agent = request.agent(app);
  await agent.post('/login').send({ username: 'admin', password: 'adminpass' }).expect(200);
  const res = await agent.post('/items').send({ name: 'plane' }).expect(201);
  assert.equal(res.body.name, 'plane');
});

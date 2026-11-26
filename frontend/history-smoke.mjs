import assert from "node:assert/strict";
const storage = new Map();
globalThis.localStorage = {
  getItem: key => storage.get(key) ?? null,
  setItem: (key, value) => storage.set(key, value),
};
const { mockRequest } = await import("./src/mock.js");
const login = email => mockRequest("/auth/login/", { body: JSON.stringify({ email }) });
const ask = data => mockRequest("/ask/", { body: JSON.stringify(data) });
await login("student@example.com");
assert.deepEqual(await mockRequest("/conversations/"), []);
const first = await ask({ question: "Ile punktów ECTS?" });
assert.ok(first.conversation_id);
const second = await ask({ question: "Jak ugotować żurek?", conversation_id: first.conversation_id });
assert.equal(second.conversation_id, first.conversation_id);
assert.equal(second.status, "refused");
const { mockRequest: afterReload } = await import("./src/mock.js?reload");
const history = await afterReload("/conversations/");
assert.equal(history.length, 1);
const thread = await afterReload("/conversations/" + first.conversation_id + "/");
assert.deepEqual(thread.messages.map(m => m.role), ["user", "assistant", "user", "assistant"]);
assert.equal(thread.messages[1].sources[0].page, 3);
assert.deepEqual(thread.messages[3].sources, []);
assert.notEqual((await ask({ question: "Nowa rozmowa" })).conversation_id, first.conversation_id);
await login("admin@example.com");
assert.deepEqual(await mockRequest("/conversations/"), []);
await assert.rejects(mockRequest("/conversations/" + first.conversation_id + "/"), { status: 404 });
console.log("History smoke test passed");

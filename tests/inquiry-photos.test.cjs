const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
function server() {
  const messages = [];
  const context = vm.createContext({
    MailApp: { sendEmail: (...args) => messages.push(args) },
    Utilities: {
      base64Decode: data => [...Buffer.from(data, 'base64')],
      newBlob: (bytes, type, name) => ({ bytes, type, name })
    },
    ContentService: { MimeType: { JSON: 'json' }, createTextOutput: text => ({
      setMimeType: () => JSON.parse(text)
    }) }
  });
  vm.runInContext(fs.readFileSync('apps-script/Code.gs', 'utf8'), context);
  return { context, messages };
}
function inquiry(count) {
  const p = { name: 'Photo test', email: 'customer@example.com', photo_count: String(count) };
  for (let i = 0; i < count; i++) {
    p[`photo_${i}_data`] = Buffer.from([255,216,255,224,0,0,255,217]).toString('base64');
    p[`photo_${i}_type`] = 'image/jpeg';
    p[`photo_${i}_name`] = `ring-${i}.jpg`;
  }
  return p;
}
for (const count of [0, 1, 2]) test(`sends inquiry with ${count} attachments`, () => {
  const { context, messages } = server();
  assert.equal(context.doPost({ parameter: inquiry(count) }).ok, true);
  assert.equal(messages.length, 1);
  assert.equal(messages[0][0], 'chloe@ringmint.com');
  assert.equal(messages[0][3].attachments.length, count);
  assert.equal(messages[0][3].replyTo, 'customer@example.com');
  if (count) assert.equal(messages[0][3].attachments[0].name, 'ring-0.jpg');
});
for (const scenario of ['too many', 'missing', 'corrupt', 'wrong type', 'fractional']) test(`rejects ${scenario} photos without sending`, () => {
  const { context, messages } = server();
  const p = inquiry(2);
  if (scenario === 'too many') p.photo_count = '3';
  if (scenario === 'missing') delete p.photo_1_data;
  if (scenario === 'corrupt') p.photo_1_data = 'bm90IGFuIGltYWdl';
  if (scenario === 'wrong type') p.photo_1_type = 'text/html';
  if (scenario === 'fractional') p.photo_count = '1.5';
  assert.equal(context.doPost({ parameter: p }).ok, false);
  assert.equal(messages.length, 0);
});
test('newsletter still sends without attachments', () => {
  const { context, messages } = server();
  assert.equal(context.doPost({ parameter: { type: 'newsletter', email: 'customer@example.com' } }).ok, true);
  assert.equal(messages.length, 1);
  assert.match(messages[0][1], /newsletter/);
});
test('both public forms offer two optional photos', () => {
  for (const path of ['index.html', 'contact/index.html']) {
    const html = fs.readFileSync(path, 'utf8');
    assert.match(html, /optional, up to 2/);
    assert.match(html, /name="photos" type="file"[^>]*multiple/);
    assert.equal((html.match(/id="inquiryPhotos"/g) || []).length, 1);
  }
});

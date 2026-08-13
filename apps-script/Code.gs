/**
 * Ring Mint inquiry form → email.
 *
 * This file is a reference copy. The code that actually runs lives in the
 * Apps Script editor at script.google.com. Pushing this repo does not
 * update it.
 *
 * TO UPDATE an existing deployment (keeps the same /exec URL, so script.js
 * needs no change):
 *   Deploy → Manage deployments → ✏️ pencil → Version: "New version" → Deploy
 *
 * Only use "New deployment" when creating the endpoint for the first time.
 * It mints a NEW /exec URL, which breaks the form until INQUIRY_ENDPOINT at
 * the top of script.js is updated to match.
 *
 * Settings either way: type "Web app", Execute as "Me", access "Anyone".
 */

var TO = 'chloe@ringmint.com';

function doPost(e) {
  var p = (e && e.parameter) || {};

  // Honeypot. Flag rather than discard: autofill can trip this for a real
  // person, and a silently dropped inquiry is worse than a tagged one.
  var suspected = !!(p.url_ref || p.company);

  var rows = [
    ['Name', p.name],
    ['Email', p.email],
    ['Phone / WhatsApp', p.phone],
    ['Timeline', p.timeline],
    ['Budget', p.budget]
  ];

  var text = rows
    .map(function (r) { return r[0] + ': ' + (r[1] || '-'); })
    .join('\n') + '\n\nWhat they\'re looking for:\n' + (p.details || '-');

  var html =
    '<h2 style="font-family:Georgia,serif">New Ring Mint inquiry</h2>' +
    '<table cellpadding="6" style="font-family:Arial,sans-serif;font-size:14px">' +
    rows.map(function (r) {
      return '<tr><td><strong>' + r[0] + '</strong></td><td>' +
        escapeHtml(r[1] || '-') + '</td></tr>';
    }).join('') +
    '</table>' +
    '<p style="font-family:Arial,sans-serif;font-size:14px"><strong>What they\'re looking for:</strong><br>' +
    escapeHtml(p.details || '-').replace(/\n/g, '<br>') + '</p>';

  var options = {
    name: 'Ring Mint Website',
    htmlBody: html
  };
  // Lets you hit reply straight from the notification.
  if (p.email && /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(p.email)) {
    options.replyTo = p.email;
  }

  MailApp.sendEmail(
    TO,
    (suspected ? '[possible spam] ' : '') +
      'Ring Mint inquiry: ' + (p.name || 'no name'),
    text,
    options
  );

  return json({ ok: true });
}

// Visiting the /exec URL in a browser, handy for confirming the deployment.
function doGet() {
  return json({ ok: true, message: 'Ring Mint inquiry endpoint is live.' });
}

function json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

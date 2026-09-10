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
var MAX_PHOTOS = 2;
// MailApp caps a message at 25 MB; stay well under it.
var MAX_ATTACHMENT_BYTES = 15 * 1024 * 1024;

function doPost(e) {
  var p = (e && e.parameter) || {};

  // Honeypot. Flag rather than discard: autofill can trip this for a real
  // person, and a silently dropped inquiry is worse than a tagged one.
  var suspected = !!(p.url_ref || p.company);

  // Email capture from guides and posts (form[data-capture] in script.js).
  // Filed as a signup, not an inquiry, so the two never get mixed up.
  if (p.type === 'newsletter') {
    return saveSubscriber(p, suspected);
  }

  var rows = [
    ['Name', p.name],
    ['Email', p.email],
    ['Phone / WhatsApp', p.phone],
    ['Timeline', p.timeline],
    ['Budget', p.budget],
    // Which guide or page sent them (the ?ref= on /contact/), for attribution.
    ['Came from', p.ref || p.page]
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

  var photos;
  try {
    photos = collectPhotos(p);
  } catch (err) {
    return json({ ok: false, error: "Please attach up to two valid images and try again." });
  }
  if (photos.length) {
    text += '\n\nAttached: ' + photos.length + ' photo(s).';
    html += '<p style="font-family:Arial,sans-serif;font-size:14px"><strong>' +
      photos.length + ' photo(s) attached.</strong></p>';
  }

  var options = {
    name: 'Ring Mint Website',
    htmlBody: html,
    attachments: photos
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

// Each submission is retained with its source. No spreadsheet data is exposed.
var SUBSCRIBER_SHEET_ID = '1IS1oZI5MU7qgDck5CFojQfRMwnVohYpA4CBIKyBtJKc';
var SUBSCRIBER_TAB = 'Subscribers';

function saveSubscriber(p, suspected) {
  var email = String(p.email || '').trim().toLowerCase();
  if (email.length > 254 || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return json({ ok: false, error: 'Please enter a valid email address.' });
  }
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(20000);
    var book = SpreadsheetApp.openById(SUBSCRIBER_SHEET_ID);
    var sheet = book.getSheetByName(SUBSCRIBER_TAB) || book.insertSheet(SUBSCRIBER_TAB);
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(['Signed up at', 'Email', 'Page', 'Source', 'Possible spam']);
      sheet.setFrozenRows(1);
    }
    // Prefix formula-like inputs so submitted text cannot execute as a formula.
    sheet.appendRow([new Date(), sheetText(email), sheetText(p.page),
      sheetText(p.ref), suspected ? 'Yes' : 'No']);
    SpreadsheetApp.flush();
    return json({ ok: true });
  } catch (err) {
    console.error('Subscriber storage failed');
    return json({ ok: false, error: 'We could not save your signup. Please try again.' });
  } finally {
    if (lock.hasLock()) lock.releaseLock();
  }
}

function sheetText(value) {
  var text = String(value || '').slice(0, 2000);
  return /^[\s]*[=+@-]/.test(text) ? "'" + text : text;
}

// Run once in the editor to authorize access before updating the web app.
function setupSubscribers() {
  var book = SpreadsheetApp.openById(SUBSCRIBER_SHEET_ID);
  var sheet = book.getSheetByName(SUBSCRIBER_TAB) || book.insertSheet(SUBSCRIBER_TAB);
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(['Signed up at', 'Email', 'Page', 'Source', 'Possible spam']);
    sheet.setFrozenRows(1);
  }
}

/** Decode the JPEG images prepared by the browser. Reject incomplete uploads
 * before sending so an inquiry never silently loses its attachments. */
function collectPhotos(p) {
  var count = Number(p.photo_count || 0);
  if (!isFinite(count) || count < 0 || count > MAX_PHOTOS || Math.floor(count) !== count) {
    throw new Error('Invalid photo count');
  }
  var blobs = [];
  var total = 0;
  for (var i = 0; i < count; i++) {
    var data = p['photo_' + i + '_data'];
    if (!data || data.length > MAX_ATTACHMENT_BYTES * 4 / 3 ||
        p['photo_' + i + '_type'] !== 'image/jpeg') throw new Error('Invalid image');
    var bytes = Utilities.base64Decode(data);
    if (bytes.length < 3 || (bytes[0] & 255) !== 255 ||
        (bytes[1] & 255) !== 216 || (bytes[2] & 255) !== 255) throw new Error('Invalid JPEG');
    total += bytes.length;
    if (total > MAX_ATTACHMENT_BYTES) throw new Error('Images too large');
    var name = String(p['photo_' + i + '_name'] || ('photo-' + (i + 1) + '.jpg'))
      .replace(/[\\/\r\n]/g, '_').slice(0, 150).replace(/\.[^.]*$/, '') + '.jpg';
    blobs.push(Utilities.newBlob(bytes, 'image/jpeg', name));
  }
  return blobs;
}

// Visiting the /exec URL in a browser, handy for confirming the deployment.
function doGet() {
  return json({ ok: true, message: 'Ring Mint inquiry endpoint is live.', maxPhotos: MAX_PHOTOS, version: 'subscribers-sheets-v1' });
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

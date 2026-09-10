/** Separate “New guides by email” project. Do not paste into the inquiry project. */
function doPost(e) {
  var p = (e && e.parameter) || {};
  if (p.type !== 'newsletter') return json({ ok: false, error: 'Unsupported form.' });
  return saveSubscriber(p, !!(p.url_ref || p.company));
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

function doGet() {
  return json({ ok: true, message: 'Ring Mint guide subscription endpoint is live.' });
}
function json(value) {
  return ContentService.createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}

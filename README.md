# Ring Mint website

GitHub Pages-ready static site.

## Deploy
1. Upload every file in this ZIP to the root of your GitHub repository.
2. Go to Settings → Pages.
3. Set source to Deploy from a branch.
4. Choose `main` and `/root`.
5. Save.

## Inquiry photos

The homepage and `/contact/` forms accept up to two optional images. The browser
resizes them to JPEG and Google Apps Script emails them as attachments to
`chloe@ringmint.com`. Customers see an error before sending if an image cannot be
prepared; JPG, PNG and WebP are recommended. HEIC support depends on the browser.

### Activate the update

1. Open the existing Ring Mint project at https://script.google.com and replace
   its `Code.gs` with [apps-script/Code.gs](apps-script/Code.gs).
2. Save, then choose **Deploy → Manage deployments → Edit (pencil) → New version
   → Deploy**. Keep **Execute as: Me** and **Who has access: Anyone**.
   Update the existing deployment to preserve the `/exec` URL in `script.js`.
3. Visit that `/exec` URL. The response should include `maxPhotos: 2` and
   `version: "photos-2-v1"`.
4. Publish the website changes through the existing GitHub Pages deployment.
5. Submit an inquiry with two photos from each form and verify both attachments
   arrive in the recipient inbox. Also check a submission with no photos.

The repository copy does not automatically update the running Apps Script.
Local checks: `node --test tests/inquiry-photos.test.cjs` (mocks email delivery;
no real email is sent).

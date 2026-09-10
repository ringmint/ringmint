/* Google Apps Script web app that emails the inquiry to chloe@ringmint.com.
   Deploy Code.gs (see apps-script/Code.gs) as a web app: "Execute as: Me",
   "Who has access: Anyone". Paste the /exec URL here. */
const INQUIRY_ENDPOINT = "https://script.google.com/macros/s/AKfycby4y5U8r_FiSB8JWMobWxrEM1BM0iMU9vxP2oCrEHzZfzZRWTBTo4jqeKWMdoFtcsBF/exec";

// Separate endpoint for the “New guides by email” subscription forms.
const SUBSCRIPTION_ENDPOINT = "https://script.google.com/macros/s/AKfycbwkMl1icggT3_D10kODoVJjUjiTDtr9R4_dYDFygE_xvRvc3Wb22olal-PL0V6Vo1xH/exec";

/* Analytics helper. gtag is absent when an ad blocker eats the GA snippet,
   so every call has to tolerate that rather than throw mid-submit. */
const track = (name, params) => {
  if (typeof window.gtag === "function") window.gtag("event", name, params || {});
};

/* Inspiration photos. Apps Script only accepts a "simple" request (see the
   fetch below), so files ride along inside the same url-encoded body as
   base64 rather than as multipart. That makes payload size the constraint,
   not the file count: every photo is re-drawn to at most PHOTO_MAX_EDGE px
   and re-encoded as JPEG in the browser first, which turns a 6 MB phone
   photo into roughly 300 KB. Anything the browser cannot decode (HEIC on a
   desktop, a PDF someone renamed) is skipped rather than sent raw. */
const PHOTO_MAX_COUNT = 2;
const PHOTO_MAX_EDGE = 1600;
const PHOTO_QUALITY = 0.82;
/* Ceiling for the whole request. Apps Script accepts far more, but a slow
   phone connection makes a bigger body feel like a broken form. */
const PHOTO_TOTAL_BUDGET = 6 * 1024 * 1024;

const readAsDataUrl = (blob) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(new Error("read failed"));
    reader.readAsDataURL(blob);
  });

/* Returns { name, type, data } with data as bare base64, or null if the
   image could not be decoded. */
const shrinkImage = async (file) => {
  let bitmap;
  try {
    bitmap = await createImageBitmap(file);
  } catch (error) {
    return null;
  }
  const scale = Math.min(1, PHOTO_MAX_EDGE / Math.max(bitmap.width, bitmap.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  canvas.getContext("2d").drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close && bitmap.close();

  const blob = await new Promise((resolve) =>
    canvas.toBlob(resolve, "image/jpeg", PHOTO_QUALITY)
  );
  if (!blob) return null;

  const dataUrl = await readAsDataUrl(blob);
  return {
    /* Always .jpg: the canvas re-encode means the original extension would
       be a lie, and Gmail trusts the extension over the MIME type. */
    name: (file.name || "photo").replace(/\.[^.]+$/, "") + ".jpg",
    type: "image/jpeg",
    data: dataUrl.slice(dataUrl.indexOf(",") + 1)
  };
};

/* Report unreadable images so the customer can correct them before sending. */
const preparePhotos = async (files) => {
  const photos = [];
  const skipped = [];
  let budget = PHOTO_TOTAL_BUDGET;
  for (const file of Array.from(files).slice(0, PHOTO_MAX_COUNT)) {
    let photo;
    try { photo = await shrinkImage(file); } catch (error) { photo = null; }
    if (!photo) {
      skipped.push(file.name || "one photo");
      continue;
    }
    if (photo.data.length > budget) {
      skipped.push(file.name || "one photo");
      continue;
    }
    budget -= photo.data.length;
    photos.push(photo);
  }
  return { photos, skipped };
};

document.addEventListener("DOMContentLoaded", () => {
  /* Inquiry form → Apps Script on the home and contact pages.
     Guard it without returning early; the header logic runs everywhere. */
  const form = document.getElementById("inquiryForm");
  /* Attribution. /contact/?ref=<slug> is how every guide, gemstone page and
     case study sends people to the form, so the lead can be traced back to
     the page that produced it. The value rides along in the email and in the
     GA4 generate_lead event (as cta_location, which is already a registered
     custom dimension). */
  const refParam = (new URLSearchParams(window.location.search).get("ref") || "").slice(0, 80);
  if (form) {
    const refField = form.querySelector("input[name='ref']");
    const pageField = form.querySelector("input[name='page']");
    if (refField) refField.value = refParam;
    if (pageField) pageField.value = window.location.pathname;
    const status = document.getElementById("formStatus");
    const button = form.querySelector("button[type='submit']");
    const photoInput = form.querySelector("input[name='photos']");
    const photoList = document.getElementById("photoList");
    /* Names the files back to the person straight away. A file input on its
       own shows nothing useful on mobile, and a silent attachment is one
       people re-pick three times. */
    if (photoInput && photoList) {
      photoInput.addEventListener("change", () => {
        const files = Array.from(photoInput.files);
        photoInput.setCustomValidity(files.length > PHOTO_MAX_COUNT
          ? "Please choose no more than two images." : "");
        photoList.textContent = "";
        files.forEach((file) => {
          const item = document.createElement("li");
          item.textContent = file.name;
          photoList.appendChild(item);
        });
        if (photoInput.files.length > PHOTO_MAX_COUNT) {
          const item = document.createElement("li");
          item.className = "photo-note";
          item.textContent = "Please choose no more than two images.";
          photoList.appendChild(item);
        }
      });
    }
    const setStatus = (message, state) => {
      if (!status) return;
      status.textContent = message;
      status.className = `form-status is-${state}`;
    };

    /* Fires once, on the first keystroke or focus in any field, so GA4 can
       show how many people start the form versus finish it. */
    let formStarted = false;
    const markStarted = () => {
      if (formStarted) return;
      formStarted = true;
      track("inquiry_form_start", { method: "inquiry_form" });
    };
    form.addEventListener("focusin", markStarted);
    form.addEventListener("input", markStarted);

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (button.disabled) return;
      if (photoInput && photoInput.files.length > PHOTO_MAX_COUNT) {
        setStatus("Please choose no more than two images.", "error");
        return;
      }
      const data = new FormData(form);

      if (!data.get("name") || !data.get("email")) {
        setStatus("Please add your name and email so we can reply.", "error");
        return;
      }
      /* The honeypot is deliberately NOT handled here. Dropping the submission
         client-side means a false positive (autofill filling the trap for a
         real person) loses the lead with no trace. Send everything; the server
         flags suspected spam in the subject line instead of discarding it. */

      button.disabled = true;
      const originalLabel = button.textContent;
      button.textContent = "Sending…";
      setStatus("Sending…", "pending");

      try {
        /* The raw File entries can't survive URLSearchParams, so they are
           replaced by base64 fields the Apps Script turns back into
           attachments. */
        data.delete("photos");
        const chosen = photoInput ? photoInput.files : [];
        let skipped = [];
        if (chosen && chosen.length) {
          setStatus("Preparing photos…", "pending");
          const prepared = await preparePhotos(chosen);
          skipped = prepared.skipped;
          if (skipped.length) {
            setStatus("We could not prepare " + skipped.join(", ") +
              ". Please choose JPG, PNG, or WebP images, or remove the photos to send your inquiry without them.", "error");
            return;
          }
          data.set("photo_count", String(prepared.photos.length));
          prepared.photos.forEach((photo, index) => {
            data.set(`photo_${index}_name`, photo.name);
            data.set(`photo_${index}_type`, photo.type);
            data.set(`photo_${index}_data`, photo.data);
          });
          setStatus("Sending…", "pending");
        }
        const response = await fetch(INQUIRY_ENDPOINT, {
          method: "POST",
          /* URL-encoded keeps this a "simple" request, so the browser skips
             the CORS preflight that Apps Script won’t answer. */
          body: new URLSearchParams(data)
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result = await response.json();
        if (result.ok !== true) throw new Error("Inquiry was not accepted");
        form.reset();
        if (photoList) photoList.textContent = "";
        if (photoInput) photoInput.setCustomValidity("");
        setStatus("Thank you, we got it. We’ll reply within one business day.", "success");
        track("generate_lead", { method: "inquiry_form", cta_location: refParam || window.location.pathname });
      } catch (error) {
        setStatus(
          "Something went wrong sending that. Please email chloe@ringmint.com or message us on WhatsApp.",
          "error"
        );
        /* Fires only when the endpoint is genuinely unreachable, so a spike
           here means the form is broken, not that nobody is interested. */
        track("form_submit_error", { method: "inquiry_form" });
      } finally {
        button.disabled = false;
        button.textContent = originalLabel;
      }
    });
  }

  /* Every call to action on the site carries a data-cta label naming the
     section it sits in (hero, cta-band, footer, ...). The channel is derived
     from the href so the markup only has to say *where* the link is, not
     what it does. GA4 reports slice cta_click by both. */
  const ctaChannel = (href) => {
    if (/wa\.me/.test(href)) return "whatsapp";
    if (/^mailto:/.test(href)) return "email";
    if (/instagram\.com/.test(href)) return "instagram";
    if (/#inquire/.test(href) || /\/contact\//.test(href)) return "inquiry_form";
    return "other";
  };
  document.addEventListener("click", (event) => {
    const cta = event.target.closest("a[data-cta]");
    if (!cta) return;
    const href = cta.getAttribute("href") || "";
    const channel = ctaChannel(href);
    track("cta_click", { cta_location: cta.dataset.cta, cta_channel: channel });
    /* WhatsApp is a real lead channel, and outbound clicks are invisible to
       GA4 by default, so form-only tracking would undercount leads. The
       location rides along so a lead can be traced back to the button. */
    if (channel === "whatsapp") {
      track("generate_lead", { method: "whatsapp", cta_location: cta.dataset.cta });
    }
  });

  /* “New guides by email” uses its own spreadsheet subscription endpoint. */
  document.querySelectorAll("form[data-capture]").forEach((capture) => {
    const cStatus = capture.querySelector(".form-status");
    const cButton = capture.querySelector("button[type='submit']");
    capture.addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = new FormData(capture);
      if (!data.get("email")) return;
      data.set("type", "newsletter");
      data.set("ref", capture.dataset.capture || "");
      data.set("page", window.location.pathname);
      cButton.disabled = true;
      try {
        const response = await fetch(SUBSCRIPTION_ENDPOINT, { method: "POST", body: new URLSearchParams(data) });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result = await response.json();
        if (result.ok !== true) throw new Error("Signup was not saved");
        capture.reset();
        if (cStatus) { cStatus.textContent = "You’re subscribed. Thanks for joining Ring Mint."; cStatus.className = "form-status is-success"; }
        track("newsletter_signup", { cta_location: capture.dataset.capture || window.location.pathname });
      } catch (error) {
        if (cStatus) { cStatus.textContent = "That did not send. Email chloe@ringmint.com and we will add you."; cStatus.className = "form-status is-error"; }
      } finally {
        cButton.disabled = false;
      }
    });
  });

  /* Purely decorative: adds a hairline under the sticky header once the
     page has scrolled. The header is sticky via CSS alone, so nothing
     here is required for the nav to work. */
  const header = document.querySelector(".site-header");
  if (header) {
    const sentinel = document.createElement("div");
    sentinel.setAttribute("aria-hidden", "true");
    sentinel.style.cssText = "position:absolute;top:0;height:1px;width:1px;";
    document.body.prepend(sentinel);
    new IntersectionObserver(
      ([entry]) => header.classList.toggle("is-stuck", !entry.isIntersecting),
      { threshold: 0 }
    ).observe(sentinel);
  }

  /* Recent-work carousel. Native scroll + snap does the real work; this only
     powers the arrow buttons and a slow auto-drift that stops for good the
     moment the visitor touches the carousel themselves. */
  const carousel = document.querySelector(".work-carousel");
  if (carousel) {
    const track = carousel.querySelector(".carousel-track");
    const slides = Array.from(track.querySelectorAll(".carousel-slide"));
    /* Scroll targets are always an exact snap position (a slide centered in
       the track); engines are picky about smooth scrolls that mandatory
       snapping would then adjust. */
    const targetLeft = (slide) => {
      const left = slide.offsetLeft + slide.offsetWidth / 2 - track.clientWidth / 2;
      return Math.max(0, Math.min(left, track.scrollWidth - track.clientWidth));
    };
    const currentIndex = () => {
      const center = track.scrollLeft + track.clientWidth / 2;
      let best = 0;
      let bestDist = Infinity;
      slides.forEach((slide, i) => {
        const dist = Math.abs(slide.offsetLeft + slide.offsetWidth / 2 - center);
        if (dist < bestDist) { bestDist = dist; best = i; }
      });
      return best;
    };
    const advance = (dir) => {
      const atEnd = track.scrollLeft + track.clientWidth >= track.scrollWidth - 8;
      const next = dir > 0 && atEnd
        ? 0
        : Math.max(0, Math.min(slides.length - 1, currentIndex() + dir));
      track.scrollTo({ left: targetLeft(slides[next]), behavior: "smooth" });
    };

    let timer = null;
    let dismissed = false;
    const stop = () => { clearInterval(timer); timer = null; };
    const dismiss = () => { dismissed = true; stop(); };
    const start = () => {
      if (timer || dismissed) return;
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      timer = setInterval(() => advance(1), 4000);
    };

    carousel.querySelector(".carousel-prev").addEventListener("click", () => { dismiss(); advance(-1); });
    carousel.querySelector(".carousel-next").addEventListener("click", () => { dismiss(); advance(1); });
    ["wheel", "touchstart", "pointerdown", "focusin"].forEach((type) =>
      track.addEventListener(type, dismiss, { passive: true })
    );

    /* Drift only while the carousel is actually on screen. */
    new IntersectionObserver(
      ([entry]) => (entry.isIntersecting ? start() : stop()),
      { threshold: 0.4 }
    ).observe(carousel);
  }
});

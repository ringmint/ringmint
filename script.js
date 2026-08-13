/* Google Apps Script web app that emails the inquiry to chloe@ringmint.com.
   Deploy Code.gs (see apps-script/Code.gs) as a web app — "Execute as: Me",
   "Who has access: Anyone" — and paste the /exec URL here. */
const INQUIRY_ENDPOINT = "https://script.google.com/macros/s/AKfycbwzSBJrrSFye2zYwinW2AvRx9OEipJbvqKd1TK-thl8OlP-haI5kgMxYmpoRW5KDJEU/exec";

/* Analytics helper. gtag is absent when an ad blocker eats the GA snippet,
   so every call has to tolerate that rather than throw mid-submit. */
const track = (name, params) => {
  if (typeof window.gtag === "function") window.gtag("event", name, params || {});
};

document.addEventListener("DOMContentLoaded", () => {
  /* Inquiry form → Apps Script. Only present on the home page, so guard it
     without returning early — the header logic below runs everywhere. */
  const form = document.getElementById("inquiryForm");
  if (form) {
    const status = document.getElementById("formStatus");
    const button = form.querySelector("button[type='submit']");
    const setStatus = (message, state) => {
      if (!status) return;
      status.textContent = message;
      status.className = `form-status is-${state}`;
    };

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = new FormData(form);

      if (!data.get("name") || !data.get("email")) {
        setStatus("Please add your name and email so we can reply.", "error");
        return;
      }
      /* The honeypot is deliberately NOT handled here. Dropping the submission
         client-side means a false positive — autofill filling the trap for a
         real person — loses the lead with no trace. Send everything; the server
         flags suspected spam in the subject line instead of discarding it. */

      button.disabled = true;
      const originalLabel = button.textContent;
      button.textContent = "Sending…";
      setStatus("Sending…", "pending");

      try {
        const response = await fetch(INQUIRY_ENDPOINT, {
          method: "POST",
          /* URL-encoded keeps this a "simple" request, so the browser skips
             the CORS preflight that Apps Script won’t answer. */
          body: new URLSearchParams(data)
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        form.reset();
        setStatus("Thank you — we got it. We’ll reply within one business day.", "success");
        track("generate_lead", { method: "inquiry_form" });
      } catch (error) {
        setStatus(
          "Something went wrong sending that. Please email chloe@ringmint.com or message us on WhatsApp.",
          "error"
        );
        /* Fires only when the endpoint is genuinely unreachable, so a spike
           here means the form is broken — not that nobody is interested. */
        track("form_submit_error", { method: "inquiry_form" });
      } finally {
        button.disabled = false;
        button.textContent = originalLabel;
      }
    });
  }

  /* WhatsApp is a real lead channel, and outbound clicks are invisible to
     GA4 by default — so form-only tracking would undercount leads. Delegated
     from the document because these links appear on every page. */
  document.addEventListener("click", (event) => {
    const link = event.target.closest('a[href*="wa.me"]');
    if (link) track("generate_lead", { method: "whatsapp" });
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
});

document.addEventListener("DOMContentLoaded", () => {
  /* Inquiry form → mailto. Only present on the home page, so guard it
     without returning early — the header logic below runs everywhere. */
  const form = document.getElementById("inquiryForm");
  if (form) {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const data = new FormData(form);
      const body = [
        `Name: ${data.get("name") || ""}`,
        `Email: ${data.get("email") || ""}`,
        `Phone / WhatsApp: ${data.get("phone") || ""}`,
        `Timeline: ${data.get("timeline") || ""}`,
        `Budget: ${data.get("budget") || ""}`,
        "",
        "What I’m looking for:",
        data.get("details") || ""
      ].join("\n");
      window.location.href = `mailto:chloe@ringmint.com?subject=${encodeURIComponent("Ring Mint custom ring inquiry")}&body=${encodeURIComponent(body)}`;
    });
  }

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

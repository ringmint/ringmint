document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("inquiryForm");
  if (!form) return;

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
});

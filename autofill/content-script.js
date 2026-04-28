(async function () {
  const response = await fetch("http://127.0.0.1:8765/api/autofill-profile");
  const profile = await response.json();

  const fieldMap = [
    { keys: ["name", "full_name", "fullname"], value: profile.fullName },
    { keys: ["email", "e-mail"], value: profile.email },
    { keys: ["phone", "mobile"], value: profile.phone },
    { keys: ["location", "city"], value: profile.location },
    { keys: ["linkedin"], value: profile.linkedin },
    { keys: ["portfolio", "website"], value: profile.portfolio },
    { keys: ["salary"], value: profile.salaryExpectation },
    { keys: ["sponsor", "sponsorship", "visa"], value: profile.commonAnswers?.sponsorship || profile.needsSponsorship },
    { keys: ["authorized", "authorization"], value: profile.commonAnswers?.authorized || profile.workAuthorization }
  ];

  function labelFor(input) {
    const id = input.id ? document.querySelector(`label[for="${CSS.escape(input.id)}"]`) : null;
    const nearby = input.closest("label") || input.parentElement;
    return [input.name, input.id, input.placeholder, input.getAttribute("aria-label"), id?.textContent, nearby?.textContent]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
  }

  let filled = 0;
  for (const input of document.querySelectorAll("input, textarea")) {
    const type = (input.getAttribute("type") || "").toLowerCase();
    if (["hidden", "file", "submit", "button", "checkbox", "radio"].includes(type)) continue;
    if (input.value && input.value.trim()) continue;
    const label = labelFor(input);
    const match = fieldMap.find((item) => item.value && item.keys.some((key) => label.includes(key)));
    if (!match) continue;
    input.value = match.value;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.dispatchEvent(new Event("change", { bubbles: true }));
    input.style.outline = "2px solid #0f766e";
    filled += 1;
  }

  const notice = document.createElement("div");
  notice.textContent = `Local Job Assistant filled ${filled} field${filled === 1 ? "" : "s"}. Review everything before submitting.`;
  Object.assign(notice.style, {
    position: "fixed",
    right: "16px",
    bottom: "16px",
    zIndex: 2147483647,
    background: "#172026",
    color: "#fff",
    padding: "12px 14px",
    borderRadius: "8px",
    font: "14px system-ui, sans-serif",
    boxShadow: "0 8px 24px rgba(0,0,0,.22)"
  });
  document.body.appendChild(notice);
  setTimeout(() => notice.remove(), 7000);
})();

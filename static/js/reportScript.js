const xVals = ['2023-10-25', '2023-11-07', '2023-12-06',
  '2024-02-20', '2024-04-12', '2024-04-17',
  '2024-04-22', '2024-04-23', '2024-04-26', '2024-05-07'];

const yVals = [7, 5.5, 3, 1, 3, 2, 1, 5, 1, 2];

new Chart("myChart", {
  type: "line",
  data: { labels: xVals, datasets: [{ data: yVals }] },
  options: {}
});
// -----------------------------------------------------------------

const ORIGIN = window.location.origin;

// Return the selected year if a <select> exists, else null (“all years”)
function getYear() {
  const sel = document.querySelector("select");
  if (!sel) return null;
  const v = (sel.value || "").trim();
  if (!v || /^all( years)?$/i.test(v)) return null;
  const n = Number(v.replace(/[^\d]/g, ""));
  return Number.isFinite(n) ? n : null;
}

// Robust fetch helper so errors are readable
async function fetchJSON(url, options) {
  let res;
  try {
    res = await fetch(url, options);
  } catch (e) {
    throw new Error("Network error: " + e.message);
  }
  const text = await res.text();
  let data = null;
  try { data = JSON.parse(text); } catch (_) {}
  if (!res.ok) {
    const msg = (data && (data.message || data.error)) || text || res.statusText;
    throw new Error(msg);
  }
  return data ?? {};
}

// Find a button by visible text (no IDs required)
function findButton(label) {
  const norm = s => (s || "").trim().toLowerCase();
  const want = norm(label);
  const els = [...document.querySelectorAll("button,a")];
  return els.find(el => norm(el.textContent) === want) || null;
}

// Click handlers
async function onCreateReport(ev) {
  ev?.preventDefault?.();
  const btn = ev?.currentTarget || this;
  btn && (btn.disabled = true);
  const y = getYear();
  const payload = (y !== null) ? { year: y } : {};

  try {
    // Try POST first
    const res = await fetch(`${ORIGIN}/api/reports/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const text = await res.text();
    let data = null; try { data = JSON.parse(text); } catch(_) {}
    if (!res.ok) throw new Error((data && (data.message||data.error)) || text || res.statusText);

    window.open(data.url, "_blank", "noopener");
  } catch (e) {
    // Fallback to GET navigation so we avoid fetch/CORS/preflight issues entirely
    const qs = y !== null ? `?year=${encodeURIComponent(y)}` : "";
    window.location.href = `${ORIGIN}/api/reports/generate${qs}`;
    // (the browser will show JSON; then click the "url" value, or keep using Download button)
  } finally {
    btn && (btn.disabled = false);
  }
}


function onDownloadReport(ev) {
  ev?.preventDefault?.();
  const y = getYear();
  const url = (y !== null)
    ? `${ORIGIN}/api/reports/export.csv?year=${encodeURIComponent(y)}`
    : `${ORIGIN}/api/reports/export.csv`;
  window.location.href = url;
}

// Bind once after DOM is ready and ensure buttons aren’t under overlays
document.addEventListener("DOMContentLoaded", () => {
  const createBtn = findButton("Create Report");
  const downloadBtn = findButton("Download Report");

  if (createBtn) {
    createBtn.style.position = "relative";
    createBtn.style.zIndex = "10000";
    createBtn.addEventListener("click", onCreateReport);
  }
  if (downloadBtn) {
    downloadBtn.style.position = "relative";
    downloadBtn.style.zIndex = "10000";
    downloadBtn.addEventListener("click", onDownloadReport);
  }
});
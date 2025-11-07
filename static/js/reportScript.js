const xVals = ['2023-10-25', '2023-11-07', '2023-12-06',
  '2024-02-20', '2024-04-12', '2024-04-17',
  '2024-04-22', '2024-04-23', '2024-04-26', '2024-05-07'];

const yVals = [7, 5.5, 3, 1, 3, 2, 1, 5, 1, 2];

new Chart("myChart", {
  type: "line",
  data: { labels: xVals, datasets: [{ data: yVals }] },
  options: {}
});

const ORIGIN = window.location.origin;

async function fetchJSON(url, options) {
  let res;
  try { res = await fetch(url, options); } catch (e) { throw new Error("Network error: " + e.message); }
  const text = await res.text();
  let data = null; try { data = JSON.parse(text); } catch {}
  if (!res.ok) throw new Error((data && (data.message || data.error)) || text || res.statusText);
  return data ?? {};
}

function findButton(label) {
  const norm = s => (s || "").trim().toLowerCase();
  return [...document.querySelectorAll("button,a")]
    .find(el => norm(el.textContent) === norm(label)) || null;
}

// fallback to years seen in the chart if the API returns none
function yearsFromChart() {
  try {
    const labels = Array.isArray(xVals) ? xVals : [];
    const ys = new Set();
    for (const s of labels) {
      const m = String(s).match(/\b(\d{4})\b/);
      if (m) ys.add(Number(m[1]));
    }
    return Array.from(ys).sort((a,b)=>a-b);
  } catch { return []; }
}

// --- Year popover ---
function showYearPicker(anchor, years) {
  document.getElementById("year-popover")?.remove();
  const box = document.createElement("div");
  box.id = "year-popover";
  box.style.position = "absolute";
  box.style.zIndex = "99999";
  box.style.background = "white";
  box.style.border = "1px solid #e5e7eb";
  box.style.borderRadius = "12px";
  box.style.padding = "10px";
  box.style.boxShadow = "0 8px 24px rgba(0,0,0,.12)";

  const sel = document.createElement("select");
  sel.style.minWidth = "140px";
  // populate
  const opts = [`<option value="all">All years</option>`]
    .concat((years || []).map(y => `<option value="${y}">${y}</option>`));
  sel.innerHTML = opts.join("");

  const row = document.createElement("div");
  row.style.display = "flex"; row.style.gap = "8px"; row.style.marginTop = "8px";

  const ok = document.createElement("button"); ok.textContent = "OK"; ok.className = "btn";
  const cancel = document.createElement("button"); cancel.textContent = "Cancel"; cancel.className = "btn";

  row.append(ok, cancel);
  box.append(sel, row);
  document.body.appendChild(box);

  const r = anchor.getBoundingClientRect();
  box.style.left = `${window.scrollX + r.left}px`;
  box.style.top  = `${window.scrollY + r.bottom + 8}px`;

  return { box, sel, ok, cancel };
}

async function pickYearAndRun(anchor, thenDo) {
  let years = [];
  try { years = await fetchJSON(`${ORIGIN}/api/events/years`); } catch {}
  if (!years || years.length === 0) {
    // fallback from chart labels
    years = yearsFromChart();
  }
  const { box, sel, ok, cancel } = showYearPicker(anchor, years);
  const close = () => box.remove();

  ok.addEventListener("click", () => {
    const v = sel.value;
    const year = (!v || v === "all") ? null : Number(v);
    close(); thenDo(year);
  });
  cancel.addEventListener("click", close);
  setTimeout(() => {
    document.addEventListener("click", function onDoc(e){
      if (!box.contains(e.target) && e.target !== anchor) { close(); document.removeEventListener("click", onDoc); }
    });
  }, 0);
}

// --- Actions ---
// Open the created report immediately (no banner)
async function createReportWithYear(year, btn) {
  btn && (btn.disabled = true);
  try {
    const payload = (Number.isFinite(year)) ? { year } : {};
    const data = await fetchJSON(`${ORIGIN}/api/reports/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    window.open(data.url, "_blank", "noopener");  // <= open new tab
  } catch (e) {
    alert("Failed to generate report: " + e.message);
    console.error(e);
  } finally {
    btn && (btn.disabled = false);
  }
}

// Download the HTML report
async function downloadReportWithYear(year) {
  // 1) Generate the report first so we have the filename/url
  const payload = Number.isFinite(year) ? { year } : {};
  const data = await fetchJSON(`${ORIGIN}/api/reports/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  // 2) Force download via Blob (never navigates the current tab)
  const u = new URL(data.url, ORIGIN);
  u.searchParams.set("download", "1");

  const res = await fetch(u, { credentials: "same-origin" });
  if (!res.ok) throw new Error(`Download failed: ${res.status} ${res.statusText}`);

  const blob = await res.blob();
  const fname = u.pathname.split("/").pop() || "report.html";

  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = fname;          // forces "Save As…" with this filename
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    URL.revokeObjectURL(a.href);
    a.remove();
  }, 0);
}



// --- Bindings ---
document.addEventListener("DOMContentLoaded", () => {
  const createBtn = findButton("Create Report");
  const downloadBtn = findButton("Download Report");

  if (createBtn) {
    createBtn.style.position = "relative"; createBtn.style.zIndex = "10000";
    createBtn.addEventListener("click", (e) => {
      e.preventDefault();
      pickYearAndRun(createBtn, (yr) => createReportWithYear(yr, createBtn));
    });
  }
  if (downloadBtn) {
    downloadBtn.style.position = "relative"; downloadBtn.style.zIndex = "10000";
    downloadBtn.addEventListener("click", (e) => {
      e.preventDefault();
      pickYearAndRun(downloadBtn, (yr) => downloadReportWithYear(yr));
    });
  }
});
const ORIGIN = window.location.origin;

// --- Fetch helper ---
async function fetchJSON(url, options) {
  let res;
  try { res = await fetch(url, options); } catch (e) { throw new Error("Network error: " + e.message); }
  const text = await res.text();
  let data = null; 
  try { data = JSON.parse(text); } catch {}
  if (!res.ok) throw new Error((data && (data.message || data.error)) || text || res.statusText);
  return data ?? {};
}

// --- Year picker modal ---
function showYearPickerModal(years) {
  // Remove existing modal if any
  document.getElementById("yearModal")?.remove();

  const modal = document.createElement("div");
  modal.id = "yearModal";
  modal.className = "modal fade show";
  modal.style.display = "block";
  modal.tabIndex = -1;
  modal.setAttribute("aria-modal", "true");
  modal.innerHTML = `
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Select Year</h5>
          <button type="button" class="btn-close" id="yearModalClose"></button>
        </div>
        <div class="modal-body">
          <select id="yearSelect" class="form-select">
            <option value="all">All years</option>
            ${years.map(y => `<option value="${y}">${y}</option>`).join('')}
          </select>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-primary" id="yearModalOk">OK</button>
          <button type="button" class="btn btn-secondary" id="yearModalCancel">Cancel</button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  return {
    modal,
    select: modal.querySelector("#yearSelect"),
    okBtn: modal.querySelector("#yearModalOk"),
    cancelBtn: modal.querySelector("#yearModalCancel"),
    closeBtn: modal.querySelector("#yearModalClose")
  };
}

async function pickYearAndRun(actionFn) {
  let years = [];
  try { years = await fetchJSON(`${ORIGIN}/api/events/years`); } catch {}
  if (!years || years.length === 0) {
    console.warn("No years returned from API, defaulting to current year.");
    years = [new Date().getFullYear()];
  }

  const { modal, select, okBtn, cancelBtn, closeBtn } = showYearPickerModal(years);

  const closeModal = () => modal.remove();

  okBtn.addEventListener("click", () => {
    const yearVal = select.value;
    const year = yearVal === "all" ? null : Number(yearVal);
    closeModal();
    actionFn(year);
  });

  cancelBtn.addEventListener("click", closeModal);
  closeBtn.addEventListener("click", closeModal);
}

// --- Report generation ---
async function createReportWithYear(year, btn) {
  if (btn) btn.disabled = true;
  try {
    const payload = year ? { year } : {};
    const data = await fetchJSON(`${ORIGIN}/api/reports/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    window.open(data.url, "_blank", "noopener");
  } catch (e) {
    alert("Failed to generate report: " + e.message);
    console.error(e);
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function downloadReportWithYear(year) {
  try {
    const payload = year ? { year } : {};
    const data = await fetchJSON(`${ORIGIN}/api/reports/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const u = new URL(data.url, ORIGIN);
    u.searchParams.set("download", "1");
    const res = await fetch(u, { credentials: "same-origin" });
    if (!res.ok) throw new Error(`Download failed: ${res.status} ${res.statusText}`);

    const blob = await res.blob();
    const fname = u.pathname.split("/").pop() || "report.html";

    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = fname;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      URL.revokeObjectURL(a.href);
      a.remove();
    }, 0);
  } catch (e) {
    alert("Failed to download report: " + e.message);
    console.error(e);
  }
}

// --- Update chart with new data ---
function updateEventSummaryChart(labels, counts) {
  if (window.eventSummaryChart) {
    window.eventSummaryChart.data.labels = labels;
    window.eventSummaryChart.data.datasets[0].data = counts;
    window.eventSummaryChart.update();
  }
}

// --- Bind buttons ---
document.addEventListener("DOMContentLoaded", () => {
  const createBtn = document.getElementById("btn-generate");
  const downloadBtn = document.getElementById("btn-export");

  if (createBtn) {
    createBtn.addEventListener("click", e => {
      e.preventDefault();
      pickYearAndRun(year => createReportWithYear(year, createBtn));
    });
  }

  if (downloadBtn) {
    downloadBtn.addEventListener("click", e => {
      e.preventDefault();
      pickYearAndRun(year => downloadReportWithYear(year));
    });
  }
});

const state = {
  jobs: [],
  selectedId: null,
};

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || `Request failed: ${res.status}`);
  return data;
}

function badge(value) {
  const label = String(value || "unknown").replaceAll("_", " ");
  return `<span class="badge ${value}">${label}</span>`;
}

function renderStats(stats) {
  const buckets = stats.buckets || {};
  const latest = stats.latest_ingest;
  $("stats").innerHTML = [
    ["Apply", buckets.apply || 0],
    ["Maybe", buckets.maybe || 0],
    ["Manual review", buckets.manual_review || 0],
    ["Skip", buckets.skip || 0],
  ]
    .map(([label, count]) => `<div class="stat"><strong>${count}</strong><span>${label}</span></div>`)
    .join("") +
    `<div class="stat"><strong>${latest ? latest.fetched_count : 0}</strong><span>Latest ingest fetched</span></div>`;
}

function renderJobs() {
  const list = $("jobList");
  if (!state.jobs.length) {
    list.innerHTML = `<div class="empty-state">No jobs yet. Load sample jobs or run live ingest.</div>`;
    return;
  }
  list.innerHTML = state.jobs
    .map(
      (job) => `
      <button class="job-card ${job.id === state.selectedId ? "active" : ""}" data-id="${job.id}">
        <h2>${escapeHtml(job.title)}</h2>
        <div class="meta">
          <span>${escapeHtml(job.company)}</span>
          <span>${escapeHtml(job.location || "Location unclear")}</span>
        </div>
        <div class="meta" style="margin-top:8px">
          ${badge(job.bucket)}
          ${badge(job.sponsorship_signal)}
          <span class="badge">${job.total_score}/100</span>
          <span class="badge">${escapeHtml(job.status)}</span>
        </div>
      </button>`
    )
    .join("");
  list.querySelectorAll(".job-card").forEach((btn) => {
    btn.addEventListener("click", () => selectJob(Number(btn.dataset.id)));
  });
}

function scoreBox(label, value) {
  return `<div class="score"><strong>${value}</strong><span>${label}</span></div>`;
}

function renderDetail(job) {
  $("jobDetail").innerHTML = `
    <h2>${escapeHtml(job.title)}</h2>
    <p>${escapeHtml(job.company)} · ${escapeHtml(job.location || "Location unclear")}</p>
    <div class="meta" style="margin-top:10px">
      ${badge(job.bucket)}
      ${badge(job.sponsorship_signal)}
      <span class="badge">${escapeHtml(job.source)}</span>
      <span class="badge">${escapeHtml(job.status)}</span>
    </div>

    <div class="score-grid">
      ${scoreBox("Total", job.total_score)}
      ${scoreBox("Role", job.role_score)}
      ${scoreBox("Location", job.location_score)}
      ${scoreBox("Sponsorship", job.sponsorship_score)}
      ${scoreBox("Seniority", job.seniority_score)}
      ${scoreBox("Effort", job.effort_score)}
    </div>

    <div class="detail-actions">
      <button data-action="shortlisted">Shortlist</button>
      <button data-action="applied">Mark applied</button>
      <button class="secondary" data-action="skip">Skip</button>
      <a href="${escapeAttribute(job.apply_url || "#")}" target="_blank" rel="noreferrer"><button class="secondary">Open apply page</button></a>
    </div>

    <div class="section">
      <h3>Why this score</h3>
      <ul>${(job.score_reasons || []).map((r) => `<li>${escapeHtml(r)}</li>`).join("")}</ul>
    </div>

    <div class="section">
      <h3>Notes</h3>
      <textarea id="notesInput" rows="4">${escapeHtml(job.notes || "")}</textarea>
      <div class="detail-actions"><button data-action="save-notes">Save notes</button></div>
    </div>

    <div class="section">
      <h3>Job description</h3>
      <div class="description">${escapeHtml(job.description || "No description available.")}</div>
    </div>
  `;

  $("jobDetail").querySelectorAll("[data-action]").forEach((el) => {
    el.addEventListener("click", () => handleAction(el.dataset.action, job.id));
  });
}

async function handleAction(action, jobId) {
  try {
    if (action === "save-notes") {
      const notes = $("notesInput").value;
      const job = await api(`/api/jobs/${jobId}`, { method: "POST", body: JSON.stringify({ notes }) });
      await loadJobs();
      renderDetail(job);
      return;
    }
    const status = action === "skip" ? "rejected" : action;
    const bucket = action === "skip" ? "skip" : undefined;
    const job = await api(`/api/jobs/${jobId}`, {
      method: "POST",
      body: JSON.stringify({ status, ...(bucket ? { bucket } : {}) }),
    });
    await loadJobs();
    renderDetail(job);
  } catch (err) {
    alert(err.message);
  }
}

async function selectJob(id) {
  state.selectedId = id;
  renderJobs();
  const job = await api(`/api/jobs/${id}`);
  renderDetail(job);
}

async function loadStats() {
  renderStats(await api("/api/stats"));
}

async function loadJobs() {
  const params = new URLSearchParams();
  if ($("searchInput").value) params.set("q", $("searchInput").value);
  if ($("bucketFilter").value) params.set("bucket", $("bucketFilter").value);
  if ($("statusFilter").value) params.set("status", $("statusFilter").value);
  state.jobs = await api(`/api/jobs?${params.toString()}`);
  renderJobs();
  await loadStats();
}

async function runIngest(live) {
  const btn = live ? $("liveIngestBtn") : $("sampleIngestBtn");
  const old = btn.textContent;
  btn.textContent = live ? "Ingesting..." : "Loading...";
  btn.disabled = true;
  try {
    const result = await api("/api/ingest", { method: "POST", body: JSON.stringify({ live }) });
    await loadJobs();
    alert(`Ingest finished. Fetched ${result.fetched_count}, inserted ${result.inserted_count}, updated ${result.updated_count}, errors ${result.error_count}.`);
  } catch (err) {
    alert(err.message);
  } finally {
    btn.textContent = old;
    btn.disabled = false;
  }
}

async function writeQueue() {
  const btn = $("queueBtn");
  const old = btn.textContent;
  btn.textContent = "Writing...";
  btn.disabled = true;
  try {
    const result = await api("/api/write-queue", { method: "POST", body: "{}" });
    alert(`Queue written:\n${result.markdown}\n${result.csv}`);
  } catch (err) {
    alert(err.message);
  } finally {
    btn.textContent = old;
    btn.disabled = false;
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
  return escapeHtml(value || "#");
}

$("sampleIngestBtn").addEventListener("click", () => runIngest(false));
$("liveIngestBtn").addEventListener("click", () => runIngest(true));
$("queueBtn").addEventListener("click", () => writeQueue());
$("searchInput").addEventListener("input", () => loadJobs());
$("bucketFilter").addEventListener("change", () => loadJobs());
$("statusFilter").addEventListener("change", () => loadJobs());

loadJobs().catch((err) => {
  $("jobList").innerHTML = `<div class="empty-state">${escapeHtml(err.message)}</div>`;
});

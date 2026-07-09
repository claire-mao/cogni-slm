const state = {
  status: null,
  cases: [],
  selectedCaseId: null,
  selectedTeacherModel: null,
};

function $(id) {
  return document.getElementById(id);
}

function pretty(value) {
  return JSON.stringify(value ?? {}, null, 2);
}

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`GET ${url} failed: ${response.status} ${text}`);
  }
  return response.json();
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || data.error || `POST ${url} failed`);
  }
  return data;
}

function fillSelect(selectEl, values) {
  const current = selectEl.value;
  const options = ['<option value="">All</option>']
    .concat(values.map((value) => `<option value="${value}">${value}</option>`));
  selectEl.innerHTML = options.join("");
  if (values.includes(current)) {
    selectEl.value = current;
  }
}

async function loadStatus() {
  state.status = await getJson("/api/status");
  fillSelect($("filter-run"), state.status.runs || []);
  fillSelect($("filter-task"), state.status.tasks || []);
  fillSelect($("filter-model"), state.status.models || []);
}

function buildCaseQuery() {
  const query = new URLSearchParams();
  query.set("offset", "0");
  query.set("limit", "200");
  const run = $("filter-run").value;
  const task = $("filter-task").value;
  const model = $("filter-model").value;
  const text = $("filter-query").value.trim();
  if (run) query.set("run_id", run);
  if (task) query.set("task_id", task);
  if (model) query.set("model", model);
  if (text) query.set("query", text);
  return query.toString();
}

function renderCaseList() {
  const container = $("cases");
  container.innerHTML = "";
  for (const item of state.cases) {
    const li = document.createElement("li");
    if (item.case_id === state.selectedCaseId) {
      li.classList.add("active");
    }
    li.dataset.caseId = item.case_id;
    li.innerHTML = `
      <div><strong>${item.example_id}</strong></div>
      <div class="case-meta">task: ${item.task_id}</div>
      <div class="case-meta">models: ${(item.teacher_models || []).join(", ")}</div>
      <div class="case-meta">run: ${item.run_id} | seed: ${item.seed}</div>
    `;
    li.addEventListener("click", () => {
      state.selectedCaseId = item.case_id;
      state.selectedTeacherModel = null;
      loadCaseDetail();
      renderCaseList();
    });
    container.appendChild(li);
  }
  $("case-count").textContent = `total: ${state.cases.length}`;
}

async function loadCases() {
  const query = buildCaseQuery();
  const payload = await getJson(`/api/cases?${query}`);
  state.cases = payload.cases || [];
  if (!state.selectedCaseId && state.cases.length > 0) {
    state.selectedCaseId = state.cases[0].case_id;
  }
  renderCaseList();
  if (state.selectedCaseId) {
    await loadCaseDetail();
  }
}

function renderTeacherSelect(models) {
  const select = $("teacher-select");
  const options = models.map((model) => `<option value="${model}">${model}</option>`);
  select.innerHTML = options.join("");
  if (!state.selectedTeacherModel && models.length > 0) {
    state.selectedTeacherModel = models[0];
  }
  if (state.selectedTeacherModel && models.includes(state.selectedTeacherModel)) {
    select.value = state.selectedTeacherModel;
  }
}

async function loadCaseDetail() {
  if (!state.selectedCaseId) return;
  const query = new URLSearchParams();
  if (state.selectedTeacherModel) {
    query.set("teacher_model", state.selectedTeacherModel);
  }
  const payload = await getJson(`/api/cases/${state.selectedCaseId}?${query.toString()}`);

  $("case-meta").innerHTML = `
    <div><strong>case_id:</strong> ${payload.case_id}</div>
    <div><strong>run:</strong> ${payload.run_id}</div>
    <div><strong>task:</strong> ${payload.task_id}</div>
    <div><strong>example:</strong> ${payload.example_id}</div>
    <div><strong>prompt version:</strong> ${payload.prompt_version}</div>
  `;
  $("gold-answer").textContent = pretty(payload.gold_answer);
  $("teacher-answer").textContent = pretty(payload.teacher_answer?.output_json);
  $("latest-review").textContent = pretty(payload.latest_review || {});

  const models = (payload.multiple_teacher_outputs || []).map((row) => row.model);
  renderTeacherSelect(models);

  const multi = $("multi-outputs");
  multi.innerHTML = "";
  for (const row of payload.multiple_teacher_outputs || []) {
    const div = document.createElement("div");
    div.className = "output-card";
    div.innerHTML = `
      <div class="title">${row.model} (confidence: ${row.confidence ?? "n/a"})</div>
      <pre>${pretty(row.output_json)}</pre>
    `;
    multi.appendChild(div);
  }
}

async function saveReview(event) {
  event.preventDefault();
  if (!state.selectedCaseId) return;

  let editedOutput = $("edited-output").value.trim();
  if (!editedOutput) {
    editedOutput = null;
  }

  const payload = {
    case_id: state.selectedCaseId,
    reviewer_id: $("reviewer-id").value.trim() || "anonymous",
    decision: $("decision").value,
    selected_teacher_model: $("teacher-select").value || null,
    edited_output: editedOutput,
    flags: {
      hallucination: $("flag-hallucination").checked,
      rubric_error: $("flag-rubric-error").checked,
    },
    notes: $("review-notes").value.trim(),
  };

  try {
    const result = await postJson("/api/reviews", payload);
    $("review-status").textContent = `saved review ${result.review.review_id}`;
    $("latest-review").textContent = pretty(result.review);
  } catch (error) {
    $("review-status").textContent = `save failed: ${error.message}`;
  }
}

function bindEvents() {
  $("refresh-cases").addEventListener("click", loadCases);
  $("filter-run").addEventListener("change", loadCases);
  $("filter-task").addEventListener("change", loadCases);
  $("filter-model").addEventListener("change", loadCases);
  $("filter-query").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      loadCases();
    }
  });
  $("teacher-select").addEventListener("change", async () => {
    state.selectedTeacherModel = $("teacher-select").value || null;
    await loadCaseDetail();
  });
  $("review-form").addEventListener("submit", saveReview);
}

async function init() {
  bindEvents();
  await loadStatus();
  await loadCases();
}

init().catch((error) => {
  $("review-status").textContent = `init failed: ${error.message}`;
});

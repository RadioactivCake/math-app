// Configuration
const API_BASE = "http://127.0.0.1:8000";

// State
let currentTopicId = null;
let selectedImageData = null;
let currentProblemId = null;
let historyOffset = 0;
const HISTORY_LIMIT = 10;

// ============================================================
// View Management
// ============================================================

function showView(viewName) {
  // Hide all views
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));

  // Show target view
  document.getElementById(`view-${viewName}`).classList.add("active");

  // Update nav buttons
  document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
  if (viewName === "topics") {
    document.getElementById("nav-home").classList.add("active");
    loadTopics();
  } else if (viewName === "history") {
    document.getElementById("nav-history").classList.add("active");
    historyOffset = 0;
    loadHistory();
  }
}

function goBackToProblems() {
  // Reset upload state when going back
  removeImage();
  hideFeedback();
  showView("problems");
}

// ============================================================
// Topics
// ============================================================

async function loadTopics() {
  const grid = document.getElementById("topics-grid");
  grid.innerHTML = '<p style="color: #94a3b8;">Loading topics...</p>';

  try {
    const res = await fetch(`${API_BASE}/api/topics`);
    if (!res.ok) throw new Error("Failed to load topics");
    const data = await res.json();

    if (data.topics.length === 0) {
      grid.innerHTML = '<p class="empty-state">No topics available.</p>';
      return;
    }

    grid.innerHTML = data.topics
      .map(
        (t) => `
      <div class="topic-card" onclick="selectTopic('${t.id}')">
        <h3>${escapeHtml(t.name)}</h3>
        <p>${escapeHtml(t.description || "")}</p>
        <div class="topic-meta">
          <span>Grade ${t.grade_level}</span>
          <span>${t.problem_count} problem${t.problem_count !== 1 ? "s" : ""}</span>
        </div>
      </div>
    `
      )
      .join("");
  } catch (err) {
    grid.innerHTML = `<div class="error-message">Could not load topics. Is the backend running?</div>`;
  }
}

async function selectTopic(topicId) {
  currentTopicId = topicId;

  try {
    const res = await fetch(`${API_BASE}/api/topics/${topicId}/problems`);
    if (!res.ok) throw new Error("Failed to load problems");
    const data = await res.json();

    // Set topic header
    document.getElementById("topic-header").innerHTML = `
      <h2>${escapeHtml(data.topic.name)}</h2>
      <p>${escapeHtml(data.topic.description || "")}</p>
    `;

    // Set problems list
    const list = document.getElementById("problems-list");
    if (data.problems.length === 0) {
      list.innerHTML = '<p class="empty-state">No problems for this topic yet.</p>';
    } else {
      list.innerHTML = data.problems
        .map(
          (p) => `
        <div class="problem-card" onclick="selectProblem('${p.id}', '${escapeHtml(p.question).replace(/'/g, "\\'")}')">
          <span class="question">${escapeHtml(p.question)}</span>
          <span class="arrow">&rarr;</span>
        </div>
      `
        )
        .join("");
    }

    showProblemsView();
  } catch (err) {
    alert("Failed to load problems. Please try again.");
  }
}

function showProblemsView() {
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
  document.getElementById("view-problems").classList.add("active");
}

// ============================================================
// Problem & Upload
// ============================================================

function selectProblem(problemId, questionText) {
  currentProblemId = problemId;

  document.getElementById("problem-display").innerHTML = `
    <h3>Problem</h3>
    <div class="question-text">${escapeHtml(questionText)}</div>
  `;

  // Reset upload state
  removeImage();
  hideFeedback();

  // Show upload view
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
  document.getElementById("view-upload").classList.add("active");
}

// Drag & Drop and File Input
document.addEventListener("DOMContentLoaded", () => {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");

  // Click to select
  dropZone.addEventListener("click", () => fileInput.click());

  // Drag events
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) {
      handleImageFile(file);
    }
  });

  // File input change
  fileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) handleImageFile(file);
  });

  // Load topics on startup
  loadTopics();
});

function handleImageFile(file) {
  // Validate size (10MB max)
  if (file.size > 10 * 1024 * 1024) {
    alert("Image is too large. Please use an image under 10MB.");
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    selectedImageData = e.target.result; // data URI (data:image/...;base64,...)

    // Show preview
    document.getElementById("preview-img").src = selectedImageData;
    document.getElementById("image-preview").classList.remove("hidden");
    document.getElementById("drop-zone").classList.add("hidden");
    document.getElementById("submit-btn").disabled = false;
  };
  reader.readAsDataURL(file);
}

function removeImage() {
  selectedImageData = null;
  document.getElementById("preview-img").src = "";
  document.getElementById("image-preview").classList.add("hidden");
  document.getElementById("drop-zone").classList.remove("hidden");
  document.getElementById("submit-btn").disabled = true;
  document.getElementById("file-input").value = "";
}

function hideFeedback() {
  document.getElementById("feedback-section").classList.add("hidden");
  document.getElementById("feedback-section").innerHTML = "";
  document.getElementById("loading").classList.add("hidden");
  document.getElementById("upload-area").classList.remove("hidden");
}

// ============================================================
// Submit Solution
// ============================================================

async function submitSolution() {
  if (!selectedImageData || !currentProblemId) return;

  // Show loading, hide upload area
  document.getElementById("upload-area").classList.add("hidden");
  document.getElementById("loading").classList.remove("hidden");
  document.getElementById("feedback-section").classList.add("hidden");

  try {
    const res = await fetch(`${API_BASE}/api/submissions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        problem_id: currentProblemId,
        image_data: selectedImageData,
      }),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || "Submission failed");
    }

    const data = await res.json();
    displayFeedback(data);
  } catch (err) {
    document.getElementById("feedback-section").innerHTML = `
      <div class="error-message">${escapeHtml(err.message)}</div>
      <button class="try-again-btn" onclick="resetUpload()">Try Again</button>
    `;
    document.getElementById("feedback-section").classList.remove("hidden");
  } finally {
    document.getElementById("loading").classList.add("hidden");
  }
}

function resetUpload() {
  removeImage();
  hideFeedback();
  document.getElementById("upload-area").classList.remove("hidden");
}

// ============================================================
// Feedback Display
// ============================================================

function displayFeedback(data) {
  const section = document.getElementById("feedback-section");
  const feedback = data.feedback;

  // Handle quality check failure
  if (data.quality_failed) {
    let html = `
      <div class="quality-warning">
        <div class="quality-warning-icon">
          <svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        </div>
        <h3>Image Quality Issue</h3>
        <p class="quality-summary">${escapeHtml(feedback.summary)}</p>
    `;

    if (feedback.suggestions && feedback.suggestions.length > 0) {
      html += `<ul class="quality-tips">`;
      feedback.suggestions.forEach((s) => {
        html += `<li>${escapeHtml(s)}</li>`;
      });
      html += `</ul>`;
    }

    if (feedback.encouragement) {
      html += `<p class="quality-encouragement">${escapeHtml(feedback.encouragement)}</p>`;
    }

    html += `<button class="try-again-btn" onclick="resetUpload()">Retake Photo</button>`;
    html += `</div>`;

    section.innerHTML = html;
    section.classList.remove("hidden");
    return;
  }

  let html = `
    <div class="feedback-header">
      <span class="result-badge ${data.is_correct ? "correct" : "incorrect"}">
        ${data.is_correct ? "Correct!" : "Not quite right"}
      </span>
    </div>

    <div class="feedback-summary">${escapeHtml(feedback.summary)}</div>
  `;

  // Steps analysis
  if (feedback.steps_analysis && feedback.steps_analysis.length > 0) {
    html += '<div class="steps-title">Step-by-step analysis:</div>';
    feedback.steps_analysis.forEach((step) => {
      html += `
        <div class="step-item ${step.evaluation}">
          <div class="step-label">${escapeHtml(step.step)}</div>
          <div class="step-comment">${escapeHtml(step.comment)}</div>
        </div>
      `;
    });
  }

  // Suggestions
  if (feedback.suggestions && feedback.suggestions.length > 0) {
    html += `
      <div class="suggestions-section">
        <h4>Suggestions:</h4>
        <ul>
          ${feedback.suggestions.map((s) => `<li>${escapeHtml(s)}</li>`).join("")}
        </ul>
      </div>
    `;
  }

  // Encouragement
  if (feedback.encouragement) {
    html += `<div class="encouragement">${escapeHtml(feedback.encouragement)}</div>`;
  }

  // Extracted work
  if (data.extracted_work) {
    html += `
      <div class="extracted-work">
        <strong>What we read from your work:</strong>
        ${escapeHtml(data.extracted_work)}
      </div>
    `;
  }

  // Try again button
  html += `<button class="try-again-btn" onclick="resetUpload()">Submit another photo</button>`;

  section.innerHTML = html;
  section.classList.remove("hidden");
}

// ============================================================
// History
// ============================================================

async function loadHistory() {
  const list = document.getElementById("history-list");
  const empty = document.getElementById("history-empty");
  const pagination = document.getElementById("history-pagination");

  list.innerHTML = '<p style="color: #94a3b8;">Loading history...</p>';
  empty.classList.add("hidden");
  pagination.innerHTML = "";

  try {
    const res = await fetch(
      `${API_BASE}/api/submissions?limit=${HISTORY_LIMIT}&offset=${historyOffset}`
    );
    if (!res.ok) throw new Error("Failed to load history");
    const data = await res.json();

    if (data.total === 0) {
      list.innerHTML = "";
      empty.classList.remove("hidden");
      return;
    }

    list.innerHTML = data.submissions
      .map(
        (s) => `
      <div class="history-card" onclick="viewSubmission(${s.id})">
        <div class="history-info">
          <div class="history-question">${escapeHtml(s.question)}</div>
          <div class="history-summary">${escapeHtml(s.feedback_summary)}</div>
        </div>
        <div class="history-meta">
          <span class="history-date">${formatDate(s.created_at)}</span>
          <span class="history-badge ${s.is_correct ? "correct" : "incorrect"}">
            ${s.is_correct ? "Correct" : "Incorrect"}
          </span>
        </div>
      </div>
    `
      )
      .join("");

    // Pagination
    if (data.total > HISTORY_LIMIT) {
      const totalPages = Math.ceil(data.total / HISTORY_LIMIT);
      const currentPage = Math.floor(historyOffset / HISTORY_LIMIT) + 1;

      pagination.innerHTML = `
        <button class="page-btn" onclick="changePage(-1)" ${currentPage <= 1 ? "disabled" : ""}>
          &larr; Prev
        </button>
        <span style="padding: 0.4rem; color: #64748b; font-size: 0.85rem;">
          Page ${currentPage} of ${totalPages}
        </span>
        <button class="page-btn" onclick="changePage(1)" ${currentPage >= totalPages ? "disabled" : ""}>
          Next &rarr;
        </button>
      `;
    }
  } catch (err) {
    list.innerHTML = `<div class="error-message">Could not load history. Is the backend running?</div>`;
  }
}

function changePage(direction) {
  historyOffset += direction * HISTORY_LIMIT;
  if (historyOffset < 0) historyOffset = 0;
  loadHistory();
}

// ============================================================
// Submission Detail
// ============================================================

async function viewSubmission(id) {
  const content = document.getElementById("detail-content");
  content.innerHTML = '<p style="color: #94a3b8;">Loading details...</p>';

  // Show detail view
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
  document.getElementById("view-detail").classList.add("active");

  try {
    const res = await fetch(`${API_BASE}/api/submissions/${id}`);
    if (!res.ok) throw new Error("Failed to load submission");
    const data = await res.json();
    const feedback = data.feedback;

    let html = `
      <div class="detail-section">
        <h3>Problem</h3>
        <div style="font-size: 1.1rem; color: #1e293b;">${escapeHtml(data.question)}</div>
      </div>

      <div class="detail-section">
        <h3>Result</h3>
        <span class="result-badge ${data.is_correct ? "correct" : "incorrect"}">
          ${data.is_correct ? "Correct!" : "Not quite right"}
        </span>
        <p style="margin-top: 0.5rem; color: #475569;">Correct answer: ${escapeHtml(data.correct_answer)}</p>
      </div>

      <div class="detail-section">
        <h3>Feedback</h3>
        <p style="color: #334155; margin-bottom: 1rem;">${escapeHtml(feedback.summary)}</p>
    `;

    // Steps
    if (feedback.steps_analysis && feedback.steps_analysis.length > 0) {
      html += '<div class="steps-title">Step-by-step analysis:</div>';
      feedback.steps_analysis.forEach((step) => {
        html += `
          <div class="step-item ${step.evaluation}">
            <div class="step-label">${escapeHtml(step.step)}</div>
            <div class="step-comment">${escapeHtml(step.comment)}</div>
          </div>
        `;
      });
    }

    // Suggestions
    if (feedback.suggestions && feedback.suggestions.length > 0) {
      html += `
        <div class="suggestions-section">
          <h4>Suggestions:</h4>
          <ul>
            ${feedback.suggestions.map((s) => `<li>${escapeHtml(s)}</li>`).join("")}
          </ul>
        </div>
      `;
    }

    // Encouragement
    if (feedback.encouragement) {
      html += `<div class="encouragement">${escapeHtml(feedback.encouragement)}</div>`;
    }

    html += "</div>"; // close feedback detail-section

    // Extracted text
    if (data.extracted_text) {
      html += `
        <div class="detail-section">
          <h3>Extracted Work</h3>
          <p style="color: #475569;">${escapeHtml(data.extracted_text)}</p>
        </div>
      `;
    }

    // Timestamp
    html += `
      <div class="detail-section">
        <h3>Submitted</h3>
        <p style="color: #475569;">${formatDate(data.created_at)}</p>
      </div>
    `;

    content.innerHTML = html;
  } catch (err) {
    content.innerHTML = `<div class="error-message">Could not load submission details.</div>`;
  }
}

// ============================================================
// Utilities
// ============================================================

function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

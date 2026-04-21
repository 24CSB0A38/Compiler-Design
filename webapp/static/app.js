/* ═══════════════════════════════════════
   INTELLIGENT COMPILER SUITE  –  app.js v9
   ═══════════════════════════════════════ */
document.addEventListener("DOMContentLoaded", () => {

    /* ── DOM references ── */
    const fileInput        = document.getElementById("file-input");
    const fileNameDisplay  = document.getElementById("file-name");
    const form             = document.getElementById("analyze-form");
    const submitBtn        = document.getElementById("submit-btn");
    const btnText          = document.getElementById("btn-text");
    const spinner          = document.getElementById("spinner");
    const btnIcon          = submitBtn.querySelector(".btn-icon");
    const toast            = document.getElementById("error-toast");

    const resultsPanel     = document.getElementById("results-panel");
    const placeholderPanel = document.getElementById("placeholder-panel");

    const badge            = document.getElementById("compiler-status");
    const successBanner    = document.getElementById("success-banner");
    const profSkill        = document.getElementById("prof-skill");
    const profTotal        = document.getElementById("prof-total");
    const profDominant     = document.getElementById("prof-dominant");
    const profileCard      = document.getElementById("profile-card");

    // Time Complexity
    const tcNotation       = document.getElementById("tc-notation");
    const tcLabel          = document.getElementById("tc-label");
    const tcExplanation    = document.getElementById("tc-explanation");

    const errorFeed        = document.getElementById("error-feed");
    const codeTextArea     = document.getElementById("code-text");
    const lineNumbers      = document.getElementById("line-numbers");
    const errorGutter      = document.getElementById("error-gutter");

    /* ── Line numbers ── */
    function updateLineNumbers() {
        const lines = codeTextArea.value.split("\n").length;
        lineNumbers.textContent = Array.from({length: lines}, (_, i) => i + 1).join("\n");
        // sync scroll
        lineNumbers.scrollTop = codeTextArea.scrollTop;
    }
    codeTextArea.addEventListener("input",  updateLineNumbers);
    codeTextArea.addEventListener("scroll", () => {
        lineNumbers.scrollTop = codeTextArea.scrollTop;
    });
    updateLineNumbers();

    /* ── File selection ── */
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            fileNameDisplay.textContent = `📎 ${e.target.files[0].name}`;
            codeTextArea.value = "";
            updateLineNumbers();
            clearErrorGutter();
        }
    });

    codeTextArea.addEventListener("input", () => {
        if (fileInput.value) {
            fileInput.value = "";
            fileNameDisplay.textContent = "";
        }
        clearErrorGutter();
    });

    /* ── Error gutter helpers ── */
    function clearErrorGutter() {
        errorGutter.innerHTML = "";
    }

    function highlightErrorLines(errors) {
        clearErrorGutter();
        const LINE_H = 0.85 * 1.6 * 16; // font-size 0.85rem * line-height 1.6 * 16px/rem
        const PADDING_TOP = 0.9 * 16;    // padding-top 0.9rem

        errors.forEach(err => {
            if (err.row === null || err.row === undefined) return;
            const row = err.row; // 1-indexed
            const top = PADDING_TOP + (row - 1) * LINE_H - codeTextArea.scrollTop;
            const div = document.createElement("div");
            div.className = "error-highlight-line";
            div.style.top  = `${top}px`;
            div.style.height = `${LINE_H}px`;
            div.title = `Line ${row}, Col ${err.col || 1}: ${err.raw}`;
            errorGutter.appendChild(div);
        });
    }

    /* ── Form submit ── */
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        // Loading UI
        btnText.textContent = "Compiling…";
        btnIcon.style.display = "none";
        spinner.style.display = "block";
        submitBtn.disabled = true;
        toast.className = "toast hidden";

        const formData = new FormData(form);

        try {
            const response = await fetch("/analyze", { method: "POST", body: formData });
            const data = await response.json();

            if (!response.ok) throw new Error(data.error || "An unknown server error occurred.");

            renderDashboard(data);

        } catch (err) {
            toast.textContent = `⚠️ ${err.message}`;
            toast.className = "toast";
        } finally {
            btnText.textContent = "Analyze & Compile";
            btnIcon.style.display = "";
            spinner.style.display = "none";
            submitBtn.disabled = false;
        }
    });

    /* ══════════════════════════════
       renderDashboard – main renderer
       ══════════════════════════════ */
    function renderDashboard(data) {
        placeholderPanel.classList.add("hidden");
        resultsPanel.classList.remove("hidden");
        errorFeed.innerHTML = "";
        successBanner.classList.add("hidden");

        // ── Time Complexity ──
        if (data.time_complexity) {
            const tc = data.time_complexity;
            tcNotation.textContent    = tc.notation    || "—";
            tcLabel.textContent       = tc.label       || "—";
            tcExplanation.textContent = tc.explanation || "—";
        }

        // ── SUCCESS path ──
        if (data.status === "success" || data.total_errors === 0) {
            badge.textContent = "✅ Compiled OK";
            badge.className   = "status-badge success";
            successBanner.classList.remove("hidden");

            // Profile
            if (data.developer_profile) {
                const prof = data.developer_profile;
                profSkill.textContent    = prof.estimated_developer_skill || "—";
                profTotal.textContent    = prof.total_errors_in_session   || 0;
                profDominant.textContent = prof.dominant_error_category   || "None";
            }
            profileCard.style.display = "";
            clearErrorGutter();
            return;
        }

        // ── ERROR path ──
        badge.textContent = `⚠ ${data.total_errors} Issue${data.total_errors !== 1 ? "s" : ""} Found`;
        badge.className   = "status-badge";
        successBanner.classList.add("hidden");

        // Profile
        if (data.developer_profile) {
            const prof = data.developer_profile;
            profSkill.textContent    = prof.estimated_developer_skill || "—";
            profTotal.textContent    = prof.total_errors_in_session   || 0;
            profDominant.textContent = prof.dominant_error_category   || "N/A";
        }
        profileCard.style.display = "";

        // ── Error section title ──
        const feedTitle = document.createElement("div");
        feedTitle.className = "error-feed-title";
        feedTitle.innerHTML = `
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            Detected Errors (${data.total_errors})
        `;
        errorFeed.appendChild(feedTitle);

        // ── Inject error cards ──
        data.errors.forEach((err, idx) => {
            const card = document.createElement("div");
            card.className = "error-card";
            card.setAttribute("data-severity", err.severity);
            card.style.animationDelay = `${idx * 0.07}s`;

            const ambiguousHtml = err.is_ambiguous
                ? `<span class="tag ambiguous">⚠️ Low Confidence</span>` : "";

            const locationHtml = (err.row !== null && err.row !== undefined)
                ? `<span class="error-location">
                       <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
                       Row&nbsp;${err.row},&nbsp;Col&nbsp;${err.col}
                   </span>`
                : "";

            const sevClass = `sev-${err.severity}`;

            card.innerHTML = `
                <div class="error-card-header">
                    <div class="error-meta-left">
                        <span class="error-class" style="color: var(--severity-${err.severity})">
                            ${err.predicted_class} ERROR
                        </span>
                        ${locationHtml}
                    </div>
                    <span class="error-confidence">Confidence: ${err.confidence}%</span>
                </div>
                <div class="error-raw">${escapeHtml(err.raw)}</div>
                <div class="tags">
                    ${err.cwe_id ? `<span class="tag cwe">${err.cwe_id}: ${err.cwe_name}</span>` : ""}
                    <span class="tag severity ${sevClass}">${err.severity}</span>
                    <span class="tag readability">Readability: ${err.readability_score}/10</span>
                    ${ambiguousHtml}
                </div>
            `;
            errorFeed.appendChild(card);
        });

        // ── Highlight error lines in editor ──
        highlightErrorLines(data.errors);
    }

    /* ── Utility ── */
    function escapeHtml(str) {
        return str
            .replace(/&/g,  "&amp;")
            .replace(/</g,  "&lt;")
            .replace(/>/g,  "&gt;")
            .replace(/"/g,  "&quot;");
    }
});

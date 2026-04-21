/* ════════════════════════════════════════════
   INTELLIGENT COMPILER SUITE  ·  app.js v10
   ════════════════════════════════════════════ */
document.addEventListener("DOMContentLoaded", () => {

    /* ── DOM ──────────────────────────────── */
    const fileInput       = document.getElementById("file-input");
    const fileNameDisplay = document.getElementById("file-name");
    const form            = document.getElementById("analyze-form");
    const submitBtn       = document.getElementById("submit-btn");
    const btnText         = document.getElementById("btn-text");
    const spinner         = document.getElementById("spinner");
    const btnIcon         = submitBtn.querySelector(".btn-icon");
    const toast           = document.getElementById("error-toast");

    const resultsPanel    = document.getElementById("results-panel");
    const placeholderPanel= document.getElementById("placeholder-panel");

    const badge           = document.getElementById("compiler-status");
    const successBanner   = document.getElementById("success-banner");

    // Time complexity
    const tcNotation      = document.getElementById("tc-notation");
    const tcLabel         = document.getElementById("tc-label");
    const tcExplanation   = document.getElementById("tc-explanation");

    // Green metrics
    const greenGrade      = document.getElementById("green-grade");
    const gcEnergy        = document.getElementById("gc-energy");
    const gcCarbon        = document.getElementById("gc-carbon");
    const gcOps           = document.getElementById("gc-ops");
    const gcScore         = document.getElementById("gc-score");
    const memWarning      = document.getElementById("memory-warning");
    const effFill         = document.getElementById("eff-bar-fill");
    const effLabel        = document.getElementById("eff-bar-label");
    const greenSuggs      = document.getElementById("green-suggestions");

    // Profile
    const profSkill       = document.getElementById("prof-skill");
    const profTotal       = document.getElementById("prof-total");
    const profDominant    = document.getElementById("prof-dominant");

    const errorFeed       = document.getElementById("error-feed");

    // Editor elements
    const codeTextArea    = document.getElementById("code-text");
    const lineNums        = document.getElementById("line-nums");
    const editorBody      = document.getElementById("editor-body");
    const editorInfo      = document.getElementById("editor-info");

    /* ════════════════════════════════════════
       EDITOR: Live line numbers (textarea mode)
       ════════════════════════════════════════ */
    function updateLineNumbers() {
        const count = codeTextArea.value.split("\n").length;
        lineNums.textContent = Array.from({length: count}, (_, i) => i + 1).join("\n");
        lineNums.scrollTop = codeTextArea.scrollTop;
    }
    codeTextArea.addEventListener("input",  updateLineNumbers);
    codeTextArea.addEventListener("scroll", () => { lineNums.scrollTop = codeTextArea.scrollTop; });
    updateLineNumbers();



    /* ════════════════════════════════════════
       FILE INPUT — read file into textarea
       ════════════════════════════════════════ */
    fileInput.addEventListener("change", async (e) => {
        if (e.target.files.length === 0) return;
        const file = e.target.files[0];
        fileNameDisplay.textContent = `📎 ${file.name}`;
        // Read file text and put in textarea (so highlighting works after analysis)
        const text = await file.text();
        codeTextArea.value = text;
        updateLineNumbers();
    });

    codeTextArea.addEventListener("input", () => {
        if (fileInput.value) {
            fileInput.value = "";
            fileNameDisplay.textContent = "";
        }
    });

    /* ════════════════════════════════════════
       FORM SUBMIT
       ════════════════════════════════════════ */
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        btnText.textContent   = "Compiling…";
        btnIcon.style.display = "none";
        spinner.classList.remove("hidden");
        submitBtn.disabled    = true;
        toast.className       = "toast hidden";

        // Build FormData — always send code_text (even if file was loaded)
        const fd = new FormData();
        const codeVal = codeTextArea.value.trim();
        // If a file is selected AND textarea is empty, send file; else send text
        if (fileInput.files.length > 0 && !codeVal) {
            fd.append("file", fileInput.files[0]);
        } else {
            fd.append("code_text", codeTextArea.value);
        }

        try {
            const res  = await fetch("/analyze", { method: "POST", body: fd });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || "Server error.");
            renderDashboard(data);
        } catch (err) {
            toast.textContent = `⚠️ ${err.message}`;
            toast.className   = "toast";
        } finally {
            btnText.textContent   = "Analyze & Compile";
            btnIcon.style.display = "";
            spinner.classList.add("hidden");
            submitBtn.disabled    = false;
        }
    });

    /* ════════════════════════════════════════
       RENDER DASHBOARD
       ════════════════════════════════════════ */
    function renderDashboard(data) {
        placeholderPanel.classList.add("hidden");
        resultsPanel.classList.remove("hidden");
        errorFeed.innerHTML = "";
        successBanner.classList.add("hidden");

        /* ── Time Complexity ── */
        if (data.time_complexity) {
            const tc = data.time_complexity;
            tcNotation.textContent    = tc.notation    || "—";
            tcLabel.textContent       = tc.label       || "—";
            tcExplanation.textContent = tc.explanation || "—";
        }

        /* ── Green Metrics ── */
        if (data.green_metrics) {
            const gm = data.green_metrics;
            greenGrade.textContent     = gm.grade          || "—";
            greenGrade.style.color     = gm.grade_color    || "#16a34a";
            gcEnergy.textContent       = gm.energy_display || "—";
            gcCarbon.textContent       = gm.carbon_display || "—";
            gcOps.textContent          = gm.estimated_ops  || "—";
            gcScore.textContent        = `${gm.efficiency_score || 0}%`;

            // Efficiency bar
            const pct = gm.efficiency_score || 0;
            effFill.style.width = `${pct}%`;
            effLabel.textContent = `${pct}% efficient`;

            // Color bar by grade
            const barColors = {
                "A+": "#059669", "A": "#10b981", "B": "#0ea5e9",
                "C": "#f59e0b", "D": "#f97316", "F": "#dc2626"
            };
            effFill.style.background = `linear-gradient(90deg, ${barColors[gm.grade] || "#10b981"}, ${barColors[gm.grade] || "#10b981"}99)`;
            effLabel.style.color     = barColors[gm.grade] || "#16a34a";

            // Memory warning
            if (gm.memory_leak_risk) {
                memWarning.classList.remove("hidden");
            } else {
                memWarning.classList.add("hidden");
            }

            // Suggestions
            greenSuggs.innerHTML = "";
            (gm.suggestions || []).forEach(s => {
                const el = document.createElement("div");
                el.className   = "suggestion-item";
                el.textContent = `💡 ${s}`;
                greenSuggs.appendChild(el);
            });
        }

        /* ── SUCCESS path ── */
        if (data.status === "success" || data.total_errors === 0) {
            badge.textContent = "✅ Compiled OK";
            badge.className   = "status-badge success";
            successBanner.classList.remove("hidden");

            if (data.developer_profile) {
                const p = data.developer_profile;
                profSkill.textContent    = p.estimated_developer_skill || "—";
                profTotal.textContent    = p.total_errors_in_session   || 0;
                profDominant.textContent = p.dominant_error_category   || "None";
            }

            return;
        }

        /* ── ERROR path ── */
        badge.textContent = `⚠ ${data.total_errors} Issue${data.total_errors !== 1 ? "s" : ""} Found`;
        badge.className   = "status-badge";

        if (data.developer_profile) {
            const p = data.developer_profile;
            profSkill.textContent    = p.estimated_developer_skill || "—";
            profTotal.textContent    = p.total_errors_in_session   || 0;
            profDominant.textContent = p.dominant_error_category   || "N/A";
        }



        /* ── Error cards ── */
        const feedTitle = document.createElement("div");
        feedTitle.className = "error-feed-title";
        feedTitle.innerHTML = `
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            Detected Errors (${data.total_errors})
        `;
        errorFeed.appendChild(feedTitle);

        data.errors.forEach((err, idx) => {
            const card = document.createElement("div");
            card.className = "error-card";
            card.setAttribute("data-severity", err.severity);
            card.style.animationDelay = `${idx * 0.07}s`;

            const locHtml = (err.row != null)
                ? `<span class="error-location">
                       <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
                       Row&nbsp;${err.row},&nbsp;Col&nbsp;${err.col}
                   </span>` : "";

            const ambHtml = err.is_ambiguous
                ? `<span class="tag ambiguous">⚠️ Low Confidence</span>` : "";

            card.innerHTML = `
                <div class="error-card-header">
                    <div class="error-meta-left">
                        <span class="error-class" style="color:var(--sev-${err.severity})">
                            ${err.predicted_class} ERROR
                        </span>
                        ${locHtml}
                    </div>
                    <span class="error-confidence">Confidence: ${err.confidence}%</span>
                </div>
                <div class="error-raw">${escapeHtml(err.raw)}</div>
                <div class="tags">
                    ${err.cwe_id ? `<span class="tag cwe">${err.cwe_id}: ${err.cwe_name}</span>` : ""}
                    <span class="tag sev-${err.severity}">${err.severity}</span>
                    <span class="tag readability">Readability: ${err.readability_score}/10</span>
                    ${ambHtml}
                </div>
            `;
            errorFeed.appendChild(card);
        });
    }

    /* ── Utility ── */
    function escapeHtml(s) {
        return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
    }
});

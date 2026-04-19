document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("file-input");
    const fileNameDisplay = document.getElementById("file-name");
    const form = document.getElementById("analyze-form");
    const submitBtn = document.getElementById("submit-btn");
    const btnText = submitBtn.querySelector("span");
    const spinner = document.getElementById("spinner");
    const toast = document.getElementById("error-toast");
    
    // Panels
    const resultsPanel = document.getElementById("results-panel");
    const placeholderPanel = document.getElementById("placeholder-panel");
    
    // Results DOM
    const badge = document.getElementById("compiler-status");
    const profSkill = document.getElementById("prof-skill");
    const profTotal = document.getElementById("prof-total");
    const profDominant = document.getElementById("prof-dominant");
    const errorFeed = document.getElementById("error-feed");

    fileInput.addEventListener("change", (e) => {
        if(e.target.files.length > 0) {
            fileNameDisplay.textContent = `Selected: ${e.target.files[0].name}`;
            document.getElementById("code-text").value = ""; // Clear text area if file picked
        }
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        // UI Loading State
        btnText.style.display = "none";
        spinner.style.display = "block";
        submitBtn.disabled = true;
        toast.className = "toast hidden";
        
        const formData = new FormData(form);

        try {
            const response = await fetch("/analyze", {
                method: "POST",
                body: formData
            });
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || "An unknown error occurred.");
            }
            
            renderDashboard(data);
            
        } catch (error) {
            toast.textContent = error.message;
            toast.className = "toast";
        } finally {
            btnText.style.display = "block";
            spinner.style.display = "none";
            submitBtn.disabled = false;
        }
    });
    
    function renderDashboard(data) {
        // Swap panels
        placeholderPanel.classList.add("hidden");
        resultsPanel.classList.remove("hidden");
        
        // Success state
        if (data.status === "success" || data.total_errors === 0) {
            badge.textContent = "Compilation Successful";
            badge.className = "status-badge success";
            errorFeed.innerHTML = `<div class="empty-state" style="padding: 2rem;"><h3>No Errors Detected</h3><p>Your code is perfectly safe.</p></div>`;
            return;
        }
        
        // Error state
        badge.textContent = `${data.total_errors} Issues Detected`;
        badge.className = "status-badge";
        
        // Profile mapping
        const prof = data.developer_profile;
        profSkill.textContent = prof.estimated_developer_skill;
        profTotal.textContent = prof.total_errors_in_session;
        profDominant.textContent = prof.dominant_error_category || "N/A";
        
        // Clear feed
        errorFeed.innerHTML = "";
        
        // Inject cards
        data.errors.forEach(err => {
            const card = document.createElement("div");
            card.className = "error-card";
            card.setAttribute("data-severity", err.severity);
            
            let ambiguousHtml = err.is_ambiguous ? `<span class="tag ambiguous">⚠️ Ambiguous Confidence</span>` : "";
            
            card.innerHTML = `
                <div class="error-card-header">
                    <span class="error-class" style="color: var(--severity-${err.severity.toLowerCase()})">
                        ${err.predicted_class} ERROR
                    </span>
                    <span style="font-size: 0.8rem; color: var(--text-muted)">Confidence: ${err.confidence}%</span>
                </div>
                <div class="error-raw">${escapeHtml(err.raw)}</div>
                <div class="tags">
                    ${err.cwe_id ? `<span class="tag cwe">${err.cwe_id}: ${err.cwe_name}</span>` : ""}
                    ${ambiguousHtml}
                    <span class="tag readability">Readability Score: ${err.readability_score}/10</span>
                </div>
            `;
            errorFeed.appendChild(card);
        });
    }
    
    function escapeHtml(unsafe) {
        return unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }
});

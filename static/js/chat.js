// Chat page: sends questions to /api/ask and renders the answer, its
// sources, and follow-up questions returned by the backend.
(function () {
    const log = document.getElementById("chat-log");
    const emptyState = document.getElementById("chat-empty");
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    const sendBtn = document.getElementById("chat-send-btn");
    const resetBtn = document.getElementById("new-conversation-btn");

    // Turns the plain-text answer from the LLM into simple HTML: blank
    // lines separate paragraphs, "### " starts a heading, "- " lines
    // become a bullet list, a lone "---" becomes a divider, and
    // "**bold**" within a line is rendered as emphasis. This matches the
    // formatting we ask the model to use in rag/prompts.py, plus the
    // markdown touches models tend to add on their own.
    function formatMythText(text) {
        const blocks = text.trim().split(/\n\s*\n/);
        return blocks.map(function (block) {
            const lines = block.split("\n").map(function (l) { return l.trim(); }).filter(Boolean);
            if (lines.length === 0) return "";

            if (lines.length === 1 && /^-{3,}$/.test(lines[0])) {
                return "<hr>";
            }

            if (lines[0].startsWith("### ")) {
                return "<h4>" + renderInline(lines[0].slice(4)) + "</h4>";
            }

            if (lines.every(function (l) { return l.startsWith("- "); })) {
                const items = lines.map(function (l) { return "<li>" + renderInline(l.slice(2)) + "</li>"; }).join("");
                return "<ul>" + items + "</ul>";
            }

            return "<p>" + lines.map(renderInline).join("<br>") + "</p>";
        }).join("");
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    // Escapes a line of text, then re-enables just "**bold**" markdown -
    // the one styling models consistently reach for even when the prompt
    // doesn't ask for it.
    function renderInline(line) {
        return escapeHtml(line).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    }

    function clearEmptyState() {
        if (emptyState) emptyState.remove();
    }

    function addUserMessage(text) {
        clearEmptyState();
        const el = document.createElement("div");
        el.className = "msg msg-user";
        el.innerHTML = '<div class="msg-bubble">' + escapeHtml(text) + "</div>";
        log.appendChild(el);
        log.scrollTop = log.scrollHeight;
    }

    function addTypingIndicator() {
        clearEmptyState();
        const el = document.createElement("div");
        el.className = "msg msg-ai";
        el.innerHTML = '<div class="msg-bubble typing-indicator">Consulting the sources...</div>';
        log.appendChild(el);
        log.scrollTop = log.scrollHeight;
        return el;
    }

    function renderAiMessage(container, data) {
        let html = '<div class="msg-bubble">' + formatMythText(data.answer);

        if (data.sources && data.sources.length > 0) {
            html += '<div class="sources-block"><h5>Sources</h5>';
            data.sources.forEach(function (s) {
                const label = s.section ? (s.source + " - " + s.section) : s.source;
                html += '<span class="source-chip">' + escapeHtml(label) + "</span>";
            });
            html += "</div>";
        }

        if (data.related_questions && data.related_questions.length > 0) {
            html += '<div class="related-block"><h5>You may also ask</h5>';
            data.related_questions.forEach(function (q) {
                html += '<button class="related-question" data-question="' + escapeHtml(q) + '">&rarr; ' + escapeHtml(q) + "</button>";
            });
            html += "</div>";
        }

        html += "</div>";
        container.innerHTML = html;

        container.querySelectorAll(".related-question").forEach(function (btn) {
            btn.addEventListener("click", function () {
                sendQuestion(btn.getAttribute("data-question"));
            });
        });

        log.scrollTop = log.scrollHeight;
    }

    function renderAiError(container, message) {
        container.innerHTML = '<div class="msg-bubble error-state">' + escapeHtml(message) + "</div>";
    }

    async function sendQuestion(question) {
        question = question.trim();
        if (!question) return;

        addUserMessage(question);
        input.value = "";
        sendBtn.disabled = true;
        const placeholder = addTypingIndicator();

        try {
            const response = await fetch("/api/ask", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: question }),
            });
            const data = await response.json();

            if (!response.ok) {
                renderAiError(placeholder, data.error || "Something went wrong.");
            } else {
                renderAiMessage(placeholder, data);
            }
        } catch (err) {
            renderAiError(placeholder, "Could not reach the server. Is Flask running?");
        } finally {
            sendBtn.disabled = false;
            input.focus();
        }
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        sendQuestion(input.value);
    });

    if (resetBtn) {
        resetBtn.addEventListener("click", async function () {
            await fetch("/api/reset", { method: "POST" });
            log.innerHTML = '<div class="empty-state" id="chat-empty">Ask a question to begin - e.g. "Who was Karna?"</div>';
        });
    }

    // If we arrived from the homepage with ?q=..., send that question right away.
    const params = new URLSearchParams(window.location.search);
    const initialQuestion = params.get("q");
    if (initialQuestion) {
        sendQuestion(initialQuestion);
        window.history.replaceState({}, "", "/chat");
    }
})();

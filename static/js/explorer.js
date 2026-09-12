// Shared logic for the Characters, Stories, Timeline, and Sources pages.
// Each page calls exactly one of the init* functions below after the DOM
// for that page has loaded.
const MythologyExplorer = (function () {

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

    // Same lightweight text formatter used by chat.js, for character profiles.
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

    function tagRow(values) {
        if (!values || values.length === 0) return "";
        return '<div class="tag-row">' + values.map(function (v) {
            return '<span class="tag">' + escapeHtml(v) + "</span>";
        }).join("") + "</div>";
    }

    async function fetchJson(url) {
        const response = await fetch(url);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Request failed.");
        return data;
    }

    // ---------------------------------------------------------------
    // Characters list
    // ---------------------------------------------------------------
    function initCharacterList() {
        const grid = document.getElementById("character-grid");
        const search = document.getElementById("character-search");
        let allNames = [];

        function render(names) {
            if (names.length === 0) {
                grid.innerHTML = '<div class="empty-state">No characters match your search.</div>';
                return;
            }
            grid.innerHTML = names.map(function (name) {
                return '<a class="card" href="/characters/' + encodeURIComponent(name) + '"><h3>' + escapeHtml(name) + "</h3></a>";
            }).join("");
        }

        fetchJson("/api/characters").then(function (data) {
            allNames = data.characters || [];
            if (allNames.length === 0) {
                grid.innerHTML = '<div class="empty-state">No characters indexed yet. Run the ingestion script to build the knowledge base.</div>';
                return;
            }
            render(allNames);
        }).catch(function () {
            grid.innerHTML = '<div class="error-state">Could not load characters. Is the knowledge base built?</div>';
        });

        search.addEventListener("input", function () {
            const q = search.value.trim().toLowerCase();
            render(allNames.filter(function (n) { return n.toLowerCase().includes(q); }));
        });
    }

    // ---------------------------------------------------------------
    // Single character detail
    // ---------------------------------------------------------------
    function initCharacterDetail(name) {
        const container = document.getElementById("character-content");

        fetchJson("/api/character/" + encodeURIComponent(name)).then(function (data) {
            let html = '<div class="panel profile-section">' + formatMythText(data.profile) + "</div>";

            if (data.sources && data.sources.length > 0) {
                html += '<div class="sources-block"><h5>Sources</h5>';
                data.sources.forEach(function (s) {
                    const label = s.section ? (s.source + " - " + s.section) : s.source;
                    html += '<span class="source-chip">' + escapeHtml(label) + "</span>";
                });
                html += "</div>";
            }

            if (data.related_characters && data.related_characters.length > 0) {
                html += '<div class="profile-section"><h4>Related Characters</h4><div class="related-chips">';
                data.related_characters.forEach(function (rel) {
                    html += '<a class="related-chip" href="/characters/' + encodeURIComponent(rel) + '">' + escapeHtml(rel) + "</a>";
                });
                html += "</div></div>";
            }

            container.innerHTML = html;
        }).catch(function (err) {
            container.innerHTML = '<div class="error-state">' + escapeHtml(err.message) + "</div>";
        });
    }

    // ---------------------------------------------------------------
    // Stories
    // ---------------------------------------------------------------
    function initStories() {
        const list = document.getElementById("story-list");

        fetchJson("/api/stories").then(function (data) {
            const stories = data.stories || [];
            list.innerHTML = stories.map(function (story) {
                const status = story.chunks_indexed > 0
                    ? story.chunks_indexed + " chunks indexed"
                    : "No documents indexed yet";
                return '<div class="panel story-card">' +
                    "<h3>" + escapeHtml(story.source) + "</h3>" +
                    "<p>" + escapeHtml(story.description) + "</p>" +
                    '<span class="tag">' + status + "</span>" +
                    tagRow(story.characters) +
                    "</div>";
            }).join("");
        }).catch(function () {
            list.innerHTML = '<div class="error-state">Could not load stories. Is the knowledge base built?</div>';
        });
    }

    // ---------------------------------------------------------------
    // Timeline
    // ---------------------------------------------------------------
    function initTimeline() {
        const tabsEl = document.getElementById("timeline-tabs");
        const trackEl = document.getElementById("timeline-track");

        fetchJson("/api/timeline").then(function (data) {
            const epics = Object.keys(data);
            if (epics.length === 0) {
                trackEl.innerHTML = '<div class="empty-state">No timeline data available.</div>';
                return;
            }

            function renderEpic(epic) {
                trackEl.innerHTML = data[epic].map(function (step, i) {
                    return '<div class="timeline-node">' +
                        '<div class="step-label">Step ' + (i + 1) + "</div>" +
                        '<div class="step-title">' + escapeHtml(step) + "</div>" +
                        "</div>";
                }).join("");
            }

            tabsEl.innerHTML = epics.map(function (epic, i) {
                return '<button class="timeline-tab' + (i === 0 ? " active" : "") + '" data-epic="' + escapeHtml(epic) + '">' + escapeHtml(epic) + "</button>";
            }).join("");

            tabsEl.querySelectorAll(".timeline-tab").forEach(function (tab) {
                tab.addEventListener("click", function () {
                    tabsEl.querySelectorAll(".timeline-tab").forEach(function (t) { t.classList.remove("active"); });
                    tab.classList.add("active");
                    renderEpic(tab.getAttribute("data-epic"));
                });
            });

            renderEpic(epics[0]);
        }).catch(function () {
            trackEl.innerHTML = '<div class="error-state">Could not load the timeline.</div>';
        });
    }

    // ---------------------------------------------------------------
    // Sources
    // ---------------------------------------------------------------
    function initSources() {
        const list = document.getElementById("sources-list");

        fetchJson("/api/sources").then(function (data) {
            const sources = data.sources || {};
            const names = Object.keys(sources);
            if (names.length === 0) {
                list.innerHTML = '<div class="empty-state">The knowledge base is empty. Run the ingestion script to index documents.</div>';
                return;
            }

            list.innerHTML = names.map(function (name) {
                const s = sources[name];
                return '<div class="panel story-card">' +
                    "<h3>" + escapeHtml(name) + "</h3>" +
                    '<span class="tag">' + s.chunks + " chunks</span>" +
                    '<div class="source-detail">' +
                    "<strong>Sections:</strong>" + tagRow(s.sections) +
                    "</div>" +
                    '<div class="source-detail">' +
                    "<strong>Characters:</strong>" + tagRow(s.characters) +
                    "</div>" +
                    "</div>";
            }).join("");
        }).catch(function () {
            list.innerHTML = '<div class="error-state">Could not load sources.</div>';
        });
    }

    return {
        initCharacterList: initCharacterList,
        initCharacterDetail: initCharacterDetail,
        initStories: initStories,
        initTimeline: initTimeline,
        initSources: initSources,
    };
})();

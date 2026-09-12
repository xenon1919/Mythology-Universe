// Homepage behaviour: example question chips and the hero search box both
// just hand the question off to the chat page via a query string.
(function () {
    function goToChat(question) {
        const trimmed = question.trim();
        if (!trimmed) return;
        window.location.href = "/chat?q=" + encodeURIComponent(trimmed);
    }

    const form = document.getElementById("hero-search-form");
    const input = document.getElementById("hero-search-input");
    if (form) {
        form.addEventListener("submit", function (event) {
            event.preventDefault();
            goToChat(input.value);
        });
    }

    document.querySelectorAll(".example-chip").forEach(function (chip) {
        chip.addEventListener("click", function () {
            goToChat(chip.textContent);
        });
    });
})();

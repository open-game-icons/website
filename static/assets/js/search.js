(() => {
  var input = document.getElementById("icon-search");
  if (!input) return;
  input.removeAttribute("hidden");

  var lookup = null;
  fetch("/search-index.json")
    .then((r) => r.json())
    .then((data) => {
      lookup = data;
    })
    .catch(() => {});

  var prevQuery = "";

  input.addEventListener("input", () => {
    var raw = input.value.trim().toLowerCase();
    if (raw === prevQuery) return;
    prevQuery = raw;

    if (!lookup) return;

    var words = raw ? raw.split(/\s+/) : [];
    var links = document.querySelectorAll(".icon-grid > a");

    for (let i = 0; i < links.length; i++) {
      const el = links[i];
      const k = lookup[el.id];
      if (!k) continue;
      const show = !raw || words.every((w) => k.some((kw) => kw.indexOf(w) !== -1));
      el.hidden = !show;
    }

    var tags = document.querySelectorAll(".tags .tag");
    for (let j = 0; j < tags.length; j++) {
      const tag = tags[j];
      const text = (tag.textContent || "").toLowerCase();
      tag.hidden = raw && text.indexOf(raw) === -1;
    }
  });
})();

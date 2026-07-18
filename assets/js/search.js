(function () {
	var input = document.getElementById("icon-search");
	if (!input) return;

	var lookup = null;
	fetch("/search-index.json")
		.then(function (r) {
			return r.json();
		})
		.then(function (data) {
			lookup = data;
		})
		.catch(function () {});

	var prevQuery = "";

	input.addEventListener("input", function () {
		var raw = input.value.trim().toLowerCase();
		if (raw === prevQuery) return;
		prevQuery = raw;

		if (!lookup) return;

		var words = raw ? raw.split(/\s+/) : [];
		var links = document.querySelectorAll(".icon-grid > a");

		for (var i = 0; i < links.length; i++) {
			var el = links[i];
			var k = lookup[el.id];
			if (!k) continue;
			var show =
				!raw ||
				words.every(function (w) {
					return k.indexOf(w) !== -1;
				});
			el.hidden = !show;
		}
	});
})();

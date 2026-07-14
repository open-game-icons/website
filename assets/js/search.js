(function () {
	var input = document.getElementById("icon-search");
	if (!input) return;

	var prevQuery = "";

	input.addEventListener("input", function () {
		var raw = input.value.trim().toLowerCase();
		if (raw === prevQuery) return;
		prevQuery = raw;

		var words = raw ? raw.split(/\s+/) : [];

		SEARCH_INDEX.forEach(function (icon) {
			var el = document.getElementById("icon--" + icon.a + "--" + icon.i);
			if (!el) return;

			var show = !raw || words.every(function (w) { return icon.k.indexOf(w) !== -1; });
			el.classList.toggle("icon-grid__item--hidden", !show);
		});
	});
})();

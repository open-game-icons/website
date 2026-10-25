(() => {
  const button = document.getElementById("png-download");
  const sizeInput = document.getElementById("png-size");
  const controls = document.getElementById("png-download-controls");
  const status = document.getElementById("png-status");
  if (!button || !sizeInput || !controls) return;

  // Cap the size so large renders stay under the canvas memory limits mobile
  // browsers enforce; 2048 is 4x the native 512px artwork.
  const DEFAULT_SIZE = 512;
  const MIN_SIZE = 16;
  const MAX_SIZE = 2048;

  controls.removeAttribute("hidden");

  let svgRequest = null;

  function getSvgText() {
    if (!svgRequest) {
      svgRequest = fetch(button.dataset.svgUrl).then((response) => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.text();
      });
      // Let a later click retry after a transient network failure.
      svgRequest.catch(() => {
        svgRequest = null;
      });
    }
    return svgRequest;
  }

  // The source SVGs only have a viewBox, so their intrinsic size is undefined.
  // Writing an explicit width/height makes rasterization consistent across
  // browsers, which otherwise fall back to a 150px default object size.
  function sizeSvg(text, width, height) {
    return text.replace(/<svg\b[^>]*>/, (tag) => {
      const attrs = tag.replace(
        /\s(?:width|height)\s*=\s*(?:"[^"]*"|'[^']*')/g,
        "",
      );
      return attrs.replace(
        /^<svg/,
        `<svg width="${width}" height="${height}"`,
      );
    });
  }

  function loadImage(url) {
    return new Promise((resolve, reject) => {
      const image = new Image();
      image.onload = () => resolve(image);
      image.onerror = () => reject(new Error("could not load SVG"));
      image.src = url;
    });
  }

  async function rasterize(svgText, width, height) {
    const svgUrl = URL.createObjectURL(
      new Blob([svgText], { type: "image/svg+xml" }),
    );
    try {
      const image = await loadImage(svgUrl);
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      canvas.getContext("2d").drawImage(image, 0, 0, width, height);
      return await new Promise((resolve, reject) => {
        canvas.toBlob((png) => {
          if (png) resolve(png);
          else reject(new Error("PNG encoding failed"));
        }, "image/png");
      });
    } finally {
      URL.revokeObjectURL(svgUrl);
    }
  }

  function saveBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    // Keep the blob alive briefly so the browser can start the download.
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function setStatus(message) {
    if (!status) return;
    status.textContent = message;
    status.hidden = message === "";
  }

  // Empty, non-numeric, and out-of-range values are normalized, and the input
  // is updated so it shows the size that will actually be rendered.
  function readSize() {
    const raw = sizeInput.value.trim();
    const parsed = raw === "" ? Number.NaN : Number(raw);
    const rounded = Number.isFinite(parsed) ? Math.round(parsed) : DEFAULT_SIZE;
    const size = Math.min(MAX_SIZE, Math.max(MIN_SIZE, rounded));
    sizeInput.value = String(size);
    return size;
  }

  button.addEventListener("click", async () => {
    const size = readSize();
    button.disabled = true;
    setStatus("");
    try {
      const svgText = await getSvgText();
      const viewBox = svgText.match(
        /viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([-\d.]+)[\s,]+([-\d.]+)\s*"/,
      );
      const aspect = viewBox ? Number(viewBox[2]) / Number(viewBox[1]) : 1;
      const height = Math.max(1, Math.round(size * aspect));
      const png = await rasterize(sizeSvg(svgText, size, height), size, height);
      saveBlob(png, `${button.dataset.iconId}-${size}.png`);
    } catch (error) {
      console.error(error);
      setStatus("Sorry, the PNG could not be generated.");
    } finally {
      button.disabled = false;
    }
  });

  sizeInput.addEventListener("change", readSize);
  sizeInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      button.click();
    }
  });
})();

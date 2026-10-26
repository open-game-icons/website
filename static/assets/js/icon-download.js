(() => {
  const container = document.getElementById("downloads");
  const svgLink = document.getElementById("svg-download");
  const pngButton = document.getElementById("png-download");
  const pngControls = document.getElementById("png-download-controls");
  const sizeInput = document.getElementById("png-size");
  const metadataOption = document.getElementById("metadata-option");
  const metadataCheckbox = document.getElementById("include-metadata");
  const status = document.getElementById("download-status");
  if (!container || !svgLink || !pngButton || !pngControls || !sizeInput) {
    return;
  }

  // Cap the size so large renders stay under the canvas memory limits mobile
  // browsers enforce; 2048 is 4x the native 512px artwork.
  const DEFAULT_SIZE = 512;
  const MIN_SIZE = 16;
  const MAX_SIZE = 2048;
  const SOFTWARE = "Open Game Icons";

  const icon = {
    title: container.dataset.iconTitle || "",
    id: container.dataset.iconId || "icon",
    fileBase: container.dataset.fileBase || "",
    author: container.dataset.author || "",
    licenseName: container.dataset.licenseName || "",
    licenseUrl: container.dataset.licenseUrl || "",
    sourceUrl: container.dataset.sourceUrl || "",
    attribution: container.dataset.attribution || "",
  };

  pngControls.removeAttribute("hidden");
  if (metadataOption) metadataOption.removeAttribute("hidden");

  function includeMetadata() {
    return !metadataCheckbox || metadataCheckbox.checked;
  }

  let svgRequest = null;

  function getSvgText() {
    if (!svgRequest) {
      svgRequest = fetch(svgLink.href).then((response) => {
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

  function escapeXml(value) {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "\"": "&quot;",
      "'": "&apos;",
    };
    return String(value).replace(/[&<>"']/g, (c) => entities[c]);
  }

  // --- PNG metadata ---

  const CRC_TABLE = (() => {
    const table = new Uint32Array(256);
    for (let n = 0; n < 256; n++) {
      let crc = n;
      for (let k = 0; k < 8; k++) {
        crc = crc & 1 ? 0xedb88320 ^ (crc >>> 1) : crc >>> 1;
      }
      table[n] = crc >>> 0;
    }
    return table;
  })();

  function crc32(bytes) {
    let crc = 0xffffffff;
    for (let i = 0; i < bytes.length; i++) {
      crc = CRC_TABLE[(crc ^ bytes[i]) & 0xff] ^ (crc >>> 8);
    }
    return (crc ^ 0xffffffff) >>> 0;
  }

  function concatBytes(parts) {
    const total = parts.reduce((length, part) => length + part.length, 0);
    const out = new Uint8Array(total);
    let offset = 0;
    for (const part of parts) {
      out.set(part, offset);
      offset += part.length;
    }
    return out;
  }

  function pngChunk(type, data) {
    const out = new Uint8Array(12 + data.length);
    const view = new DataView(out.buffer);
    view.setUint32(0, data.length);
    for (let i = 0; i < 4; i++) out[4 + i] = type.charCodeAt(i);
    out.set(data, 8);
    view.setUint32(8 + data.length, crc32(out.subarray(4, 8 + data.length)));
    return out;
  }

  // iTXt: keyword\0 compressionFlag(0) compressionMethod(0) lang\0 translated\0
  // text (UTF-8). Uncompressed, which is what the XMP spec requires anyway.
  function itxtChunk(keyword, text) {
    const encoder = new TextEncoder();
    return pngChunk(
      "iTXt",
      concatBytes([
        encoder.encode(keyword),
        new Uint8Array(5),
        encoder.encode(text),
      ]),
    );
  }

  // tEXt is Latin-1 only, so anything else falls back to iTXt.
  function textChunk(keyword, value) {
    if (!/^[\x20-\x7e]*$/.test(value)) return itxtChunk(keyword, value);
    const bytes = new Uint8Array(keyword.length + 1 + value.length);
    for (let i = 0; i < keyword.length; i++) {
      bytes[i] = keyword.charCodeAt(i);
    }
    for (let i = 0; i < value.length; i++) {
      bytes[keyword.length + 1 + i] = value.charCodeAt(i);
    }
    return pngChunk("tEXt", bytes);
  }

  function xmpPacket(meta) {
    return `<?xpacket begin="\uFEFF" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:cc="http://creativecommons.org/ns#"
    xmlns:xmpRights="http://ns.adobe.com/xap/1.0/rights/"
    xmlns:xmp="http://ns.adobe.com/xap/1.0/">
   <dc:title><rdf:Alt><rdf:li xml:lang="x-default">${escapeXml(meta.title)}</rdf:li></rdf:Alt></dc:title>
   <dc:creator><rdf:Seq><rdf:li>${escapeXml(meta.author)}</rdf:li></rdf:Seq></dc:creator>
   <dc:description><rdf:Alt><rdf:li xml:lang="x-default">${
      escapeXml(meta.attribution)
    }</rdf:li></rdf:Alt></dc:description>
   <dc:rights><rdf:Alt><rdf:li xml:lang="x-default">${escapeXml(meta.licenseName)}</rdf:li></rdf:Alt></dc:rights>
   <dc:source rdf:resource="${escapeXml(meta.sourceUrl)}"/>
   <cc:license rdf:resource="${escapeXml(meta.licenseUrl)}"/>
   <cc:attributionName>${escapeXml(meta.author)}</cc:attributionName>
   <cc:attributionURL rdf:resource="${escapeXml(meta.sourceUrl)}"/>
   <xmpRights:WebStatement rdf:resource="${escapeXml(meta.licenseUrl)}"/>
   <xmp:CreatorTool>${escapeXml(SOFTWARE)}</xmp:CreatorTool>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>`;
  }

  // Text and XMP chunks are ancillary, so they go between IHDR and IDAT, which
  // is read by the widest range of tools.
  function withPngMetadata(pngBytes, meta) {
    const view = new DataView(
      pngBytes.buffer,
      pngBytes.byteOffset,
      pngBytes.byteLength,
    );
    const insertAt = 8 + 12 + view.getUint32(8);
    const chunks = [
      textChunk("Title", meta.title),
      textChunk("Author", meta.author),
      textChunk("Copyright", meta.attribution),
      textChunk("Source", meta.sourceUrl),
      textChunk("Software", SOFTWARE),
      itxtChunk("XML:com.adobe.xmp", xmpPacket(meta)),
    ];
    return new Blob(
      [pngBytes.subarray(0, insertAt), ...chunks, pngBytes.subarray(insertAt)],
      { type: "image/png" },
    );
  }

  // --- SVG metadata ---

  function withSvgMetadata(svgText, meta) {
    const block = `<title>${escapeXml(meta.title)}</title>`
      + `<desc>${escapeXml(meta.attribution)}</desc>`
      + "<metadata>"
      + "<rdf:RDF xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\""
      + " xmlns:dc=\"http://purl.org/dc/elements/1.1/\""
      + " xmlns:cc=\"http://creativecommons.org/ns#\">"
      + "<cc:Work rdf:about=\"\">"
      + "<dc:format>image/svg+xml</dc:format>"
      + "<dc:type rdf:resource=\"http://purl.org/dc/dcmitype/StillImage\"/>"
      + `<dc:title>${escapeXml(meta.title)}</dc:title>`
      + `<dc:creator><cc:Agent><dc:title>${escapeXml(meta.author)}</dc:title></cc:Agent></dc:creator>`
      + `<dc:rights><cc:Agent><dc:title>${escapeXml(meta.licenseName)}</dc:title></cc:Agent></dc:rights>`
      + `<cc:license rdf:resource="${escapeXml(meta.licenseUrl)}"/>`
      + `<dc:source rdf:resource="${escapeXml(meta.sourceUrl)}"/>`
      + `<dc:description>${escapeXml(meta.attribution)}</dc:description>`
      + "</cc:Work></rdf:RDF></metadata>";
    return svgText.replace(/<svg\b[^>]*>/, (tag) => tag + block);
  }

  // --- Rasterization and saving ---

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

  function saveUrl(href, filename) {
    const link = document.createElement("a");
    link.href = href;
    if (filename) link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
  }

  function saveBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    saveUrl(url, filename);
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

  // --- Handlers ---

  pngButton.addEventListener("click", async () => {
    const size = readSize();
    pngButton.disabled = true;
    setStatus("");
    try {
      const svgText = await getSvgText();
      const viewBox = svgText.match(
        /viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([-\d.]+)[\s,]+([-\d.]+)\s*"/,
      );
      const aspect = viewBox ? Number(viewBox[2]) / Number(viewBox[1]) : 1;
      const height = Math.max(1, Math.round(size * aspect));
      let png = await rasterize(sizeSvg(svgText, size, height), size, height);
      if (includeMetadata()) {
        png = withPngMetadata(new Uint8Array(await png.arrayBuffer()), icon);
      }
      saveBlob(png, `${icon.fileBase || icon.id}-${size}.png`);
    } catch (error) {
      console.error(error);
      setStatus("Sorry, the PNG could not be generated.");
    } finally {
      pngButton.disabled = false;
    }
  });

  // With metadata disabled (or without JS), the anchor's own download is used,
  // so the saved file is the untouched SVG.
  svgLink.addEventListener("click", async (event) => {
    if (
      !includeMetadata()
      || event.button !== 0
      || event.metaKey
      || event.ctrlKey
      || event.shiftKey
      || event.altKey
    ) {
      return;
    }
    event.preventDefault();
    setStatus("");
    try {
      const svgText = await getSvgText();
      const svg = withSvgMetadata(svgText, icon);
      saveBlob(
        new Blob([svg], { type: "image/svg+xml" }),
        svgLink.getAttribute("download") || `${icon.id}.svg`,
      );
    } catch (error) {
      console.error(error);
      setStatus(
        "Sorry, the SVG could not be annotated. Downloading the original file.",
      );
      saveUrl(svgLink.href, svgLink.getAttribute("download"));
    }
  });

  sizeInput.addEventListener("change", readSize);
  sizeInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      pngButton.click();
    }
  });
})();

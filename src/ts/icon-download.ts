function main(): void {
  function byId<T extends HTMLElement>(
    id: string,
    constructor: { new(): T },
  ): T | null {
    const element = document.getElementById(id);
    return element instanceof constructor ? element : null;
  }

  const container = byId("downloads", HTMLElement);
  const svgLink = byId("svg-download", HTMLAnchorElement);
  const pngButton = byId("png-download", HTMLButtonElement);
  const pngControls = byId("png-download-controls", HTMLElement);
  const downloadSizeControls = byId("download-size-controls", HTMLElement);
  const sizeInput = byId("download-size", HTMLInputElement);
  const metadataOption = byId("metadata-option", HTMLElement);
  const metadataCheckbox = byId("include-metadata", HTMLInputElement);
  const status = byId("download-status", HTMLElement);
  const preview = byId("icon-preview", HTMLImageElement);
  const recolorControls = byId("recolor-controls", HTMLElement);
  const foregroundColor = byId("foreground-color", HTMLInputElement);
  const foregroundAlpha = byId("foreground-alpha", HTMLInputElement);
  const foregroundAlphaNumber = byId(
    "foreground-alpha-number",
    HTMLInputElement,
  );
  const backgroundColor = byId("background-color", HTMLInputElement);
  const backgroundAlpha = byId("background-alpha", HTMLInputElement);
  const backgroundAlphaNumber = byId(
    "background-alpha-number",
    HTMLInputElement,
  );
  const resetButton = byId("reset-settings", HTMLButtonElement);
  if (!container || !svgLink || !pngButton || !pngControls || !sizeInput) {
    return;
  }

  // These are used inside event handlers, where TypeScript does not retain the
  // narrowing from the guard above. Keep non-nullable aliases for closures.
  const svgDownloadLink: HTMLAnchorElement = svgLink;
  const pngDownloadButton: HTMLButtonElement = pngButton;
  const downloadSizeInput: HTMLInputElement = sizeInput;

  type RecolorElements = {
    preview: HTMLImageElement;
    recolorControls: HTMLElement;
    foregroundColor: HTMLInputElement;
    foregroundAlpha: HTMLInputElement;
    foregroundAlphaNumber: HTMLInputElement;
    backgroundColor: HTMLInputElement;
    backgroundAlpha: HTMLInputElement;
    backgroundAlphaNumber: HTMLInputElement;
  };

  function findRecolorElements(): RecolorElements | null {
    if (
      !preview
      || !recolorControls
      || !foregroundColor
      || !foregroundAlpha
      || !foregroundAlphaNumber
      || !backgroundColor
      || !backgroundAlpha
      || !backgroundAlphaNumber
    ) {
      return null;
    }
    return {
      preview,
      recolorControls,
      foregroundColor,
      foregroundAlpha,
      foregroundAlphaNumber,
      backgroundColor,
      backgroundAlpha,
      backgroundAlphaNumber,
    };
  }

  const recolor = findRecolorElements();

  // Cap the size so large PNG renders stay under the canvas memory limits mobile
  // browsers enforce; 2048 is 4x the native 512px artwork.
  const DEFAULT_SIZE = 512;
  const MIN_SIZE = 16;
  const MAX_SIZE = 2048;
  const ALPHA_MAX = 255;
  const SOFTWARE = "Open Game Icons";
  const DEFAULT_FOREGROUND = "#ffffff";
  const DEFAULT_BACKGROUND = "#000000";
  const originalPreviewSrc = preview
    ? (preview.getAttribute("src") ?? "")
    : "";

  type IconMetadata = {
    title: string;
    id: string;
    fileBase: string;
    author: string;
    licenseName: string;
    licenseUrl: string;
    sourceUrl: string;
    attribution: string;
  };

  const icon: IconMetadata = {
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
  if (downloadSizeControls) downloadSizeControls.removeAttribute("hidden");
  if (metadataOption) metadataOption.removeAttribute("hidden");
  if (recolor) recolor.recolorControls.removeAttribute("hidden");
  if (resetButton) resetButton.removeAttribute("hidden");

  function includeMetadata(): boolean {
    return !metadataCheckbox || metadataCheckbox.checked;
  }

  // --- Recoloring ---

  type Color = {
    hex: string;
    alpha: number;
  };

  type Colors = {
    foreground: Color;
    background: Color;
  };

  function readColors(): Colors {
    if (!recolor) {
      return {
        foreground: { hex: DEFAULT_FOREGROUND, alpha: 1 },
        background: { hex: DEFAULT_BACKGROUND, alpha: 1 },
      };
    }
    return {
      foreground: {
        hex: recolor.foregroundColor.value.toLowerCase(),
        alpha: alphaFraction(recolor.foregroundAlphaNumber.value),
      },
      background: {
        hex: recolor.backgroundColor.value.toLowerCase(),
        alpha: alphaFraction(recolor.backgroundAlphaNumber.value),
      },
    };
  }

  // Three decimals keep every 0-255 value distinct while staying readable in the
  // generated fill-opacity attributes.
  function alphaFraction(value: string): number {
    return Math.round((Number(value) / ALPHA_MAX) * 1000) / 1000;
  }

  function hasCustomColors(): boolean {
    if (!recolor) return false;
    return (
      recolor.foregroundColor.value.toLowerCase() !== DEFAULT_FOREGROUND
      || recolor.backgroundColor.value.toLowerCase() !== DEFAULT_BACKGROUND
      || Number(recolor.foregroundAlphaNumber.value) !== ALPHA_MAX
      || Number(recolor.backgroundAlphaNumber.value) !== ALPHA_MAX
    );
  }

  // Every published icon follows the same structure: a full-bleed background
  // shape first, then a white foreground path. (Badges add a stroked ring,
  // which is treated as foreground outline over an unfilled interior.)
  const PAINTED_ELEMENTS = new Set([
    "circle",
    "ellipse",
    "line",
    "path",
    "polygon",
    "polyline",
    "rect",
  ]);

  function applyPaint(
    element: Element,
    attribute: "fill" | "stroke",
    color: Color,
  ): void {
    element.setAttribute(attribute, color.hex);
    const opacity = `${attribute}-opacity`;
    if (color.alpha < 1) {
      element.setAttribute(opacity, String(color.alpha));
    } else {
      element.removeAttribute(opacity);
    }
  }

  function recolorSvg(svgText: string, colors: Colors): string {
    const doc = new DOMParser().parseFromString(svgText, "image/svg+xml");
    const root = doc.documentElement;
    if (!root || root.localName !== "svg") return svgText;

    const shapes = Array.from(root.children).filter((element) => PAINTED_ELEMENTS.has(element.localName));
    if (shapes.length === 0) return svgText;

    shapes.forEach((shape, index) => {
      if (index === 0) {
        applyPaint(shape, "fill", colors.background);
        return;
      }
      if (shape.hasAttribute("stroke")) {
        applyPaint(shape, "stroke", colors.foreground);
        if (shape.hasAttribute("fill")) {
          applyPaint(shape, "fill", colors.foreground);
        } else {
          // An implicit fill would match the background and double up opacity.
          shape.setAttribute("fill", "none");
        }
        return;
      }
      applyPaint(shape, "fill", colors.foreground);
    });

    return new XMLSerializer().serializeToString(root);
  }

  // Returns false when the number input is empty or not yet a usable value, so
  // the caller can skip a preview update until it becomes valid.
  function applyAlphaNumber(
    range: HTMLInputElement,
    number: HTMLInputElement,
  ): boolean {
    const raw = number.value.trim();
    if (raw === "") return false;
    const parsed = Number(raw);
    if (!Number.isFinite(parsed)) return false;
    const value = Math.min(ALPHA_MAX, Math.max(0, Math.round(parsed)));
    range.value = String(value);
    if (raw !== String(value)) number.value = String(value);
    return true;
  }

  function normalizeAlphaNumber(
    range: HTMLInputElement,
    number: HTMLInputElement,
  ): void {
    if (!applyAlphaNumber(range, number)) number.value = range.value;
  }

  async function updatePreview(): Promise<void> {
    if (!recolor) return;
    const previewElement = recolor.preview;
    if (!hasCustomColors()) {
      if (previewElement.getAttribute("src") !== originalPreviewSrc) {
        previewElement.src = originalPreviewSrc;
      }
      return;
    }
    try {
      const svgText = await getSvgText();
      // A reset may have happened while the SVG was loading.
      if (!hasCustomColors()) {
        previewElement.src = originalPreviewSrc;
        return;
      }
      const svg = recolorSvg(svgText, readColors());
      // A data URL avoids tracking and revoking blob URLs on every input event.
      previewElement.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
    } catch (error) {
      console.error(error);
    }
  }

  let svgRequest: Promise<string> | null = null;

  function getSvgText(): Promise<string> {
    if (svgRequest) return svgRequest;
    const request = fetch(svgDownloadLink.href).then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.text();
    });
    // Let a later click retry after a transient network failure.
    request.catch(() => {
      svgRequest = null;
    });
    svgRequest = request;
    return request;
  }

  function escapeXml(value: string): string {
    const entities: Record<string, string> = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "\"": "&quot;",
      "'": "&apos;",
    };
    return String(value).replace(/[&<>"']/g, (c) => entities[c] ?? c);
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

  function crc32(bytes: Uint8Array): number {
    let crc = 0xffffffff;
    for (const byte of bytes) {
      // The mask guarantees the index is within the 256-entry table.
      crc = CRC_TABLE[(crc ^ byte) & 0xff]! ^ (crc >>> 8);
    }
    return (crc ^ 0xffffffff) >>> 0;
  }

  function concatBytes(parts: Uint8Array<ArrayBuffer>[]): Uint8Array<ArrayBuffer> {
    const total = parts.reduce((length, part) => length + part.length, 0);
    const out = new Uint8Array(total);
    let offset = 0;
    for (const part of parts) {
      out.set(part, offset);
      offset += part.length;
    }
    return out;
  }

  function pngChunk(
    type: string,
    data: Uint8Array<ArrayBuffer>,
  ): Uint8Array<ArrayBuffer> {
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
  function itxtChunk(
    keyword: string,
    text: string,
  ): Uint8Array<ArrayBuffer> {
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
  function textChunk(
    keyword: string,
    value: string,
  ): Uint8Array<ArrayBuffer> {
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

  function xmpPacket(meta: IconMetadata): string {
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
  function withPngMetadata(
    pngBytes: Uint8Array<ArrayBuffer>,
    meta: IconMetadata,
  ): Blob {
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

  function withSvgMetadata(svgText: string, meta: IconMetadata): string {
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

  // --- Sizing, rasterization, and saving ---

  // The size input sets the width; the height follows the viewBox aspect ratio
  // so non-square icons are not distorted.
  function dimensionsForSvg(
    text: string,
    size: number,
  ): { width: number; height: number } {
    const viewBox = text.match(
      /viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([-\d.]+)[\s,]+([-\d.]+)\s*"/,
    );
    const viewBoxWidth = viewBox?.[1];
    const viewBoxHeight = viewBox?.[2];
    const aspect = viewBoxWidth && viewBoxHeight
      ? Number(viewBoxHeight) / Number(viewBoxWidth)
      : 1;
    return {
      width: size,
      height: Math.max(1, Math.round(size * aspect)),
    };
  }

  // The source SVGs only have a viewBox, so their intrinsic size is undefined.
  // Writing an explicit width/height makes the downloaded SVG self-describing
  // and rasterization consistent across browsers, which otherwise fall back to
  // a 150px default object size.
  function sizeSvg(text: string, width: number, height: number): string {
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

  function loadImage(url: string): Promise<HTMLImageElement> {
    return new Promise((resolve, reject) => {
      const image = new Image();
      image.onload = () => resolve(image);
      image.onerror = () => reject(new Error("could not load SVG"));
      image.src = url;
    });
  }

  async function rasterize(
    svgText: string,
    width: number,
    height: number,
  ): Promise<Blob> {
    const svgUrl = URL.createObjectURL(
      new Blob([svgText], { type: "image/svg+xml" }),
    );
    try {
      const image = await loadImage(svgUrl);
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const context = canvas.getContext("2d");
      if (!context) throw new Error("2D canvas is unavailable");
      context.drawImage(image, 0, 0, width, height);
      return await new Promise<Blob>((resolve, reject) => {
        canvas.toBlob((png) => {
          if (png) resolve(png);
          else reject(new Error("PNG encoding failed"));
        }, "image/png");
      });
    } finally {
      URL.revokeObjectURL(svgUrl);
    }
  }

  function saveUrl(href: string, filename?: string | null): void {
    const link = document.createElement("a");
    link.href = href;
    if (filename) link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
  }

  function saveBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    saveUrl(url, filename);
    // Keep the blob alive briefly so the browser can start the download.
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function setStatus(message: string): void {
    if (!status) return;
    status.textContent = message;
    status.hidden = message === "";
  }

  // Empty, non-numeric, and out-of-range values are normalized, and the input
  // is updated so it shows the size that will actually be rendered.
  function readSize(): number {
    const raw = downloadSizeInput.value.trim();
    const parsed = raw === "" ? Number.NaN : Number(raw);
    const rounded = Number.isFinite(parsed) ? Math.round(parsed) : DEFAULT_SIZE;
    const size = Math.min(MAX_SIZE, Math.max(MIN_SIZE, rounded));
    downloadSizeInput.value = String(size);
    return size;
  }

  // --- Handlers ---

  pngDownloadButton.addEventListener("click", async () => {
    const size = readSize();
    pngDownloadButton.disabled = true;
    setStatus("");
    try {
      const svgText = await getSvgText();
      const recolored = hasCustomColors()
        ? recolorSvg(svgText, readColors())
        : svgText;
      const { width, height } = dimensionsForSvg(recolored, size);
      let png = await rasterize(
        sizeSvg(recolored, width, height),
        width,
        height,
      );
      if (includeMetadata()) {
        png = withPngMetadata(new Uint8Array(await png.arrayBuffer()), icon);
      }
      saveBlob(png, `${icon.fileBase || icon.id}_${size}.png`);
    } catch (error) {
      console.error(error);
      setStatus("Sorry, the PNG could not be generated.");
    } finally {
      pngDownloadButton.disabled = false;
    }
  });

  // Without JS, or when metadata, colors, and size are all unchanged, the
  // anchor's own download is used, so the saved file is the untouched SVG.
  svgDownloadLink.addEventListener("click", async (event) => {
    if (
      event.button !== 0
      || event.metaKey
      || event.ctrlKey
      || event.shiftKey
      || event.altKey
    ) {
      return;
    }
    const size = readSize();
    // A changed size is a download customization, like colors or metadata.
    if (!includeMetadata() && !hasCustomColors() && size === DEFAULT_SIZE) {
      return;
    }
    event.preventDefault();
    setStatus("");
    try {
      const svgText = await getSvgText();
      let svg = hasCustomColors()
        ? recolorSvg(svgText, readColors())
        : svgText;
      if (includeMetadata()) svg = withSvgMetadata(svg, icon);
      const { width, height } = dimensionsForSvg(svgText, size);
      svg = sizeSvg(svg, width, height);
      saveBlob(
        new Blob([svg], { type: "image/svg+xml" }),
        svgDownloadLink.getAttribute("download") || `${icon.id}.svg`,
      );
    } catch (error) {
      console.error(error);
      setStatus(
        "Sorry, the SVG could not be generated. Downloading the original file.",
      );
      saveUrl(
        svgDownloadLink.href,
        svgDownloadLink.getAttribute("download"),
      );
    }
  });

  downloadSizeInput.addEventListener("change", readSize);
  downloadSizeInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      pngDownloadButton.click();
    }
  });

  if (recolor) {
    for (const input of [recolor.foregroundColor, recolor.backgroundColor]) {
      input.addEventListener("input", updatePreview);
      input.addEventListener("change", updatePreview);
    }

    const alphaPairs: Array<[HTMLInputElement, HTMLInputElement]> = [
      [recolor.foregroundAlpha, recolor.foregroundAlphaNumber],
      [recolor.backgroundAlpha, recolor.backgroundAlphaNumber],
    ];
    for (const [range, number] of alphaPairs) {
      range.addEventListener("input", () => {
        number.value = range.value;
        updatePreview();
      });
      number.addEventListener("input", () => {
        if (applyAlphaNumber(range, number)) updatePreview();
      });
      number.addEventListener("change", () => {
        normalizeAlphaNumber(range, number);
        updatePreview();
      });
    }
  }

  if (resetButton) {
    resetButton.addEventListener("click", () => {
      if (recolor) {
        recolor.foregroundColor.value = DEFAULT_FOREGROUND;
        recolor.backgroundColor.value = DEFAULT_BACKGROUND;
        recolor.foregroundAlpha.value = String(ALPHA_MAX);
        recolor.backgroundAlpha.value = String(ALPHA_MAX);
        recolor.foregroundAlphaNumber.value = String(ALPHA_MAX);
        recolor.backgroundAlphaNumber.value = String(ALPHA_MAX);
      }
      downloadSizeInput.value = String(DEFAULT_SIZE);
      setStatus("");
      updatePreview();
    });
  }
}

main();

export {};

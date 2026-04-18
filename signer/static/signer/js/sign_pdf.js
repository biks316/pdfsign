import * as pdfjsLib from 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.min.mjs';

pdfjsLib.GlobalWorkerOptions.workerSrc =
  'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.worker.min.mjs';

const layout = document.querySelector('.signing-layout');
const pdfUrl = layout?.dataset?.pdfUrl;

const pagesContainer = document.getElementById('pdf-pages');
const signatureCanvas = document.getElementById('signature-canvas');
const clearButton = document.getElementById('clear-signature');
const removeLastPlacementButton = document.getElementById('remove-last-placement');
const submitButton = document.getElementById('submit-sign');
const signForm = document.getElementById('sign-form');
const placementStatus = document.getElementById('placement-status');
const includeSignatureCheckbox = document.getElementById('include-signature');
const includeDateCheckbox = document.getElementById('include-date');
const placementsInput = document.getElementById('placements-json');

let hasSignatureInk = false;
let drawing = false;
let latestSignatureDataUrl = '';
let placementIdCounter = 0;
const placements = [];

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function pointerPosition(event) {
  const rect = signatureCanvas.getBoundingClientRect();
  const x = (event.clientX - rect.left) * (signatureCanvas.width / rect.width);
  const y = (event.clientY - rect.top) * (signatureCanvas.height / rect.height);
  return { x, y };
}

function buildTrimmedSignatureDataUrl() {
  const ctx = signatureCanvas.getContext('2d');
  const { width, height } = signatureCanvas;
  const imageData = ctx.getImageData(0, 0, width, height).data;

  let minX = width;
  let minY = height;
  let maxX = -1;
  let maxY = -1;

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const alpha = imageData[(y * width + x) * 4 + 3];
      if (alpha > 0) {
        minX = Math.min(minX, x);
        minY = Math.min(minY, y);
        maxX = Math.max(maxX, x);
        maxY = Math.max(maxY, y);
      }
    }
  }

  if (maxX < 0 || maxY < 0) {
    return '';
  }

  const trimWidth = Math.max(1, maxX - minX + 1);
  const trimHeight = Math.max(1, maxY - minY + 1);
  const trimmedCanvas = document.createElement('canvas');
  trimmedCanvas.width = trimWidth;
  trimmedCanvas.height = trimHeight;
  trimmedCanvas
    .getContext('2d')
    .drawImage(signatureCanvas, minX, minY, trimWidth, trimHeight, 0, 0, trimWidth, trimHeight);
  return trimmedCanvas.toDataURL('image/png');
}

function updateLatestSignatureData() {
  if (!hasSignatureInk) {
    return;
  }
  const dataUrl = buildTrimmedSignatureDataUrl();
  if (!dataUrl) {
    return;
  }
  latestSignatureDataUrl = dataUrl;
}

function syncPlacementsInput() {
  const payload = placements.map((placement) => ({
    page_number: placement.pageNumber,
    x_ratio: placement.xRatio,
    y_ratio: placement.yRatio,
    width_ratio: placement.widthRatio,
    height_ratio: placement.heightRatio,
    signature_data: placement.signatureData,
    include_signature: placement.includeSignature,
    include_date: placement.includeDate,
  }));
  placementsInput.value = JSON.stringify(payload);
  placementStatus.textContent = `Placements: ${placements.length}`;
}

function removeLastPlacement() {
  if (!placements.length) {
    placementStatus.textContent = 'Placements: 0';
    return;
  }
  const last = placements.pop();
  const markers = pagesContainer.querySelectorAll(`[data-placement-id="${last.id}"]`);
  markers.forEach((marker) => marker.remove());
  syncPlacementsInput();
}

function renderPlacementPreview(overlay, placement, clickX, clickY, pageWidth, pageHeight) {
  if (placement.includeSignature && placement.signatureData) {
    const box = document.createElement('div');
    box.className = 'sig-preview-box';
    box.dataset.placementId = String(placement.id);
    box.style.left = `${placement.x}px`;
    box.style.top = `${placement.y}px`;
    box.style.width = `${placement.displayWidth}px`;
    box.style.height = `${placement.displayHeight}px`;

    const image = document.createElement('img');
    image.className = 'sig-preview';
    image.alt = 'Signature preview';
    image.src = placement.signatureData;
    box.appendChild(image);

    const resizeHandle = document.createElement('button');
    resizeHandle.type = 'button';
    resizeHandle.className = 'sig-resize-handle';
    resizeHandle.title = 'Resize signature';
    resizeHandle.setAttribute('aria-label', 'Resize signature');
    box.appendChild(resizeHandle);

    let resizeState = null;
    resizeHandle.addEventListener('pointerdown', (event) => {
      event.preventDefault();
      event.stopPropagation();
      const boxRect = box.getBoundingClientRect();
      const pageRect = overlay.getBoundingClientRect();
      resizeState = {
        pointerId: event.pointerId,
        startX: event.clientX,
        startWidth: boxRect.width,
        left: parseFloat(box.style.left) || 0,
        top: parseFloat(box.style.top) || 0,
        pageWidth: pageRect.width,
        pageHeight: pageRect.height,
        aspectRatio: boxRect.width / Math.max(1, boxRect.height),
      };
    });

    const onResizeMove = (event) => {
      if (!resizeState || event.pointerId !== resizeState.pointerId) {
        return;
      }
      event.preventDefault();

      const minWidth = Math.max(56, resizeState.pageWidth * 0.08);
      const maxWidth = Math.max(minWidth, resizeState.pageWidth - resizeState.left);
      let nextWidth = clamp(
        resizeState.startWidth + (event.clientX - resizeState.startX),
        minWidth,
        maxWidth,
      );
      let nextHeight = nextWidth / resizeState.aspectRatio;
      const maxHeight = Math.max(20, resizeState.pageHeight - resizeState.top);
      if (nextHeight > maxHeight) {
        nextHeight = maxHeight;
        nextWidth = nextHeight * resizeState.aspectRatio;
      }

      box.style.width = `${nextWidth}px`;
      box.style.height = `${nextHeight}px`;

      placement.displayWidth = nextWidth;
      placement.displayHeight = nextHeight;
      placement.widthRatio = nextWidth / resizeState.pageWidth;
      placement.heightRatio = nextHeight / resizeState.pageHeight;
      syncPlacementsInput();
    };

    const onResizeUp = (event) => {
      if (!resizeState || event.pointerId !== resizeState.pointerId) {
        return;
      }
      resizeState = null;
    };

    window.addEventListener('pointermove', onResizeMove);
    window.addEventListener('pointerup', onResizeUp);
    window.addEventListener('pointercancel', onResizeUp);

    overlay.appendChild(box);
  }

  if (placement.includeDate) {
    const datePreview = document.createElement('span');
    datePreview.className = 'sig-date-preview';
    datePreview.textContent = new Date().toISOString().slice(0, 10);
    datePreview.dataset.placementId = String(placement.id);
    const estimatedWidth = 72;
    const verticalOffset = 16;
    const dateX = clamp(clickX, 0, Math.max(0, pageWidth - estimatedWidth));
    const dateY = clamp(clickY + verticalOffset, 0, Math.max(0, pageHeight - 16));
    datePreview.style.left = `${dateX}px`;
    datePreview.style.top = `${dateY}px`;
    datePreview.style.display = 'block';
    overlay.appendChild(datePreview);
  }
}

function addPlacementClickHandler(canvas, pageNumber) {
  canvas.addEventListener('pointerdown', (event) => {
    if (event.button !== 0) {
      return;
    }
    const shouldIncludeSignature = includeSignatureCheckbox?.checked ?? true;
    const shouldIncludeDate = includeDateCheckbox?.checked ?? false;

    if (!shouldIncludeSignature && !shouldIncludeDate) {
      placementStatus.textContent = 'Placements: select signature, date, or both';
      return;
    }

    updateLatestSignatureData();

    if (shouldIncludeSignature && (!hasSignatureInk || !latestSignatureDataUrl)) {
      placementStatus.textContent = 'Placements: draw signature first';
      return;
    }

    const rect = canvas.getBoundingClientRect();
    const clickX = clamp(event.clientX - rect.left, 0, rect.width);
    const clickY = clamp(event.clientY - rect.top, 0, rect.height);
    const pageWrapper = canvas.parentElement;
    const overlay = pageWrapper.querySelector('.pdf-overlay');
    if (!overlay) {
      return;
    }
    const displayWidth = Math.max(80, rect.width * 0.28);
    const displayHeight = Math.max(26, displayWidth * 0.35);
    const x = clamp(clickX, 0, Math.max(0, rect.width - displayWidth));
    const y = clamp(clickY, 0, Math.max(0, rect.height - displayHeight));

    const placement = {
      id: placementIdCounter,
      pageNumber,
      xRatio: x / rect.width,
      yRatio: y / rect.height,
      widthRatio: displayWidth / rect.width,
      heightRatio: displayHeight / rect.height,
      x,
      y,
      displayWidth,
      displayHeight,
      signatureData: shouldIncludeSignature ? latestSignatureDataUrl : '',
      includeSignature: shouldIncludeSignature,
      includeDate: shouldIncludeDate,
    };
    placementIdCounter += 1;
    placements.push(placement);

    renderPlacementPreview(overlay, placement, clickX, clickY, rect.width, rect.height);
    syncPlacementsInput();
  });
}

function initSignaturePad() {
  const ctx = signatureCanvas.getContext('2d');
  ctx.lineWidth = 2.2;
  ctx.lineCap = 'round';
  ctx.strokeStyle = '#101418';

  signatureCanvas.addEventListener('pointerdown', (event) => {
    event.preventDefault();
    drawing = true;
    const { x, y } = pointerPosition(event);
    ctx.beginPath();
    ctx.moveTo(x, y);
  });

  signatureCanvas.addEventListener('pointermove', (event) => {
    if (!drawing) {
      return;
    }
    event.preventDefault();
    const { x, y } = pointerPosition(event);
    ctx.lineTo(x, y);
    ctx.stroke();
    hasSignatureInk = true;
    updateLatestSignatureData();
  });

  ['pointerup', 'pointerleave', 'pointercancel'].forEach((eventName) => {
    signatureCanvas.addEventListener(eventName, () => {
      drawing = false;
    });
  });

  clearButton.addEventListener('click', () => {
    ctx.clearRect(0, 0, signatureCanvas.width, signatureCanvas.height);
    hasSignatureInk = false;
    latestSignatureDataUrl = '';
    placementStatus.textContent = `Placements: ${placements.length} (signature cleared)`;
  });

  removeLastPlacementButton.addEventListener('click', removeLastPlacement);
}

async function renderPdf() {
  if (!pdfUrl || !pagesContainer) {
    return;
  }

  const loadingTask = pdfjsLib.getDocument(pdfUrl);
  const pdf = await loadingTask.promise;

  for (let pageNum = 1; pageNum <= pdf.numPages; pageNum += 1) {
    const page = await pdf.getPage(pageNum);
    const viewport = page.getViewport({ scale: 1.35 });

    const pageWrapper = document.createElement('div');
    pageWrapper.className = 'pdf-page';

    const canvas = document.createElement('canvas');
    canvas.className = 'pdf-canvas';
    canvas.width = viewport.width;
    canvas.height = viewport.height;

    const context = canvas.getContext('2d');
    pageWrapper.appendChild(canvas);
    const overlay = document.createElement('div');
    overlay.className = 'pdf-overlay';
    pageWrapper.appendChild(overlay);
    pagesContainer.appendChild(pageWrapper);

    await page.render({ canvasContext: context, viewport }).promise;
    addPlacementClickHandler(canvas, pageNum);
  }
}

signForm.addEventListener('submit', (event) => {
  const shouldIncludeSignature = includeSignatureCheckbox?.checked ?? true;
  const shouldIncludeDate = includeDateCheckbox?.checked ?? false;

  if (!shouldIncludeSignature && !shouldIncludeDate) {
    event.preventDefault();
    placementStatus.textContent = 'Placements: select signature, date, or both';
    return;
  }

  if (!placements.length) {
    event.preventDefault();
    placementStatus.textContent = 'Placements: click one or more positions on the PDF';
    return;
  }

  syncPlacementsInput();
  submitButton.disabled = true;
  submitButton.textContent = 'Signing...';
});

initSignaturePad();
syncPlacementsInput();
renderPdf().catch(() => {
  placementStatus.textContent = 'Placements: failed to render PDF preview';
});

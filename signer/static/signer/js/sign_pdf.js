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

function initSignaturePad() {
  const ctx = signatureCanvas.getContext('2d');
  ctx.lineWidth = 2.2;
  ctx.lineCap = 'round';
  ctx.strokeStyle = '#101418';

  const pointerPosition = (event) => {
    const rect = signatureCanvas.getBoundingClientRect();
    const x = (event.clientX - rect.left) * (signatureCanvas.width / rect.width);
    const y = (event.clientY - rect.top) * (signatureCanvas.height / rect.height);
    return { x, y };
  };

  const start = (event) => {
    event.preventDefault();
    drawing = true;
    const { x, y } = pointerPosition(event);
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const move = (event) => {
    if (!drawing) {
      return;
    }
    event.preventDefault();
    const { x, y } = pointerPosition(event);
    ctx.lineTo(x, y);
    ctx.stroke();
    hasSignatureInk = true;
    updateLatestSignatureData();
  };

  const stop = () => {
    drawing = false;
  };

  signatureCanvas.addEventListener('pointerdown', start);
  signatureCanvas.addEventListener('pointermove', move);
  signatureCanvas.addEventListener('pointerup', stop);
  signatureCanvas.addEventListener('pointerleave', stop);

  clearButton.addEventListener('click', () => {
    ctx.clearRect(0, 0, signatureCanvas.width, signatureCanvas.height);
    hasSignatureInk = false;
    latestSignatureDataUrl = '';
    placementStatus.textContent = `Placements: ${placements.length} (signature cleared)`;
  });

  removeLastPlacementButton.addEventListener('click', () => {
    removeLastPlacement();
  });
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
    return null;
  }

  const trimWidth = Math.max(1, maxX - minX + 1);
  const trimHeight = Math.max(1, maxY - minY + 1);
  const trimmedCanvas = document.createElement('canvas');
  trimmedCanvas.width = trimWidth;
  trimmedCanvas.height = trimHeight;
  const trimmedCtx = trimmedCanvas.getContext('2d');
  trimmedCtx.drawImage(signatureCanvas, minX, minY, trimWidth, trimHeight, 0, 0, trimWidth, trimHeight);
  return trimmedCanvas.toDataURL('image/png');
}

function renderPlacementPreview(pageWrapper, placement) {
  const {
    id,
    x,
    y,
    displayWidth,
    displayHeight,
    signatureData,
    includeSignature,
    includeDate,
  } = placement;

  if (includeSignature && signatureData) {
    const image = document.createElement('img');
    image.className = 'sig-preview';
    image.alt = 'Signature preview';
    image.src = signatureData;
    image.style.left = `${x}px`;
    image.style.top = `${y}px`;
    image.style.width = `${displayWidth}px`;
    image.style.height = `${displayHeight}px`;
    image.style.display = 'block';
    image.dataset.placementId = String(id);
    pageWrapper.appendChild(image);
  }

  if (includeDate) {
    const datePreview = document.createElement('span');
    datePreview.className = 'sig-date-preview';
    datePreview.textContent = new Date().toISOString().slice(0, 10);
    datePreview.dataset.placementId = String(id);
    const estimatedWidth = 72;
    const verticalOffset = 16;
    const maxDateX = Math.max(0, pageWrapper.clientWidth - estimatedWidth);
    const maxDateY = Math.max(0, pageWrapper.clientHeight - verticalOffset);
    const dateX = Math.min(Math.max(0, x), maxDateX);
    const dateY = Math.min(Math.max(0, y + verticalOffset), maxDateY);
    datePreview.style.left = `${dateX}px`;
    datePreview.style.top = `${dateY}px`;

    datePreview.style.display = 'block';
    pageWrapper.appendChild(datePreview);
  }
}

function syncPlacementsInput() {
  const payload = placements.map((placement) => ({
    page_number: placement.pageNumber,
    x_ratio: placement.xRatio,
    y_ratio: placement.yRatio,
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

function addPlacementClickHandler(canvas, pageNumber) {
  canvas.addEventListener('click', (event) => {
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
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const xRatio = x / rect.width;
    const yRatio = y / rect.height;

    const pageWrapper = canvas.parentElement;
    const displayWidth = Math.max(80, rect.width * 0.28);
    const displayHeight = displayWidth * 0.35;
    const signatureData = shouldIncludeSignature ? latestSignatureDataUrl : '';

    const placementId = placementIdCounter;
    placementIdCounter += 1;

    const placement = {
      id: placementId,
      pageNumber,
      xRatio,
      yRatio,
      x,
      y,
      displayWidth,
      displayHeight,
      signatureData,
      includeSignature: shouldIncludeSignature,
      includeDate: shouldIncludeDate,
    };
    placements.push(placement);

    renderPlacementPreview(pageWrapper, placement);

    syncPlacementsInput();
  });
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

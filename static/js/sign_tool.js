import * as pdfjsLib from 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.min.mjs';

pdfjsLib.GlobalWorkerOptions.workerSrc =
  'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.worker.min.mjs';

const layout = document.querySelector('[data-sign-tool]');
if (!layout) {
  // No-op outside sign page.
} else {
  const pdfUrl = layout.dataset.pdfUrl;
  const pagesContainer = document.getElementById('pdf-pages');
  const signatureCanvas = document.getElementById('signature-canvas');
  const signatureUpload = document.getElementById('signature-upload');
  const clearButton = document.getElementById('clear-signature');
  const removeButton = document.getElementById('remove-last-placement');
  const placementStatus = document.getElementById('placement-status');
  const includeSignatureCheckbox = document.getElementById('include-signature');
  const includeDateCheckbox = document.getElementById('include-date');
  const signForm = document.getElementById('sign-form');
  const placementsInput = document.getElementById('placements-json');

  let hasInk = false;
  let drawing = false;
  let signatureDataUrl = '';
  const placements = [];
  let placementCounter = 0;

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function pointFromEvent(event) {
    const rect = signatureCanvas.getBoundingClientRect();
    return {
      x: (event.clientX - rect.left) * (signatureCanvas.width / rect.width),
      y: (event.clientY - rect.top) * (signatureCanvas.height / rect.height),
    };
  }

  function trimmedDataUrl() {
    const ctx = signatureCanvas.getContext('2d');
    const { width, height } = signatureCanvas;
    const pixels = ctx.getImageData(0, 0, width, height).data;

    let minX = width;
    let minY = height;
    let maxX = -1;
    let maxY = -1;

    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const alpha = pixels[(y * width + x) * 4 + 3];
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

    const trimmed = document.createElement('canvas');
    trimmed.width = Math.max(1, maxX - minX + 1);
    trimmed.height = Math.max(1, maxY - minY + 1);
    trimmed.getContext('2d').drawImage(signatureCanvas, minX, minY, trimmed.width, trimmed.height, 0, 0, trimmed.width, trimmed.height);
    return trimmed.toDataURL('image/png');
  }

  function syncInput() {
    placementsInput.value = JSON.stringify(placements.map((item) => ({
      page_number: item.pageNumber,
      x_ratio: item.xRatio,
      y_ratio: item.yRatio,
      width_ratio: item.widthRatio,
      height_ratio: item.heightRatio,
      signature_data: item.signatureData,
      include_signature: item.includeSignature,
      include_date: item.includeDate,
    })));
    placementStatus.textContent = `Placements: ${placements.length}`;
  }

  function removeLastPlacement() {
    const last = placements.pop();
    if (!last) {
      placementStatus.textContent = 'Placements: 0';
      return;
    }
    pagesContainer.querySelectorAll(`[data-placement-id="${last.id}"]`).forEach((node) => node.remove());
    syncInput();
  }

  function addPlacement(overlay, pageNumber, clickX, clickY, rectWidth, rectHeight) {
    const includeSignature = includeSignatureCheckbox.checked;
    const includeDate = includeDateCheckbox.checked;

    if (!includeSignature && !includeDate) {
      placementStatus.textContent = 'Choose signature, date, or both.';
      return;
    }

    if (includeSignature) {
      if (!signatureDataUrl) {
        signatureDataUrl = trimmedDataUrl();
      }
      if (!signatureDataUrl) {
        placementStatus.textContent = 'Draw or upload a signature first.';
        return;
      }
    }

    const placement = {
      id: placementCounter,
      pageNumber,
      xRatio: clickX / rectWidth,
      yRatio: clickY / rectHeight,
      widthRatio: null,
      heightRatio: null,
      signatureData: includeSignature ? signatureDataUrl : '',
      includeSignature,
      includeDate,
    };
    placementCounter += 1;
    placements.push(placement);

    if (includeSignature) {
      const initialWidth = Math.max(90, rectWidth * 0.26);
      const initialHeight = Math.max(26, rectHeight * 0.06);
      const left = clamp(clickX, 0, Math.max(0, rectWidth - initialWidth));
      const top = clamp(clickY, 0, Math.max(0, rectHeight - initialHeight));
      placement.xRatio = left / rectWidth;
      placement.yRatio = top / rectHeight;
      placement.widthRatio = initialWidth / rectWidth;
      placement.heightRatio = initialHeight / rectHeight;

      const box = document.createElement('div');
      box.className = 'sig-preview-box';
      box.dataset.placementId = String(placement.id);
      box.style.left = `${left}px`;
      box.style.top = `${top}px`;
      box.style.width = `${initialWidth}px`;
      box.style.height = `${initialHeight}px`;

      const img = document.createElement('img');
      img.className = 'sig-preview';
      img.src = signatureDataUrl;
      img.alt = 'signature preview';
      box.appendChild(img);

      const resizeHandle = document.createElement('button');
      resizeHandle.type = 'button';
      resizeHandle.className = 'sig-resize-handle';
      resizeHandle.title = 'Resize signature';
      resizeHandle.setAttribute('aria-label', 'Resize signature');
      box.appendChild(resizeHandle);

      let resizeState = null;
      const stopResize = () => {
        resizeState = null;
      };

      resizeHandle.addEventListener('pointerdown', (event) => {
        event.preventDefault();
        event.stopPropagation();
        const pageRect = overlay.getBoundingClientRect();
        const boxRect = box.getBoundingClientRect();
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
        placement.widthRatio = nextWidth / resizeState.pageWidth;
        placement.heightRatio = nextHeight / resizeState.pageHeight;
        syncInput();
      };

      const onResizeUp = (event) => {
        if (!resizeState || event.pointerId !== resizeState.pointerId) {
          return;
        }
        stopResize();
      };

      window.addEventListener('pointermove', onResizeMove);
      window.addEventListener('pointerup', onResizeUp);
      window.addEventListener('pointercancel', onResizeUp);

      overlay.appendChild(box);
    }

    if (includeDate) {
      const dateEl = document.createElement('span');
      dateEl.className = 'date-preview';
      dateEl.dataset.placementId = String(placement.id);
      dateEl.textContent = new Date().toISOString().slice(0, 10);
      dateEl.style.left = `${clickX}px`;
      dateEl.style.top = `${clickY + 14}px`;
      overlay.appendChild(dateEl);
    }

    syncInput();
  }

  function initSignatureCanvas() {
    const ctx = signatureCanvas.getContext('2d');
    ctx.lineWidth = 2.3;
    ctx.lineCap = 'round';
    ctx.strokeStyle = '#111827';

    signatureCanvas.addEventListener('pointerdown', (event) => {
      drawing = true;
      const p = pointFromEvent(event);
      ctx.beginPath();
      ctx.moveTo(p.x, p.y);
    });

    signatureCanvas.addEventListener('pointermove', (event) => {
      if (!drawing) {
        return;
      }
      const p = pointFromEvent(event);
      ctx.lineTo(p.x, p.y);
      ctx.stroke();
      hasInk = true;
      signatureDataUrl = trimmedDataUrl();
    });

    ['pointerup', 'pointerleave', 'pointercancel'].forEach((name) => {
      signatureCanvas.addEventListener(name, () => {
        drawing = false;
      });
    });

    clearButton.addEventListener('click', () => {
      ctx.clearRect(0, 0, signatureCanvas.width, signatureCanvas.height);
      hasInk = false;
      signatureDataUrl = '';
      placementStatus.textContent = 'Signature cleared.';
    });

    removeButton.addEventListener('click', removeLastPlacement);

    signatureUpload.addEventListener('change', (event) => {
      const [file] = event.target.files || [];
      if (!file) {
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          signatureDataUrl = reader.result;
          hasInk = true;
          placementStatus.textContent = 'Signature image loaded.';
        }
      };
      reader.readAsDataURL(file);
    });
  }

  async function renderPdf() {
    const pdf = await pdfjsLib.getDocument(pdfUrl).promise;

    for (let pageNum = 1; pageNum <= pdf.numPages; pageNum += 1) {
      const page = await pdf.getPage(pageNum);
      const viewport = page.getViewport({ scale: 1.35 });
      const pageWrapper = document.createElement('div');
      pageWrapper.className = 'pdf-page';

      const canvas = document.createElement('canvas');
      canvas.className = 'pdf-canvas';
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      pageWrapper.appendChild(canvas);
      const overlay = document.createElement('div');
      overlay.className = 'pdf-overlay';
      pageWrapper.appendChild(overlay);
      pagesContainer.appendChild(pageWrapper);

      const context = canvas.getContext('2d');
      await page.render({ canvasContext: context, viewport }).promise;

      canvas.addEventListener('pointerdown', (event) => {
        if (event.button !== 0) {
          return;
        }
        const rect = canvas.getBoundingClientRect();
        const clickX = clamp(event.clientX - rect.left, 0, rect.width);
        const clickY = clamp(event.clientY - rect.top, 0, rect.height);
        addPlacement(overlay, pageNum, clickX, clickY, rect.width, rect.height);
      });
    }
  }

  signForm.addEventListener('submit', (event) => {
    if (!placements.length) {
      event.preventDefault();
      placementStatus.textContent = 'Add at least one placement before applying.';
      return;
    }
    syncInput();
  });

  initSignatureCanvas();
  syncInput();
  renderPdf().catch(() => {
    placementStatus.textContent = 'Failed to load PDF preview.';
  });
}

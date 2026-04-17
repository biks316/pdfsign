import * as pdfjsLib from 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.min.mjs';

pdfjsLib.GlobalWorkerOptions.workerSrc =
  'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.worker.min.mjs';

const layout = document.querySelector('[data-date-tool]');
if (!layout) {
  // No-op outside date page.
} else {
  const pdfUrl = layout.dataset.pdfUrl;
  const pagesContainer = document.getElementById('pdf-pages');
  const pageInput = document.getElementById('id_page_number');
  const xInput = document.getElementById('id_x_ratio');
  const yInput = document.getElementById('id_y_ratio');
  const status = document.getElementById('date-placement-status');

  function clearPreviews() {
    pagesContainer.querySelectorAll('.date-preview').forEach((el) => el.remove());
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
      pagesContainer.appendChild(pageWrapper);

      const context = canvas.getContext('2d');
      await page.render({ canvasContext: context, viewport }).promise;

      canvas.addEventListener('click', (event) => {
        const rect = canvas.getBoundingClientRect();
        const xRatio = (event.clientX - rect.left) / rect.width;
        const yRatio = (event.clientY - rect.top) / rect.height;

        pageInput.value = pageNum;
        xInput.value = xRatio.toFixed(6);
        yInput.value = yRatio.toFixed(6);

        clearPreviews();
        const marker = document.createElement('span');
        marker.className = 'date-preview';
        marker.textContent = 'Date here';
        marker.style.left = `${event.clientX - rect.left}px`;
        marker.style.top = `${event.clientY - rect.top}px`;
        pageWrapper.appendChild(marker);

        status.textContent = `Selected page ${pageNum} (${xRatio.toFixed(3)}, ${yRatio.toFixed(3)})`;
      });
    }
  }

  renderPdf().catch(() => {
    status.textContent = 'Failed to load PDF preview.';
  });
}

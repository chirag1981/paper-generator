let currentZoom = 1.0;
let currentImageIndex = 0;
let uploadedImages = [];

function initViewer(images) {
  uploadedImages = images || [];
  const strip = document.getElementById('imageStrip');
  const mainImg = document.getElementById('mainViewerImg');
  const emptyState = document.getElementById('viewerEmptyState');
  const counter = document.getElementById('pageCounter');
  const countEl = document.getElementById('scanAllCount');
  const btnAll = document.getElementById('btnRunOcrAll');
  const btnCurrent = document.getElementById('btnRunOcrCurrent');

  if (!strip) return;
  strip.innerHTML = '';

  if (uploadedImages.length === 0) {
    strip.innerHTML = '<span style="font-size: 0.82rem; color: #94a3b8; padding: 10px; display: block; text-align: center;">No uploaded pages</span>';
    if (mainImg) {
      mainImg.src = '';
      mainImg.style.display = 'none';
    }
    if (emptyState) {
      emptyState.style.display = 'flex';
    }
    if (counter) counter.innerText = 'Page 0 of 0';
    if (countEl) countEl.innerText = '0';
    if (btnAll) {
      btnAll.disabled = true;
      btnAll.style.opacity = '0.45';
      btnAll.style.cursor = 'not-allowed';
    }
    if (btnCurrent) {
      btnCurrent.disabled = true;
      btnCurrent.style.opacity = '0.45';
      btnCurrent.style.cursor = 'not-allowed';
    }
    return;
  }

  if (emptyState) emptyState.style.display = 'none';
  if (mainImg) mainImg.style.display = 'block';
  if (btnAll) {
    btnAll.disabled = false;
    btnAll.style.opacity = '1';
    btnAll.style.cursor = 'pointer';
  }
  if (btnCurrent) {
    btnCurrent.disabled = false;
    btnCurrent.style.opacity = '1';
    btnCurrent.style.cursor = 'pointer';
  }
  if (countEl) countEl.innerText = String(uploadedImages.length);

  uploadedImages.forEach((imgObj, idx) => {
    const thumb = document.createElement('div');
    thumb.className = `thumb-item ${idx === 0 ? 'active' : ''}`;
    thumb.onclick = () => selectImage(idx);
    thumb.innerHTML = `<img src="${imgObj.url}" alt="Page ${idx + 1}">`;
    strip.appendChild(thumb);
  });

  selectImage(0);
}

function clearViewer() {
  initViewer([]);
}

function selectImage(index) {
  if (index < 0 || index >= uploadedImages.length) return;
  currentImageIndex = index;
  
  const mainImg = document.getElementById('mainViewerImg');
  if (mainImg) {
    mainImg.src = uploadedImages[index].url;
    mainImg.style.display = 'block';
    resetZoom();
  }

  const counter = document.getElementById('pageCounter');
  if (counter) {
    counter.innerText = `Page ${index + 1} of ${uploadedImages.length}`;
  }

  const thumbs = document.querySelectorAll('.thumb-item');
  thumbs.forEach((t, i) => {
    t.classList.toggle('active', i === index);
  });
}

function zoomImage(delta) {
  const mainImg = document.getElementById('mainViewerImg');
  if (!mainImg) return;
  currentZoom = Math.min(Math.max(0.5, currentZoom + delta), 3.0);
  mainImg.style.transform = `scale(${currentZoom})`;
}

function resetZoom() {
  const mainImg = document.getElementById('mainViewerImg');
  if (!mainImg) return;
  currentZoom = 1.0;
  mainImg.style.transform = 'scale(1.0)';
}

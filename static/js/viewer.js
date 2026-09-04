let currentZoom = 1.0;
let currentImageIndex = 0;
let uploadedImages = [];

function initViewer(images) {
  uploadedImages = images || [];
  const strip = document.getElementById('imageStrip');
  if (!strip) return;
  strip.innerHTML = '';

  if (uploadedImages.length === 0) {
    strip.innerHTML = '<span style="font-size: 0.85rem; color: #94a3b8; padding: 6px;">No uploaded images yet. Using sample template.</span>';
    return;
  }

  uploadedImages.forEach((imgObj, idx) => {
    const thumb = document.createElement('div');
    thumb.className = `thumb-item ${idx === 0 ? 'active' : ''}`;
    thumb.onclick = () => selectImage(idx);
    thumb.innerHTML = `<img src="${imgObj.url}" alt="Page ${idx + 1}">`;
    strip.appendChild(thumb);
  });

  selectImage(0);
}

function selectImage(index) {
  if (index < 0 || index >= uploadedImages.length) return;
  currentImageIndex = index;
  
  const mainImg = document.getElementById('mainViewerImg');
  if (mainImg) {
    mainImg.src = uploadedImages[index].url;
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

let paperData = null;

document.addEventListener('DOMContentLoaded', () => {
  loadPaperState();
  loadUploadedImages();
  checkApiKeyStatus();

  // Close dropdown on outside click
  window.addEventListener('click', (e) => {
    const langMenu = document.getElementById('langMenu');
    const langBtn = document.getElementById('btnLangDropdown');
    if (langMenu && langBtn && !langBtn.contains(e.target) && !langMenu.contains(e.target)) {
      langMenu.style.display = 'none';
    }
    const resetMenu = document.getElementById('resetMenu');
    const resetBtn = document.getElementById('btnResetDropdown');
    if (resetMenu && resetBtn && !resetBtn.contains(e.target) && !resetMenu.contains(e.target)) {
      resetMenu.style.display = 'none';
    }
  });

  // Check if OCR language was set from uploader
  const savedLang = localStorage.getItem('selected_ocr_lang');
  const ocrLangSelect = document.getElementById('ocrLangSelect');
  if (savedLang && ocrLangSelect) {
    ocrLangSelect.value = savedLang;
  }

  // Check if auto-scan should be offered after a new upload
  if (localStorage.getItem('auto_trigger_ocr') === 'true') {
    localStorage.removeItem('auto_trigger_ocr');
    const stored = JSON.parse(localStorage.getItem('uploaded_images') || '[]');
    const count = stored.length || 1;
    setTimeout(() => {
      if (confirm(`${count} new handwritten exam page(s) uploaded!\n\nDo you want to run AI Multilingual OCR to automatically scan and extract all questions from all ${count} page(s)?`)) {
        triggerAiScan(false);
      }
    }, 400);
  }
});

function loadUploadedImages() {
  const stored = JSON.parse(localStorage.getItem('uploaded_images') || '[]');
  const countEl = document.getElementById('scanAllCount');
  if (typeof initViewer === 'function') {
    if (stored.length === 0) {
      const defaults = [
        { url: '/uploads/WhatsApp Image 2026-09-01 at 1.06.53 PM.jpeg', filename: 'page1' },
        { url: '/uploads/WhatsApp Image 2026-09-01 at 1.07.13 PM.jpeg', filename: 'page2' },
        { url: '/uploads/WhatsApp Image 2026-09-01 at 1.07.30 PM.jpeg', filename: 'page3' },
        { url: '/uploads/WhatsApp Image 2026-09-01 at 1.07.46 PM.jpeg', filename: 'page4' },
        { url: '/uploads/WhatsApp Image 2026-09-01 at 1.08.01 PM.jpeg', filename: 'page5' }
      ];
      initViewer(defaults);
      if (countEl) countEl.innerText = '5';
    } else {
      initViewer(stored);
      if (countEl) countEl.innerText = String(stored.length);
    }
  }
}

function handleEditorFileUpload(files) {
  if (!files || files.length === 0) return;

  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }

  showToast(`Uploading ${files.length} document page(s)...`, 'info');

  fetch('/api/upload', {
    method: 'POST',
    body: formData
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      // 1. Reset previous paper structure cleanly for the new document
      paperData = {
        metadata: {
          exam_title: "Uploaded Exam Paper",
          standard: "Std. ",
          subject: "",
          total_marks: "0",
          date: "",
          day: "",
          roll_no: "",
          time_limit: "2 Hours"
        },
        sections: [],
        custom_marks_table: []
      };
      localStorage.setItem('current_paper', JSON.stringify(paperData));
      
      // 2. Save new uploaded images
      localStorage.setItem('uploaded_images', JSON.stringify(data.files));
      
      // 3. Re-init viewer with new images
      loadUploadedImages();
      
      // 4. Render editor with empty state
      renderEditor();

      showToast(`Uploaded ${data.files.length} page(s)! Paper Structure & Questions reset for new document.`, 'success');

      setTimeout(() => {
        if (confirm(`Uploaded ${data.files.length} page(s) successfully!\n\nDo you want to run AI Multilingual OCR to automatically scan and digitize all ${data.files.length} pages now?`)) {
          triggerAiScan(false);
        }
      }, 400);
    } else {
      showToast(data.error || 'Upload failed', 'error');
    }
  })
  .catch(err => {
    showToast('Network error during upload: ' + err.message, 'error');
  });
}

function loadPaperState() {
  const local = localStorage.getItem('current_paper');
  if (local) {
    try {
      paperData = JSON.parse(local);
      if (document.getElementById('sectionsContainer')) {
        renderEditor();
      }
    } catch(e) {
      fetchSamplePaper();
    }
  } else {
    fetchSamplePaper();
  }
}

function fetchSamplePaper() {
  fetch('/api/sample-paper')
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        paperData = data.paper;
        saveToLocal();
        if (document.getElementById('sectionsContainer')) {
          renderEditor();
        }
      }
    });
}

function saveToLocal() {
  syncFormToState();
  if (paperData) {
    localStorage.setItem('current_paper', JSON.stringify(paperData));
  }
}

function toggleResetMenu() {
  const menu = document.getElementById('resetMenu');
  if (menu) {
    menu.style.display = (menu.style.display === 'none' || menu.style.display === '') ? 'block' : 'none';
  }
}

function clearPaperToBlank() {
  const menu = document.getElementById('resetMenu');
  if (menu) menu.style.display = 'none';

  if (confirm('Are you sure you want to clear all questions and start with a blank paper?')) {
    paperData = {
      metadata: {
        exam_title: "Exam Paper",
        standard: "Std. ",
        subject: "",
        total_marks: "0",
        date: "",
        day: "",
        roll_no: "",
        time_limit: "2 Hours"
      },
      sections: [],
      custom_marks_table: []
    };
    saveToLocal();
    renderEditor();
    showToast('Cleared all questions. Ready for new paper!', 'info');
  }
}

function resetToSamplePaper() {
  const menu = document.getElementById('resetMenu');
  if (menu) menu.style.display = 'none';

  if (confirm('Reset paper back to the preloaded Std. 6 Mathematics sample exam?')) {
    localStorage.removeItem('current_paper');
    fetchSamplePaper();
    showToast('Reset to default Std. 6 sample paper', 'success');
  }
}

function resetToDefault() {
  toggleResetMenu();
}

function syncFormToState() {
  if (!paperData) return;
  if (!paperData.metadata) paperData.metadata = {};

  const titleEl = document.getElementById('metaExamTitle');
  if (titleEl) paperData.metadata.exam_title = titleEl.value.trim();

  const stdEl = document.getElementById('metaStandard');
  if (stdEl) paperData.metadata.standard = stdEl.value.trim();

  const subEl = document.getElementById('metaSubject');
  if (subEl) paperData.metadata.subject = subEl.value.trim();

  const marksEl = document.getElementById('metaMarks');
  if (marksEl) paperData.metadata.total_marks = marksEl.value.trim();

  const dateEl = document.getElementById('metaDate');
  if (dateEl) paperData.metadata.date = dateEl.value.trim();

  const dayEl = document.getElementById('metaDay');
  if (dayEl) paperData.metadata.day = dayEl.value.trim();

  const rollEl = document.getElementById('metaRollNo');
  if (rollEl) paperData.metadata.roll_no = rollEl.value.trim();
}

function triggerDownload(url, filename) {
  const a = document.createElement('a');
  a.href = url;
  a.download = filename || 'Exam_Paper';
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  setTimeout(() => a.remove(), 200);
}

// ==================== OCR MULTILINGUAL SCAN ====================
function triggerAiScan(onlyCurrentPage = false) {
  const overlay = document.getElementById('ocrLoadingOverlay');
  const btnAll = document.getElementById('btnRunOcrAll');
  const btnCurrent = document.getElementById('btnRunOcrCurrent');
  const legacyBtn = document.getElementById('btnRunOcr');
  const titleEl = document.getElementById('ocrLoadingTitle');
  const subtitleEl = document.getElementById('ocrLoadingSubtitle');
  const ocrLang = document.getElementById('ocrLangSelect')?.value || 'auto';
  const storedImages = JSON.parse(localStorage.getItem('uploaded_images') || '[]');

  let targetFilenames = [];
  if (onlyCurrentPage) {
    // Scan only the current page in the viewer
    if (typeof currentImageIndex !== 'undefined' && typeof uploadedImages !== 'undefined' && uploadedImages[currentImageIndex]) {
      const curImg = uploadedImages[currentImageIndex];
      const fn = curImg.filename || curImg.original_name || curImg.url?.split('/').pop();
      if (fn) targetFilenames = [fn];
    }
    if (targetFilenames.length === 0 && storedImages.length > 0) {
      targetFilenames = [storedImages[0].filename];
    }
  } else {
    // Scan ALL uploaded pages in batch
    targetFilenames = storedImages.map(img => img.filename || img.url?.split('/').pop()).filter(Boolean);
  }

  if (targetFilenames.length === 0) {
    showToast('No uploaded images found to scan. Please upload document images first.', 'error');
    return;
  }

  const count = targetFilenames.length;
  if (overlay) {
    overlay.style.display = 'flex';
    if (titleEl) {
      titleEl.innerText = onlyCurrentPage 
        ? `AI Scanning Current Page (${(typeof currentImageIndex !== 'undefined' ? currentImageIndex : 0) + 1} of ${storedImages.length || 1})...`
        : `AI Scanning All ${count} Uploaded Pages...`;
    }
    if (subtitleEl) {
      subtitleEl.innerText = onlyCurrentPage
        ? `Transcribing current page with Gemini Multimodal Vision AI...`
        : `Transcribing all ${count} pages sequentially with Multimodal Vision AI...`;
    }
  }

  if (btnAll) btnAll.disabled = true;
  if (btnCurrent) btnCurrent.disabled = true;
  if (legacyBtn) legacyBtn.disabled = true;

  showToast(onlyCurrentPage ? `Scanning current page with AI...` : `Scanning all ${count} pages in batch with AI...`, 'info');

  fetch('/api/scan-ocr', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filenames: targetFilenames,
      language: ocrLang
    })
  })
  .then(r => r.json())
  .then(data => {
    if (overlay) overlay.style.display = 'none';
    if (btnAll) btnAll.disabled = false;
    if (btnCurrent) btnCurrent.disabled = false;
    if (legacyBtn) legacyBtn.disabled = false;

    if (data.success && data.paper) {
      if (onlyCurrentPage && paperData && Array.isArray(paperData.sections) && paperData.sections.length > 0) {
        // Appending single scanned page to existing sections
        const newSecs = data.paper.sections || [];
        paperData.sections = paperData.sections.concat(newSecs);
        if (data.paper.metadata && (!paperData.metadata.subject || paperData.metadata.subject === 'ENV')) {
          paperData.metadata = { ...paperData.metadata, ...data.paper.metadata };
        }
        showToast(`Extracted and appended ${newSecs.length} section(s) from current page!`, 'success');
      } else {
        // Full scan: replace paper structure
        paperData = data.paper;
        showToast(data.message || `All ${count} pages successfully digitized into Paper Structure!`, 'success');
      }
      saveToLocal();
      renderEditor();
    } else {
      showToast(data.error || 'OCR scanning failed', 'error');
      if (data.error && data.error.includes('API Key')) {
        openApiKeyModal();
      }
    }
  })
  .catch(err => {
    if (overlay) overlay.style.display = 'none';
    if (btnAll) btnAll.disabled = false;
    if (btnCurrent) btnCurrent.disabled = false;
    if (legacyBtn) legacyBtn.disabled = false;
    showToast('Network error during OCR: ' + err.message, 'error');
  });
}

// ==================== 1-CLICK LANGUAGE TRANSLATION ====================
function toggleLangMenu() {
  const menu = document.getElementById('langMenu');
  if (menu) {
    menu.style.display = (menu.style.display === 'none' || menu.style.display === '') ? 'block' : 'none';
  }
}

function convertLanguage(targetLang) {
  const menu = document.getElementById('langMenu');
  if (menu) menu.style.display = 'none';

  syncFormToState();
  if (!paperData) return;

  const langLabels = {
    'en': 'English',
    'gu': 'ગુજરાતી (Gujarati)',
    'hi': 'हिन्दी (Hindi)'
  };

  const targetLabel = langLabels[targetLang] || targetLang;
  showToast(`Converting exam paper to ${targetLabel}...`, 'info');

  fetch('/api/translate-paper', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      paper: paperData,
      target_lang: targetLang
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.success && data.paper) {
      paperData = data.paper;
      saveToLocal();
      renderEditor();
      
      const labelEl = document.getElementById('currentLangLabel');
      if (labelEl) labelEl.innerText = targetLang.toUpperCase();
      
      showToast(data.message || `Paper translated to ${targetLabel}!`, 'success');
    } else {
      showToast(data.error || 'Language conversion failed', 'error');
      if (data.error && data.error.includes('API Key')) {
        openApiKeyModal();
      }
    }
  })
  .catch(err => {
    showToast('Translation error: ' + err.message, 'error');
  });
}

// ==================== API KEY SETTINGS MODAL ====================
function openApiKeyModal() {
  const modal = document.getElementById('apiKeyModal');
  if (modal) modal.style.display = 'flex';
}

function closeApiKeyModal() {
  const modal = document.getElementById('apiKeyModal');
  if (modal) modal.style.display = 'none';
}

function saveApiKey() {
  const keyInput = document.getElementById('inputApiKey');
  const key = keyInput ? keyInput.value.trim() : '';

  if (!key) {
    showToast('Please enter a valid Gemini API key', 'error');
    return;
  }

  fetch('/api/save-api-key', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: key })
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      showToast('API Key verified & saved!', 'success');
      closeApiKeyModal();
      checkApiKeyStatus();
    } else {
      showToast(data.error || 'Failed to save API key', 'error');
    }
  })
  .catch(err => {
    showToast('Error saving key: ' + err.message, 'error');
  });
}

function checkApiKeyStatus() {
  fetch('/api/config-status')
    .then(r => r.json())
    .then(data => {
      const btnText = document.getElementById('apiKeyBtnText');
      if (data.has_gemini_key) {
        if (btnText) btnText.innerHTML = 'AI Key <i class="fa-solid fa-circle-check" style="color: #10b981; font-size: 0.75rem; margin-left: 2px;"></i>';
      } else {
        if (btnText) btnText.innerText = 'AI Key (Set)';
      }
    })
    .catch(() => {});
}

function calcQuestionSummary(paper) {
  const sections = paper?.sections || [];
  const indicDigits = { '૦':'0','૧':'1','૨':'2','૩':'3','૪':'4','૫':'5','૬':'6','૭':'7','૮':'8','૯':'9', '०':'0','१':'1','२':'2','३':'3','४':'4','५':'5','६':'6','७':'7','८':'8','९':'9' };
  const replaceIndic = str => String(str || '').replace(/[૦-૯०-९]/g, d => indicDigits[d] || d);

  const qMap = {};
  sections.forEach((sec, idx) => {
    const title = replaceIndic(sec.title || '').trim();
    const secId = String(sec.id || '').toLowerCase();
    const marksStr = replaceIndic(sec.marks || '0');
    const mNum = marksStr.match(/\d+/);
    const marksVal = mNum ? parseInt(mNum[0], 10) : 0;

    // Match patterns like Q-1, Q.1, Q:-1, Q: 1, Q:-3(A), Q.3(C), Que 1, Question 1, પ્ર. ૧, પ્ર:-૧, प्रश्न १, etc.
    let match = title.match(/(?:Q|Que|Question|Sec|Section|પ્ર|પ્રશ્ન|प्रश्न)[\.\s\-:_]*(\d+)/i);
    let qKey;
    if (match) {
      qKey = `Q-${match[1]}`;
    } else {
      let leadDigitMatch = title.match(/^[\s\-:_]*(\d+)/);
      if (leadDigitMatch) {
        qKey = `Q-${leadDigitMatch[1]}`;
      } else {
        let idMatch = secId.match(/(?:sec|q)[\-_]*(\d+)/);
        qKey = idMatch ? `Q-${idMatch[1]}` : `Q-${idx + 1}`;
      }
    }

    qMap[qKey] = (qMap[qKey] || 0) + marksVal;
  });

  let list = Object.keys(qMap).map(k => ({ name: k, marks: qMap[k] }));
  if (list.length === 0) {
    list = [{ name: 'Q-1', marks: 18 }, { name: 'Q-2', marks: 17 }, { name: 'Q-3', marks: 25 }];
  }
  const totalCalc = list.reduce((acc, cur) => acc + cur.marks, 0);
  const metaTotalStr = replaceIndic(paper?.metadata?.total_marks || '');
  const metaNum = metaTotalStr.match(/\d+/);
  const total = metaNum ? parseInt(metaNum[0], 10) : (totalCalc || 60);

  return { questions: list, total: total };
}

function getMarksTableQuestions(paper) {
  if (paper && Array.isArray(paper.custom_marks_table) && paper.custom_marks_table.length > 0) {
    return paper.custom_marks_table;
  }
  const qSum = calcQuestionSummary(paper);
  if (paper && !paper.custom_marks_table) {
    paper.custom_marks_table = qSum.questions;
  }
  return paper ? paper.custom_marks_table : qSum.questions;
}

function toggleAssessmentMarksTable() {
  if (!paperData) return;
  paperData.show_marks_table = (paperData.show_marks_table === false) ? true : false;
  saveToLocal();
  renderEditorAssessmentTable();
}

function renderEditorAssessmentTable() {
  const marksContainer = document.getElementById('editorMarksTableContainer');
  const btnToggle = document.getElementById('btnToggleMarksTable');
  if (!marksContainer || !paperData) return;

  if (paperData.show_marks_table === false) {
    if (btnToggle) {
      btnToggle.className = 'btn btn-outline-primary btn-sm';
      btnToggle.innerHTML = '<i class="fa-solid fa-plus"></i> Restore Table';
      btnToggle.title = 'Restore Question Assessment Marks Table';
    }
    marksContainer.innerHTML = `
      <div style="padding: 14px 16px; background: white; border: 1.5px dashed #cbd5e1; border-radius: 6px; text-align: center; color: var(--slate-600); font-size: 0.85rem;">
        <i class="fa-solid fa-eye-slash" style="color: #94a3b8; font-size: 1.1rem; margin-right: 6px;"></i>
        <span>Assessment Marks Table is <strong>deleted / hidden</strong> from this exam paper output.</span>
        <button type="button" class="btn btn-secondary btn-sm" style="margin-left: 12px; font-size: 0.78rem; padding: 2px 10px;" onclick="toggleAssessmentMarksTable()">
          <i class="fa-solid fa-rotate-left"></i> Restore Table
        </button>
      </div>
    `;
    return;
  }

  if (btnToggle) {
    btnToggle.className = 'btn btn-outline-danger btn-sm';
    btnToggle.innerHTML = '<i class="fa-solid fa-trash"></i> Delete Table';
    btnToggle.title = 'Delete Question Assessment Marks Table from paper';
  }

  const questions = getMarksTableQuestions(paperData);
  const total = questions.reduce((acc, q) => acc + (parseInt(q.marks, 10) || 0), 0);

  // Sync total marks to header field if present
  const metaMarksInput = document.getElementById('metaMarks');
  if (metaMarksInput && !metaMarksInput.matches(':focus')) {
    metaMarksInput.value = total;
  }
  if (paperData.metadata) {
    paperData.metadata.total_marks = String(total);
  }

  let qHeadersHtml = questions.map((q, idx) => `
    <th style="border: 1px solid #cbd5e1; padding: 4px 6px; text-align: center; background: #e2e8f0; font-size: 0.78rem; min-width: 65px;">
      <div style="display: flex; align-items: center; justify-content: center; gap: 3px;">
        <input type="text" value="${q.name}" oninput="updateCustomQuestionName(${idx}, this.value)" 
          style="width: 50px; font-weight: 700; text-align: center; font-size: 0.78rem; padding: 2px 3px; border: 1px solid #94a3b8; border-radius: 3px; background: white; color: #0f172a;" title="Edit Question Name">
        ${questions.length > 1 ? `<button type="button" onclick="deleteCustomQuestionColumn(${idx})" title="Remove Column" style="border: none; background: transparent; color: #ef4444; font-size: 0.75rem; cursor: pointer; padding: 0 2px;"><i class="fa-solid fa-xmark"></i></button>` : ''}
      </div>
    </th>
  `).join('');

  let qBlankCellsHtml = questions.map(() => `<td style="border: 1px solid #cbd5e1; padding: 4px 8px; text-align: center; font-size: 0.78rem; color: #94a3b8;">—</td>`).join('');

  let qMarksHtml = questions.map((q, idx) => `
    <td style="border: 1px solid #cbd5e1; padding: 4px 6px; text-align: center;">
      <input type="number" min="0" max="100" value="${q.marks}" oninput="updateCustomQuestionMarks(${idx}, this.value)" 
        style="width: 50px; font-weight: 700; text-align: center; font-size: 0.82rem; padding: 2px 3px; border: 1px solid #94a3b8; border-radius: 3px; background: white; color: var(--primary-700);" title="Edit Marks for ${q.name}">
    </td>
  `).join('');

  marksContainer.innerHTML = `
    <table style="border-collapse: collapse; width: 100%; border: 1.5px solid #000; text-align: center; background: white;">
      <thead>
        <tr>
          <th style="border: 1.5px solid #000; padding: 6px 10px; text-align: left; background: #e2e8f0; font-size: 0.8rem; white-space: nowrap;">Question</th>
          ${qHeadersHtml}
          <th style="border: 1.5px solid #000; padding: 6px 10px; text-align: center; background: #e2e8f0; font-size: 0.8rem; min-width: 60px;">Total</th>
          <th rowspan="3" style="border: 1.5px solid #000; padding: 0; width: 30px; min-width: 30px; background: #f8fafc;">&nbsp;</th>
          <th style="border: 1.5px solid #000; padding: 6px 10px; text-align: left; background: #e2e8f0; font-size: 0.8rem; white-space: nowrap; width: 110px;">Teacher's Sign</th>
          <th style="border: 1.5px solid #000; padding: 6px 10px; width: 90px; background: #fff;">&nbsp;</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td style="border: 1.5px solid #000; padding: 6px 10px; text-align: left; font-size: 0.8rem; font-weight: 600; white-space: nowrap;">Obtain Marks</td>
          ${qBlankCellsHtml}
          <td style="border: 1.5px solid #000; padding: 6px 10px; text-align: center; font-size: 0.8rem; color: #94a3b8;">&nbsp;</td>
          <td style="border: 1.5px solid #000; padding: 6px 10px; text-align: left; font-size: 0.8rem; font-weight: 600; white-space: nowrap;">Supe. Sign</td>
          <td style="border: 1.5px solid #000; padding: 6px 10px;">&nbsp;</td>
        </tr>
        <tr>
          <td style="border: 1.5px solid #000; padding: 6px 10px; text-align: left; font-size: 0.8rem; font-weight: 600; white-space: nowrap;">Marks</td>
          ${qMarksHtml}
          <td style="border: 1.5px solid #000; padding: 6px 10px; text-align: center; font-weight: 800; font-size: 0.85rem; color: var(--primary-700); background: #f8fafc;">${total}</td>
          <td style="border: 1.5px solid #000; padding: 6px 10px; text-align: left; font-size: 0.8rem; font-weight: 600; white-space: nowrap;">Rechk. Sign</td>
          <td style="border: 1.5px solid #000; padding: 6px 10px;">&nbsp;</td>
        </tr>
      </tbody>
    </table>
  `;
}

function updateCustomQuestionName(idx, val) {
  if (paperData && Array.isArray(paperData.custom_marks_table) && paperData.custom_marks_table[idx]) {
    paperData.custom_marks_table[idx].name = val;
    saveToLocal();
  }
}

function updateCustomQuestionMarks(idx, val) {
  if (paperData && Array.isArray(paperData.custom_marks_table) && paperData.custom_marks_table[idx]) {
    paperData.custom_marks_table[idx].marks = parseInt(val, 10) || 0;
    saveToLocal();
    renderEditorAssessmentTable();
  }
}

function addCustomQuestionColumn() {
  if (!paperData) return;
  if (!Array.isArray(paperData.custom_marks_table)) {
    getMarksTableQuestions(paperData);
  }
  const nextNum = paperData.custom_marks_table.length + 1;
  paperData.custom_marks_table.push({ name: `Q-${nextNum}`, marks: 10 });
  saveToLocal();
  renderEditorAssessmentTable();
  showToast(`Added Q-${nextNum} to Assessment Table`, 'success');
}

function deleteCustomQuestionColumn(idx) {
  if (paperData && Array.isArray(paperData.custom_marks_table) && paperData.custom_marks_table.length > 1) {
    paperData.custom_marks_table.splice(idx, 1);
    saveToLocal();
    renderEditorAssessmentTable();
  }
}

function autoSyncMarksTableFromSections() {
  if (!paperData) return;
  const qSum = calcQuestionSummary(paperData);
  paperData.custom_marks_table = qSum.questions;
  saveToLocal();
  renderEditorAssessmentTable();
  showToast('Assessment Table auto-synced with questions below!', 'info');
}

// ==================== MATH FRACTIONS FORMATTER ====================
function formatMathFractions(text) {
  if (!text) return '';
  let s = String(text);

  // Escape HTML entities for safety except our span replacements
  s = s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  // Replace LaTeX \frac{num}{den}
  s = s.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '<span class="math-fraction"><span class="num">$1</span><span class="den">$2</span></span>');

  // Replace standard inline fractions: (\d+)/(\d+)
  // e.g. 3/4, 7/4, 5071/1000, 15/24, 2/7, 5/9
  s = s.replace(/(^|[\s\+\-\=\(\[\,\:\;\&])(\d+)\/(\d+)(?![\/\d])/g, '$1<span class="math-fraction"><span class="num">$2</span><span class="den">$3</span></span>');

  return s;
}

function updateQuestionLivePreview(sIdx, qIdx) {
  const previewEl = document.getElementById(`q_preview_${sIdx}_${qIdx}`);
  if (!previewEl || !paperData?.sections?.[sIdx]?.questions?.[qIdx]) return;

  const q = paperData.sections[sIdx].questions[qIdx];
  const sec = paperData.sections[sIdx];
  
  const effectiveLayout = q.options_layout || sec.options_layout || sec.subquestions_layout || 'horizontal';
  const isTwoCol = ['two_columns', '2_columns', '2col', 'two-columns'].includes(effectiveLayout);
  const isVert = ['vertical', 'stacked', '1_col'].includes(effectiveLayout);
  let optGridCols = isTwoCol ? 'repeat(2, 1fr)' : (isVert ? '1fr' : `repeat(${q.options?.length || 4}, 1fr)`);

  let html = `<div style="font-weight: 600;">${formatMathFractions(q.text || 'Question...')}</div>`;
  const hasOpts = Array.isArray(q.options) && q.options.length > 0;
  if ((sec.type === 'mcq' || hasOpts) && q.options) {
    html += `
      <div class="math-options-grid" style="display: grid; grid-template-columns: ${optGridCols}; gap: 8px;">
        ${q.options.map(opt => `<div>${formatMathFractions(opt)}</div>`).join('')}
      </div>
    `;
  }
  previewEl.innerHTML = html;
}

// ==================== RENDER EDITOR UI ====================
function renderEditor() {
  if (!paperData) return;

  const meta = paperData.metadata || {};
  if (document.getElementById('metaExamTitle')) document.getElementById('metaExamTitle').value = meta.exam_title || '';
  if (document.getElementById('metaStandard')) document.getElementById('metaStandard').value = meta.standard || '';
  if (document.getElementById('metaSubject')) document.getElementById('metaSubject').value = meta.subject || '';
  if (document.getElementById('metaMarks')) document.getElementById('metaMarks').value = meta.total_marks || '';
  if (document.getElementById('metaDate')) document.getElementById('metaDate').value = meta.date || '';
  if (document.getElementById('metaDay')) document.getElementById('metaDay').value = meta.day || '';
  if (document.getElementById('metaRollNo')) document.getElementById('metaRollNo').value = meta.roll_no || '';

  renderEditorAssessmentTable();

  const container = document.getElementById('sectionsContainer');
  if (!container) return;
  container.innerHTML = '';

  const sections = paperData.sections || [];
  if (sections.length === 0) {
    const stored = JSON.parse(localStorage.getItem('uploaded_images') || '[]');
    const count = stored.length || (typeof uploadedImages !== 'undefined' ? uploadedImages.length : 0);
    container.innerHTML = `
      <div style="background: white; border: 2px dashed #cbd5e1; border-radius: 12px; padding: 48px 24px; text-align: center; margin-top: 10px; box-shadow: var(--shadow-sm);">
        <div style="width: 60px; height: 60px; background: #e0f2fe; color: #0284c7; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.6rem; margin: 0 auto 16px;">
          <i class="fa-solid fa-cloud-arrow-up"></i>
        </div>
        <h3 style="font-size: 1.25rem; font-weight: 800; color: #0f172a; margin-bottom: 8px;">
          ${count > 0 ? `${count} Document Page(s) Uploaded!` : 'Ready for New Exam Paper'}
        </h3>
        <p style="color: #64748b; font-size: 0.95rem; max-width: 520px; margin: 0 auto 24px; line-height: 1.5;">
          ${count > 0 
            ? `Old questions have been reset. Click <strong>"Scan All (${count} Pages)"</strong> to automatically extract questions with AI Multilingual OCR, or add your questions manually.` 
            : `Upload your handwritten exam pages on the left, or click "Add Section" to manually create questions.`}
        </p>
        <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
          ${count > 0 ? `
            <button type="button" class="btn btn-primary" onclick="triggerAiScan(false)" style="background: linear-gradient(135deg, #06b6d4, #2563eb); border: none; font-weight: 700; padding: 10px 20px;">
              <i class="fa-solid fa-wand-magic-sparkles"></i> Scan All (${count} Pages) with AI OCR
            </button>
          ` : `
            <button type="button" class="btn btn-primary" onclick="document.getElementById('editorFileInput').click()" style="padding: 10px 20px;">
              <i class="fa-solid fa-cloud-arrow-up"></i> Upload Document Pages
            </button>
          `}
          <button type="button" class="btn btn-secondary" onclick="addNewSection()" style="padding: 10px 18px;">
            <i class="fa-solid fa-plus"></i> Add Section Manually
          </button>
          <button type="button" class="btn btn-secondary" onclick="resetToSamplePaper()" style="padding: 10px 18px;" title="Load the preloaded Std. 6 Mathematics exam">
            <i class="fa-solid fa-book-open"></i> Load Sample Exam
          </button>
        </div>
      </div>
    `;
    return;
  }

  sections.forEach((sec, sIdx) => {
    const card = document.createElement('div');
    card.className = 'section-card';
    card.id = `sec_card_${sIdx}`;

    // Header bar
    const headerBar = document.createElement('div');
    headerBar.className = 'section-header-bar';
    headerBar.innerHTML = `
      <div style="flex: 1; display: flex; gap: 10px; align-items: center;">
        <input type="text" class="section-title-input" value="${sec.title || ''}" placeholder="Section Title (e.g. Q-1 (A) Choose the correct answer)" onchange="updateSectionTitle(${sIdx}, this.value)">
      </div>
      <div style="display: flex; gap: 8px; align-items: center;">
        <select class="input-control" style="width: auto; font-size: 0.8rem; padding: 2px 6px; font-weight: 600;" onchange="updateSectionType(${sIdx}, this.value)" title="Section Type">
          <option value="mcq" ${sec.type === 'mcq' ? 'selected' : ''}>MCQ / Options</option>
          <option value="fill_in_blanks" ${sec.type === 'fill_in_blanks' ? 'selected' : ''}>Fill in Blanks</option>
          <option value="true_false" ${sec.type === 'true_false' ? 'selected' : ''}>True / False</option>
          <option value="general" ${sec.type === 'general' ? 'selected' : ''}>General / Math</option>
        </select>
        <input type="text" class="section-marks-input" value="${sec.marks || ''}" placeholder="Marks e.g. (5)" onchange="updateSectionMarks(${sIdx}, this.value)">
        <button type="button" class="btn btn-sm btn-danger" style="padding: 2px 6px; font-size: 0.8rem;" onclick="deleteSection(${sIdx})" title="Delete Section"><i class="fa-solid fa-trash"></i></button>
      </div>
    `;
    card.appendChild(headerBar);

    // Section Body
    const body = document.createElement('div');
    body.className = 'section-body';

    // Options box editor
    if (sec.type === 'fill_in_blanks' || sec.options_box) {
      body.innerHTML += `
        <div class="field-group">
          <label class="field-label">Options Box Words</label>
          <input type="text" class="input-control" value="${sec.options_box || ''}" onchange="updateOptionsBox(${sIdx}, this.value)">
        </div>
      `;
    }

    // Intro text editor
    if (sec.intro_text !== undefined) {
      body.innerHTML += `
        <div class="field-group">
          <label class="field-label">Section Introduction / Prompt</label>
          <textarea class="input-control" rows="2" onchange="updateIntroText(${sIdx}, this.value)">${sec.intro_text || ''}</textarea>
        </div>
      `;
    }

    // Section Diagram / Figure Selector
    const secDiagram = sec.diagram_type || '';
    const secDiagPreview = secDiagram === 'geometry_lines' ? '<img src="/static/img/figure_q3c.png" style="max-height: 70px; border: 1px solid #cbd5e1; border-radius: 4px; margin-top: 6px;">' :
      (secDiagram === 'zigzag' ? '<img src="/static/img/figure_q3a3.png" style="max-height: 60px; border: 1px solid #cbd5e1; border-radius: 4px; margin-top: 6px;">' :
      (secDiagram === 'pictograph' ? '<img src="/static/img/pictograph_clean.png" style="max-height: 80px; border: 1px solid #cbd5e1; border-radius: 4px; margin-top: 6px;">' : ''));
    const secLayout = sec.diagram_layout || 'side_by_side';

    body.innerHTML += `
      <div class="field-group" style="margin-bottom: 12px; background: #f8fafc; padding: 8px 10px; border-radius: 6px; border: 1px solid #e2e8f0;">
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap;">
          <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
            <label class="field-label" style="margin: 0; font-weight: 700; color: #1e293b;"><i class="fa-solid fa-shapes" style="color: var(--primary-600);"></i> Section Diagram / Figure:</label>
            <select class="input-control" style="width: auto; font-size: 0.82rem; padding: 3px 8px; font-weight: 600;" onchange="updateSectionDiagramType(${sIdx}, this.value)">
              <option value="" ${!secDiagram ? 'selected' : ''}>— None —</option>
              <option value="geometry_lines" ${secDiagram === 'geometry_lines' ? 'selected' : ''}>📐 Geometry: Intersecting Lines & Rays (G-A-C-E, Ray AB, Line FD)</option>
              <option value="zigzag" ${secDiagram === 'zigzag' ? 'selected' : ''}>📐 Geometry: Zigzag Polyline (L-M-P-Q-R)</option>
              <option value="pictograph" ${secDiagram === 'pictograph' ? 'selected' : ''}>📊 Chart: Pictograph (Girl Students)</option>
            </select>
          </div>
          ${secDiagram ? `
          <div style="display: flex; align-items: center; gap: 6px;">
            <label class="field-label" style="margin: 0; font-size: 0.78rem; font-weight: 700; color: #475569;">Layout:</label>
            <select class="input-control" style="width: auto; font-size: 0.78rem; padding: 2px 6px; font-weight: 600;" onchange="updateSectionDiagramLayout(${sIdx}, this.value)" title="Choose options and diagram layout">
              <option value="side_by_side" ${secLayout !== 'stacked' ? 'selected' : ''}>Options Left, Figure Right (Space Saver)</option>
              <option value="stacked" ${secLayout === 'stacked' ? 'selected' : ''}>Figure Centered, Options Below</option>
            </select>
          </div>
          ` : ''}
        </div>
        ${secDiagPreview ? `<div style="text-align: center; margin-top: 6px;">${secDiagPreview}</div>` : ''}
      </div>
    `;

    // Section Options / Sub-questions Layout Selector
    const secOptLayout = sec.options_layout || sec.subquestions_layout || 'horizontal';
    const isSecTwoCol = ['two_columns', '2_columns', '2col', 'two-columns'].includes(secOptLayout);
    const hasSecOpts = (sec.questions || []).some(q => q.options && q.options.length > 0);
    body.innerHTML += `
      <div class="field-group" style="margin-bottom: 12px; background: #f8fafc; padding: 8px 10px; border-radius: 6px; border: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
          <label class="field-label" style="margin: 0; font-weight: 700; color: #1e293b;">
            <i class="fa-solid fa-table-columns" style="color: var(--primary-600);"></i> ${(sec.type === 'mcq' || hasSecOpts) ? 'MCQ Options Layout:' : 'Sub-Questions Layout:'}
          </label>
          <select class="input-control" style="width: auto; font-size: 0.82rem; padding: 3px 8px; font-weight: 600;" onchange="updateSectionOptionsLayout(${sIdx}, this.value)">
            <option value="horizontal" ${(!isSecTwoCol && secOptLayout !== 'vertical') ? 'selected' : ''}>Horizontal (1 Row - Side-by-side across page)</option>
            <option value="two_columns" ${isSecTwoCol ? 'selected' : ''}>2 Columns (Side-by-Side / 2x2 Grid)</option>
            <option value="vertical" ${secOptLayout === 'vertical' ? 'selected' : ''}>Vertical (Stacked - 1 per line)</option>
          </select>
        </div>
        <span style="font-size: 0.76rem; color: #64748b;">Controls 2-column or horizontal grid for options and sub-questions in docx, pdf & preview</span>
      </div>
    `;

    // Table Data Editor (e.g. Q-2 (B) Complete the following table)
    if (sec.table_data) {
      const tblDiv = document.createElement('div');
      tblDiv.style.marginBottom = '14px';
      tblDiv.style.background = '#f8fafc';
      tblDiv.style.border = '1px solid #cbd5e1';
      tblDiv.style.borderRadius = '6px';
      tblDiv.style.padding = '10px';

      const headers = sec.table_data.headers || [];
      const rows = sec.table_data.rows || [];

      let tableHtml = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <strong style="font-size: 0.85rem; color: #334155;"><i class="fa-solid fa-table"></i> Section Table Editor</strong>
          <button type="button" class="btn btn-secondary btn-sm" style="padding: 2px 8px; font-size: 0.78rem;" onclick="addTableRow(${sIdx})"><i class="fa-solid fa-plus"></i> Add Row</button>
        </div>
        <div style="overflow-x: auto;">
          <table style="width: 100%; border-collapse: collapse; font-size: 0.82rem; background: white;">
            <thead>
              <tr style="background: #e2e8f0;">
                ${headers.map((h, hIdx) => `
                  <th style="border: 1px solid #cbd5e1; padding: 4px 6px;">
                    <input type="text" style="width: 100%; border: none; background: transparent; font-weight: bold; text-align: center;" value="${h}" onchange="updateTableHeader(${sIdx}, ${hIdx}, this.value)">
                  </th>
                `).join('')}
                <th style="border: 1px solid #cbd5e1; padding: 4px; width: 30px;"></th>
              </tr>
            </thead>
            <tbody>
              ${rows.map((row, rIdx) => `
                <tr>
                  ${headers.map((_, cIdx) => `
                    <td style="border: 1px solid #cbd5e1; padding: 4px 6px;">
                      <input type="text" style="width: 100%; border: none; background: transparent; text-align: ${cIdx===1?'left':'center'};" value="${row[cIdx] || ''}" onchange="updateTableCell(${sIdx}, ${rIdx}, ${cIdx}, this.value)">
                    </td>
                  `).join('')}
                  <td style="border: 1px solid #cbd5e1; padding: 2px; text-align: center;">
                    <button type="button" style="border: none; background: transparent; color: #ef4444; cursor: pointer;" onclick="deleteTableRow(${sIdx}, ${rIdx})"><i class="fa-solid fa-trash-can"></i></button>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
      tblDiv.innerHTML = tableHtml;
      body.appendChild(tblDiv);
    }

    // Questions List
    const qList = document.createElement('div');
    qList.style.marginTop = '12px';

    (sec.questions || []).forEach((q, qIdx) => {
      const qRow = document.createElement('div');
      qRow.style.padding = '10px 12px';
      qRow.style.background = 'white';
      qRow.style.border = '1px solid #e2e8f0';
      qRow.style.borderRadius = '6px';
      qRow.style.marginBottom = '10px';

      const effectiveLayout = q.options_layout || sec.options_layout || sec.subquestions_layout || 'horizontal';
      const isQTwoCol = ['two_columns', '2_columns', '2col', 'two-columns'].includes(effectiveLayout);
      const isQVert = ['vertical', 'stacked', '1_col'].includes(effectiveLayout);
      let optGridCols = isQTwoCol ? 'repeat(2, 1fr)' : (isQVert ? '1fr' : `repeat(${q.options?.length || 4}, 1fr)`);

      const hasQOpts = Array.isArray(q.options) && q.options.length > 0;
      let extraContent = '';
      if (sec.type === 'mcq' || hasQOpts) {
        if (!q.options || q.options.length === 0) {
          q.options = ['(A) ', '(B) ', '(C) ', '(D) '];
        }
        extraContent = `
          <div style="display: grid; grid-template-columns: ${optGridCols}; gap: 6px; margin-top: 8px;">
            ${q.options.map((opt, oIdx) => `
              <input type="text" class="input-control" style="font-size: 0.82rem; padding: 4px 6px;" value="${opt}" oninput="handleOptionInput(${sIdx}, ${qIdx}, ${oIdx}, this.value)">
            `).join('')}
          </div>
        `;
      }

      const qDiag = q.diagram_type || '';
      const qDiagImg = qDiag === 'zigzag' ? '<img src="/static/img/figure_q3a3.png" style="max-height: 55px; border: 1px solid #cbd5e1; border-radius: 4px; display: block; margin: 6px auto;">' :
        (qDiag === 'geometry_lines' ? '<img src="/static/img/figure_q3c.png" style="max-height: 65px; border: 1px solid #cbd5e1; border-radius: 4px; display: block; margin: 6px auto;">' :
        (qDiag === 'pictograph' ? '<img src="/static/img/pictograph_clean.png" style="max-height: 75px; border: 1px solid #cbd5e1; border-radius: 4px; display: block; margin: 6px auto;">' : ''));

      // Live formatted math preview
      const previewHtml = `
        <div class="math-preview-card" id="q_preview_${sIdx}_${qIdx}">
          <div style="font-weight: 600;">${formatMathFractions(q.text || 'Question...')}</div>
          ${qDiagImg}
          ${(sec.type === 'mcq' || hasQOpts) && q.options ? `
            <div class="math-options-grid" style="display: grid; grid-template-columns: ${optGridCols}; gap: 8px;">
              ${q.options.map(opt => `<div>${formatMathFractions(opt)}</div>`).join('')}
            </div>
          ` : ''}
        </div>
      `;

      qRow.innerHTML = `
        <div style="display: flex; gap: 8px; align-items: flex-start;">
          <span style="font-weight: 700; color: #64748b; font-size: 0.85rem; padding-top: 6px;">#${qIdx+1}</span>
          <div style="flex: 1;">
            <textarea class="input-control" rows="1" style="width: 100%; font-family: monospace; font-size: 0.88rem;" oninput="handleQuestionTextInput(${sIdx}, ${qIdx}, this.value)">${q.text || ''}</textarea>
            
            <div style="display: flex; justify-content: space-between; align-items: center; margin: 4px 0; flex-wrap: wrap; gap: 8px;">
              <div style="display: flex; align-items: center; gap: 6px; font-size: 0.78rem; color: #475569;">
                <span><i class="fa-solid fa-shapes"></i> Question Figure:</span>
                <select style="font-size: 0.76rem; padding: 2px 4px; border: 1px solid #cbd5e1; border-radius: 4px; background: #f8fafc;" onchange="updateQuestionDiagramType(${sIdx}, ${qIdx}, this.value)">
                  <option value="" ${!qDiag ? 'selected' : ''}>None</option>
                  <option value="zigzag" ${qDiag === 'zigzag' ? 'selected' : ''}>Zigzag Polyline (L-M-P-Q-R)</option>
                  <option value="geometry_lines" ${qDiag === 'geometry_lines' ? 'selected' : ''}>Intersecting Lines & Rays</option>
                  <option value="pictograph" ${qDiag === 'pictograph' ? 'selected' : ''}>Pictograph Chart</option>
                </select>
              </div>
              ${(sec.type === 'mcq' || hasQOpts) ? `
              <div style="display: flex; align-items: center; gap: 6px; font-size: 0.78rem; color: #475569;">
                <span><i class="fa-solid fa-table-columns"></i> Layout:</span>
                <select style="font-size: 0.76rem; padding: 2px 4px; border: 1px solid #cbd5e1; border-radius: 4px; background: #f8fafc; font-weight: 600;" onchange="updateQuestionOptionsLayout(${sIdx}, ${qIdx}, this.value)">
                  <option value="" ${!q.options_layout ? 'selected' : ''}>Default (${isSecTwoCol ? '2 Cols' : (secOptLayout === 'vertical' ? 'Vertical' : 'Horizontal')})</option>
                  <option value="horizontal" ${q.options_layout === 'horizontal' ? 'selected' : ''}>Horizontal (1 Row)</option>
                  <option value="two_columns" ${['two_columns', '2_columns', '2col', 'two-columns'].includes(q.options_layout) ? 'selected' : ''}>2 Columns (Side-by-Side)</option>
                  <option value="vertical" ${q.options_layout === 'vertical' ? 'selected' : ''}>Vertical (Stacked)</option>
                </select>
              </div>
              ` : ''}
            </div>

            ${previewHtml}
          </div>
          <button type="button" class="btn btn-sm btn-secondary" style="padding: 4px 6px;" onclick="deleteQuestion(${sIdx}, ${qIdx})" title="Delete question"><i class="fa-solid fa-times"></i></button>
        </div>
        ${extraContent}
      `;
      qList.appendChild(qRow);
    });

    body.appendChild(qList);

    // Add Question Button
    const addQBtn = document.createElement('button');
    addQBtn.type = 'button';
    addQBtn.className = 'btn btn-secondary btn-sm';
    addQBtn.style.marginTop = '6px';
    addQBtn.innerHTML = '<i class="fa-solid fa-plus"></i> Add Question';
    addQBtn.onclick = () => addQuestion(sIdx);
    body.appendChild(addQBtn);

    card.appendChild(body);
    container.appendChild(card);
  });
}

function updateSectionDiagramType(sIdx, val) {
  if (paperData && paperData.sections[sIdx]) {
    if (val) {
      paperData.sections[sIdx].diagram_type = val;
      if (!paperData.sections[sIdx].diagram_layout) {
        paperData.sections[sIdx].diagram_layout = 'side_by_side';
      }
    } else {
      delete paperData.sections[sIdx].diagram_type;
    }
    saveToLocal();
    renderEditor();
  }
}

function updateSectionDiagramLayout(sIdx, val) {
  if (paperData && paperData.sections[sIdx]) {
    paperData.sections[sIdx].diagram_layout = val;
    saveToLocal();
    renderEditor();
  }
}

function updateSectionOptionsLayout(sIdx, val) {
  if (paperData && paperData.sections[sIdx]) {
    paperData.sections[sIdx].options_layout = val;
    paperData.sections[sIdx].subquestions_layout = val;
    // Clear question-level overrides so all questions follow the chosen section layout
    if (Array.isArray(paperData.sections[sIdx].questions)) {
      paperData.sections[sIdx].questions.forEach(q => {
        delete q.options_layout;
      });
    }
    saveToLocal();
    renderEditor();
  }
}

function updateSectionType(sIdx, val) {
  if (paperData && paperData.sections[sIdx]) {
    paperData.sections[sIdx].type = val;
    saveToLocal();
    renderEditor();
  }
}

function updateQuestionOptionsLayout(sIdx, qIdx, val) {
  if (paperData?.sections?.[sIdx]?.questions?.[qIdx]) {
    if (val) {
      paperData.sections[sIdx].questions[qIdx].options_layout = val;
    } else {
      delete paperData.sections[sIdx].questions[qIdx].options_layout;
    }
    saveToLocal();
    renderEditor();
  }
}

function updateQuestionDiagramType(sIdx, qIdx, val) {
  if (paperData?.sections?.[sIdx]?.questions?.[qIdx]) {
    if (val) {
      paperData.sections[sIdx].questions[qIdx].diagram_type = val;
    } else {
      delete paperData.sections[sIdx].questions[qIdx].diagram_type;
    }
    saveToLocal();
    renderEditor();
  }
}

function handleQuestionTextInput(sIdx, qIdx, val) {
  if (paperData?.sections?.[sIdx]?.questions?.[qIdx]) {
    paperData.sections[sIdx].questions[qIdx].text = val;
    saveToLocal();
    updateQuestionLivePreview(sIdx, qIdx);
  }
}

function handleOptionInput(sIdx, qIdx, oIdx, val) {
  if (paperData?.sections?.[sIdx]?.questions?.[qIdx]?.options) {
    paperData.sections[sIdx].questions[qIdx].options[oIdx] = val;
    saveToLocal();
    updateQuestionLivePreview(sIdx, qIdx);
  }
}

function updateTableHeader(sIdx, hIdx, val) {
  if (paperData?.sections?.[sIdx]?.table_data?.headers) {
    paperData.sections[sIdx].table_data.headers[hIdx] = val;
    saveToLocal();
  }
}

function updateTableCell(sIdx, rIdx, cIdx, val) {
  if (paperData?.sections?.[sIdx]?.table_data?.rows?.[rIdx]) {
    paperData.sections[sIdx].table_data.rows[rIdx][cIdx] = val;
    saveToLocal();
  }
}

function addTableRow(sIdx) {
  if (paperData?.sections?.[sIdx]?.table_data) {
    const numCols = paperData.sections[sIdx].table_data.headers?.length || 4;
    const newRow = Array(numCols).fill('');
    if (!paperData.sections[sIdx].table_data.rows) paperData.sections[sIdx].table_data.rows = [];
    paperData.sections[sIdx].table_data.rows.push(newRow);
    saveToLocal();
    renderEditor();
  }
}

function deleteTableRow(sIdx, rIdx) {
  if (paperData?.sections?.[sIdx]?.table_data?.rows) {
    paperData.sections[sIdx].table_data.rows.splice(rIdx, 1);
    saveToLocal();
    renderEditor();
  }
}

function updateSectionTitle(sIdx, val) {
  if (paperData && paperData.sections[sIdx]) {
    paperData.sections[sIdx].title = val;
    saveToLocal();
    renderEditorAssessmentTable();
  }
}

function updateSectionMarks(sIdx, val) {
  if (paperData && paperData.sections[sIdx]) {
    paperData.sections[sIdx].marks = val;
    saveToLocal();
    renderEditorAssessmentTable();
  }
}

function updateOptionsBox(sIdx, val) {
  if (paperData && paperData.sections[sIdx]) {
    paperData.sections[sIdx].options_box = val;
    saveToLocal();
  }
}

function updateIntroText(sIdx, val) {
  if (paperData && paperData.sections[sIdx]) {
    paperData.sections[sIdx].intro_text = val;
    saveToLocal();
  }
}

function updateQuestionText(sIdx, qIdx, val) {
  if (paperData && paperData.sections[sIdx] && paperData.sections[sIdx].questions[qIdx]) {
    paperData.sections[sIdx].questions[qIdx].text = val;
    saveToLocal();
  }
}

function updateMcqOption(sIdx, qIdx, oIdx, val) {
  if (paperData && paperData.sections[sIdx]?.questions[qIdx]?.options) {
    paperData.sections[sIdx].questions[qIdx].options[oIdx] = val;
    saveToLocal();
  }
}

function addQuestion(sIdx) {
  if (paperData && paperData.sections[sIdx]) {
    if (!paperData.sections[sIdx].questions) paperData.sections[sIdx].questions = [];
    paperData.sections[sIdx].questions.push({ text: 'New Question...' });
    saveToLocal();
    renderEditor();
  }
}

function deleteQuestion(sIdx, qIdx) {
  if (paperData && paperData.sections[sIdx]?.questions) {
    paperData.sections[sIdx].questions.splice(qIdx, 1);
    saveToLocal();
    renderEditor();
  }
}

function addNewSection() {
  if (!paperData) return;
  if (!paperData.sections) paperData.sections = [];
  paperData.sections.push({
    title: `Q.${paperData.sections.length + 1} New Section:`,
    marks: '(4)',
    type: 'general',
    questions: [{ text: '1. Example question text...' }]
  });
  saveToLocal();
  renderEditor();
  showToast('New section added', 'success');
}

function deleteSection(sIdx) {
  if (confirm('Delete this entire section?')) {
    paperData.sections.splice(sIdx, 1);
    saveToLocal();
    renderEditor();
    showToast('Section deleted', 'info');
  }
}


function exportDocx() {
  if (typeof syncFormToState === 'function') {
    syncFormToState();
  }
  
  // Prefer the freshest state in localStorage if available
  const local = localStorage.getItem('current_paper');
  if (local) {
    try {
      const parsed = JSON.parse(local);
      if (parsed && Array.isArray(parsed.sections) && parsed.sections.length > 0) {
        paperData = parsed;
      }
    } catch (e) {
      console.error('Error reading current_paper from localStorage', e);
    }
  }

  if (!paperData || !Array.isArray(paperData.sections) || paperData.sections.length === 0) {
    showToast('No questions found to export. Please load or build an exam paper first.', 'error');
    return;
  }
  
  const btn = document.getElementById('btnExportDocx') || document.getElementById('btnPreviewDocx');
  const origHtml = btn ? btn.innerHTML : '';
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating Word...';
  }

  showToast('Generating formatted Word (.docx) document...', 'info');

  fetch('/api/generate-docx', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ paper: paperData })
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      showToast('Word document created! Downloading...', 'success');
      triggerDownload(data.download_url, data.filename);
    } else {
      showToast('Error creating Word doc: ' + (data.error || 'Unknown error'), 'error');
    }
  })
  .catch(err => {
    showToast('Request failed: ' + err.message, 'error');
  })
  .finally(() => {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = origHtml;
    }
  });
}

function exportPdf() {
  if (typeof syncFormToState === 'function') {
    syncFormToState();
  }

  // Prefer the freshest state in localStorage if available
  const local = localStorage.getItem('current_paper');
  if (local) {
    try {
      const parsed = JSON.parse(local);
      if (parsed && Array.isArray(parsed.sections) && parsed.sections.length > 0) {
        paperData = parsed;
      }
    } catch (e) {
      console.error('Error reading current_paper from localStorage', e);
    }
  }

  if (!paperData || !Array.isArray(paperData.sections) || paperData.sections.length === 0) {
    showToast('No questions found to export. Please load or build an exam paper first.', 'error');
    return;
  }

  const btn = document.getElementById('btnExportPdf') || document.getElementById('btnPreviewPdf');
  const origHtml = btn ? btn.innerHTML : '';
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating PDF...';
  }

  showToast('Generating print-ready PDF...', 'info');

  fetch('/api/generate-pdf', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ paper: paperData })
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      showToast('PDF created successfully! Downloading...', 'success');
      triggerDownload(data.download_url, data.filename);
    } else {
      showToast('Error creating PDF: ' + (data.error || 'Unknown error'), 'error');
    }
  })
  .catch(err => {
    showToast('Request failed: ' + err.message, 'error');
  })
  .finally(() => {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = origHtml;
    }
  });
}

// Auto-sync paper to localStorage whenever navigating or unloading
window.addEventListener('beforeunload', () => {
  if (typeof syncFormToState === 'function') {
    saveToLocal();
  }
});

window.addEventListener('pagehide', () => {
  if (typeof syncFormToState === 'function') {
    saveToLocal();
  }
});

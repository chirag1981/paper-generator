document.addEventListener('DOMContentLoaded', () => {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');
  const uploadProgress = document.getElementById('uploadProgress');
  const progressBar = document.getElementById('progressBar');
  const uploadStatusText = document.getElementById('uploadStatusText');
  const langSelect = document.getElementById('uploadLangSelect');

  if (!dropzone || !fileInput) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('drag-over');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('drag-over');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      handleFiles(files);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (fileInput.files.length > 0) {
      handleFiles(fileInput.files);
    }
  });

  function handleFiles(files) {
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    uploadProgress.style.display = 'block';
    progressBar.style.width = '20%';
    uploadStatusText.innerText = `Uploading and processing ${files.length} file(s)...`;

    const selectedLang = langSelect ? langSelect.value : 'auto';
    localStorage.setItem('selected_ocr_lang', selectedLang);

    fetch('/api/upload', {
      method: 'POST',
      body: formData
    })
    .then(r => r.json())
    .then(data => {
      progressBar.style.width = '100%';
      if (data.success) {
        uploadStatusText.innerText = 'Upload complete! Launching live editor...';
        showToast(data.message, 'success');
        
        // Reset previous paper structure so old questions from previous paper do not persist
        const freshPaper = {
          metadata: {
            exam_title: "Uploaded Exam Paper",
            standard: "Std. ",
            subject: "",
            total_marks: "",
            time_limit: "2 Hours"
          },
          sections: [],
          custom_marks_table: []
        };
        localStorage.setItem('current_paper', JSON.stringify(freshPaper));
        localStorage.setItem('is_new_upload', 'true');
        
        // Save newly uploaded files to local session storage
        localStorage.setItem('uploaded_images', JSON.stringify(data.files));
        localStorage.setItem('auto_trigger_ocr', 'true');

        setTimeout(() => {
          window.location.href = '/editor';
        }, 700);
      } else {
        showToast(data.error || 'Upload failed', 'error');
        uploadProgress.style.display = 'none';
      }
    })
    .catch(err => {
      showToast('Network error during upload: ' + err.message, 'error');
      uploadProgress.style.display = 'none';
    });
  }
});

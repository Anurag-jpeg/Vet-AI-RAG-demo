
const uploadForm = document.getElementById('upload-form');
const pdfInput = document.getElementById('pdf-input');
const uploadStatus = document.getElementById('upload-status');

const askBtn = document.getElementById('ask-btn');
const questionEl = document.getElementById('question');
const answerBox = document.getElementById('answer');
const kSlider = document.getElementById('k-slider');
const kValue = document.getElementById('k-value');

function showMessage(el, msg, isError = false) {
  el.textContent = msg;
  el.style.color = isError ? '#e74c3c' : '#27ae60';
}

uploadForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const file = pdfInput.files[0];
  if (!file) {
    showMessage(uploadStatus, 'Please select a PDF file.', true);
    return;
  }
  const formData = new FormData();
  formData.append('file', file);
  try {
    showMessage(uploadStatus, 'Uploading …');
    const resp = await fetch('/api/upload', {
      method: 'POST',
      body: formData,
    });
    const data = await resp.json();
    if (resp.ok) {
      showMessage(uploadStatus, data.message);
    } else {
      showMessage(uploadStatus, data.detail || 'Upload failed.', true);
    }
  } catch (err) {
    console.error(err);
    showMessage(uploadStatus, 'Network error.', true);
  }
});

// --------------------------------------------------------------
// Question / answer handler
askBtn.addEventListener('click', async () => {
  const question = questionEl.value.trim();
  const k = parseInt(kSlider.value, 10);
  if (!question) {
    showMessage(answerBox, 'Please type a question.', true);
    return;
  }
  answerBox.textContent = 'Thinking …';
  try {
    const resp = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, k }),
    });
    const data = await resp.json();
    if (resp.ok) {
      answerBox.textContent = data.answer;
    } else {
      answerBox.textContent = data.detail || 'Error while answering.';
      answerBox.style.color = '#e74c3c';
    }
  } catch (err) {
    console.error(err);
    answerBox.textContent = 'Network error.';
    answerBox.style.color = '#e74c3c';
  }
});

// Update the visible "k" value while the slider moves
kSlider.addEventListener('input', () => {
  kValue.textContent = kSlider.value;
});

const uploadForm = document.getElementById('upload-form');
const pdfInput = document.getElementById('pdf-input');
const uploadStatus = document.getElementById('upload-status');

const askBtn = document.getElementById('ask-btn');
const questionEl = document.getElementById('question');
const answerBox = document.getElementById('answer');
const kSlider = document.getElementById('k-slider');
const kValue = document.getElementById('k-value');

function setMessage(el, msg, type = 'info') {
  // type: 'info' (default), 'error', 'success'
  el.textContent = msg;
  el.style.color = type === 'error' ? '#e53935' : type === 'success' ? '#43a047' : 'inherit';
}

uploadForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const file = pdfInput.files[0];
  if (!file) {
    setMessage(uploadStatus, 'Please select a PDF file.', 'error');
    return;
  }
  const formData = new FormData();
  formData.append('file', file);
  try {
    setMessage(uploadStatus, 'Uploading…');
    const resp = await fetch('/api/upload', { method: 'POST', body: formData });
    const data = await resp.json();
    if (resp.ok) {
      setMessage(uploadStatus, data.message, 'success');
    } else {
      setMessage(uploadStatus, data.detail || 'Upload failed.', 'error');
    }
  } catch (err) {
    console.error(err);
    setMessage(uploadStatus, 'Network error.', 'error');
  }
});

askBtn.addEventListener('click', async () => {
  const question = questionEl.value.trim();
  const k = parseInt(kSlider.value, 10);
  if (!question) {
    setMessage(answerBox, 'Please type a question.', 'error');
    return;
  }
  answerBox.textContent = 'Thinking…';
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
      answerBox.style.color = '#e53935';
    }
  } catch (err) {
    console.error(err);
    answerBox.textContent = 'Network error.';
    answerBox.style.color = '#e53935';
  }
});

kSlider.addEventListener('input', () => {
  kValue.textContent = kSlider.value;
});

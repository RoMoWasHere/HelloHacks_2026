// Backend endpoint (FastAPI running locally)
const API_URL = 'http://localhost:8000/v1/analyze';

// Restore saved text and save on every edit so it survives closing the popup
const textBox = document.getElementById('textBox');

chrome.storage.local.get('textBoxContent', ({ textBoxContent }) => {
  textBox.value = textBoxContent || '';
});

textBox.addEventListener('input', () => {
  chrome.storage.local.set({ textBoxContent: textBox.value });
});

// Send a dummy listing for the current tab to the backend and show the reply
const analyzeButton = document.getElementById('analyze');

analyzeButton.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  const dummyRequest = {
    source: 'facebook_marketplace',
    url: tab.url,
    listing: {
      title: 'Sunny 2BR apartment near downtown',
      price: 900,
      currency: 'USD',
      description: 'Owner is out of the country. Send deposit via Zelle to hold.',
      location: 'Vancouver, BC',
      images: [],
      seller: { name: 'Test Seller', profile_url: '', joined: '2026' }
    }
  };

  analyzeButton.disabled = true;
  textBox.value = 'Sending request...';

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(dummyRequest)
    });
    const data = await response.json();
    textBox.value = `Status ${response.status}\n\n${JSON.stringify(data, null, 2)}`;
  } catch (error) {
    textBox.value = `Request failed: ${error.message}\n\nIs the backend running at ${API_URL}?`;
  } finally {
    analyzeButton.disabled = false;
  }
});

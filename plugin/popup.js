// DeepVerify Studio Chrome Extension - Popup Script

document.addEventListener('DOMContentLoaded', function() {
  loadLastVerification()
})

function loadLastVerification() {
  chrome.runtime.sendMessage({ action: 'getLastVerification' }, (response) => {
    const contentDiv = document.getElementById('content')
    
    if (response) {
      // Show verification result
      contentDiv.innerHTML = createVerificationCard(response)
    } else {
      // Show no verification state
      contentDiv.innerHTML = createNoVerificationCard()
    }
  })
}

function createVerificationCard(verification) {
  const verdict = verification.verdict
  const confidence = Math.round(verification.confidence_score * 100)
  const timestamp = new Date(verification.timestamp).toLocaleString()
  
  let verdictIcon = '✅'
  let verdictClass = 'authentic'
  
  if (verdict === 'suspicious') {
    verdictIcon = '⚠️'
    verdictClass = 'suspicious'
  } else if (verdict === 'malicious') {
    verdictIcon = '🚨'
    verdictClass = 'malicious'
  }
  
  return `
    <div class="status-card">
      <div class="status-title">Last Verification Result</div>
      <div class="verdict ${verdictClass}">
        ${verdictIcon} ${verdict.charAt(0).toUpperCase() + verdict.slice(1)}
      </div>
      <div class="confidence">Confidence: ${confidence}%</div>
      <div class="timestamp">Verified: ${timestamp}</div>
      
      <div class="actions">
        <button class="btn btn-primary" onclick="openWebApp()">
          Open Web App
        </button>
        <button class="btn btn-secondary" onclick="clearVerification()">
          Clear
        </button>
      </div>
    </div>
  `
}

function createNoVerificationCard() {
  return `
    <div class="no-verification">
      <div class="no-verification-icon">🔍</div>
      <div class="no-verification-text">
        No verification performed yet.<br>
        Right-click on a file link to start analysis.
      </div>
      
      <div class="actions">
        <button class="btn btn-primary" onclick="openWebApp()">
          Open Web App
        </button>
      </div>
    </div>
  `
}

function openWebApp() {
  chrome.tabs.create({ url: 'http://localhost:3000' })
}

function clearVerification() {
  chrome.runtime.sendMessage({ action: 'clearLastVerification' }, (response) => {
    if (response.success) {
      loadLastVerification()
    }
  })
}

// Make functions globally available
window.openWebApp = openWebApp
window.clearVerification = clearVerification

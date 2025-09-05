// DeepVerify Studio Chrome Extension - Background Service Worker

const API_BASE_URL = 'http://localhost:8000'

// Create context menu on installation
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'verifyWithDeepVerify',
    title: 'Verify with DeepVerify',
    contexts: ['link', 'image']
  })
})

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === 'verifyWithDeepVerify') {
    try {
      const url = info.srcUrl || info.linkUrl
      if (!url) {
        showNotification('No file URL found', 'error')
        return
      }

      // Show loading notification
      showNotification('Starting verification...', 'info')

      // Download and verify the file
      const result = await verifyFile(url)
      
      if (result.success) {
        const verdict = result.verdict
        const confidence = Math.round(result.confidence_score * 100)
        
        let message = `Analysis complete: ${verdict} (${confidence}% confidence)`
        let type = verdict === 'authentic' ? 'success' : 'warning'
        
        if (verdict === 'malicious') {
          type = 'error'
        }
        
        showNotification(message, type)
        
        // Store result for popup
        chrome.storage.local.set({
          lastVerification: {
            url,
            verdict,
            confidence_score: result.confidence_score,
            timestamp: Date.now()
          }
        })
      } else {
        showNotification('Verification failed: ' + result.error, 'error')
      }
      
    } catch (error) {
      console.error('Verification error:', error)
      showNotification('Verification failed', 'error')
    }
  }
})

// Verify file by downloading and analyzing
async function verifyFile(url) {
  try {
    // Download the file
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error('Failed to download file')
    }
    
    const blob = await response.blob()
    const file = new File([blob], 'file', { type: blob.type })
    
    // Upload to DeepVerify API
    const formData = new FormData()
    formData.append('file', file)
    
    const uploadResponse = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      body: formData
    })
    
    if (!uploadResponse.ok) {
      throw new Error('Upload failed')
    }
    
    const uploadResult = await uploadResponse.json()
    
    // Analyze the file
    const fileType = uploadResult.file_type
    const endpoint = fileType === 'pdf' ? '/api/analyze/pdf' : '/api/analyze/image'
    
    const analyzeResponse = await fetch(`${API_BASE_URL}${endpoint}/${uploadResult.file_id}`, {
      method: 'POST'
    })
    
    if (!analyzeResponse.ok) {
      throw new Error('Analysis failed')
    }
    
    const analyzeResult = await analyzeResponse.json()
    
    // Poll for results
    let attempts = 0
    const maxAttempts = 30 // 30 seconds
    
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      const statusResponse = await fetch(`${API_BASE_URL}/api/upload/status/${uploadResult.file_id}`)
      const statusResult = await statusResponse.json()
      
      if (statusResult.analysis_status === 'completed') {
        return {
          success: true,
          verdict: statusResult.verdict,
          confidence_score: statusResult.confidence_score
        }
      } else if (statusResult.analysis_status === 'failed') {
        throw new Error('Analysis failed')
      }
      
      attempts++
    }
    
    throw new Error('Analysis timeout')
    
  } catch (error) {
    console.error('Verification error:', error)
    return {
      success: false,
      error: error.message
    }
  }
}

// Show notification
function showNotification(message, type = 'info') {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'icons/icon48.png',
    title: 'DeepVerify Studio',
    message: message
  })
}

// Handle messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getLastVerification') {
    chrome.storage.local.get(['lastVerification'], (result) => {
      sendResponse(result.lastVerification || null)
    })
    return true // Keep message channel open for async response
  }
  
  if (request.action === 'clearLastVerification') {
    chrome.storage.local.remove(['lastVerification'], () => {
      sendResponse({ success: true })
    })
    return true
  }
})

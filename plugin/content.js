// DeepVerify Studio Chrome Extension - Content Script

// Listen for messages from the background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getPageInfo') {
    const pageInfo = {
      url: window.location.href,
      title: document.title,
      hasImages: document.querySelectorAll('img').length > 0,
      hasLinks: document.querySelectorAll('a[href]').length > 0
    }
    sendResponse(pageInfo)
  }
})

// Add visual indicators for verifiable content
function addVerificationIndicators() {
  // Add indicators to images
  const images = document.querySelectorAll('img')
  images.forEach(img => {
    if (img.src && (img.src.endsWith('.pdf') || img.src.match(/\.(jpg|jpeg|png|gif|bmp|tiff)$/i))) {
      addVerificationBadge(img, 'image')
    }
  })
  
  // Add indicators to PDF links
  const links = document.querySelectorAll('a[href]')
  links.forEach(link => {
    if (link.href && link.href.endsWith('.pdf')) {
      addVerificationBadge(link, 'pdf')
    }
  })
}

function addVerificationBadge(element, type) {
  // Create verification badge
  const badge = document.createElement('div')
  badge.className = 'deepverify-badge'
  badge.innerHTML = '🔍'
  badge.title = 'Click to verify with DeepVerify Studio'
  badge.style.cssText = `
    position: absolute;
    top: 5px;
    right: 5px;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 12px;
    z-index: 1000;
    transition: all 0.2s;
  `
  
  // Make parent element relative positioned
  if (getComputedStyle(element).position === 'static') {
    element.style.position = 'relative'
  }
  
  // Add hover effect
  badge.addEventListener('mouseenter', () => {
    badge.style.background = 'rgba(59, 130, 246, 0.9)'
    badge.style.transform = 'scale(1.1)'
  })
  
  badge.addEventListener('mouseleave', () => {
    badge.style.background = 'rgba(0, 0, 0, 0.7)'
    badge.style.transform = 'scale(1)'
  })
  
  // Add click handler
  badge.addEventListener('click', (e) => {
    e.preventDefault()
    e.stopPropagation()
    
    const url = element.src || element.href
    if (url) {
      // Send message to background script to verify
      chrome.runtime.sendMessage({
        action: 'verifyFile',
        url: url,
        type: type
      })
    }
  })
  
  element.appendChild(badge)
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', addVerificationIndicators)
} else {
  addVerificationIndicators()
}

// Watch for dynamic content changes
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.type === 'childList') {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE) {
          // Check for new images or links
          const images = node.querySelectorAll ? node.querySelectorAll('img') : []
          const links = node.querySelectorAll ? node.querySelectorAll('a[href]') : []
          
          images.forEach(img => {
            if (img.src && (img.src.endsWith('.pdf') || img.src.match(/\.(jpg|jpeg|png|gif|bmp|tiff)$/i))) {
              addVerificationBadge(img, 'image')
            }
          })
          
          links.forEach(link => {
            if (link.href && link.href.endsWith('.pdf')) {
              addVerificationBadge(link, 'pdf')
            }
          })
        }
      })
    }
  })
})

observer.observe(document.body, {
  childList: true,
  subtree: true
})

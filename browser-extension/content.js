let isRecording = false;
let highlightedElements = [];

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'START_RECORDING') {
    isRecording = true;
    console.log('AI Test Recorder: Started');
    showOverlay('Recording Started');
    sendResponse({ success: true });
  } else if (message.type === 'STOP_RECORDING') {
    isRecording = false;
    console.log('AI Test Recorder: Stopped');
    showOverlay('Recording Stopped');
    sendResponse({ success: true });
  } else if (message.type === 'CHECK_CONNECTION') {
    sendResponse({ connected: true });
  } else if (message.type === 'VALIDATE_SELECTOR') {
    const result = validateSelector(message.selector);
    sendResponse({ success: true, ...result });
  } else if (message.type === 'HIGHLIGHT_ELEMENT') {
    highlightElementsBySelector(message.selector);
    sendResponse({ success: true });
  } else if (message.type === 'CLEAR_HIGHLIGHTS') {
    clearHighlights();
    sendResponse({ success: true });
  }
  return true;
});

// Check initial state
chrome.storage.local.get(['recording'], (result) => {
  isRecording = result.recording || false;
});

// Event listeners
document.addEventListener('click', handleEvent, true);
document.addEventListener('input', handleEvent, true);
document.addEventListener('change', handleEvent, true);

async function handleEvent(event) {
  if (!isRecording) return;
  
  // Ignore events from our own overlay
  if (event.target.id === 'ai-test-recorder-overlay') return;

  const target = event.target;
  const action = {
    type: event.type,
    timestamp: Date.now(),
    selector: getSelector(target),
    value: target.value || target.innerText,
    tagName: target.tagName,
    inputType: target.type
  };

  // Filter out irrelevant events
  if (event.type === 'input' && target.type === 'password') {
    // Don't record password values directly, maybe mark as sensitive
    action.value = '***'; 
  }

  console.log('Recorded action:', action);

  // Save action
  const { actions = [] } = await chrome.storage.local.get(['actions']);
  actions.push(action);
  await chrome.storage.local.set({ actions });
  
  // Visual feedback
  highlightElement(target);
}

function getSelector(element) {
  // 1. Try data-testid or data-cy
  if (element.dataset.testid) return `[data-testid="${element.dataset.testid}"]`;
  if (element.dataset.cy) return `[data-cy="${element.dataset.cy}"]`;
  
  // 2. Try ID
  if (element.id) return `#${element.id}`;
  
  // 3. Try name
  if (element.name) return `[name="${element.name}"]`;
  
  // 4. Try class (if unique)
  if (element.className && typeof element.className === 'string') {
    const classes = element.className.split(' ').filter(c => c).join('.');
    if (classes) {
      const selector = `.${classes}`;
      if (document.querySelectorAll(selector).length === 1) return selector;
    }
  }
  
  // 5. Fallback to path
  return getPathTo(element);
}

function getPathTo(element) {
  if (element.id !== '') return 'id("' + element.id + '")';
  if (element === document.body) return element.tagName;

  var ix = 0;
  var siblings = element.parentNode.childNodes;
  for (var i = 0; i < siblings.length; i++) {
    var sibling = siblings[i];
    if (sibling === element) return getPathTo(element.parentNode) + '/' + element.tagName + '[' + (ix + 1) + ']';
    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) ix++;
  }
}

function highlightElement(element) {
  const originalOutline = element.style.outline;
  element.style.outline = '2px solid #0d6efd';
  setTimeout(() => {
    element.style.outline = originalOutline;
  }, 500);
}

function showOverlay(text) {
  let overlay = document.getElementById('ai-test-recorder-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'ai-test-recorder-overlay';
    overlay.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 10px 20px;
      border-radius: 5px;
      z-index: 999999;
      font-family: sans-serif;
      pointer-events: none;
      transition: opacity 0.5s;
    `;
    document.body.appendChild(overlay);
  }
  
  overlay.textContent = text;
  overlay.style.opacity = '1';
  
  setTimeout(() => {
    overlay.style.opacity = '0';
  }, 3000);
}

function validateSelector(selector) {
  try {
    const elements = document.querySelectorAll(selector);
    const elementCount = elements.length;
    
    if (elementCount === 0) {
      return {
        valid: false,
        elementCount: 0,
        selector: selector,
        error: 'No elements found'
      };
    }
    
    const suggestedSelectors = [];
    
    if (elementCount > 1) {
      suggestedSelectors.push(...generateBetterSelectors(elements));
    }
    
    return {
      valid: true,
      elementCount: elementCount,
      selector: selector,
      suggestedSelectors: suggestedSelectors
    };
  } catch (error) {
    return {
      valid: false,
      elementCount: 0,
      selector: selector,
      error: error.message
    };
  }
}

function generateBetterSelectors(elements) {
  const suggestions = [];
  const seen = new Set();
  
  for (const element of elements) {
    const betterSelector = getBestSelector(element);
    if (betterSelector && !seen.has(betterSelector)) {
      seen.add(betterSelector);
      suggestions.push(betterSelector);
    }
    
    if (suggestions.length >= 3) break;
  }
  
  return suggestions;
}

function getBestSelector(element) {
  if (element.dataset.testid) return `[data-testid="${element.dataset.testid}"]`;
  if (element.dataset.cy) return `[data-cy="${element.dataset.cy}"]`;
  if (element.dataset.test) return `[data-test="${element.dataset.test}"]`;
  
  if (element.id) {
    const idSelector = `#${element.id}`;
    if (document.querySelectorAll(idSelector).length === 1) {
      return idSelector;
    }
  }
  
  if (element.name) {
    const nameSelector = `[name="${element.name}"]`;
    if (document.querySelectorAll(nameSelector).length === 1) {
      return nameSelector;
    }
  }
  
  const ariaLabel = element.getAttribute('aria-label');
  if (ariaLabel) {
    const ariaSelector = `[aria-label="${ariaLabel}"]`;
    if (document.querySelectorAll(ariaSelector).length === 1) {
      return ariaSelector;
    }
  }
  
  const role = element.getAttribute('role');
  if (role) {
    const roleSelector = `[role="${role}"]`;
    const roleElements = document.querySelectorAll(roleSelector);
    if (roleElements.length === 1) {
      return roleSelector;
    }
    
    if (element.textContent && element.textContent.trim()) {
      const text = element.textContent.trim().substring(0, 50);
      const textSelector = `${roleSelector}:has-text("${text}")`;
      return textSelector;
    }
  }
  
  return null;
}

function highlightElementsBySelector(selector) {
  clearHighlights();
  
  try {
    const elements = document.querySelectorAll(selector);
    elements.forEach((element, index) => {
      const highlight = document.createElement('div');
      highlight.className = 'ai-test-highlight';
      highlight.style.cssText = `
        position: absolute;
        pointer-events: none;
        z-index: 999998;
        border: 3px solid ${index === 0 ? '#22c55e' : '#f59e0b'};
        background-color: ${index === 0 ? 'rgba(34, 197, 94, 0.2)' : 'rgba(245, 158, 11, 0.2)'};
        box-sizing: border-box;
      `;
      
      const rect = element.getBoundingClientRect();
      highlight.style.left = rect.left + window.scrollX + 'px';
      highlight.style.top = rect.top + window.scrollY + 'px';
      highlight.style.width = rect.width + 'px';
      highlight.style.height = rect.height + 'px';
      
      document.body.appendChild(highlight);
      highlightedElements.push(highlight);
      
      if (index === 0) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
    
    if (elements.length > 0) {
      showOverlay(`Found ${elements.length} element(s)`);
    } else {
      showOverlay('No elements found');
    }
  } catch (error) {
    showOverlay('Invalid selector');
  }
}

function clearHighlights() {
  highlightedElements.forEach(highlight => {
    if (highlight.parentNode) {
      highlight.parentNode.removeChild(highlight);
    }
  });
  highlightedElements = [];
}

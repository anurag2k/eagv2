// Content script for handling text selection, floating button, and inline popup
// Runs on all web pages

class WordDefinitionHandler {
  constructor() {
    this.floatingButton = null;
    this.popup = null;
    this.selectedText = '';
    this.selectionRange = null;
    
    this.init();
  }

  init() {
    // Listen for text selection
    document.addEventListener('mouseup', this.handleTextSelection.bind(this));
    document.addEventListener('keyup', this.handleTextSelection.bind(this));
    
    // Listen for clicks to hide elements
    document.addEventListener('click', this.handleDocumentClick.bind(this));
    
    // Listen for scroll to reposition elements
    window.addEventListener('scroll', this.handleScroll.bind(this));
    window.addEventListener('resize', this.handleResize.bind(this));
    
    // Listen for messages from background script
    chrome.runtime.onMessage.addListener(this.handleMessage.bind(this));
  }

  /**
   * Handle text selection events
   * @param {Event} event - Mouse or keyboard event
   */
  handleTextSelection(event) {
    // Small delay to ensure selection is complete
    setTimeout(() => {
      const selection = window.getSelection();
      const selectedText = selection.toString().trim();
      
      // Hide existing elements if no text is selected
      if (!selectedText) {
        this.hideFloatingButton();
        this.hidePopup();
        return;
      }

      // Validate selected text is a word (not too long, contains letters)
      if (this.isValidSelection(selectedText)) {
        this.selectedText = selectedText;
        this.selectionRange = selection.getRangeAt(0);
        this.showFloatingButton();
      } else {
        this.hideFloatingButton();
      }
    }, 50);
  }

  /**
   * Validate if selection is a valid word
   * @param {string} text - Selected text
   * @returns {boolean} True if valid
   */
  isValidSelection(text) {
    // Check if text is reasonable length and contains letters
    return text.length > 0 && 
           text.length <= 50 && 
           /[a-zA-Z]/.test(text) &&
           // Avoid very long selections or those with too many special characters
           text.split(' ').length <= 3;
  }

  /**
   * Show floating "Lookup" button near selection
   */
  showFloatingButton() {
    this.hideFloatingButton(); // Remove existing button
    
    if (!this.selectionRange) return;

    const rect = this.selectionRange.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;

    this.floatingButton = document.createElement('button');
    this.floatingButton.className = 'word-lookup-floating-btn';
    this.floatingButton.textContent = 'Lookup';
    this.floatingButton.addEventListener('click', this.handleLookupClick.bind(this));

    // Position button above selection
    const buttonTop = rect.top + window.scrollY - 35;
    const buttonLeft = rect.left + window.scrollX + (rect.width / 2) - 25;

    this.floatingButton.style.top = `${Math.max(buttonTop, window.scrollY + 10)}px`;
    this.floatingButton.style.left = `${Math.max(buttonLeft, 10)}px`;

    document.body.appendChild(this.floatingButton);
  }

  /**
   * Hide floating button
   */
  hideFloatingButton() {
    if (this.floatingButton) {
      this.floatingButton.remove();
      this.floatingButton = null;
    }
  }

  /**
   * Handle lookup button click
   * @param {Event} event - Click event
   */
  handleLookupClick(event) {
    event.stopPropagation();
    this.showDefinitionPopup(this.selectedText);
  }

  /**
   * Show definition popup
   * @param {string} word - Word to lookup
   */
  async showDefinitionPopup(word) {
    this.hidePopup(); // Remove existing popup
    this.hideFloatingButton();

    if (!word) return;

    // Create popup container
    this.popup = document.createElement('div');
    this.popup.className = 'word-lookup-popup';
    
    // Position popup near selection or button
    this.positionPopup();
    
    // Show loading state
    this.popup.innerHTML = this.getLoadingHTML();
    document.body.appendChild(this.popup);

    try {
      // Fetch definition
      const response = await this.requestDefinition(word);
      
      if (response.success) {
        this.popup.innerHTML = this.getDefinitionHTML(response.data);
      } else {
        this.popup.innerHTML = this.getErrorHTML(response.error || 'Failed to fetch definition');
      }
    } catch (error) {
      this.popup.innerHTML = this.getErrorHTML('Network error occurred');
    }

    // Add close button functionality
    const closeBtn = this.popup.querySelector('.word-lookup-popup-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.hidePopup());
    }
  }

  /**
   * Position popup near selection
   */
  positionPopup() {
    if (!this.popup) return;

    let top, left;

    if (this.selectionRange) {
      const rect = this.selectionRange.getBoundingClientRect();
      top = rect.bottom + window.scrollY + 10;
      left = rect.left + window.scrollX;
    } else {
      // Fallback positioning
      top = window.scrollY + 100;
      left = window.scrollX + 100;
    }

    // Adjust to keep popup on screen
    const popupWidth = 320; // max-width from CSS
    const popupHeight = 200; // estimated height

    // Adjust horizontal position
    const maxLeft = window.innerWidth - popupWidth - 20;
    left = Math.max(10, Math.min(left, maxLeft));

    // Adjust vertical position
    const maxTop = window.innerHeight + window.scrollY - popupHeight - 20;
    if (top > maxTop) {
      // Position above selection instead
      if (this.selectionRange) {
        const rect = this.selectionRange.getBoundingClientRect();
        top = rect.top + window.scrollY - popupHeight - 10;
      }
    }
    top = Math.max(window.scrollY + 10, top);

    this.popup.style.top = `${top}px`;
    this.popup.style.left = `${left}px`;
  }

  /**
   * Hide definition popup
   */
  hidePopup() {
    if (this.popup) {
      this.popup.remove();
      this.popup = null;
    }
  }

  /**
   * Request definition from background script
   * @param {string} word - Word to look up
   * @returns {Promise<Object>} Response object
   */
  requestDefinition(word) {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({
        action: 'fetchDefinition',
        word: word
      }, resolve);
    });
  }

  /**
   * Generate loading HTML
   * @returns {string} HTML string
   */
  getLoadingHTML() {
    return `
      <button class="word-lookup-popup-close">&times;</button>
      <div class="word-lookup-popup-loading">
        Loading definition...
      </div>
    `;
  }

  /**
   * Generate error HTML
   * @param {string} error - Error message
   * @returns {string} HTML string
   */
  getErrorHTML(error) {
    const safeError = this.escapeHtml(error);
    return `
      <button class="word-lookup-popup-close">&times;</button>
      <div class="word-lookup-popup-error">
        ${safeError}
      </div>
    `;
  }

  /**
   * Generate definition HTML
   * @param {Object} data - Definition data
   * @returns {string} HTML string
   */
  getDefinitionHTML(data) {
    const word = this.escapeHtml(data.word);
    const phonetic = data.phonetic ? this.escapeHtml(data.phonetic) : '';
    
    let meaningsHTML = '';
    
    if (data.meanings && data.meanings.length > 0) {
      meaningsHTML = data.meanings.map(meaning => {
        const partOfSpeech = this.escapeHtml(meaning.partOfSpeech);
        const definitions = meaning.definitions?.slice(0, 3).map(def => {
          const definition = this.escapeHtml(def.definition);
          const example = def.example ? this.escapeHtml(def.example) : '';
          
          return `
            <div class="word-lookup-popup-definition">
              <div class="word-lookup-popup-def-text">${definition}</div>
              ${example ? `<div class="word-lookup-popup-example">${example}</div>` : ''}
            </div>
          `;
        }).join('') || '';

        return `
          <div class="word-lookup-popup-meaning">
            <div class="word-lookup-popup-pos">${partOfSpeech}</div>
            ${definitions}
          </div>
        `;
      }).join('');
    }

    return `
      <button class="word-lookup-popup-close">&times;</button>
      <div class="word-lookup-popup-header">
        <h3 class="word-lookup-popup-word">${word}</h3>
        ${phonetic ? `<div class="word-lookup-popup-phonetic">${phonetic}</div>` : ''}
      </div>
      ${meaningsHTML || '<div class="word-lookup-popup-error">No definitions found</div>'}
    `;
  }

  /**
   * Escape HTML to prevent XSS
   * @param {string} text - Text to escape
   * @returns {string} Escaped text
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Handle document clicks to hide elements
   * @param {Event} event - Click event
   */
  handleDocumentClick(event) {
    // Don't hide if clicking on our elements
    if (event.target.closest('.word-lookup-floating-btn') || 
        event.target.closest('.word-lookup-popup')) {
      return;
    }
    
    // Hide elements on outside click
    this.hideFloatingButton();
    this.hidePopup();
  }

  /**
   * Handle scroll events
   */
  handleScroll() {
    // Reposition popup if it exists
    if (this.popup) {
      this.positionPopup();
    }
  }

  /**
   * Handle resize events
   */
  handleResize() {
    // Reposition popup if it exists
    if (this.popup) {
      this.positionPopup();
    }
  }

  /**
   * Handle messages from background script
   * @param {Object} request - Message object
   * @param {Object} sender - Sender info
   * @param {Function} sendResponse - Response function
   */
  handleMessage(request, sender, sendResponse) {
    if (request.action === 'showDefinition') {
      this.showDefinitionPopup(request.word);
    }
  }
}

// Initialize the word definition handler when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new WordDefinitionHandler();
  });
} else {
  new WordDefinitionHandler();
}
// Popup script for the extension toolbar popup interface

class PopupController {
  constructor() {
    this.wordInput = document.getElementById('wordInput');
    this.searchBtn = document.getElementById('searchBtn');
    this.results = document.getElementById('results');
    
    this.init();
  }

  init() {
    // Event listeners
    this.searchBtn.addEventListener('click', this.handleSearch.bind(this));
    this.wordInput.addEventListener('keypress', this.handleKeyPress.bind(this));
    this.wordInput.addEventListener('input', this.handleInput.bind(this));
    
    // Focus on input when popup opens
    this.wordInput.focus();
    
    // Load recent search if available
    this.loadRecentSearch();
  }

  /**
   * Handle search button click
   */
  async handleSearch() {
    const word = this.wordInput.value.trim();
    if (!word) return;

    await this.searchWord(word);
  }

  /**
   * Handle Enter key press in input
   * @param {KeyboardEvent} event - Keypress event
   */
  handleKeyPress(event) {
    if (event.key === 'Enter') {
      this.handleSearch();
    }
  }

  /**
   * Handle input changes
   * @param {InputEvent} event - Input event
   */
  handleInput(event) {
    const word = event.target.value.trim();
    // Enable/disable search button
    this.searchBtn.disabled = !word;
  }

  /**
   * Search for a word definition
   * @param {string} word - Word to search
   */
  async searchWord(word) {
    if (!this.validateWord(word)) {
      this.showError('Please enter a valid word (letters only, max 50 characters)');
      return;
    }

    // Show loading state
    this.showLoading();
    this.searchBtn.disabled = true;

    try {
      // Request definition from background script
      const response = await this.requestDefinition(word);
      
      if (response.success) {
        this.showDefinition(response.data);
        this.saveRecentSearch(word);
      } else {
        this.showError(response.error || 'Failed to fetch definition');
      }
    } catch (error) {
      this.showError('Network error occurred. Please check your connection.');
    } finally {
      this.searchBtn.disabled = false;
    }
  }

  /**
   * Validate word input
   * @param {string} word - Word to validate
   * @returns {boolean} True if valid
   */
  validateWord(word) {
    return word && 
           word.length > 0 && 
           word.length <= 50 && 
           /^[a-zA-Z\s\-']+$/.test(word);
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
   * Show loading state
   */
  showLoading() {
    this.results.innerHTML = `
      <div class="loading">
        Searching for definition...
      </div>
    `;
  }

  /**
   * Show error message
   * @param {string} message - Error message
   */
  showError(message) {
    const safeMessage = this.escapeHtml(message);
    this.results.innerHTML = `
      <div class="error">
        ${safeMessage}
      </div>
    `;
  }

  /**
   * Show definition results
   * @param {Object} data - Definition data
   */
  showDefinition(data) {
    if (!data || !data.word) {
      this.showError('No definition found');
      return;
    }

    const word = this.escapeHtml(data.word);
    const phonetic = data.phonetic ? this.escapeHtml(data.phonetic) : '';
    
    let meaningsHTML = '';
    
    if (data.meanings && data.meanings.length > 0) {
      meaningsHTML = data.meanings.map(meaning => {
        const partOfSpeech = this.escapeHtml(meaning.partOfSpeech);
        
        const definitionsHTML = meaning.definitions?.map(def => {
          const definition = this.escapeHtml(def.definition);
          const example = def.example ? this.escapeHtml(def.example) : '';
          
          return `
            <div class="definition">
              <div class="definition-text">${definition}</div>
              ${example ? `<div class="example">${example}</div>` : ''}
            </div>
          `;
        }).join('') || '';

        return `
          <div class="meaning">
            <div class="part-of-speech">${partOfSpeech}</div>
            ${definitionsHTML}
          </div>
        `;
      }).join('');
    }

    this.results.innerHTML = `
      <div class="definition-result">
        <h2 class="word-title">${word}</h2>
        ${phonetic ? `<div class="phonetic">${phonetic}</div>` : ''}
        ${meaningsHTML || '<div class="error">No definitions available</div>'}
      </div>
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
   * Save recent search to storage
   * @param {string} word - Word that was searched
   */
  async saveRecentSearch(word) {
    try {
      await chrome.storage.local.set({ recentSearch: word });
    } catch (error) {
      console.error('Error saving recent search:', error);
    }
  }

  /**
   * Load recent search from storage
   */
  async loadRecentSearch() {
    try {
      const result = await chrome.storage.local.get('recentSearch');
      if (result.recentSearch) {
        this.wordInput.placeholder = `Try "${result.recentSearch}" or enter a new word...`;
      }
    } catch (error) {
      console.error('Error loading recent search:', error);
    }
  }
}

// Initialize popup controller when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new PopupController();
});
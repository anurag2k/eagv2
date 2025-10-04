// Background service worker for handling context menus and API requests
// Manifest V3 compliant service worker

// Create context menu when extension is installed
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'define-word',
    title: 'Lookup "%s"',
    contexts: ['selection']
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'define-word' && info.selectionText) {
    // Send message to content script to show definition
    chrome.tabs.sendMessage(tab.id, {
      action: 'showDefinition',
      word: info.selectionText.trim(),
      source: 'contextMenu'
    });
  }
});

// Handle messages from content script and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'fetchDefinition') {
    fetchWordDefinition(request.word)
      .then(definition => {
        sendResponse({ success: true, data: definition });
      })
      .catch(error => {
        sendResponse({ success: false, error: error.message });
      });
    return true; // Will respond asynchronously
  }
});

/**
 * Fetch word definition from dictionary API
 * @param {string} word - The word to look up
 * @returns {Promise<Object>} Definition data
 */
async function fetchWordDefinition(word) {
  try {
    const cleanWord = word.toLowerCase().trim();
    if (!cleanWord || !isValidWord(cleanWord)) {
      throw new Error('Invalid word format');
    }

    const response = await fetch(`https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(cleanWord)}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('No definition found for this word');
      }
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    
    if (!data || !Array.isArray(data) || data.length === 0) {
      throw new Error('No definition found');
    }

    return parseDefinitionData(data[0]);
  } catch (error) {
    console.error('Error fetching definition:', error);
    throw error;
  }
}

/**
 * Validate if the input is a valid word
 * @param {string} word - Word to validate
 * @returns {boolean} True if valid
 */
function isValidWord(word) {
  // Basic validation: only letters, spaces, hyphens, and apostrophes
  return /^[a-zA-Z\s\-']+$/.test(word) && word.length > 0 && word.length < 50;
}

/**
 * Parse and structure the API response
 * @param {Object} data - Raw API response
 * @returns {Object} Structured definition data
 */
function parseDefinitionData(data) {
  const result = {
    word: data.word || '',
    phonetic: '',
    meanings: []
  };

  // Extract phonetic pronunciation
  if (data.phonetic) {
    result.phonetic = data.phonetic;
  } else if (data.phonetics && data.phonetics.length > 0) {
    result.phonetic = data.phonetics.find(p => p.text)?.text || '';
  }

  // Extract meanings (limit to 3 for UI purposes)
  if (data.meanings && Array.isArray(data.meanings)) {
    result.meanings = data.meanings.slice(0, 3).map(meaning => ({
      partOfSpeech: meaning.partOfSpeech || '',
      definitions: meaning.definitions?.slice(0, 3).map(def => ({
        definition: def.definition || '',
        example: def.example || ''
      })) || []
    }));
  }

  return result;
}

// Cache management for better performance
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours

/**
 * Cache definition data
 * @param {string} word - The word
 * @param {Object} data - Definition data
 */
async function cacheDefinition(word, data) {
  try {
    const cacheData = {
      [word.toLowerCase()]: {
        data: data,
        timestamp: Date.now()
      }
    };
    await chrome.storage.local.set(cacheData);
  } catch (error) {
    console.error('Error caching definition:', error);
  }
}

/**
 * Get cached definition
 * @param {string} word - The word to look up
 * @returns {Promise<Object|null>} Cached data or null
 */
async function getCachedDefinition(word) {
  try {
    const result = await chrome.storage.local.get(word.toLowerCase());
    const cached = result[word.toLowerCase()];
    
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      return cached.data;
    }
    
    return null;
  } catch (error) {
    console.error('Error getting cached definition:', error);
    return null;
  }
}
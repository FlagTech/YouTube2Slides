/**
 * History Manager for localStorage operations
 */

import { getVideoHistory } from '../api/api';

const HISTORY_KEY = 'videoHistory';
const FOLDERS_KEY = 'historyFolders';
const MAX_HISTORY_ITEMS = 20;
const LAST_SYNC_KEY = 'lastHistorySync';

export const saveToHistory = (result, jobId) => {
  try {
    const historyItem = {
      jobId: jobId,
      videoId: result.video_id || null,  // Store videoId for deletion
      title: result.title || '未命名影片',
      totalFrames: result.total_frames || 0,
      timestamp: new Date().toISOString(),
      folderId: null,  // null means "uncategorized"
      result: result
    };

    // Get existing history
    const history = getHistory();

    // Check if this jobId already exists
    const existingIndex = history.findIndex(item => item.jobId === jobId);

    if (existingIndex >= 0) {
      // Update existing item
      history[existingIndex] = historyItem;
    } else {
      // Add new item at the beginning
      history.unshift(historyItem);
    }

    // Keep only last MAX_HISTORY_ITEMS items
    const trimmedHistory = history.slice(0, MAX_HISTORY_ITEMS);

    // Save to localStorage
    localStorage.setItem(HISTORY_KEY, JSON.stringify(trimmedHistory));

    console.log('History saved:', historyItem.title);
    return true;
  } catch (error) {
    console.error('Failed to save history:', error);
    return false;
  }
};

export const getHistory = () => {
  try {
    const savedHistory = localStorage.getItem(HISTORY_KEY);
    if (savedHistory) {
      return JSON.parse(savedHistory);
    }
    return [];
  } catch (error) {
    console.error('Failed to get history:', error);
    return [];
  }
};

export const clearHistory = () => {
  try {
    localStorage.removeItem(HISTORY_KEY);
    console.log('History cleared');
    return true;
  } catch (error) {
    console.error('Failed to clear history:', error);
    return false;
  }
};

export const deleteHistoryItem = (index) => {
  try {
    const history = getHistory();
    history.splice(index, 1);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    console.log('History item deleted at index:', index);
    return true;
  } catch (error) {
    console.error('Failed to delete history item:', error);
    return false;
  }
};

export const syncHistoryFromBackend = async () => {
  try {
    console.log('Syncing history from backend...');
    const response = await getVideoHistory();
    const backendHistory = response.history || [];

    if (backendHistory.length === 0) {
      console.log('No history found on backend');
      return false;
    }

    // Get current localStorage history
    const localHistory = getHistory();

    // Create a map of local items by jobId to preserve folderId
    const localItemsMap = new Map();
    for (const localItem of localHistory) {
      localItemsMap.set(localItem.jobId, localItem);
    }

    // Merge: use backend as source of truth, but preserve local folderId
    const mergedHistory = backendHistory.map(backendItem => {
      const localItem = localItemsMap.get(backendItem.jobId);

      // If item exists locally, preserve its folderId
      if (localItem) {
        return {
          ...backendItem,
          folderId: localItem.folderId || null  // Preserve folder classification
        };
      }

      // New item from backend, set folderId to null (uncategorized)
      return {
        ...backendItem,
        folderId: null
      };
    });

    // Add local items that are not in backend
    for (const localItem of localHistory) {
      const existsInBackend = backendHistory.some(
        item => item.jobId === localItem.jobId
      );
      if (!existsInBackend) {
        mergedHistory.push(localItem);
      }
    }

    // Sort by timestamp, newest first
    mergedHistory.sort((a, b) => {
      const timeA = new Date(a.timestamp || 0);
      const timeB = new Date(b.timestamp || 0);
      return timeB - timeA;
    });

    // Keep only MAX_HISTORY_ITEMS
    const trimmedHistory = mergedHistory.slice(0, MAX_HISTORY_ITEMS);

    // Save to localStorage
    localStorage.setItem(HISTORY_KEY, JSON.stringify(trimmedHistory));
    localStorage.setItem(LAST_SYNC_KEY, new Date().toISOString());

    console.log(`History synced: ${trimmedHistory.length} items`);
    return true;
  } catch (error) {
    console.error('Failed to sync history from backend:', error);
    return false;
  }
};

export const shouldSync = () => {
  try {
    const lastSync = localStorage.getItem(LAST_SYNC_KEY);
    if (!lastSync) return true;

    const lastSyncTime = new Date(lastSync);
    const now = new Date();
    const diffMinutes = (now - lastSyncTime) / 1000 / 60;

    // Sync if more than 5 minutes since last sync
    return diffMinutes > 5;
  } catch {
    return true;
  }
};

// ========== Folder Management ==========

export const getFolders = () => {
  try {
    const savedFolders = localStorage.getItem(FOLDERS_KEY);
    if (savedFolders) {
      return JSON.parse(savedFolders);
    }
    return [];
  } catch (error) {
    console.error('Failed to get folders:', error);
    return [];
  }
};

export const createFolder = (name) => {
  try {
    const folders = getFolders();
    const newFolder = {
      id: Date.now().toString(),
      name: name,
      createdAt: new Date().toISOString(),
      expanded: true
    };
    folders.push(newFolder);
    localStorage.setItem(FOLDERS_KEY, JSON.stringify(folders));
    console.log('Folder created:', name);
    return newFolder;
  } catch (error) {
    console.error('Failed to create folder:', error);
    return null;
  }
};

export const deleteFolder = (folderId) => {
  try {
    // Remove folder
    let folders = getFolders();
    folders = folders.filter(f => f.id !== folderId);
    localStorage.setItem(FOLDERS_KEY, JSON.stringify(folders));

    // Move items in this folder back to uncategorized
    const history = getHistory();
    history.forEach(item => {
      if (item.folderId === folderId) {
        item.folderId = null;
      }
    });
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));

    console.log('Folder deleted:', folderId);
    return true;
  } catch (error) {
    console.error('Failed to delete folder:', error);
    return false;
  }
};

export const renameFolder = (folderId, newName) => {
  try {
    const folders = getFolders();
    const folder = folders.find(f => f.id === folderId);
    if (folder) {
      folder.name = newName;
      localStorage.setItem(FOLDERS_KEY, JSON.stringify(folders));
      console.log('Folder renamed:', newName);
      return true;
    }
    return false;
  } catch (error) {
    console.error('Failed to rename folder:', error);
    return false;
  }
};

export const toggleFolderExpanded = (folderId) => {
  try {
    const folders = getFolders();
    const folder = folders.find(f => f.id === folderId);
    if (folder) {
      folder.expanded = !folder.expanded;
      localStorage.setItem(FOLDERS_KEY, JSON.stringify(folders));
      return folder.expanded;
    }
    return false;
  } catch (error) {
    console.error('Failed to toggle folder:', error);
    return false;
  }
};

export const moveHistoryToFolder = (historyIndex, folderId) => {
  try {
    const history = getHistory();
    if (historyIndex >= 0 && historyIndex < history.length) {
      history[historyIndex].folderId = folderId;
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
      console.log('History item moved to folder:', folderId);
      return true;
    }
    return false;
  } catch (error) {
    console.error('Failed to move history to folder:', error);
    return false;
  }
};

export const reorderHistory = (fromIndex, toIndex) => {
  try {
    const history = getHistory();
    if (fromIndex >= 0 && fromIndex < history.length && toIndex >= 0 && toIndex < history.length) {
      // Remove item from original position
      const [movedItem] = history.splice(fromIndex, 1);
      // Insert at new position
      history.splice(toIndex, 0, movedItem);

      localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
      console.log(`History reordered: moved item from ${fromIndex} to ${toIndex}`);
      return true;
    }
    return false;
  } catch (error) {
    console.error('Failed to reorder history:', error);
    return false;
  }
};

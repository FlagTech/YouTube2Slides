import React, { useState, useEffect } from 'react';
import './Sidebar.css';
import {
  getHistory,
  clearHistory as clearHistoryStorage,
  deleteHistoryItem as deleteHistoryItemStorage,
  syncHistoryFromBackend,
  shouldSync,
  getFolders,
  createFolder,
  deleteFolder,
  renameFolder,
  toggleFolderExpanded,
  moveHistoryToFolder,
  reorderHistory
} from '../utils/historyManager';
import { deleteVideo } from '../api/api';

function Sidebar({ onSelectHistory, onGoHome, currentJobId }) {
  const [isOpen, setIsOpen] = useState(false);
  const [history, setHistory] = useState([]);
  const [folders, setFolders] = useState([]);
  const [draggedItem, setDraggedItem] = useState(null);
  const [dragOverItem, setDragOverItem] = useState(null);
  const [editingFolderId, setEditingFolderId] = useState(null);
  const [editingFolderName, setEditingFolderName] = useState('');

  useEffect(() => {
    // Load history and folders from localStorage on mount
    const loadData = () => {
      const loadedHistory = getHistory();
      const loadedFolders = getFolders();
      setHistory(loadedHistory);
      setFolders(loadedFolders);
    };

    // Initial load
    loadData();

    // Sync from backend if needed
    const syncIfNeeded = async () => {
      if (shouldSync()) {
        await syncHistoryFromBackend();
        loadData(); // Reload after sync
      }
    };
    syncIfNeeded();

    // Set up an interval to check for updates
    const interval = setInterval(loadData, 1000);
    return () => clearInterval(interval);
  }, []);

  const toggleSidebar = () => {
    setIsOpen(!isOpen);
  };

  const handleSelectHistory = (item) => {
    onSelectHistory(item);
    setIsOpen(false);
  };

  const handleGoHome = () => {
    onGoHome();
    setIsOpen(false);
  };

  const deleteHistoryItem = async (e, index) => {
    e.stopPropagation();

    const history = getHistory();
    const item = history[index];

    if (!item) {
      console.error('Invalid history item');
      return;
    }

    // Get videoId from result object or fallback to jobId
    const videoId = item.videoId || (item.result && item.result.video_id) || item.jobId;

    if (!videoId) {
      console.error('No video ID found in history item');
      return;
    }

    // Confirm deletion
    if (!window.confirm(`確定要刪除「${item.title}」嗎？\n\n這將同時刪除本地儲存的影片和圖片檔案。`)) {
      return;
    }

    try {
      // Call backend API to delete files (pass videoId, not jobId)
      await deleteVideo(videoId);
      console.log('Video files deleted successfully');

      // Delete from localStorage
      if (deleteHistoryItemStorage(index)) {
        const updatedHistory = getHistory();
        setHistory(updatedHistory);
        console.log('History item deleted successfully');
      }
    } catch (error) {
      console.error('Failed to delete video files:', error);
      alert('刪除檔案失敗，請稍後再試');
    }
  };

  const clearAllHistory = async () => {
    if (!window.confirm('確定要清除所有歷史記錄嗎？\n\n這將同時刪除所有本地儲存的影片和圖片檔案。')) {
      return;
    }

    const currentHistory = getHistory();
    let deletedCount = 0;
    let failedCount = 0;

    // Delete all videos from backend
    for (const item of currentHistory) {
      // Get videoId from result object or fallback to jobId
      const videoId = item.videoId || (item.result && item.result.video_id) || item.jobId;

      if (videoId) {
        try {
          await deleteVideo(videoId);
          deletedCount++;
          console.log(`Deleted video: ${item.title}`);
        } catch (error) {
          console.error(`Failed to delete video ${item.title}:`, error);
          failedCount++;
        }
      }
    }

    // Clear localStorage and sync timestamp
    if (clearHistoryStorage()) {
      setHistory([]);
      // Clear last sync timestamp to prevent re-sync from bringing back deleted items
      localStorage.removeItem('lastHistorySync');
    }

    // Show result
    if (failedCount > 0) {
      alert(`已刪除 ${deletedCount} 個項目，${failedCount} 個項目刪除失敗`);
    } else {
      console.log(`All ${deletedCount} items deleted successfully`);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '剛剛';
    if (diffMins < 60) return `${diffMins} 分鐘前`;
    if (diffHours < 24) return `${diffHours} 小時前`;
    if (diffDays < 7) return `${diffDays} 天前`;
    return date.toLocaleDateString('zh-TW');
  };

  // Folder management functions
  const handleCreateFolder = () => {
    const folderName = prompt('請輸入資料夾名稱：');
    if (folderName && folderName.trim()) {
      createFolder(folderName.trim());
      setFolders(getFolders());
    }
  };

  const handleDeleteFolder = (e, folderId) => {
    e.stopPropagation();
    const folder = folders.find(f => f.id === folderId);
    if (window.confirm(`確定要刪除「${folder.name}」資料夾嗎？\n\n資料夾內的項目將移回未分類。`)) {
      deleteFolder(folderId);
      setFolders(getFolders());
      setHistory(getHistory());
    }
  };

  const handleRenameFolder = (folderId) => {
    const folder = folders.find(f => f.id === folderId);
    setEditingFolderId(folderId);
    setEditingFolderName(folder.name);
  };

  const handleRenameSubmit = (folderId) => {
    if (editingFolderName.trim()) {
      renameFolder(folderId, editingFolderName.trim());
      setFolders(getFolders());
    }
    setEditingFolderId(null);
    setEditingFolderName('');
  };

  const handleToggleFolder = (folderId) => {
    toggleFolderExpanded(folderId);
    setFolders(getFolders());
  };

  // Drag and drop functions
  const handleDragStart = (e, index) => {
    setDraggedItem(index);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDragOverItem = (e, index) => {
    e.preventDefault();
    e.stopPropagation();
    if (draggedItem !== null && draggedItem !== index) {
      setDragOverItem(index);
    }
  };

  const handleDragLeaveItem = (e) => {
    e.preventDefault();
    setDragOverItem(null);
  };

  const handleDropOnItem = (e, targetIndex) => {
    e.preventDefault();
    e.stopPropagation();

    if (draggedItem !== null && draggedItem !== targetIndex) {
      // Check if both items are in the same folder
      const currentHistory = getHistory();
      const draggedFolderId = currentHistory[draggedItem]?.folderId;
      const targetFolderId = currentHistory[targetIndex]?.folderId;

      if (draggedFolderId === targetFolderId) {
        // Same folder or both uncategorized - reorder
        reorderHistory(draggedItem, targetIndex);
        setHistory(getHistory());
      }
    }

    setDraggedItem(null);
    setDragOverItem(null);
  };

  const handleDropOnFolder = (e, folderId) => {
    e.preventDefault();
    if (draggedItem !== null) {
      moveHistoryToFolder(draggedItem, folderId);
      setHistory(getHistory());
      setDraggedItem(null);
      setDragOverItem(null);
    }
  };

  const handleDropOnUncategorized = (e) => {
    e.preventDefault();
    if (draggedItem !== null) {
      moveHistoryToFolder(draggedItem, null);
      setHistory(getHistory());
      setDraggedItem(null);
      setDragOverItem(null);
    }
  };

  const handleDragEnd = () => {
    setDraggedItem(null);
    setDragOverItem(null);
  };

  return (
    <>
      <button className="sidebar-toggle" onClick={toggleSidebar}>
        {isOpen ? '✕' : '☰'}
      </button>

      <div className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2>YouTube 影片轉換工具</h2>
          <button className="close-btn" onClick={toggleSidebar}>✕</button>
        </div>

        <div className="sidebar-content">
          <button className="home-btn" onClick={handleGoHome}>
            🏠 返回首頁
          </button>

          <div className="history-section">
            <div className="history-header">
              <h3>📋 歷史記錄</h3>
              <div className="history-header-actions">
                <button className="add-folder-btn" onClick={handleCreateFolder} title="新增資料夾">
                  📁+
                </button>
                {history.length > 0 && (
                  <button className="clear-all-btn" onClick={clearAllHistory}>
                    清除全部
                  </button>
                )}
              </div>
            </div>

            {history.length === 0 && folders.length === 0 ? (
              <p className="empty-message">尚無歷史記錄</p>
            ) : (
              <div className="history-list">
                {/* Folders */}
                {folders.map((folder) => (
                  <div key={folder.id} className="folder-container">
                    <div
                      className="folder-header"
                      onDragOver={handleDragOver}
                      onDrop={(e) => handleDropOnFolder(e, folder.id)}
                    >
                      <div className="folder-header-left" onClick={() => handleToggleFolder(folder.id)}>
                        <span className="folder-icon">{folder.expanded ? '📂' : '📁'}</span>
                        {editingFolderId === folder.id ? (
                          <input
                            type="text"
                            value={editingFolderName}
                            onChange={(e) => setEditingFolderName(e.target.value)}
                            onBlur={() => handleRenameSubmit(folder.id)}
                            onKeyPress={(e) => e.key === 'Enter' && handleRenameSubmit(folder.id)}
                            onClick={(e) => e.stopPropagation()}
                            autoFocus
                            className="folder-name-input"
                          />
                        ) : (
                          <span className="folder-name">{folder.name}</span>
                        )}
                        <span className="folder-count">
                          ({history.filter(item => item.folderId === folder.id).length})
                        </span>
                      </div>
                      <div className="folder-actions">
                        <button
                          className="rename-folder-btn"
                          onClick={(e) => { e.stopPropagation(); handleRenameFolder(folder.id); }}
                          title="重新命名"
                        >
                          ✏️
                        </button>
                        <button
                          className="delete-folder-btn"
                          onClick={(e) => handleDeleteFolder(e, folder.id)}
                          title="刪除資料夾"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>

                    {folder.expanded && (
                      <div className="folder-items">
                        {history
                          .map((item, index) => ({ item, index }))
                          .filter(({ item }) => item.folderId === folder.id)
                          .map(({ item, index }) => (
                            <div
                              key={index}
                              draggable
                              onDragStart={(e) => handleDragStart(e, index)}
                              onDragOver={(e) => handleDragOverItem(e, index)}
                              onDragLeave={handleDragLeaveItem}
                              onDrop={(e) => handleDropOnItem(e, index)}
                              onDragEnd={handleDragEnd}
                              className={`history-item ${item.jobId === currentJobId ? 'active' : ''} ${draggedItem === index ? 'dragging' : ''} ${dragOverItem === index ? 'drag-over' : ''}`}
                              onClick={() => handleSelectHistory(item)}
                            >
                              <div className="history-item-content">
                                <div className="history-title">{item.title || '未命名影片'}</div>
                                <div className="history-meta">
                                  <span className="history-time">{formatDate(item.timestamp)}</span>
                                  <span className="history-frames">{item.totalFrames} 張</span>
                                </div>
                              </div>
                              <button
                                className="delete-btn"
                                onClick={(e) => deleteHistoryItem(e, index)}
                                title="刪除"
                              >
                                🗑️
                              </button>
                            </div>
                          ))}
                      </div>
                    )}
                  </div>
                ))}

                {/* Uncategorized items */}
                {history.filter(item => !item.folderId).length > 0 && (
                  <div className="uncategorized-section">
                    <div
                      className="uncategorized-header"
                      onDragOver={handleDragOver}
                      onDrop={handleDropOnUncategorized}
                    >
                      <span>📄 未分類</span>
                    </div>
                    <div className="uncategorized-items">
                      {history
                        .map((item, index) => ({ item, index }))
                        .filter(({ item }) => !item.folderId)
                        .map(({ item, index }) => (
                          <div
                            key={index}
                            draggable
                            onDragStart={(e) => handleDragStart(e, index)}
                            onDragOver={(e) => handleDragOverItem(e, index)}
                            onDragLeave={handleDragLeaveItem}
                            onDrop={(e) => handleDropOnItem(e, index)}
                            onDragEnd={handleDragEnd}
                            className={`history-item ${item.jobId === currentJobId ? 'active' : ''} ${draggedItem === index ? 'dragging' : ''} ${dragOverItem === index ? 'drag-over' : ''}`}
                            onClick={() => handleSelectHistory(item)}
                          >
                            <div className="history-item-content">
                              <div className="history-title">{item.title || '未命名影片'}</div>
                              <div className="history-meta">
                                <span className="history-time">{formatDate(item.timestamp)}</span>
                                <span className="history-frames">{item.totalFrames} 張</span>
                              </div>
                            </div>
                            <button
                              className="delete-btn"
                              onClick={(e) => deleteHistoryItem(e, index)}
                              title="刪除"
                            >
                              🗑️
                            </button>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {isOpen && <div className="sidebar-overlay" onClick={toggleSidebar}></div>}
    </>
  );
}

export default Sidebar;

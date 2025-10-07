import React, { useState, useEffect } from 'react';
import './Sidebar.css';
import {
  getHistory,
  clearHistory as clearHistoryStorage,
  deleteHistoryItem as deleteHistoryItemStorage,
  syncHistoryFromBackend,
  shouldSync
} from '../utils/historyManager';
import { deleteVideo } from '../api/api';

function Sidebar({ onSelectHistory, onGoHome, currentJobId }) {
  const [isOpen, setIsOpen] = useState(false);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    // Load history from localStorage on mount
    const loadHistory = () => {
      const loadedHistory = getHistory();
      setHistory(loadedHistory);
    };

    // Initial load
    loadHistory();

    // Sync from backend if needed
    const syncIfNeeded = async () => {
      if (shouldSync()) {
        await syncHistoryFromBackend();
        loadHistory(); // Reload after sync
      }
    };
    syncIfNeeded();

    // Set up an interval to check for updates
    const interval = setInterval(loadHistory, 1000);
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

    if (!item || !item.jobId) {
      console.error('Invalid history item');
      return;
    }

    // Confirm deletion
    if (!window.confirm(`確定要刪除「${item.title}」嗎？\n\n這將同時刪除本地儲存的影片和圖片檔案。`)) {
      return;
    }

    try {
      // Call backend API to delete files
      await deleteVideo(item.jobId);
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
      if (item.jobId) {
        try {
          await deleteVideo(item.jobId);
          deletedCount++;
          console.log(`Deleted video: ${item.title}`);
        } catch (error) {
          console.error(`Failed to delete video ${item.title}:`, error);
          failedCount++;
        }
      }
    }

    // Clear localStorage
    if (clearHistoryStorage()) {
      setHistory([]);
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
              {history.length > 0 && (
                <button className="clear-all-btn" onClick={clearAllHistory}>
                  清除全部
                </button>
              )}
            </div>

            {history.length === 0 ? (
              <p className="empty-message">尚無歷史記錄</p>
            ) : (
              <div className="history-list">
                {history.map((item, index) => (
                  <div
                    key={index}
                    className={`history-item ${item.jobId === currentJobId ? 'active' : ''}`}
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
        </div>
      </div>

      {isOpen && <div className="sidebar-overlay" onClick={toggleSidebar}></div>}
    </>
  );
}

export default Sidebar;

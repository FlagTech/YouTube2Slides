import React, { useState, useEffect } from 'react';
import './Sidebar.css';
import {
  getHistory,
  clearHistory as clearHistoryStorage,
  deleteHistoryItem as deleteHistoryItemStorage,
  syncHistoryFromBackend,
  shouldSync
} from '../utils/historyManager';

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

  const deleteHistoryItem = (e, index) => {
    e.stopPropagation();
    if (deleteHistoryItemStorage(index)) {
      const updatedHistory = getHistory();
      setHistory(updatedHistory);
    }
  };

  const clearAllHistory = () => {
    if (window.confirm('確定要清除所有歷史記錄嗎？')) {
      if (clearHistoryStorage()) {
        setHistory([]);
      }
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

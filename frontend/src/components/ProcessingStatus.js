import React, { useState, useEffect, useMemo } from 'react';
import './ProcessingStatus.css';
import { getJobStatus } from '../api/api';

const formatTimestamp = (timestamp) => {
  if (!timestamp) return '';
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-TW', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch (err) {
    return timestamp;
  }
};

// 定義處理步驟（無圖示）
const PROCESSING_STEPS = [
  { key: 'queued', label: '等待中' },
  { key: 'prepare', label: '準備中' },
  { key: 'metadata', label: '擷取資訊' },
  { key: 'download_video', label: '下載影片' },
  { key: 'fetch_subtitles', label: '獲取字幕' },
  { key: 'ai_transcription', label: 'AI字幕' },
  { key: 'subtitle_optimize', label: '優化字幕' },
  { key: 'subtitle_parse', label: '解析字幕' },
  { key: 'keyframe_selection', label: '選擇關鍵幀' },
  { key: 'translate', label: '翻譯字幕' },
  { key: 'frame_capture', label: '擷取影格' },
  { key: 'frame_optimize', label: '壓縮影格' },
  { key: 'ai_outline', label: 'AI大綱' },
  { key: 'finalize', label: '整理結果' },
  { key: 'complete', label: '完成' },
];

function ProcessingStatus({ jobId }) {
  const [status, setStatus] = useState({
    progress: 0,
    message: '等待處理...',
    status: 'pending',
    history: [],
    currentStep: 'queued',
  });
  const [displayProgress, setDisplayProgress] = useState(0);
  const [targetProgress, setTargetProgress] = useState(0);

  // Debug: Log jobId on mount
  useEffect(() => {
    console.log('[ProcessingStatus] Mounted with jobId:', jobId);
  }, [jobId]);

  // Smooth progress animation
  useEffect(() => {
    const animationInterval = setInterval(() => {
      setDisplayProgress((current) => {
        if (current < targetProgress) {
          // Gradually increase progress (faster when far from target, slower when close)
          const diff = targetProgress - current;
          const increment = Math.max(0.5, diff / 10);
          return Math.min(current + increment, targetProgress);
        } else if (current > targetProgress) {
          // Immediately jump down if target decreased
          return targetProgress;
        }
        return current;
      });
    }, 50); // Update animation every 50ms for smooth effect

    return () => clearInterval(animationInterval);
  }, [targetProgress]);

  useEffect(() => {
    if (!jobId) return;

    let isMounted = true;
    const pollStatus = async () => {
      try {
        const jobStatus = await getJobStatus(jobId);
        if (!isMounted) return;

        const newProgress = jobStatus.progress ?? 0;
        const newMessage = jobStatus.message ?? '處理中...';
        const newStatus = jobStatus.status ?? 'processing';

        // Debug: 顯示進度更新
        console.log('[ProcessingStatus] Job Status Update:', {
          jobId: jobId,
          progress: newProgress,
          currentStep: jobStatus.current_step,
          message: newMessage,
          status: newStatus,
          timestamp: new Date().toLocaleTimeString()
        });

        setStatus({
          progress: newProgress,
          message: newMessage,
          status: newStatus,
          history: jobStatus.history ?? [],
          currentStep: jobStatus.current_step ?? null,
        });

        // Update target progress for animation
        setTargetProgress(newProgress);

        if (newStatus === 'completed' || newStatus === 'failed') {
          // When completed, set display progress immediately to 100%
          if (newStatus === 'completed') {
            setDisplayProgress(100);
          }
          return false;
        }
      } catch (err) {
        console.error('[ProcessingStatus] Failed to get job status:', err);
        console.error('[ProcessingStatus] Error details:', {
          message: err.message,
          response: err.response?.data,
          status: err.response?.status
        });
      }
      return true;
    };

    const interval = setInterval(async () => {
      const shouldContinue = await pollStatus();
      if (shouldContinue === false) {
        console.log('[ProcessingStatus] Polling stopped - job completed or failed');
        clearInterval(interval);
      }
    }, 500);

    // Fetch immediately instead of waiting for the first interval tick
    pollStatus();

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [jobId]);

  // 獲取當前步驟信息
  const getCurrentStepInfo = () => {
    if (!status.currentStep) return null;
    const step = PROCESSING_STEPS.find(s => s.key === status.currentStep);
    return step ? step.label : status.currentStep;
  };

  const isComplete = status.status === 'completed';
  const isFailed = status.status === 'failed';
  const currentStepLabel = getCurrentStepInfo();

  return (
    <div className="processing-status">
      <h2>處理進度</h2>

      {!isComplete && !isFailed && <div className="spinner" aria-hidden="true"></div>}
      {isComplete && <div className="status-badge status-badge--success">已完成</div>}
      {isFailed && <div className="status-badge status-badge--error">處理失敗</div>}

      {/* 當前步驟顯示 */}
      {!isComplete && !isFailed && currentStepLabel && (
        <div className="current-step">
          <div className="current-step-label">當前步驟</div>
          <div className="current-step-name">{currentStepLabel}</div>
        </div>
      )}

      {/* 進度條 */}
      <div className="progress-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow={Math.round(displayProgress)}>
        <div
          className="progress-fill"
          style={{
            width: `${displayProgress}%`,
            transition: 'width 0.3s ease-out'
          }}
        ></div>
      </div>
      <p className="progress-text">{Math.round(displayProgress)}%</p>
      <p className="status-message">{status.message}</p>
    </div>
  );
}

export default ProcessingStatus;

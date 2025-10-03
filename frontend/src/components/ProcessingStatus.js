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

function ProcessingStatus({ jobId }) {
  const [status, setStatus] = useState({
    progress: 0,
    message: '初始化...',
    status: 'pending',
    history: [],
    currentStep: null,
  });
  const [displayProgress, setDisplayProgress] = useState(0);
  const [targetProgress, setTargetProgress] = useState(0);

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
        console.error('Failed to get job status:', err);
      }
      return true;
    };

    const interval = setInterval(async () => {
      const shouldContinue = await pollStatus();
      if (shouldContinue === false) {
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

  const timeline = useMemo(() => {
    if (!status.history || status.history.length === 0) {
      return [
        {
          timestamp: new Date().toISOString(),
          status: status.status,
          progress: status.progress,
          step: status.currentStep || 'processing',
          message: status.message,
        },
      ];
    }

    return status.history;
  }, [status.history, status.currentStep, status.message, status.progress, status.status]);

  const isComplete = status.status === 'completed';
  const isFailed = status.status === 'failed';

  return (
    <div className="processing-status">
      <h2>處理進度</h2>

      {!isComplete && !isFailed && <div className="spinner" aria-hidden="true"></div>}
      {isComplete && <div className="status-badge status-badge--success">已完成</div>}
      {isFailed && <div className="status-badge status-badge--error">處理失敗</div>}

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

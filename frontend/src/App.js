import React, { useState } from 'react';
import './App.css';
import VideoInput from './components/VideoInput';
import ProcessingStatus from './components/ProcessingStatus';
import SlideViewer from './components/SlideViewer';
import Sidebar from './components/Sidebar';
import { processVideo, getJobStatus } from './api/api';
import { saveToHistory } from './utils/historyManager';

function App() {
  const [jobId, setJobId] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (videoData) => {
    console.log('[App] Starting video processing with data:', videoData);
    setProcessing(true);
    setError(null);
    setResult(null);

    try {
      const response = await processVideo(videoData);
      const newJobId = response.job_id;
      console.log('[App] Job created with ID:', newJobId);
      setJobId(newJobId);

      // Poll for job status
      pollJobStatus(newJobId);
    } catch (err) {
      console.error('[App] Error processing video:', err);
      setError(err.message || 'Failed to process video');
      setProcessing(false);
    }
  };

  const pollJobStatus = async (currentJobId) => {
    console.log('[App] Starting to poll job status for:', currentJobId);
    const interval = setInterval(async () => {
      try {
        const status = await getJobStatus(currentJobId);
        console.log('[App] Polled job status:', status);

        if (status.status === 'completed') {
          console.log('[App] Job completed, stopping poll');
          clearInterval(interval);
          setResult(status.result);
          setProcessing(false);

          // Save to history
          saveToHistory(status.result, currentJobId);
        } else if (status.status === 'failed') {
          console.log('[App] Job failed:', status.error);
          clearInterval(interval);
          setError(status.error || 'Processing failed');
          setProcessing(false);
        }
      } catch (err) {
        console.error('[App] Error polling job status:', err);
        clearInterval(interval);
        setError('Failed to get job status');
        setProcessing(false);
      }
    }, 2000); // Poll every 2 seconds
  };

  const handleSelectHistory = (historyItem) => {
    setResult(historyItem.result);
    setJobId(historyItem.jobId);
    setProcessing(false);
    setError(null);
  };

  const handleGoHome = () => {
    handleReset();
  };

  const handleReset = () => {
    setJobId(null);
    setProcessing(false);
    setResult(null);
    setError(null);
  };

  return (
    <div className="App">
      <Sidebar
        onSelectHistory={handleSelectHistory}
        onGoHome={handleGoHome}
        currentJobId={jobId}
      />

      <header className="App-header">
        <h1>YouTube 影片懶人觀看術</h1>
        <p>將 YouTube 影片轉換為靜態投影片與字幕</p>
      </header>

      <main className="App-main">
        {!processing && !result && (
          <VideoInput onSubmit={handleSubmit} />
        )}

        {processing && (
          <ProcessingStatus jobId={jobId} />
        )}

        {error && (
          <div className="error-message">
            <h3>錯誤</h3>
            <p>{error}</p>
            <button onClick={handleReset}>重試</button>
          </div>
        )}

        {result && (
          <SlideViewer result={result} onReset={handleReset} />
        )}
      </main>

      <footer className="App-footer">
        <p>&copy; 2025 YouTube 影片懶人觀看術</p>
      </footer>
    </div>
  );
}

export default App;

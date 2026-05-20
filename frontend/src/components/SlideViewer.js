import React, { useState, useEffect, useCallback, useRef } from 'react';
import './SlideViewer.css';

function SlideViewer({ result, onReset }) {
  const [currentSlide, setCurrentSlide] = useState(0);

  const frames = result?.frames || [];
  const title = result?.title || '';
  const total_frames = result?.total_frames || 0;
  const ai_outline = result?.ai_outline || null;
  const ai_outline_error = result?.ai_outline_error || null;
  const ai_provider = result?.ai_provider || null;
  const video_id = result?.video_id || '';
  const translated_subtitle = result?.translated_subtitle || null;
  const frame = frames[currentSlide];
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Format seconds to MM:SS
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Get video duration from last frame
  const videoDuration = frames.length > 0 ? frames[frames.length - 1].timestamp : 0;
  const safeDuration = videoDuration || 0;

  const thumbnailStripRef = useRef(null);

  // Download functions
  const downloadFile = async (url, filename) => {
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error('下載失敗:', error);
      alert('下載失敗，請稍後再試');
    }
  };

  const downloadCurrentFrame = async () => {
    if (!frame) return;
    const url = `${API_BASE_URL}/${frame.path.replace(/\\/g, '/')}`;
    await downloadFile(url, frame.filename);
  };

  const downloadAllFrames = async () => {
    if (!video_id) return;

    try {
      // 顯示下載中提示
      const downloadBtn = document.activeElement;
      const originalText = downloadBtn?.textContent;
      if (downloadBtn) downloadBtn.textContent = '⏳ 打包中...';

      // 呼叫後端 API 打包所有截圖
      const response = await fetch(`${API_BASE_URL}/api/video/${video_id}/download-frames`);

      if (!response.ok) {
        throw new Error('打包失敗');
      }

      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `${video_id}_all_frames.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);

      if (downloadBtn) downloadBtn.textContent = originalText;
    } catch (error) {
      console.error('下載全部截圖失敗:', error);
      alert('下載失敗，請稍後再試');
    }
  };

  const downloadSubtitles = async () => {
    if (!result?.subtitles) return;

    for (const [lang, path] of Object.entries(result.subtitles)) {
      const url = `${API_BASE_URL}/${path.replace(/\\/g, '/')}`;
      await downloadFile(url, `${video_id}_${lang}.srt`);
      // 小延遲避免瀏覽器阻擋多個下載
      await new Promise(resolve => setTimeout(resolve, 300));
    }
  };

  const downloadTranslatedSubtitle = async () => {
    if (!translated_subtitle) return;

    const url = `${API_BASE_URL}/${translated_subtitle.replace(/\\/g, '/')}`;
    const filename = translated_subtitle.split(/[\\/]/).pop();
    await downloadFile(url, filename);
  };

  const downloadAIOutline = () => {
    if (!ai_outline) return;
    const blob = new Blob([ai_outline], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${video_id}_outline_${ai_provider}.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const nextSlide = useCallback(() => {
    if (currentSlide < frames.length - 1) {
      setCurrentSlide(currentSlide + 1);
    }
  }, [currentSlide, frames.length]);

  const prevSlide = useCallback(() => {
    if (currentSlide > 0) {
      setCurrentSlide(currentSlide - 1);
    }
  }, [currentSlide]);

  const goToSlide = useCallback((index) => {
    setCurrentSlide(index);
  }, []);

  // Auto-scroll to center the active thumbnail
  useEffect(() => {
    if (!thumbnailStripRef.current) return;

    const container = thumbnailStripRef.current;
    const thumbnails = container.querySelectorAll('.thumbnail');
    const activeThumbnail = thumbnails[currentSlide];

    if (activeThumbnail) {
      const containerRect = container.getBoundingClientRect();
      const thumbnailRect = activeThumbnail.getBoundingClientRect();

      const scrollLeft = container.scrollLeft;
      const thumbnailCenter = thumbnailRect.left - containerRect.left + scrollLeft + thumbnailRect.width / 2;
      const containerCenter = containerRect.width / 2;

      container.scrollTo({
        left: thumbnailCenter - containerCenter,
        behavior: 'smooth'
      });
    }
  }, [currentSlide]);

  const handleKeyPress = useCallback((e) => {
    if (e.key === 'ArrowRight') nextSlide();
    if (e.key === 'ArrowLeft') prevSlide();
  }, [nextSlide, prevSlide]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [handleKeyPress]);

  if (!result || !result.frames || result.frames.length === 0) {
    return (
      <div className="slide-viewer">
        <p>沒有可用的投影片</p>
      </div>
    );
  }

  // Construct YouTube URL from video_id
  const youtubeUrl = video_id ? `https://www.youtube.com/watch?v=${video_id}` : null;

  return (
    <div className="slide-viewer" tabIndex="0">
      <div className="viewer-header">
        {youtubeUrl ? (
          <h2>
            <a
              href={youtubeUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                color: 'inherit',
                textDecoration: 'none',
                borderBottom: '2px solid transparent',
                transition: 'border-color 0.3s ease'
              }}
              onMouseEnter={(e) => e.target.style.borderBottom = '2px solid #764ba2'}
              onMouseLeave={(e) => e.target.style.borderBottom = '2px solid transparent'}
            >
              {title} 🔗
            </a>
          </h2>
        ) : (
          <h2>{title}</h2>
        )}
        <p>
          第 {currentSlide + 1} 張，共 {total_frames} 張
        </p>
        <div className="header-actions">
          <button onClick={onReset} className="reset-btn">
            處理其他影片
          </button>
        </div>
      </div>

      <div className="slide-container">
        <button
          className="nav-btn prev-btn"
          onClick={prevSlide}
          disabled={currentSlide === 0}
        >
          ‹
        </button>

        <div className="slide-content">
          <img
            src={`${API_BASE_URL}/${frame.path.replace(/\\/g, '/')}`}
            alt={`Slide ${currentSlide + 1}`}
            className="slide-image"
          />
          {frame.subtitle && (
            <div className="subtitle-box original-subtitle">
              <div className="subtitle-label">原文</div>
              <p dangerouslySetInnerHTML={{ __html: frame.subtitle }}></p>
            </div>
          )}
          {frame.subtitle_translated && (
            <div className="subtitle-box translated-subtitle">
              <div className="subtitle-label">翻譯</div>
              <p dangerouslySetInnerHTML={{ __html: frame.subtitle_translated }}></p>
            </div>
          )}
        </div>

        <button
          className="nav-btn next-btn"
          onClick={nextSlide}
          disabled={currentSlide === frames.length - 1}
        >
          ›
        </button>
      </div>

      <div className="thumbnail-strip-container">
        <div
          className="thumbnail-strip"
          ref={thumbnailStripRef}
        >
          {frames.map((f, index) => (
            <div
              key={index}
              className={`thumbnail ${index === currentSlide ? 'active' : ''}`}
              onClick={(e) => {
                // Prevent event from bubbling to container
                e.stopPropagation();
                goToSlide(index);
              }}
              style={{ pointerEvents: 'auto' }}
            >
              <img
                src={`${API_BASE_URL}/${f.path.replace(/\\/g, '/')}`}
                alt={`Thumbnail ${index + 1}`}
                draggable="false"
              />
              <span>{index + 1}</span>
            </div>
          ))}
        </div>

        <div className="thumbnail-strip-footer">
          <span className="timeline-time">{formatTime(frame?.timestamp ?? 0)}</span>
          <span className="timeline-time">{formatTime(safeDuration)}</span>
        </div>
      </div>

      <div className="download-section">
        <h3>📥 下載選項</h3>
        <div className="download-buttons">
          <button onClick={downloadCurrentFrame} className="download-btn">
            📷 下載當前截圖
          </button>
          <button onClick={downloadAllFrames} className="download-btn">
            🖼️ 下載全部截圖 ({total_frames})
          </button>
          <button onClick={downloadSubtitles} className="download-btn">
            📝 下載原始字幕檔
          </button>
          {translated_subtitle && (
            <button onClick={downloadTranslatedSubtitle} className="download-btn">
              🌐 下載翻譯字幕檔
            </button>
          )}
          {ai_outline && (
            <button onClick={downloadAIOutline} className="download-btn">
              🤖 下載 AI 大綱
            </button>
          )}
        </div>
      </div>

      {ai_outline && (
        <div className="ai-outline-section">
          <h3>📝 AI 影片大綱 {ai_provider && `(${ai_provider})`}</h3>
          <div className="ai-outline-content">
            <pre>{ai_outline}</pre>
          </div>
        </div>
      )}

      {!ai_outline && ai_outline_error && (
        <div className="ai-outline-section ai-outline-error">
          <h3>📝 AI 影片大綱</h3>
          <div className="ai-outline-error-content">
            <p>⚠️ AI 大綱產生失敗</p>
            <p className="error-detail">{ai_outline_error}</p>
            <p className="error-hint">
              {ai_outline_error.includes('Ollama') || ai_outline_error.includes('Connection') || ai_outline_error.includes('connect')
                ? '請確認 Ollama 服務已啟動（ollama serve），並已下載所需模型（ollama pull qwen3:8b）'
                : '請確認 API 金鑰正確，或稍後再試'}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default SlideViewer;

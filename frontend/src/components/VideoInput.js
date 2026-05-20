import React, { useState, useEffect } from 'react';
import './VideoInput.css';
import { getSettings, saveSettings, getDefaultSettings } from '../utils/settingsManager';

function VideoInput({ onSubmit }) {
  const [url, setUrl] = useState('');
  const [quality, setQuality] = useState('720');
  const [translateTo, setTranslateTo] = useState('');
  const [generateOutline, setGenerateOutline] = useState(false);
  const [aiProvider, setAiProvider] = useState('openai');
  const [aiModel, setAiModel] = useState('gpt-4o-mini');
  const [apiKey, setApiKey] = useState('');
  const [screenshotPosition, setScreenshotPosition] = useState('middle');
  const [screenshotOffset, setScreenshotOffset] = useState(0);
  const [ollamaModels, setOllamaModels] = useState([]);
  const [loadingOllamaModels, setLoadingOllamaModels] = useState(false);
  const [useAiTranscription, setUseAiTranscription] = useState(false);
  const [whisperApiKey, setWhisperApiKey] = useState('');
  const [screenshotSettingsExpanded, setScreenshotSettingsExpanded] = useState(false);

  // Load saved settings on mount
  useEffect(() => {
    const savedSettings = getSettings();
    if (savedSettings) {
      if (savedSettings.quality) setQuality(savedSettings.quality);
      if (savedSettings.translateTo !== undefined) setTranslateTo(savedSettings.translateTo);
      if (savedSettings.screenshotPosition) setScreenshotPosition(savedSettings.screenshotPosition);
      if (savedSettings.screenshotOffset !== undefined) setScreenshotOffset(savedSettings.screenshotOffset);
      if (savedSettings.generateOutline !== undefined) setGenerateOutline(savedSettings.generateOutline);
      if (savedSettings.aiProvider) setAiProvider(savedSettings.aiProvider);
      if (savedSettings.aiModel) setAiModel(savedSettings.aiModel);
      if (savedSettings.apiKey) setApiKey(savedSettings.apiKey);
      if (savedSettings.useAiTranscription !== undefined) setUseAiTranscription(savedSettings.useAiTranscription);
      if (savedSettings.whisperApiKey) setWhisperApiKey(savedSettings.whisperApiKey);
    }
  }, []);

  // Load Ollama models when provider changes to Ollama
  useEffect(() => {
    if (aiProvider === 'ollama' && generateOutline) {
      loadOllamaModels();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [aiProvider, generateOutline]);

  const loadOllamaModels = async () => {
    setLoadingOllamaModels(true);
    try {
      const response = await fetch('http://localhost:8000/api/ollama/models');
      const data = await response.json();
      if (data.models && data.models.length > 0) {
        setOllamaModels(data.models);
        // Set first model as default if no model is selected
        if (!aiModel || aiModel === 'gpt-5.4-mini' || aiModel === 'claude-sonnet-4-6') {
          setAiModel(data.models[0].name);
        }
      } else {
        setOllamaModels([]);
        alert('未檢測到 Ollama 模型。請確認 Ollama 已安裝並運行。');
      }
    } catch (error) {
      console.error('Failed to load Ollama models:', error);
      setOllamaModels([]);
      alert('無法連接到 Ollama 服務。請確認 Ollama 已啟動。');
    } finally {
      setLoadingOllamaModels(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!url.trim()) {
      alert('請輸入 YouTube 網址');
      return;
    }

    // Validation: Check if Whisper API key is provided when AI transcription is enabled
    if (useAiTranscription && !whisperApiKey.trim()) {
      alert('請輸入 OpenAI API Key 以使用 AI 字幕生成');
      return;
    }

    // Save current settings
    const currentSettings = {
      quality,
      translateTo,
      screenshotPosition,
      screenshotOffset,
      generateOutline,
      aiProvider,
      aiModel,
      apiKey,
      useAiTranscription,
      whisperApiKey
    };
    saveSettings(currentSettings);

    onSubmit({
      url,
      quality,
      subtitle_languages: null, // Auto-detect
      translate_to: translateTo || null,
      screenshot_position: screenshotPosition,
      screenshot_offset: parseFloat(screenshotOffset),
      generate_outline: generateOutline,
      ai_provider: generateOutline ? aiProvider : null,
      ai_model: generateOutline ? aiModel : null,
      api_key: generateOutline ? apiKey : null,
      use_ai_transcription: useAiTranscription,
      whisper_api_key: useAiTranscription ? whisperApiKey : null,
    });
  };


  const handleProviderChange = (provider) => {
    setAiProvider(provider);
    // Set default model based on provider
    if (provider === 'openai') {
      setAiModel('gpt-5.4-mini');
    } else if (provider === 'claude') {
      setAiModel('claude-sonnet-4-6');
    } else if (provider === 'gemini') {
      setAiModel('gemini-3.5-flash');
    } else if (provider === 'ollama') {
      // Will be set when models are loaded
      setAiModel('qwen3:8b');
    }
  };

  const getModelOptions = () => {
    switch (aiProvider) {
      case 'openai':
        return [
          { value: 'gpt-5.4-mini', label: 'GPT-5.4 Mini (推薦)' },
          { value: 'gpt-5.5', label: 'GPT-5.5 (旗艦)' },
          { value: 'gpt-5.5-pro', label: 'GPT-5.5 Pro (最高精度)' },
          { value: 'gpt-5.4', label: 'GPT-5.4' },
          { value: 'gpt-4o', label: 'GPT-4o (舊版)' },
          { value: 'gpt-4o-mini', label: 'GPT-4o Mini (舊版)' }
        ];
      case 'claude':
        return [
          { value: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6 (推薦)' },
          { value: 'claude-opus-4-7', label: 'Claude Opus 4.7 (最強)' },
          { value: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5 (最快)' }
        ];
      case 'gemini':
        return [
          { value: 'gemini-3.5-flash', label: 'Gemini 3.5 Flash (推薦)' },
          { value: 'gemini-3.1-pro-preview', label: 'Gemini 3.1 Pro Preview (最強)' },
          { value: 'gemini-3.1-flash-lite', label: 'Gemini 3.1 Flash Lite (最省錢)' },
          { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro (上一代)' },
          { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash (上一代)' }
        ];
      case 'ollama':
        return ollamaModels.map(model => ({
          value: model.name,
          label: `${model.name} (本機)`
        }));
      default:
        return [];
    }
  };

  const handleClearSettings = () => {
    if (window.confirm('確定要清除已儲存的設定嗎？')) {
      const defaults = getDefaultSettings();
      setQuality(defaults.quality);
      setTranslateTo(defaults.translateTo);
      setScreenshotPosition('middle');
      setScreenshotOffset(0);
      setGenerateOutline(defaults.generateOutline);
      setAiProvider(defaults.aiProvider);
      setAiModel(defaults.aiModel);
      setApiKey(defaults.apiKey);
      localStorage.removeItem('videoConverterSettings');
      alert('✅ 設定已重置為預設值');
    }
  };

  return (
    <div className="video-input">
      <div className="header-with-clear">
        <h2>YouTube 影片懶人觀看術</h2>
        <button type="button" className="clear-settings-btn" onClick={handleClearSettings} title="清除已儲存的設定">
          🔄 重置設定
        </button>
      </div>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>YouTube 網址</label>
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.youtube.com/watch?v=..."
            required
          />
        </div>

        <div className="form-group">
          <label>影片畫質</label>
          <select value={quality} onChange={(e) => setQuality(e.target.value)}>
            <option value="360">360p</option>
            <option value="480">480p</option>
            <option value="720">720p (推薦)</option>
            <option value="1080">1080p (Full HD)</option>
          </select>
        </div>

        <div className="info-box" style={{marginBottom: '1rem'}}>
          <p>💡 字幕語言將自動偵測（優先順序：繁體中文 → 簡體中文 → 英文）</p>
        </div>

        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={useAiTranscription}
              onChange={(e) => setUseAiTranscription(e.target.checked)}
            />
            <span>使用 AI 生成字幕（無字幕或字幕品質不佳時適用）</span>
          </label>
        </div>

        {useAiTranscription && (
          <div className="ai-config-section">
            <div className="form-group">
              <label>OpenAI API Key（用於 Whisper 語音辨識）</label>
              <input
                type="password"
                value={whisperApiKey}
                onChange={(e) => setWhisperApiKey(e.target.value)}
                placeholder="sk-..."
                className="api-key-input"
              />
              <small className="help-text">
                💡 使用 OpenAI Whisper 模型從影片音訊生成字幕。您的 API Key 僅用於此次請求，不會儲存於伺服器
              </small>
            </div>
            <div className="info-box" style={{marginTop: '1rem'}}>
              <p>⚠️ AI 字幕生成會從影片中提取音訊並使用 Whisper 模型轉錄，可能需要較長時間且消耗 API 額度</p>
            </div>
          </div>
        )}

        <div className="form-group">
          <label>翻譯語言（可選）</label>
          <select value={translateTo} onChange={(e) => setTranslateTo(e.target.value)}>
            <option value="">-- 不翻譯 --</option>
            <option value="zh-TW">繁體中文</option>
            <option value="zh-CN">简体中文</option>
            <option value="en">English</option>
            <option value="ja">日本語</option>
            <option value="ko">한국어</option>
          </select>
        </div>

        <div className="screenshot-settings">
          <div
            className="screenshot-settings-header"
            onClick={() => setScreenshotSettingsExpanded(!screenshotSettingsExpanded)}
          >
            <h3>📸 截圖時間點設定</h3>
            <span className="expand-icon">{screenshotSettingsExpanded ? '▼' : '▶'}</span>
          </div>

          {screenshotSettingsExpanded && (
            <div className="screenshot-settings-content">
              <div className="form-group">
                <label>截圖位置</label>
                <select value={screenshotPosition} onChange={(e) => setScreenshotPosition(e.target.value)}>
                  <option value="start">字幕開始</option>
                  <option value="middle">字幕中間（推薦）</option>
                  <option value="end">字幕結尾</option>
                </select>
                <small className="help-text">
                  選擇在字幕時間段的哪個位置截圖
                </small>
              </div>

              <div className="form-group">
                <label>時間偏移（秒）</label>
                <input
                  type="number"
                  step="0.1"
                  value={screenshotOffset}
                  onChange={(e) => setScreenshotOffset(e.target.value)}
                  placeholder="0.0"
                />
                <small className="help-text">
                  微調截圖時間（負數向前、正數向後）例如：-0.5 表示提前 0.5 秒截圖
                </small>
              </div>
            </div>
          )}
        </div>

        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={generateOutline}
              onChange={(e) => setGenerateOutline(e.target.checked)}
            />
            <span>AI 翻譯 & 生成 AI 影片大綱</span>
          </label>
        </div>

        {generateOutline && (
          <div className="ai-config-section">
            <div className="form-group">
              <label>AI 服務提供商</label>
              <select value={aiProvider} onChange={(e) => handleProviderChange(e.target.value)}>
                <option value="openai">OpenAI</option>
                <option value="claude">Claude (Anthropic)</option>
                <option value="gemini">Gemini (Google)</option>
                <option value="ollama">Ollama (本機運行)</option>
              </select>
            </div>

            <div className="form-group">
              <label>AI 模型</label>
              <select
                value={aiModel}
                onChange={(e) => setAiModel(e.target.value)}
                disabled={aiProvider === 'ollama' && loadingOllamaModels}
              >
                {loadingOllamaModels ? (
                  <option>載入中...</option>
                ) : getModelOptions().length > 0 ? (
                  getModelOptions().map(model => (
                    <option key={model.value} value={model.value}>
                      {model.label}
                    </option>
                  ))
                ) : aiProvider === 'ollama' ? (
                  <option>未檢測到模型</option>
                ) : (
                  <option>請選擇提供商</option>
                )}
              </select>
              {aiProvider === 'ollama' && ollamaModels.length > 0 && (
                <small className="help-text">
                  ✓ 已檢測到 {ollamaModels.length} 個本機模型
                </small>
              )}
              {aiProvider === 'ollama' && ollamaModels.length === 0 && !loadingOllamaModels && (
                <small className="help-text" style={{color: '#f44336'}}>
                  ⚠ 未檢測到 Ollama 模型，請確認 Ollama 已安裝並運行
                </small>
              )}
            </div>

            {aiProvider !== 'ollama' && (
              <div className="form-group">
                <label>API 金鑰</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={`請輸入您的 ${aiProvider.toUpperCase()} API 金鑰`}
                  className="api-key-input"
                />
                <small className="help-text">
                  您的 API Key 僅用於此次請求，不會儲存於伺服器
                </small>
              </div>
            )}

            {aiProvider === 'ollama' && (
              <div className="info-box" style={{marginTop: '1rem'}}>
                <p>💡 Ollama 在本機運行，無需 API 金鑰</p>
              </div>
            )}
          </div>
        )}

        <button type="submit" className="submit-btn">
          開始處理影片
        </button>
      </form>
    </div>
  );
}

export default VideoInput;

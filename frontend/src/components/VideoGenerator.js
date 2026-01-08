import { useState, useEffect, useRef } from "react";
import "./VideoGenerator.css";

export default function VideoGenerator() {
  const [activeTab, setActiveTab] = useState("file"); // 'file' or 'text'
  const [file, setFile] = useState(null);
  const [text, setText] = useState("");
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null); // 'queued', 'started', 'completed', 'failed'
  const [videoUrl, setVideoUrl] = useState(null);
  const [error, setError] = useState("");
  const fileInputRef = useRef(null);
  const [videos, setVideos] = useState([]);

  // Add this useEffect to load history
  useEffect(() => {
    fetchHistory();
    const interval = setInterval(fetchHistory, 5000); // Auto-refresh every 5s
    return () => clearInterval(interval);
  }, []);

  async function fetchHistory() {
    const token = localStorage.getItem("token");
    const res = await fetch("http://localhost:8000/videos/mine", {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) setVideos(await res.json());
  }
  // Poll for status when a Job ID exists and isn't finished
  useEffect(() => {
    let intervalId;

    if (jobId && status !== "completed" && status !== "failed") {
      intervalId = setInterval(checkStatus, 3000); // Poll every 3 seconds
    }

    return () => clearInterval(intervalId);
  }, [jobId, status]);

  async function checkStatus() {
    const token = localStorage.getItem("token");
    try {
      const res = await fetch(
        `http://localhost:8000/chat/video_status/${jobId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (!res.ok) return;

      const data = await res.json();
      setStatus(data.status);

      if (data.status === "completed" && data.video_url) {
        setVideoUrl(data.video_url);
      } else if (data.status === "failed") {
        setError(data.message || "Video generation failed.");
      }
    } catch (err) {
      console.error("Polling error:", err);
    }
  }

  async function handleGenerate(e) {
    e.preventDefault();
    setError("");
    setVideoUrl(null);
    setStatus("queued");
    setJobId(null);

    const token = localStorage.getItem("token");
    const formData = new FormData();

    if (activeTab === "file") {
      if (!file) {
        setError("Please select a file.");
        return;
      }
      formData.append("file", file);
    } else {
      if (!text.trim()) {
        setError("Please enter some text.");
        return;
      }
      formData.append("text", text);
    }

    try {
      const res = await fetch("http://localhost:8000/generate/from-doc", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to start generation");
      }

      const data = await res.json();
      setJobId(data.job_id);
    } catch (err) {
      setError(err.message);
      setStatus(null);
    }
  }

  return (
    <div className="video-gen-wrapper">
      <h2>🎥 AI Video Generator</h2>
      <p className="subtitle">
        Turn documents or notes into educational videos.
      </p>

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab-btn ${activeTab === "file" ? "active" : ""}`}
          onClick={() => setActiveTab("file")}
        >
          Upload File
        </button>
        <button
          className={`tab-btn ${activeTab === "text" ? "active" : ""}`}
          onClick={() => setActiveTab("text")}
        >
          Enter Text
        </button>
      </div>

      <form onSubmit={handleGenerate} className="gen-form">
        {activeTab === "file" ? (
          <div
            className="file-drop-zone"
            onClick={() => fileInputRef.current.click()}
          >
            <span className="icon">📂</span>
            <p>{file ? file.name : "Click to select PDF, TXT, or TEX"}</p>
            <input
              type="file"
              accept=".pdf,.txt,.tex"
              ref={fileInputRef}
              hidden
              onChange={(e) => setFile(e.target.files[0])}
            />
          </div>
        ) : (
          <textarea
            className="text-input"
            rows="6"
            placeholder="Paste your lesson content or math expressions here..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        )}

        {error && <div className="error-msg">{error}</div>}

        <button
          type="submit"
          className="btn-primary"
          disabled={status === "queued" || status === "started"}
        >
          {status === "queued" || status === "started"
            ? "Processing..."
            : "Generate Video"}
        </button>
      </form>
      <div className="video-history-section">
    <h3>📚 Your Video Library</h3>
    <div className="video-list">
        {videos.map(v => (
            <div key={v.id} className="video-card">
                <div className="video-info">
                    <strong>{v.topic}</strong>
                    <span className={`status ${v.status}`}>{v.status}</span>
                </div>
                {v.status === 'completed' && (
                    <div className="video-player">
                        <video controls src={v.video_url} width="100%" />
                        <a href={v.video_url} download>⬇ Download</a>
                    </div>
                )}
            </div>
        ))}
    </div>
</div>
      {/* Status & Result */}
      {status && (
        <div className="status-container">
          <p>
            Status: <strong>{status.toUpperCase()}</strong>
          </p>
          {(status === "queued" || status === "started") && (
            <div className="loading-bar">
              <div className="loading-fill"></div>
            </div>
          )}
        </div>
      )}

      {videoUrl && (
        <div className="video-result">
          <h3>✅ Video Ready!</h3>
          <video controls src={videoUrl} width="100%" />
          <a href={videoUrl} download className="download-link">
            Download Video
          </a>
        </div>
      )}
    </div>
  );
}

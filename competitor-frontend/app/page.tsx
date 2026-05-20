"use client";
import { useState } from "react";
import { Search, Download, RefreshCw, AlertCircle, Users, Video, Eye } from "lucide-react";

export default function Dashboard() {
  const [targetCompany, setTargetCompany] = useState("");
  const [competitors, setCompetitors] = useState(["", "", "", ""]);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [reportData, setReportData] = useState<any>(null);
  const [error, setError] = useState("");

  const handleCompetitorChange = (index: number, value: string) => {
    const updated = [...competitors];
    updated[index] = value;
    setCompetitors(updated);
  };

  const executePipeline = async () => {
    if (!targetCompany.trim()) {
      setError("Please specify your baseline target company.");
      return;
    }
    setError("");
    setLoading(true);
    setReportData(null);
    
    const stages = [
      "Connecting to YouTube Data API...",
      "Fetching channel metadata...",
      "Analyzing video performance...",
      "Running AI analysis...",
      "Generating PowerPoint report..."
    ];

    let currentStage = 0;
    setStatusMessage(stages[0]);
    const interval = setInterval(() => {
      currentStage++;
      if (currentStage < stages.length) {
        setStatusMessage(stages[currentStage]);
      }
    }, 3000);

    try {
      const res = await fetch("https://competitor-video-analysis.onrender.com/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_company: targetCompany,
          competitors: competitors.filter(c => c.trim() !== "")
        })
      });
      
      if (!res.ok) throw new Error("Pipeline data processing failure.");
      const payload = await res.json();
      setReportData(payload.web_report);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      clearInterval(interval);
      setLoading(false);
    }
  };

  return (
    <div className="container">
      {/* Hero */}
      <div className="hero">
        <h1>Competitor Intelligence Hub</h1>
        <p>Analyze YouTube competitors and get AI-powered strategic insights instantly</p>
      </div>

      {/* Form */}
      <div className="form-section">
        <div className="form-group">
          <label className="form-label">Your Company</label>
          <input 
            type="text" 
            placeholder="e.g., Slack, Netflix, Spotify..." 
            className="form-input"
            value={targetCompany}
            onChange={(e) => setTargetCompany(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Competitors (Up to 4)</label>
          <div className="competitors-grid">
            {competitors.map((comp, idx) => (
              <input 
                key={idx}
                type="text" 
                placeholder={`Competitor ${idx + 1}`} 
                className="form-input"
                value={comp}
                onChange={(e) => handleCompetitorChange(idx, e.target.value)}
              />
            ))}
          </div>
        </div>

        {error && (
          <div className="error-box">
            <AlertCircle size={20} /> {error}
          </div>
        )}

        <button 
          onClick={executePipeline}
          disabled={loading}
          className="btn btn-primary"
        >
          {loading ? (
            <>
              <RefreshCw className="animate-spin" size={20} />
              Processing...
            </>
          ) : (
            <>
              <Search size={20} />
              Analyze Competitors
            </>
          )}
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="loading-box">
          <div className="loading-spinner"></div>
          <h2>{statusMessage}</h2>
          <p>This typically takes 15-30 seconds...</p>
        </div>
      )}

      {/* Results */}
      {reportData && !loading && (
        <div className="results-section">
          {/* Download */}
          <div className="success-box">
            <div>
              <div className="success-badge">✓ Analysis Complete</div>
              <h3>Your Strategic Report Ready</h3>
            </div>
            <a 
              href="https://competitor-video-analysis.onrender.com/report.pptx" 
              download
              className="btn-download"
            >
              <Download size={18} /> Download PowerPoint
            </a>
          </div>

          {/* Metrics */}
          <h2 style={{ fontSize: "28px", fontWeight: "900", marginBottom: "24px" }}>Performance Metrics</h2>
          <div className="metrics-grid">
            {reportData.raw_metrics.map((metric: any, idx: number) => (
              <div key={idx} className="metric-card">
                <h4>{metric.channel_title}</h4>
                <p>{metric.company_name}</p>
                
                <div className="metric-item">
                  <span className="metric-label"><Users size={16} /> Subscribers</span>
                  <span className="metric-value">{(metric.subscribers/1000).toFixed(1)}K</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label"><Video size={16} /> Videos</span>
                  <span className="metric-value">{metric.total_videos}</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label"><Eye size={16} /> Total Views</span>
                  <span className="metric-value">{(metric.total_views/1000000).toFixed(1)}M</span>
                </div>
              </div>
            ))}
          </div>

          {/* Insights */}
          <div className="insights-section">
            <h2>Strategic Insights</h2>
            <div className="insights-text">{reportData.ai_analysis}</div>
          </div>

          {/* Reset */}
          <div style={{ textAlign: "center" }}>
            <button 
              onClick={() => {
                setReportData(null);
                setTargetCompany("");
                setCompetitors(["", "", "", ""]);
              }}
              className="reset-btn"
            >
              Analyze Another Company
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

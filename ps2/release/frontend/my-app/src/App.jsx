import { useState } from "react";
import { useNavigate } from "react-router-dom";

function App() {
  const navigate = useNavigate();
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState("");

  const handleUpload = async () => {
    setUploading(true);
    setProgress(20);
    setStatusMsg("Processing demo video…");

    try {
      const response = await fetch("/upload", {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Server error");
      }

      const result = await response.json();

      setProgress(100);
      setStatusMsg("Done!");

      navigate(
        `/results?video=${encodeURIComponent(result.annotated_video)}` +
          `&report=${encodeURIComponent(result.report_file)}` +
          `&csv=${encodeURIComponent(result.csv_file)}` +
          `&thumbnail=${encodeURIComponent(result.thumbnail)}`,
      );
    } catch {
      alert("Backend error. Make sure server is running.");
      setUploading(false);
      setProgress(0);
    }
  };
  const steps = ["Upload", "Analyse", "Render"];
  const stepPct = [0, 55, 90];

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 font-sans">
      {/* ── Header ── */}
      <div className="text-center mb-10 select-none">
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-emerald-500/10 border border-emerald-500/30 mb-5 shadow-lg shadow-emerald-900/20">
          {/* Cricket ball icon */}
          <svg
            className="w-10 h-10 text-emerald-400"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <circle cx="12" cy="12" r="9.5" />
            <path
              d="M4.5 7.5 C7 9 9 11 9 12 S7 15 4.5 16.5"
              strokeLinecap="round"
            />
            <path
              d="M19.5 7.5 C17 9 15 11 15 12 S17 15 19.5 16.5"
              strokeLinecap="round"
            />
            <path d="M12 2.5 v19" strokeLinecap="round" />
          </svg>
        </div>
        <h1 className="text-4xl font-extrabold text-white tracking-tight">
          Frame Drop and Merge&nbsp;
          <span className="text-emerald-400">Detector</span>
        </h1>
        <p className="text-slate-400 mt-2 text-base">
          Detect drops &amp; merge artefacts in broadcast footage
        </p>
        {/* Add My Team Name for Demo */}
        <p className="text-slate-600 mt-1 text-sm">
          By{" "}
          <span className="text-emerald-400 font-semibold">
            Team Ctrl + Shift
          </span>
        </p>
      </div>

      {/* ── Demo Mode Card ── */}
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
        {/* Demo Mode Info */}
        <div className="border-2 border-dashed border-emerald-500/50 rounded-xl p-10 text-center mb-6 bg-emerald-950/20">
          <div className="w-14 h-14 bg-emerald-500/15 rounded-full flex items-center justify-center mx-auto mb-3 border border-emerald-600/40">
            <svg
              className="w-7 h-7 text-emerald-400"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <p className="text-white font-semibold text-lg">Demo Mode Enabled</p>
          <p className="text-slate-400 text-sm mt-2">
            Click the button below to run analysis on the sample cricket match
            footage
          </p>
        </div>

        {/* Progress */}
        {uploading && (
          <div className="mt-6 space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-slate-400 text-sm">{statusMsg}</span>
              <span className="text-emerald-400 font-bold text-sm">
                {progress}%
              </span>
            </div>
            <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-linear-to-r from-emerald-500 to-green-400 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
            {/* Step indicators */}
            <div className="flex gap-2 pt-1">
              {steps.map((step, i) => {
                const active = progress >= stepPct[i];
                return (
                  <div key={step} className="flex-1 text-center">
                    <div
                      className={`h-0.5 rounded-full mb-1.5 transition-all duration-500 ${active ? "bg-emerald-500" : "bg-slate-700"}`}
                    />
                    <span
                      className={`text-xs font-medium transition-colors duration-300 ${active ? "text-emerald-400" : "text-slate-600"}`}
                    >
                      {step}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Run Analysis button */}
        {!uploading && (
          <button
            onClick={handleUpload}
            className="mt-6 w-full py-3.5 px-6 bg-emerald-500 hover:bg-emerald-400 active:scale-95 text-white font-bold text-base rounded-xl transition-all duration-150 shadow-lg shadow-emerald-900/30 hover:shadow-emerald-700/40"
          >
            Run Analysis →
          </button>
        )}
      </div>

      {/* ── Feature chips ── */}
      <div className="flex gap-3 mt-8 flex-wrap justify-center">
        {[
          "YOLOv8 Detection",
          "Kalman Filter Tracking",
          "Drop & Merge Analysis",
        ].map((f) => (
          <span
            key={f}
            className="px-3 py-1 bg-slate-900 border border-slate-800 text-slate-500 text-xs rounded-full"
          >
            {f}
          </span>
        ))}
      </div>
    </div>
  );
}

export default App;

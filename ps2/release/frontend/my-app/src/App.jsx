import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";

function App() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusMsg, setStatusMsg] = useState("");
  const [dragging, setDragging] = useState(false);

  const selectFile = (f) => {
    if (f && f.type.startsWith("video/")) {
      setFile(f);
    } else if (f) {
      alert("Please select a valid video file (MP4, AVI, MOV, MKV, WebM)");
    }
  };

  const handleFileChange = (e) => selectFile(e.target.files[0]);
  const handleDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };
  const handleDragLeave = () => setDragging(false);
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    selectFile(e.dataTransfer.files[0]);
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(5);
    setStatusMsg("Uploading video…");

    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        const pct = Math.round((e.loaded / e.total) * 45) + 5;
        setProgress(pct);
        setStatusMsg(`Uploading… ${Math.round((e.loaded / e.total) * 100)}%`);
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status === 200) {
        try {
          const result = JSON.parse(xhr.responseText);
          setProgress(100);
          setStatusMsg("Done!");
          if (result.annotated_video && result.report_file && result.csv_file) {
            navigate(
              `/results?video=${encodeURIComponent(result.annotated_video)}` +
                `&report=${encodeURIComponent(result.report_file)}` +
                `&csv=${encodeURIComponent(result.csv_file)}`,
            );
          } else {
            alert("Unexpected response: " + JSON.stringify(result));
            resetState();
          }
        } catch {
          alert("Failed to parse server response.");
          resetState();
        }
      } else {
        let msg = `Upload failed (${xhr.status})`;
        try {
          msg = JSON.parse(xhr.responseText).detail || msg;
        } catch {}
        alert(msg);
        resetState();
      }
    });

    xhr.addEventListener("error", () => {
      alert("Network error — make sure the backend is running on port 8000.");
      resetState();
    });

    const resetState = () => {
      setUploading(false);
      setProgress(0);
      setStatusMsg("");
    };

    xhr.open("POST", "/upload");
    xhr.send(formData);

    // After upload completes the backend does heavy processing — show that
    setTimeout(() => {
      if (progress < 55) {
        setProgress(55);
        setStatusMsg("Analysing frames with YOLOv8…");
      }
    }, 2000);
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

      {/* ── Upload Card ── */}
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
        {/* Drop zone */}
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() =>
            !uploading && document.getElementById("file-input").click()
          }
          className={[
            "border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-200",
            dragging
              ? "border-emerald-400 bg-emerald-400/5 scale-[1.01]"
              : file
                ? "border-emerald-600/70 bg-emerald-950/20"
                : "border-slate-700 hover:border-slate-500 hover:bg-slate-800/40",
          ].join(" ")}
        >
          <input
            id="file-input"
            type="file"
            accept="video/*"
            onChange={handleFileChange}
            disabled={uploading}
            className="hidden"
          />

          {file ? (
            <>
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
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <p className="text-white font-semibold text-base truncate max-w-xs mx-auto">
                {file.name}
              </p>
              <p className="text-slate-500 text-sm mt-1">
                {(file.size / 1024 / 1024).toFixed(1)} MB
                {!uploading && (
                  <span className="ml-2 text-slate-600">· click to change</span>
                )}
              </p>
            </>
          ) : (
            <>
              <div className="w-14 h-14 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-3 border border-slate-700">
                <svg
                  className="w-7 h-7 text-slate-400"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
              </div>
              <p className="text-slate-300 font-medium text-sm">
                Drop video here or{" "}
                <span className="text-emerald-400 font-semibold">browse</span>
              </p>
              <p className="text-slate-600 text-xs mt-1">
                MP4 · AVI · MOV · MKV · WebM — max 500 MB
              </p>
            </>
          )}
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
                className="h-full bg-gradient-to-r from-emerald-500 to-green-400 rounded-full transition-all duration-500 ease-out"
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

        {/* Analyse button */}
        {file && !uploading && (
          <button
            onClick={handleUpload}
            className="mt-6 w-full py-3.5 px-6 bg-emerald-500 hover:bg-emerald-400 active:scale-95 text-white font-bold text-base rounded-xl transition-all duration-150 shadow-lg shadow-emerald-900/30 hover:shadow-emerald-700/40"
          >
            Analyse Video →
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

import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  ReferenceLine,
  BarChart,
  Bar,
} from "recharts";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

/* ── Frame → readable timestamp ─────────────────────────────────────── */
function frameToTimestamp(frame, fps) {
  if (!fps || fps === 0) return `f${frame}`;
  const totalMs = Math.round((frame / fps) * 1000);
  const ms = totalMs % 1000;
  const sec = Math.floor(totalMs / 1000) % 60;
  const min = Math.floor(totalMs / 60000) % 60;
  const hr = Math.floor(totalMs / 3600000);
  const pad = (n, d = 2) => String(n).padStart(d, "0");
  return hr > 0
    ? `${pad(hr)}:${pad(min)}:${pad(sec)}.${pad(ms, 3)}`
    : `${pad(min)}:${pad(sec)}.${pad(ms, 3)}`;
}

/* ── PDF Report generator ────────────────────────────────────────────── */
function generatePDF(data) {
  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
  const { summary } = data;
  const fps = data.fps || 25;
  const W = doc.internal.pageSize.getWidth();
  const now = new Date();
  const pad2 = (n) => String(n).padStart(2, "0");
  const days = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
  ];
  const months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  const generatedAt = `${days[now.getDay()]}, ${now.getDate()} ${months[now.getMonth()]} ${now.getFullYear()}  ${pad2(now.getHours())}:${pad2(now.getMinutes())}:${pad2(now.getSeconds())} (local)`;
  const reportId = `RPT-${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, "0")}${String(now.getDate()).padStart(2, "0")}-${String(now.getHours()).padStart(2, "0")}${String(now.getMinutes()).padStart(2, "0")}${String(now.getSeconds()).padStart(2, "0")}`;
  const normalFrames = Math.max(
    0,
    summary.total_frames - summary.drop_frames - summary.merge_frames,
  );
  const accuracy =
    summary.total_frames > 0
      ? ((normalFrames / summary.total_frames) * 100).toFixed(2)
      : "0.00";
  const verdict =
    summary.drop_frames === 0 && summary.merge_frames === 0
      ? "CLEAN - No temporal artefacts detected."
      : `ARTEFACTS FOUND - ${summary.drop_frames} drop(s), ${summary.merge_frames} merge(s) require review.`;

  // ── colour palette
  const GREEN = [16, 185, 129];
  const RED = [239, 68, 68];
  const AMBER = [245, 158, 11];
  const SLATE = [30, 41, 59];
  const LIGHT = [241, 245, 249];
  const WHITE = [255, 255, 255];
  const DARK = [15, 23, 42];

  // ══════════════════════════════
  // PAGE 1 — Cover / Summary
  // ══════════════════════════════

  // Header band
  doc.setFillColor(...DARK);
  doc.rect(0, 0, W, 52, "F");

  // Accent stripe
  doc.setFillColor(...GREEN);
  doc.rect(0, 52, W, 2, "F");

  // Org / title
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  doc.setTextColor(...GREEN);
  doc.text("CRICKET BROADCAST INTEGRITY UNIT", 14, 14);

  doc.setFontSize(20);
  doc.setTextColor(...WHITE);
  doc.text("Ball Detection Analysis Report", 14, 27);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(8);
  doc.setTextColor(148, 163, 184);
  doc.text(`Report ID : ${reportId}`, 14, 36);
  doc.text(`Generated : ${generatedAt}`, 14, 42);
  doc.text(`Analyst   : Automated YOLOv8 + Kalman Detection System`, 14, 48);

  // ── Section: Video Metadata
  let y = 66;
  const sectionHeader = (title, yPos) => {
    doc.setFillColor(...SLATE);
    doc.roundedRect(14, yPos, W - 28, 8, 1, 1, "F");
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.setTextColor(...GREEN);
    doc.text(title.toUpperCase(), 18, yPos + 5.5);
    return yPos + 13;
  };

  y = sectionHeader("1. Video Metadata", y);

  autoTable(doc, {
    startY: y,
    margin: { left: 14, right: 14 },
    theme: "grid",
    styles: { fontSize: 9, cellPadding: 3 },
    headStyles: { fillColor: SLATE, textColor: LIGHT, fontStyle: "bold" },
    alternateRowStyles: { fillColor: [248, 250, 252] },
    head: [["Field", "Value"]],
    body: [
      ["Source File", data.source ?? "-"],
      ["Frame Rate", `${fps.toFixed(3)} FPS`],
      ["Resolution", data.resolution ?? "-"],
      ["Total Frames", String(summary.total_frames)],
      ["Total Duration", frameToTimestamp(summary.total_frames, fps)],
    ],
    columnStyles: { 0: { fontStyle: "bold", cellWidth: 50 } },
  });

  y = doc.lastAutoTable.finalY + 10;

  // ── Section: Detection Summary
  y = sectionHeader("2. Detection Summary", y);

  autoTable(doc, {
    startY: y,
    margin: { left: 14, right: 14 },
    theme: "grid",
    styles: { fontSize: 9, cellPadding: 3 },
    headStyles: { fillColor: SLATE, textColor: LIGHT, fontStyle: "bold" },
    alternateRowStyles: { fillColor: [248, 250, 252] },
    head: [["Metric", "Count", "% of Total"]],
    body: [
      [
        "Tracked Positions",
        String(summary.tracked_positions),
        `${summary.total_frames ? ((summary.tracked_positions / summary.total_frames) * 100).toFixed(1) : 0}%`,
      ],
      ["Normal Frames", String(normalFrames), `${accuracy}%`],
      [
        "Drop Frames",
        String(summary.drop_frames),
        `${summary.total_frames ? ((summary.drop_frames / summary.total_frames) * 100).toFixed(2) : 0}%`,
      ],
      [
        "Merge Frames",
        String(summary.merge_frames),
        `${summary.total_frames ? ((summary.merge_frames / summary.total_frames) * 100).toFixed(2) : 0}%`,
      ],
    ],
    columnStyles: { 0: { fontStyle: "bold", cellWidth: 70 } },
    didParseCell(hookData) {
      if (hookData.row.index === 2 && hookData.section === "body") {
        hookData.cell.styles.textColor = RED;
        hookData.cell.styles.fontStyle = "bold";
      }
      if (hookData.row.index === 3 && hookData.section === "body") {
        hookData.cell.styles.textColor = AMBER;
        hookData.cell.styles.fontStyle = "bold";
      }
    },
  });

  y = doc.lastAutoTable.finalY + 10;

  // ── Verdict box
  const verdictColor =
    summary.drop_frames === 0 && summary.merge_frames === 0 ? GREEN : RED;
  doc.setFillColor(...verdictColor.map((v) => v * 0.15 + 240));
  doc.setDrawColor(...verdictColor);
  doc.setLineWidth(0.5);
  doc.roundedRect(14, y, W - 28, 14, 2, 2, "FD");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9);
  doc.setTextColor(...verdictColor);
  doc.text("VERDICT:", 19, y + 6);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(30, 41, 59);
  doc.text(verdict, 42, y + 6);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(8);
  doc.setTextColor(100, 116, 139);
  doc.text(
    `Clean Frame Ratio: ${accuracy}%  |  Detection Engine: YOLOv8 + Kalman Filter  |  SSIM Merge Analysis active`,
    19,
    y + 11,
  );

  y += 22;

  // ── Add page if running low
  const ensurePage = (neededMm = 40) => {
    if (y + neededMm > 272) {
      doc.addPage();
      y = 20;
    }
  };

  // ── Build per-frame lookup from data.frames (center, conf, predicted)
  const frameMap = {};
  if (Array.isArray(data.frames)) {
    data.frames.forEach((fr) => {
      frameMap[fr.frame] = fr;
    });
  }
  const dropSet = new Set(summary.drop_frame_list);
  const mergeSet = new Set(summary.merge_frame_list);

  // ── Helper: group consecutive frame numbers into contiguous clusters
  const buildClusters = (frameList) => {
    if (!frameList.length) return [];
    const clusters = [];
    let cur = [frameList[0]];
    for (let i = 1; i < frameList.length; i++) {
      if (frameList[i] - frameList[i - 1] <= 2) {
        cur.push(frameList[i]);
      } else {
        clusters.push(cur);
        cur = [frameList[i]];
      }
    }
    clusters.push(cur);
    return clusters;
  };

  // ── Helper: describe ball region of frame
  const frameZone = (cx, cy, res) => {
    if (!cx || !cy || !res) return "-";
    const [rw, rh] = res.split("x").map(Number);
    if (!rw || !rh) return `(${cx}, ${cy})`;
    const hZone = cx < rw * 0.33 ? "Left" : cx < rw * 0.66 ? "Center" : "Right";
    const vZone = cy < rh * 0.33 ? "Top" : cy < rh * 0.66 ? "Mid" : "Bottom";
    return `${vZone}-${hZone}  (${cx}, ${cy})`;
  };

  // ══════════════════════════════════════════════════════
  // SECTION 3 — Incident Cluster Map (DROP + MERGE runs)
  // ══════════════════════════════════════════════════════
  ensurePage(50);
  y = sectionHeader("3. Incident Cluster Map", y);

  // Intro blurb
  doc.setFont("helvetica", "italic");
  doc.setFontSize(8);
  doc.setTextColor(100, 116, 139);
  doc.text(
    "Consecutive flagged frames are grouped into incidents. An incident spanning multiple frames indicates a sustained detection loss or broadcast artefact.",
    14,
    y,
    { maxWidth: W - 28 },
  );
  y += 9;

  // Build unified incident list (drop clusters + merge clusters)
  const dropClusters = buildClusters(summary.drop_frame_list);
  const mergeClusters = buildClusters(summary.merge_frame_list);

  const allIncidents = [
    ...dropClusters.map((c) => ({ type: "DROP", frames: c })),
    ...mergeClusters.map((c) => ({ type: "MERGE", frames: c })),
  ].sort((a, b) => a.frames[0] - b.frames[0]);

  if (allIncidents.length === 0) {
    doc.setFont("helvetica", "italic");
    doc.setFontSize(9);
    doc.setTextColor(...GREEN);
    doc.text("No incidents detected in this footage.", 18, y);
    y += 10;
  } else {
    const incidentRows = allIncidents.map((inc, i) => {
      const first = inc.frames[0];
      const last = inc.frames[inc.frames.length - 1];
      const dur = last - first + 1;
      const durSec = (dur / fps).toFixed(3);
      const tsStart = frameToTimestamp(first, fps);
      const tsEnd = frameToTimestamp(last, fps);
      // Pick center of first and last frame for spatial context
      const fi = frameMap[first];
      const li = frameMap[last];
      const startPos = fi
        ? frameZone(fi.center?.[0], fi.center?.[1], data.resolution)
        : "-";
      const endPos =
        dur > 1 && li
          ? frameZone(li.center?.[0], li.center?.[1], data.resolution)
          : startPos;
      // Also merged / also dropped flag
      const alsoMerged =
        inc.type === "DROP" && inc.frames.some((f) => mergeSet.has(f));
      const alsoDropped =
        inc.type === "MERGE" && inc.frames.some((f) => dropSet.has(f));
      const overlap =
        alsoMerged || alsoDropped
          ? inc.type === "DROP"
            ? "[!] Also MERGE"
            : "[!] Also DROP"
          : "-";
      return [
        String(i + 1),
        inc.type,
        dur > 1 ? `${first} - ${last}` : String(first),
        dur > 1 ? `${tsStart} -> ${tsEnd}` : tsStart,
        dur > 1 ? `${dur} frames (${durSec}s)` : "1 frame",
        startPos,
        overlap,
      ];
    });

    autoTable(doc, {
      startY: y,
      margin: { left: 14, right: 14 },
      theme: "striped",
      styles: { fontSize: 7.8, cellPadding: 2.2, overflow: "linebreak" },
      headStyles: { fillColor: SLATE, textColor: LIGHT, fontStyle: "bold" },
      head: [
        [
          "#",
          "Type",
          "Frame(s)",
          "Timestamp(s)",
          "Duration",
          "Ball Position",
          "Overlap",
        ],
      ],
      body: incidentRows,
      columnStyles: {
        0: { cellWidth: 8 },
        1: { cellWidth: 16, fontStyle: "bold" },
        2: { cellWidth: 22 },
        3: { cellWidth: 32 },
        4: { cellWidth: 26 },
        5: { cellWidth: "auto" },
        6: { cellWidth: 22 },
      },
      didParseCell(hk) {
        if (hk.section !== "body") return;
        const type = incidentRows[hk.row.index]?.[1];
        if (hk.column.index === 1) {
          hk.cell.styles.textColor = type === "DROP" ? RED : AMBER;
        }
        if (hk.column.index === 6 && hk.cell.raw !== "-") {
          hk.cell.styles.textColor = [239, 68, 68];
          hk.cell.styles.fontStyle = "bold";
        }
      },
    });
    y = doc.lastAutoTable.finalY + 10;
  }

  // ══════════════════════════════════════════════════════
  // SECTION 4 — Drop Frame Detailed Log
  // ══════════════════════════════════════════════════════
  ensurePage(50);
  y = sectionHeader("4. Drop Frame Detailed Log", y);

  if (summary.drop_frame_list.length === 0) {
    doc.setFont("helvetica", "italic");
    doc.setFontSize(9);
    doc.setTextColor(...GREEN);
    doc.text("No drop frames detected in this footage.", 18, y);
    y += 10;
  } else {
    const dropRows = summary.drop_frame_list.map((f, i) => {
      const ts = frameToTimestamp(f, fps);
      const reasons =
        (summary.drop_reasons?.[String(f)] || []).join(", ") || "-";
      const fi = frameMap[f];
      const cx = fi?.center?.[0] ?? "-";
      const cy = fi?.center?.[1] ?? "-";
      const conf = fi?.conf != null ? fi.conf.toFixed(3) : "-";
      const pred = fi?.predicted ? "Yes (estimated)" : "No (detected)";
      const alsoMerge = mergeSet.has(f) ? "YES (!)" : "No";
      return [
        String(i + 1),
        String(f),
        ts,
        `(${cx}, ${cy})`,
        conf,
        pred,
        reasons,
        alsoMerge,
      ];
    });

    autoTable(doc, {
      startY: y,
      margin: { left: 14, right: 14 },
      theme: "striped",
      styles: { fontSize: 7.8, cellPadding: 2.2, overflow: "linebreak" },
      headStyles: { fillColor: RED, textColor: WHITE, fontStyle: "bold" },
      alternateRowStyles: { fillColor: [255, 245, 245] },
      head: [
        [
          "#",
          "Frame",
          "Timestamp",
          "Ball Pos (px)",
          "Conf",
          "Position src",
          "Reason(s)",
          "Also Merge?",
        ],
      ],
      body: dropRows,
      columnStyles: {
        0: { cellWidth: 8 },
        1: { cellWidth: 16, fontStyle: "bold" },
        2: { cellWidth: 24 },
        3: { cellWidth: 24 },
        4: { cellWidth: 14 },
        5: { cellWidth: 26 },
        6: { cellWidth: "auto" },
        7: { cellWidth: 20 },
      },
      didParseCell(hk) {
        if (hk.section !== "body") return;
        // Highlight "Also Merge?" YES cells
        if (hk.column.index === 7 && hk.cell.raw === "YES (!)") {
          hk.cell.styles.textColor = AMBER;
          hk.cell.styles.fontStyle = "bold";
        }
        // Highlight predicted positions in orange
        if (hk.column.index === 5 && String(hk.cell.raw).startsWith("Yes")) {
          hk.cell.styles.textColor = [249, 115, 22];
        }
      },
    });
    y = doc.lastAutoTable.finalY + 10;
  }

  // ══════════════════════════════════════════════════════
  // SECTION 5 — Merge Frame Detailed Log
  // ══════════════════════════════════════════════════════
  ensurePage(50);
  y = sectionHeader("5. Merge Frame Detailed Log", y);

  if (summary.merge_frame_list.length === 0) {
    doc.setFont("helvetica", "italic");
    doc.setFontSize(9);
    doc.setTextColor(...GREEN);
    doc.text("No merge frames detected in this footage.", 18, y);
    y += 10;
  } else {
    const mergeRows = summary.merge_frame_list.map((f, i) => {
      const ts = frameToTimestamp(f, fps);
      const fi = frameMap[f];
      const cx = fi?.center?.[0] ?? "-";
      const cy = fi?.center?.[1] ?? "-";
      const zone = frameZone(fi?.center?.[0], fi?.center?.[1], data.resolution);
      const conf = fi?.conf != null ? fi.conf.toFixed(3) : "-";
      // Derive which merge criterion triggered
      const isLowConf = fi?.conf != null && fi.conf < 0.4;
      const reason = isLowConf
        ? `Low confidence (${conf} < 0.40)`
        : "SSIM similarity high + low blur vs neighbours";
      const alsoDropped = dropSet.has(f) ? "YES (!)" : "No";
      return [
        String(i + 1),
        String(f),
        ts,
        `(${cx}, ${cy})`,
        zone,
        conf,
        reason,
        alsoDropped,
      ];
    });

    autoTable(doc, {
      startY: y,
      margin: { left: 14, right: 14 },
      theme: "striped",
      styles: { fontSize: 7.8, cellPadding: 2.2, overflow: "linebreak" },
      headStyles: { fillColor: AMBER, textColor: DARK, fontStyle: "bold" },
      alternateRowStyles: { fillColor: [255, 251, 235] },
      head: [
        [
          "#",
          "Frame",
          "Timestamp",
          "Ball Pos (px)",
          "Frame Zone",
          "Conf",
          "Merge Trigger",
          "Also Drop?",
        ],
      ],
      body: mergeRows,
      columnStyles: {
        0: { cellWidth: 8 },
        1: { cellWidth: 16, fontStyle: "bold" },
        2: { cellWidth: 22 },
        3: { cellWidth: 22 },
        4: { cellWidth: 28 },
        5: { cellWidth: 14 },
        6: { cellWidth: "auto" },
        7: { cellWidth: 20 },
      },
      didParseCell(hk) {
        if (hk.section !== "body") return;
        if (hk.column.index === 7 && hk.cell.raw === "YES (!)") {
          hk.cell.styles.textColor = RED;
          hk.cell.styles.fontStyle = "bold";
        }
        if (hk.column.index === 5) {
          const v = parseFloat(hk.cell.raw);
          if (!isNaN(v) && v < 0.4) hk.cell.styles.textColor = RED;
        }
      },
    });
    y = doc.lastAutoTable.finalY + 10;
  }

  // ══════════════════════════════
  // Technical Notes
  // ══════════════════════════════
  ensurePage(70);
  y = sectionHeader("6. Technical Notes", y);

  const notes = [
    [
      "Detection Model",
      "YOLOv8 custom-trained on cricket ball dataset (best.pt)",
    ],
    ["Tracking Algorithm", "OpenCV Kalman Filter (4-state: x, y, vx, vy)"],
    [
      "ROI Strategy",
      "Search window +/-200 px around Kalman prediction; fallback to full-frame",
    ],
    [
      "Drop Criterion",
      "Frame flagged when: detection absent (NO_DET), outside gate threshold (GATE), or frame gap >= 2 (GAP)",
    ],
    [
      "Merge Criterion",
      "SSIM similarity to adjacent frames > 0.75 AND blur < 70% of neighbours' blur, OR detection confidence < 0.40",
    ],
    [
      "Confidence Threshold",
      "YOLO confidence >= 0.15 (low threshold for maximum recall)",
    ],
    [
      "Output Video Codec",
      "H.264 (avc1) MP4 - annotated with trajectory, event labels, and frame counter",
    ],
  ];

  autoTable(doc, {
    startY: y,
    margin: { left: 14, right: 14 },
    theme: "grid",
    styles: { fontSize: 8, cellPadding: 2.5, overflow: "linebreak" },
    headStyles: { fillColor: SLATE, textColor: LIGHT, fontStyle: "bold" },
    alternateRowStyles: { fillColor: [248, 250, 252] },
    head: [["Parameter", "Description"]],
    body: notes,
    columnStyles: { 0: { fontStyle: "bold", cellWidth: 55 } },
  });

  y = doc.lastAutoTable.finalY + 10;

  // ── Footer on every page
  const totalPages = doc.internal.getNumberOfPages();
  for (let p = 1; p <= totalPages; p++) {
    doc.setPage(p);
    doc.setFillColor(...DARK);
    doc.rect(0, 287, W, 10, "F");
    doc.setFont("helvetica", "normal");
    doc.setFontSize(7);
    doc.setTextColor(100, 116, 139);
    doc.text(
      `Cricket Ball Detection System  |  Report ID: ${reportId}  |  CONFIDENTIAL`,
      14,
      293,
    );
    doc.text(`Page ${p} of ${totalPages}`, W - 14, 293, { align: "right" });
    // top accent line on continuation pages
    if (p > 1) {
      doc.setFillColor(...GREEN);
      doc.rect(0, 0, W, 1.5, "F");
    }
  }

  doc.save(`${reportId}_ball_detection_report.pdf`);
}

const RADIAN = Math.PI / 180;
const renderCustomLabel = ({
  cx,
  cy,
  midAngle,
  innerRadius,
  outerRadius,
  percent,
}) => {
  if (percent < 0.04) return null;
  const r = innerRadius + (outerRadius - innerRadius) * 0.55;
  const x = cx + r * Math.cos(-midAngle * RADIAN);
  const y = cy + r * Math.sin(-midAngle * RADIAN);
  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor="middle"
      dominantBaseline="central"
      fontSize={12}
      fontWeight={600}
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

/* ── Stat card ─────────────────────────────────────────────────────── */
function StatCard({ label, value, color = "text-white", sub }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-1">
      <span className={`text-3xl font-extrabold ${color}`}>{value}</span>
      <span className="text-slate-400 text-sm font-medium">{label}</span>
      {sub && <span className="text-slate-600 text-xs">{sub}</span>}
    </div>
  );
}

export default function Results() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);

  const videoFile = searchParams.get("video");
  const reportFile = searchParams.get("report");
  const csvFile = searchParams.get("csv");
  const thumbnail = searchParams.get("thumbnail");

  useEffect(() => {
    if (!reportFile) {
      setLoading(false);
      setError(true);
      return;
    }
    fetch(`/report/${reportFile}`)
      .then((r) => {
        if (!r.ok) throw new Error(r.status);
        return r.json();
      })
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
        setError(true);
      });
  }, [reportFile]);

  /* ── Loading / error states ── */
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Loading results…</p>
        </div>
      </div>
    );
  }
  if (error || !data) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-lg font-semibold mb-4">
            Failed to load report
          </p>
          <button
            onClick={() => navigate("/")}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm transition-colors"
          >
            ← Back
          </button>
        </div>
      </div>
    );
  }

  const { summary } = data;
  const normalFrames = Math.max(
    0,
    summary.total_frames - summary.drop_frames - summary.merge_frames,
  );

  const chartData = [
    { name: "Normal", value: normalFrames, color: "#10b981" },
    { name: "Drop", value: summary.drop_frames, color: "#ef4444" },
    { name: "Merge", value: summary.merge_frames, color: "#f59e0b" },
  ].filter((d) => d.value > 0);

  const accuracy =
    summary.tracked_positions > 0
      ? ((normalFrames / summary.total_frames) * 100).toFixed(1)
      : 0;

  /* ── Analytical chart data ─────────────────────────────────────────── */
  const GATE_THRESHOLD = 80;

  // Timeline: three scatter series, y = 0/1/2 per class
  const timelineNormal = (data.frames || [])
    .filter((f) => f.label === "NORMAL")
    .map((f) => ({ x: f.frame, y: 0 }));
  const timelineDrop = (data.frames || [])
    .filter((f) => f.label === "DROP")
    .map((f) => ({ x: f.frame, y: 1 }));
  const timelineMerge = (data.frames || [])
    .filter((f) => f.label === "MERGE")
    .map((f) => ({ x: f.frame, y: 2 }));

  // Motion error: GATE(Xpx) value if present, otherwise Euclidean centre delta
  const motionData = (data.frames || []).map((f, frameIdx) => {
    const gateReason = f.reasons?.find((r) => r.startsWith("GATE("));
    let error = 0;
    if (gateReason) {
      error = parseInt(gateReason.match(/GATE\((\d+)px\)/)?.[1] || "0", 10);
    } else if (frameIdx > 0) {
      const prev = data.frames[frameIdx - 1];
      const dx = (f.center?.[0] ?? 0) - (prev.center?.[0] ?? 0);
      const dy = (f.center?.[1] ?? 0) - (prev.center?.[1] ?? 0);
      error = Math.round(Math.sqrt(dx * dx + dy * dy));
    }
    return { frame: f.frame, error, label: f.label };
  });

  return (
    <div className="min-h-screen bg-slate-950 font-sans pb-16">
      {/* ── Top Nav ── */}
      <nav className="sticky top-0 z-50 bg-slate-950/90 backdrop-blur border-b border-slate-800 px-6 py-3 flex items-center justify-between">
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M10 19l-7-7m0 0l7-7m-7 7h18"
            />
          </svg>
          New Analysis
        </button>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
          <span className="text-slate-300 text-sm font-medium">
            Analysis Complete
          </span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => window.open(`/download/${videoFile}`, "_blank")}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white rounded-lg text-xs font-medium transition-all"
          >
            ↓ Video
          </button>
          <button
            onClick={() => window.open(`/download/${csvFile}`, "_blank")}
            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium transition-all"
          >
            ↓ CSV Report
          </button>
          <button
            disabled={pdfLoading}
            onClick={() => {
              setPdfLoading(true);
              // run in next tick so button state updates before heavy PDF work
              setTimeout(() => {
                try {
                  generatePDF(data);
                } finally {
                  setPdfLoading(false);
                }
              }, 0);
            }}
            className="px-3 py-1.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 disabled:cursor-wait text-white rounded-lg text-xs font-medium transition-all flex items-center gap-1.5"
          >
            {pdfLoading ? (
              <>
                <span className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin" />
                Building…
              </>
            ) : (
              "↓ PDF Report"
            )}
          </button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 pt-8 space-y-6">
        {/* ── Header ── */}
        <div>
          <h1 className="text-2xl font-bold text-white">📹 {data.source}</h1>
          <p className="text-slate-500 text-sm mt-1">
            {data.fps?.toFixed(1)} FPS · {data.resolution} ·{" "}
            {summary.total_frames} total frames
          </p>
        </div>

        {/* ── Stats Grid ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Total Frames"
            value={summary.total_frames}
            color="text-white"
          />
          <StatCard
            label="Tracked"
            value={summary.tracked_positions}
            color="text-sky-400"
            sub={`${accuracy}% clean`}
          />
          <StatCard
            label="Drop Frames"
            value={summary.drop_frames}
            color="text-red-400"
          />
          <StatCard
            label="Merge Frames"
            value={summary.merge_frames}
            color="text-amber-400"
          />
        </div>

        {/* ── Video + Chart row ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Video player */}
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h2 className="text-white font-semibold mb-3 flex items-center gap-2">
              <span className="w-2 h-2 bg-emerald-400 rounded-full" />
              Video Preview
            </h2>
            <div className="relative bg-black rounded-xl overflow-hidden">
              <img
                src={`/download/${thumbnail}`}
                alt="First frame"
                className="w-full rounded-xl"
                style={{ maxHeight: "420px", objectFit: "contain" }}
              />
            </div>
          </div>

          {/* Pie chart */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col">
            <h2 className="text-white font-semibold mb-3 flex items-center gap-2">
              <span className="w-2 h-2 bg-sky-400 rounded-full" />
              Detection Distribution
            </h2>
            <div className="flex-1" style={{ minHeight: 200 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius="40%"
                    outerRadius="70%"
                    paddingAngle={3}
                    dataKey="value"
                    labelLine={false}
                    label={renderCustomLabel}
                  >
                    {chartData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={entry.color}
                        stroke="transparent"
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: "#1e293b",
                      border: "1px solid #334155",
                      borderRadius: 8,
                      color: "#f1f5f9",
                    }}
                    formatter={(val, name) => [val, name]}
                  />
                  <Legend
                    iconType="circle"
                    formatter={(val) => (
                      <span style={{ color: "#94a3b8", fontSize: 13 }}>
                        {val}
                      </span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            {/* Breakdown */}
            <div className="mt-3 space-y-2">
              {[
                {
                  label: "Normal",
                  value: normalFrames,
                  color: "bg-emerald-500",
                },
                {
                  label: "Drop",
                  value: summary.drop_frames,
                  color: "bg-red-500",
                },
                {
                  label: "Merge",
                  value: summary.merge_frames,
                  color: "bg-amber-500",
                },
              ].map(({ label, value, color }) => (
                <div key={label} className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full shrink-0 ${color}`} />
                  <span className="text-slate-400 text-xs flex-1">{label}</span>
                  <span className="text-white text-xs font-semibold">
                    {value}
                  </span>
                  <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${color}`}
                      style={{
                        width: `${summary.total_frames ? (value / summary.total_frames) * 100 : 0}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Analytical Charts ── */}
        {data.frames && data.frames.length > 0 && (
          <div className="space-y-6">
            {/* 1 — Timeline Classification Graph */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <h2 className="text-white font-semibold mb-1 flex items-center gap-2">
                <span className="w-2 h-2 bg-violet-400 rounded-full" />
                Frame Classification Timeline
                <span className="ml-auto text-slate-500 text-xs font-normal">
                  {data.frames.length} frames · drop={summary.drop_frames} ·
                  merge={summary.merge_frames}
                </span>
              </h2>
              <p className="text-slate-500 text-xs mb-4">
                Each dot = one frame &mdash; shows temporal distribution of
                Normal, Drop, and Merge events
              </p>
              <div style={{ height: 220 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart
                    margin={{ top: 8, right: 24, bottom: 24, left: 12 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis
                      dataKey="x"
                      type="number"
                      name="Frame"
                      tick={{ fill: "#94a3b8", fontSize: 11 }}
                      label={{
                        value: "Frame #",
                        position: "insideBottom",
                        offset: -12,
                        fill: "#64748b",
                        fontSize: 11,
                      }}
                    />
                    <YAxis
                      dataKey="y"
                      type="number"
                      domain={[-0.5, 2.5]}
                      ticks={[0, 1, 2]}
                      tick={{ fill: "#94a3b8", fontSize: 11 }}
                      tickFormatter={(v) =>
                        ["Normal", "Drop", "Merge"][v] ?? ""
                      }
                      width={58}
                    />
                    <Tooltip
                      cursor={{ strokeDasharray: "3 3", stroke: "#475569" }}
                      contentStyle={{
                        background: "#1e293b",
                        border: "1px solid #334155",
                        borderRadius: 8,
                        color: "#f1f5f9",
                        fontSize: 12,
                      }}
                      formatter={(val, name, props) => [
                        `Frame ${props.payload.x}`,
                        name,
                      ]}
                    />
                    <Legend
                      iconType="circle"
                      iconSize={8}
                      wrapperStyle={{ paddingTop: 4 }}
                      formatter={(v) => (
                        <span style={{ color: "#94a3b8", fontSize: 12 }}>
                          {v}
                        </span>
                      )}
                    />
                    <Scatter
                      name="Normal"
                      data={timelineNormal}
                      fill="#10b981"
                      opacity={0.85}
                    />
                    <Scatter
                      name="Drop"
                      data={timelineDrop}
                      fill="#ef4444"
                      opacity={0.95}
                    />
                    <Scatter
                      name="Merge"
                      data={timelineMerge}
                      fill="#f59e0b"
                      opacity={0.85}
                    />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* 2 — Motion Prediction Error Graph */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <h2 className="text-white font-semibold mb-1 flex items-center gap-2">
                <span className="w-2 h-2 bg-red-400 rounded-full" />
                Motion Prediction Error
                <span className="ml-auto text-slate-500 text-xs font-normal">
                  Kalman gate &mdash; threshold = {GATE_THRESHOLD} px
                </span>
              </h2>
              <p className="text-slate-500 text-xs mb-4">
                Distance (px) between Kalman-predicted ball position and
                observed detection. Bars exceeding the red dashed line trigger a
                DROP.
              </p>
              <div style={{ height: 240 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={motionData}
                    margin={{ top: 8, right: 24, bottom: 24, left: 12 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="#1e293b"
                      vertical={false}
                    />
                    <XAxis
                      dataKey="frame"
                      tick={{ fill: "#94a3b8", fontSize: 11 }}
                      label={{
                        value: "Frame #",
                        position: "insideBottom",
                        offset: -12,
                        fill: "#64748b",
                        fontSize: 11,
                      }}
                    />
                    <YAxis
                      tick={{ fill: "#94a3b8", fontSize: 11 }}
                      label={{
                        value: "Error (px)",
                        angle: -90,
                        position: "insideLeft",
                        offset: 8,
                        fill: "#64748b",
                        fontSize: 11,
                      }}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "#1e293b",
                        border: "1px solid #334155",
                        borderRadius: 8,
                        color: "#f1f5f9",
                        fontSize: 12,
                      }}
                      formatter={(val, _name, props) => [
                        `${val} px`,
                        props.payload.label,
                      ]}
                      labelFormatter={(label) => `Frame ${label}`}
                    />
                    <ReferenceLine
                      y={GATE_THRESHOLD}
                      stroke="#ef4444"
                      strokeDasharray="6 3"
                      strokeWidth={2}
                      label={{
                        value: `Gate threshold: ${GATE_THRESHOLD} px`,
                        position: "insideTopRight",
                        fill: "#ef4444",
                        fontSize: 11,
                        fontWeight: 600,
                      }}
                    />
                    <Bar dataKey="error" radius={[3, 3, 0, 0]} maxBarSize={20}>
                      {motionData.map((entry, idx) => (
                        <Cell
                          key={idx}
                          fill={
                            entry.error > GATE_THRESHOLD
                              ? "#ef4444"
                              : entry.label === "MERGE"
                                ? "#f59e0b"
                                : "#3b82f6"
                          }
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="flex flex-wrap gap-5 mt-3 justify-end">
                {[
                  ["#3b82f6", "Normal — within gate"],
                  ["#f59e0b", "Merge Frame"],
                  ["#ef4444", "Drop — gate exceeded"],
                ].map(([color, label]) => (
                  <div key={label} className="flex items-center gap-1.5">
                    <span
                      className="w-3 h-3 rounded-sm shrink-0"
                      style={{ background: color }}
                    />
                    <span className="text-slate-400 text-xs">{label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Drop / Merge Frame Lists ── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Drop frames */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
              Drop Frames
              <span className="ml-auto px-2 py-0.5 bg-red-500/15 text-red-400 rounded-full text-xs font-bold">
                {summary.drop_frames}
              </span>
            </h3>
            {summary.drop_frame_list.length === 0 ? (
              <p className="text-slate-600 text-sm">
                No drop frames detected ✓
              </p>
            ) : (
              <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto pr-1">
                {summary.drop_frame_list.map((f) => {
                  const reasons = summary.drop_reasons?.[String(f)];
                  return (
                    <span
                      key={f}
                      title={reasons?.join(", ")}
                      className="px-2.5 py-1 bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg text-xs font-medium cursor-default hover:bg-red-500/20 transition-colors"
                    >
                      #{f}
                    </span>
                  );
                })}
              </div>
            )}
          </div>

          {/* Merge frames */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
            <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
              Merge Frames
              <span className="ml-auto px-2 py-0.5 bg-amber-500/15 text-amber-400 rounded-full text-xs font-bold">
                {summary.merge_frames}
              </span>
            </h3>
            {summary.merge_frame_list.length === 0 ? (
              <p className="text-slate-600 text-sm">
                No merge frames detected ✓
              </p>
            ) : (
              <div className="flex flex-wrap gap-2 max-h-40 overflow-y-auto pr-1">
                {summary.merge_frame_list.map((f) => (
                  <span
                    key={f}
                    className="px-2.5 py-1 bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded-lg text-xs font-medium"
                  >
                    #{f}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

# Cricket Ball Detection - Frontend

Modern React frontend for cricket ball detection with video upload, analysis, and visualization.

## Features

- 📤 **Video Upload** - Drag & drop or select video files
- 🎯 **Real-time Progress** - Upload and processing progress tracking
- 📊 **Visualizations** - Charts showing detection distribution and ball trajectory
- 🎥 **Annotated Video** - View processed video with detections highlighted
- 📥 **Download Reports** - Download JSON reports and processed videos
- 🆕 **New Tab Results** - Results open in a separate tab for easy comparison

## Setup

### 1. Install Dependencies

```bash
cd frontend/my-app
npm install
```

### 2. Start Backend (in separate terminal)

```bash
cd backend
pip install fastapi uvicorn opencv-python ultralytics scikit-image numpy
uvicorn main:app --reload
```

Backend will run on `http://localhost:8000`

### 3. Start Frontend

```bash
npm run dev
```

Frontend will run on `http://localhost:5173`

## Usage

1. Open `http://localhost:5173` in your browser
2. Click or drag to upload a cricket video
3. Click "Analyze Video" button
4. Wait for processing (progress bar shows status)
5. Results automatically open in a new tab with:
   - Summary statistics (total frames, drops, merges)
   - Annotated video player
   - Drop and merge frame lists
   - Detection distribution chart
   - Ball trajectory visualization
   - Download buttons for video and report

## API Endpoints Used

- `POST /upload` - Upload and process video
- `GET /video/{filename}` - Stream processed video
- `GET /report/{filename}` - Get JSON report

## Build for Production

```bash
npm run build
```

Built files will be in `dist/` directory.

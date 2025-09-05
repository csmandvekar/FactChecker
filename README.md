# DeepVerify Studio

A consumer-facing browser plugin + web UI that verifies any corporate-media content (video, audio, PDF, images) in one click using SOTA deepfake & document forensics — plus a provenance score and suggested remediation steps.

## 🚀 Features

- **PDF Forensics**: Detect metadata tampering, embedded JavaScript, and suspicious objects
- **Image Analysis**: Error Level Analysis (ELA) + CASIA CNN for tampering detection
- **Browser Plugin**: Right-click verification for files and links
- **Real-time Reports**: Forensic analysis with confidence scores and evidence
- **Provenance Tracking**: SHA256 checksums and detailed audit trails

## 🏗️ Architecture

```
DeepVerify Studio/
├── backend/           # FastAPI server
├── frontend/          # React/Next.js web UI
├── plugin/            # Chrome Extension
├── models/            # Pretrained models
├── tests/             # Unit and integration tests
└── docs/              # Documentation
```

## 🛠️ Tech Stack

- **Backend**: FastAPI, PostgreSQL, S3/MinIO
- **Frontend**: React/Next.js, TypeScript
- **Forensics**: PDFiD, pikepdf, ELA, CASIA CNN
- **Plugin**: Chrome Extension API
- **Deployment**: Docker, AWS/GCP

## 📋 Project Phases

1. ✅ **Phase 1**: Planning & Setup
2. 🔄 **Phase 2**: Data Input & Storage
3. ⏳ **Phase 3**: Forensic Analysis — PDF
4. ⏳ **Phase 4**: Forensic Analysis — Image
5. ⏳ **Phase 5**: Backend (FastAPI)
6. ⏳ **Phase 6**: Frontend (React/Next.js)
7. ⏳ **Phase 7**: Browser Plugin
8. ⏳ **Phase 8**: Integration & Testing
9. ⏳ **Phase 9**: Deployment
10. ⏳ **Phase 10**: Final Touches

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL
- Docker (optional)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Plugin Setup
```bash
cd plugin
# Load unpacked extension in Chrome
```

## 📊 API Endpoints

- `POST /api/upload` - Upload file for analysis
- `GET /api/analyze/pdf/{file_id}` - Analyze PDF
- `GET /api/analyze/image/{file_id}` - Analyze image
- `GET /api/report/{file_id}` - Get forensic report

## 🔒 Security

- SHA256 file integrity checks
- JWT authentication
- Rate limiting
- Secure file storage

## 📝 License

MIT License - see LICENSE file for details

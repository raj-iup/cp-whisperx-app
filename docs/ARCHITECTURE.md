# Architecture Blueprint

**CP-WhisperX-App System Architecture**

---

## Overview

CP-WhisperX-App is a modular subtitle generation pipeline designed for scalability from single-user CLI to multi-user web service.

### Current Architecture (v1.0)

```
CLI Job Submission → Native Python Pipeline → File-based Output
```

### Target Architecture (v2.0+)

```
Web UI / API → Job Queue → Distributed Workers → Database → Admin Dashboard
```

---

## Current Architecture (v1.0)

### System Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                       User Interface Layer                      │
├────────────────────────────────────────────────────────────────┤
│  CLI Tools:                                                     │
│  • prepare-job.sh      - Create job from video file           │
│  • run_pipeline.sh     - Execute pipeline                      │
│  • resume-pipeline.sh  - Resume interrupted jobs               │
│  • test-pipeline-status.sh - Check job status                  │
└──────────────────┬─────────────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────────────┐
│                      Job Management Layer                       │
├────────────────────────────────────────────────────────────────┤
│  scripts/prepare_job.py                                         │
│  • Parses video filename → metadata                            │
│  • Creates job directory structure                             │
│  • Generates job-specific .env file                            │
│  • Assigns unique job ID (YYYYMMDD-NNNN)                       │
└──────────────────┬─────────────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────────────┐
│                   Pipeline Orchestrator                         │
├────────────────────────────────────────────────────────────────┤
│  scripts/pipeline.py (JobOrchestrator class)                    │
│  • Loads job configuration                                     │
│  • Manages stage execution sequence                            │
│  • Tracks progress in manifest (job.json)                      │
│  • Handles device selection (CPU/MPS/CUDA)                     │
│  • Implements resume capability                                │
│  • Executes stages natively (no Docker)                        │
└──────────────────┬─────────────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────────────┐
│                      Processing Stages                          │
├────────────────────────────────────────────────────────────────┤
│  Stage Pipeline (14 stages):                                   │
│                                                                 │
│  1. Demux (demux.py)                                           │
│     └─ Extract audio/video streams using ffmpeg               │
│                                                                 │
│  2. TMDB (tmdb.py)                                             │
│     └─ Fetch movie metadata (cast, crew, characters)          │
│                                                                 │
│  3. Pre-NER (pre_ner.py)                                       │
│     └─ Extract named entities from metadata                    │
│                                                                 │
│  4. Silero VAD (silero_vad.py)                                 │
│     └─ Voice Activity Detection (PyTorch)                      │
│                                                                 │
│  5. PyAnnote VAD (pyannote_vad.py)                             │
│     └─ Enhanced VAD (PyTorch)                                  │
│                                                                 │
│  6. Diarization (diarization.py)                               │
│     └─ Speaker identification (PyTorch, WhisperX)              │
│                                                                 │
│  7. ASR (whisperx_integration.py)                              │
│     ├─ Load bias terms from TMDB + Pre-NER                    │
│     ├─ Create bias windows (45s, 15s stride)                  │
│     ├─ Generate global bias prompts                           │
│     └─ Transcribe with active bias (faster-whisper)           │
│                                                                 │
│  8. Glossary Builder (glossary_builder.py)                     │
│     └─ Build film-specific glossary from transcript            │
│                                                                 │
│  9. Second Pass Translation (translation_refine.py)             │
│     └─ Refine translation using glossary                       │
│                                                                 │
│ 10. Lyrics Detection (lyrics_detection.py)                     │
│     └─ Detect and format song sequences                        │
│                                                                 │
│ 11. Post-NER (post_ner.py)                                     │
│     └─ Entity resolution and linking                           │
│                                                                 │
│ 12. Subtitle Generation (subtitle_gen.py)                      │
│     └─ Generate SRT/VTT with CPS optimization                  │
│                                                                 │
│ 13. Mux (mux.py)                                               │
│     └─ Embed subtitles in video using ffmpeg                   │
│                                                                 │
│ 14. Finalize (finalize.py)                                     │
│     └─ Organize output files                                   │
└──────────────────┬─────────────────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────────────┐
│                      Storage Layer                              │
├────────────────────────────────────────────────────────────────┤
│  File-based Storage:                                            │
│  • Jobs: out/YYYY/MM/DD/USER_ID/JOB_ID/                        │
│  • Logs: out/YYYY/MM/DD/USER_ID/JOB_ID/logs/                   │
│  • Config: out/YYYY/MM/DD/USER_ID/JOB_ID/.JOB_ID.env           │
│  • Manifest: out/YYYY/MM/DD/USER_ID/JOB_ID/job.json            │
│  • Glossaries: glossary/cache/                                 │
└────────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. Job Manager
- **Location**: `scripts/prepare_job.py`
- **Responsibilities**:
  - Parse video metadata from filename
  - Create job directory structure
  - Generate unique job IDs
  - Initialize job configuration

#### 2. Pipeline Orchestrator
- **Location**: `scripts/pipeline.py`
- **Responsibilities**:
  - Load and validate job configuration
  - Manage stage execution sequence
  - Track progress in manifest
  - Handle stage dependencies
  - Implement resume capability
  - Device selection and optimization

#### 3. Stage Processors
- **Location**: `scripts/*.py`
- **Responsibilities**:
  - Execute specific processing tasks
  - Read input from previous stages
  - Write output for next stages
  - Log progress and errors

#### 4. Shared Utilities
- **Location**: `shared/*.py`
- **Responsibilities**:
  - Common logging framework
  - Configuration management
  - Device selection utilities
  - Manifest tracking

---

## Future Architecture (v2.0+)

### Vision: Multi-User Web Service

```
┌─────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │   Web UI        │  │  Admin Dashboard │  │   Mobile App   │ │
│  │   (React/Vue)   │  │   (Admin Panel)  │  │   (Future)     │ │
│  └────────┬────────┘  └────────┬─────────┘  └────────┬───────┘ │
│           │                    │                      │         │
│           └────────────────────┴──────────────────────┘         │
│                                │                                 │
└────────────────────────────────┼─────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                                │
├─────────────────────────────────────────────────────────────────┤
│  RESTful API (FastAPI / Django REST Framework)                  │
│  • POST /api/jobs          - Submit new job                     │
│  • GET  /api/jobs/{id}     - Get job status                     │
│  • GET  /api/jobs          - List user jobs                     │
│  • WS   /ws/jobs/{id}      - Real-time updates                  │
│  • POST /api/glossary      - Manage glossaries                  │
│  • GET  /api/analytics     - Usage analytics                    │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  Job Management Service                                          │
│  • Job creation and validation                                  │
│  • File upload handling                                         │
│  • Job queue management                                         │
│  • Priority scheduling                                          │
│  • User quota management                                        │
│                                                                  │
│  Pipeline Orchestration Service                                 │
│  • Stage execution coordination                                 │
│  • Worker assignment                                            │
│  • Progress tracking                                            │
│  • Error handling and retries                                   │
│  • Resource optimization                                        │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Message Queue Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  RabbitMQ / Redis / Celery                                      │
│  • Job queue (priority-based)                                   │
│  • Stage task queue                                             │
│  • Real-time notifications                                      │
│  • Worker coordination                                          │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Worker Pool Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  Distributed Workers (Kubernetes / Docker Swarm)                │
│  • CPU Workers    - General processing                          │
│  • GPU Workers    - ASR, VAD, Diarization (MPS/CUDA)           │
│  • FFmpeg Workers - Video processing (Demux, Mux)              │
│  • ML Workers     - Glossary ML, Lyrics Detection              │
│  • Auto-scaling based on queue depth                           │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Database Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL / MySQL                                              │
│  • users          - User accounts and profiles                  │
│  • jobs           - Job metadata and status                     │
│  • stages         - Stage execution history                     │
│  • glossaries     - Film-specific glossaries                    │
│  • analytics      - Usage metrics                               │
│  • preferences    - User preferences                            │
│                                                                  │
│  Redis Cache                                                     │
│  • Job status cache                                             │
│  • TMDB metadata cache                                          │
│  • Session management                                           │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Storage Layer                             │
├─────────────────────────────────────────────────────────────────┤
│  Object Storage (S3 / MinIO / Azure Blob)                       │
│  • Input videos                                                 │
│  • Processing artifacts                                         │
│  • Output subtitles                                             │
│  • Final videos with embedded subs                              │
│                                                                  │
│  File System (NFS / GlusterFS)                                  │
│  • Shared glossary database                                     │
│  • ML model cache                                               │
│  • Logs and diagnostics                                         │
└─────────────────────────────────────────────────────────────────┘
```

### Database Schema (v2.0)

```sql
-- Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    tier VARCHAR(50) DEFAULT 'free',  -- free, premium, enterprise
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Jobs
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(50) UNIQUE NOT NULL,  -- YYYYMMDD-NNNN
    user_id INTEGER REFERENCES users(id),
    filename VARCHAR(500) NOT NULL,
    title VARCHAR(500),
    year INTEGER,
    status VARCHAR(50) NOT NULL,  -- pending, processing, completed, failed
    current_stage VARCHAR(100),
    progress INTEGER DEFAULT 0,  -- 0-100
    device VARCHAR(20),  -- cpu, mps, cuda
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    config JSONB  -- Job configuration
);

-- Stages
CREATE TABLE stages (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(50) REFERENCES jobs(job_id),
    stage_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- pending, running, completed, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    device VARCHAR(20),
    error_message TEXT,
    output JSONB  -- Stage-specific output data
);

-- Glossaries
CREATE TABLE glossaries (
    id SERIAL PRIMARY KEY,
    film_title VARCHAR(500),
    tmdb_id INTEGER,
    terms JSONB NOT NULL,  -- Glossary terms
    source VARCHAR(50),  -- auto, manual, hybrid
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0
);

-- User Preferences
CREATE TABLE user_preferences (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    default_glossary_strategy VARCHAR(50) DEFAULT 'adaptive',
    default_device VARCHAR(20) DEFAULT 'auto',
    notify_on_completion BOOLEAN DEFAULT TRUE,
    preferences JSONB  -- Other preferences
);

-- Analytics
CREATE TABLE analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    job_id VARCHAR(50) REFERENCES jobs(job_id),
    event_type VARCHAR(100) NOT NULL,  -- job_created, stage_completed, etc.
    event_data JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints (v2.0)

```yaml
# Job Management
POST   /api/jobs                    # Submit new job
GET    /api/jobs                    # List user jobs
GET    /api/jobs/{job_id}           # Get job details
DELETE /api/jobs/{job_id}           # Cancel/delete job
WS     /ws/jobs/{job_id}            # Real-time job updates

# Job Actions
POST   /api/jobs/{job_id}/resume    # Resume interrupted job
POST   /api/jobs/{job_id}/retry     # Retry failed job
GET    /api/jobs/{job_id}/logs      # Get job logs
GET    /api/jobs/{job_id}/download  # Download output

# Glossary Management
GET    /api/glossaries              # List glossaries
GET    /api/glossaries/{id}         # Get glossary
POST   /api/glossaries              # Create glossary
PUT    /api/glossaries/{id}         # Update glossary
DELETE /api/glossaries/{id}         # Delete glossary

# Analytics
GET    /api/analytics/usage         # User usage stats
GET    /api/analytics/performance   # System performance
GET    /api/analytics/jobs          # Job statistics

# Admin
GET    /api/admin/workers           # Worker status
GET    /api/admin/queue             # Queue status
GET    /api/admin/users             # User management
POST   /api/admin/workers/{id}/restart  # Restart worker
```

### Web UI Features (v2.0)

#### User Dashboard
- Drag-and-drop video upload
- Job list with status
- Real-time progress tracking
- Download manager
- Usage statistics

#### Job Configuration
- Visual configuration builder
- Preset templates (speed, quality, balanced)
- Advanced options (collapsible)
- Live validation

#### Results Viewer
- Embedded video player with subtitles
- Side-by-side comparison
- Subtitle editor (inline corrections)
- Export options (SRT, VTT, embedded)

#### Admin Dashboard
- System health monitoring
- Worker pool management
- Job queue visualization
- User management
- Performance analytics
- Cost tracking

---

## Migration Path (v1.0 → v2.0)

### Phase 1: Database Integration (Q1 2025)
- [ ] Set up PostgreSQL database
- [ ] Create database schema
- [ ] Migrate job tracking to database
- [ ] Implement job history API
- [ ] Add analytics tracking

### Phase 2: API Layer (Q2 2025)
- [ ] Develop RESTful API (FastAPI)
- [ ] Implement authentication (JWT)
- [ ] Create WebSocket for real-time updates
- [ ] Build API documentation (Swagger)
- [ ] Add rate limiting and quotas

### Phase 3: Worker Pool (Q3 2025)
- [ ] Containerize pipeline stages
- [ ] Set up message queue (RabbitMQ)
- [ ] Implement distributed workers
- [ ] Add auto-scaling
- [ ] Optimize resource allocation

### Phase 4: Web UI (Q4 2025)
- [ ] Design UI/UX
- [ ] Implement frontend (React)
- [ ] Integrate with API
- [ ] Add admin dashboard
- [ ] User testing and refinement

### Phase 5: Production Deployment (Q1 2026)
- [ ] Set up Kubernetes cluster
- [ ] Configure load balancing
- [ ] Implement monitoring (Prometheus/Grafana)
- [ ] Set up backups and disaster recovery
- [ ] Launch beta program

---

## Technology Stack

### Current (v1.0)
- **Language**: Python 3.11+
- **ML Frameworks**: PyTorch, WhisperX, faster-whisper
- **GPU**: MPS (Apple), CUDA (NVIDIA)
- **Storage**: File system
- **Deployment**: Native installation

### Future (v2.0)
- **Backend**: FastAPI / Django
- **Frontend**: React / Vue.js
- **Database**: PostgreSQL + Redis
- **Message Queue**: RabbitMQ / Celery
- **Storage**: S3 / MinIO
- **Containerization**: Docker + Kubernetes
- **Monitoring**: Prometheus + Grafana
- **CI/CD**: GitHub Actions

---

## Scalability Considerations

### Current Limitations (v1.0)
- Single-user, single-machine execution
- No job queuing
- No distributed processing
- File-based storage only
- Manual job management

### Target Capabilities (v2.0)
- Multi-user support with authentication
- Distributed worker pool
- Auto-scaling based on load
- Priority job queuing
- Cloud storage integration
- Real-time monitoring
- Automated failover

---

## Security Considerations (v2.0)

- **Authentication**: JWT tokens, OAuth2
- **Authorization**: Role-based access control (RBAC)
- **Data Encryption**: TLS/SSL for transit, at-rest encryption
- **API Security**: Rate limiting, CORS policies
- **File Scanning**: Virus/malware detection on uploads
- **Audit Logging**: All user actions logged
- **Secrets Management**: Vault integration

---

**Current Version**: v1.0 (CLI-based, single-user)  
**Target Version**: v2.0 (Web-based, multi-user)  
**Timeline**: 12-18 months

For current implementation details, see **[Technical Documentation](docs/technical/)**.

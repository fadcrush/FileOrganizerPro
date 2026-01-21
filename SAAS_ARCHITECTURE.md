

<boltFillSpan />

# FileOrganizer Pro - SaaS Architecture Document

**Version:** 1.0
**Date:** 2026-01-19
**Author:** David - JSMS Academy

---

## 🎯 Executive Summary

FileOrganizer Pro SaaS transforms the desktop application into a cloud-based platform with subscription-based access, real-time collaboration, and cross-platform support. This document outlines the complete technical architecture, database schemas, API design, and implementation roadmap.

---

## 📐 System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                          │
├─────────────────────────────────────────────────────────────┤
│  Web App (React)  │  Desktop (Electron)  │  Mobile (React Native)  │
└─────────────┬───────────────────┬───────────────────┬────────┘
              │                   │                   │
              └───────────────────┴───────────────────┘
                              │
                      ┌───────▼────────┐
                      │   API Gateway   │
                      │  (Kong/AWS)     │
                      └───────┬────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
      ┌───────▼────────┐            ┌────────▼────────┐
      │  REST API       │            │  WebSocket      │
      │  (FastAPI)      │            │  (Socket.io)    │
      └───────┬────────┘            └────────┬────────┘
              │                               │
      ┌───────▼───────────────────────────────▼────────┐
      │          APPLICATION SERVICES LAYER             │
      ├────────────────────────────────────────────────┤
      │ • Auth Service      • File Processing Service  │
      │ • Organization Svc  • Duplicate Detection      │
      │ • Billing Service   • AI Categorization        │
      │ • Analytics Service • Notification Service     │
      └───────┬────────────────────────────────────────┘
              │
      ┌───────▼────────────────────────────────────────┐
      │             DATA LAYER                          │
      ├────────────────────────────────────────────────┤
      │  PostgreSQL  │  Redis   │  S3/R2  │  Elasticsearch │
      │  (Metadata)  │  (Cache) │  (Files)│  (Search)      │
      └────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema

### PostgreSQL Schema

#### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    storage_quota_gb INTEGER DEFAULT 5,
    storage_used_bytes BIGINT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,

    CONSTRAINT valid_tier CHECK (subscription_tier IN ('free', 'pro', 'business', 'enterprise'))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_subscription ON users(subscription_tier);
```

#### Subscriptions Table
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plan_id VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    stripe_subscription_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),
    current_period_start TIMESTAMP NOT NULL,
    current_period_end TIMESTAMP NOT NULL,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    trial_start TIMESTAMP,
    trial_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_status CHECK (status IN ('active', 'canceled', 'past_due', 'trialing', 'paused'))
);

CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_stripe ON subscriptions(stripe_subscription_id);
```

#### Files Table
```sql
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(500) NOT NULL,
    original_path TEXT,
    storage_path TEXT NOT NULL,
    category VARCHAR(100),
    file_extension VARCHAR(50),
    file_size_bytes BIGINT NOT NULL,
    mime_type VARCHAR(100),
    md5_hash VARCHAR(32),
    sha256_hash VARCHAR(64),
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of UUID REFERENCES files(id),
    thumbnail_url TEXT,
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    organized_at TIMESTAMP,
    deleted_at TIMESTAMP,

    CONSTRAINT positive_size CHECK (file_size_bytes >= 0)
);

CREATE INDEX idx_files_user ON files(user_id);
CREATE INDEX idx_files_md5 ON files(md5_hash);
CREATE INDEX idx_files_category ON files(category);
CREATE INDEX idx_files_tags ON files USING GIN(tags);
CREATE INDEX idx_files_deleted ON files(deleted_at) WHERE deleted_at IS NULL;
```

#### Organization Jobs Table
```sql
CREATE TABLE organization_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    source_path TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    organization_mode VARCHAR(50) NOT NULL,
    operation_type VARCHAR(20) NOT NULL,
    options JSONB DEFAULT '{}',
    files_processed INTEGER DEFAULT 0,
    files_moved INTEGER DEFAULT 0,
    duplicates_found INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'canceled')),
    CONSTRAINT valid_operation CHECK (operation_type IN ('move', 'copy'))
);

CREATE INDEX idx_jobs_user ON organization_jobs(user_id);
CREATE INDEX idx_jobs_status ON organization_jobs(status);
CREATE INDEX idx_jobs_created ON organization_jobs(created_at DESC);
```

#### File Tags Table
```sql
CREATE TABLE file_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tag_name VARCHAR(100) NOT NULL,
    tag_color VARCHAR(7) DEFAULT '#00f7ff',
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, tag_name)
);

CREATE INDEX idx_file_tags_user ON file_tags(user_id);
CREATE INDEX idx_file_tags_name ON file_tags(tag_name);
```

#### Analytics Events Table
```sql
CREATE TABLE analytics_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_analytics_user ON analytics_events(user_id);
CREATE INDEX idx_analytics_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_created ON analytics_events(created_at DESC);
```

#### API Keys Table (for Enterprise)
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,
    name VARCHAR(200) NOT NULL,
    permissions JSONB DEFAULT '{}',
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_user ON api_keys(user_id);
```

---

## 🔌 REST API Specification

### Base URL
```
Production: https://api.fileorganizerpro.com/v1
Staging: https://staging-api.fileorganizerpro.com/v1
```

### Authentication
All authenticated endpoints require JWT token in Authorization header:
```
Authorization: Bearer <jwt_token>
```

### API Endpoints

#### Authentication Endpoints

**POST /auth/register**
```json
Request:
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "username": "johndoe",
  "full_name": "John Doe"
}

Response: 201 Created
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "johndoe",
    "subscription_tier": "free"
  },
  "access_token": "jwt_token",
  "refresh_token": "refresh_token"
}
```

**POST /auth/login**
```json
Request:
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response: 200 OK
{
  "user": {...},
  "access_token": "jwt_token",
  "refresh_token": "refresh_token"
}
```

**POST /auth/refresh**
```json
Request:
{
  "refresh_token": "refresh_token"
}

Response: 200 OK
{
  "access_token": "new_jwt_token"
}
```

#### File Management Endpoints

**POST /files/upload**
```
Content-Type: multipart/form-data

Form Data:
  - file: (binary)
  - category: "Images" (optional)
  - tags: ["vacation", "2024"] (optional)

Response: 201 Created
{
  "file": {
    "id": "uuid",
    "filename": "photo.jpg",
    "size_bytes": 2048000,
    "category": "Images",
    "storage_path": "s3://bucket/user-id/files/uuid.jpg",
    "thumbnail_url": "https://cdn.../thumb.jpg",
    "md5_hash": "abc123...",
    "created_at": "2024-01-19T10:00:00Z"
  }
}
```

**GET /files**
```
Query Parameters:
  - page: 1
  - per_page: 50
  - category: "Images"
  - tags: ["vacation"]
  - sort_by: "created_at" | "size" | "filename"
  - order: "asc" | "desc"

Response: 200 OK
{
  "files": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 250,
    "pages": 5
  }
}
```

**GET /files/{file_id}**
```json
Response: 200 OK
{
  "file": {
    "id": "uuid",
    "filename": "photo.jpg",
    "size_bytes": 2048000,
    "category": "Images",
    "tags": ["vacation", "2024"],
    "metadata": {
      "width": 1920,
      "height": 1080,
      "camera": "Canon EOS R5"
    },
    "download_url": "https://cdn.../download/secure-token",
    "created_at": "2024-01-19T10:00:00Z"
  }
}
```

**DELETE /files/{file_id}**
```json
Response: 204 No Content
```

#### Organization Endpoints

**POST /organize/jobs**
```json
Request:
{
  "source_path": "/uploads/batch-123",
  "organization_mode": "category_year",
  "operation_type": "move",
  "options": {
    "skip_duplicates": true,
    "create_backup": false,
    "apply_icons": true
  }
}

Response: 202 Accepted
{
  "job": {
    "id": "uuid",
    "status": "pending",
    "created_at": "2024-01-19T10:00:00Z"
  }
}
```

**GET /organize/jobs/{job_id}**
```json
Response: 200 OK
{
  "job": {
    "id": "uuid",
    "status": "running",
    "progress": 45.5,
    "files_processed": 455,
    "files_moved": 320,
    "duplicates_found": 135,
    "errors_count": 0,
    "started_at": "2024-01-19T10:00:00Z",
    "estimated_completion": "2024-01-19T10:15:00Z"
  }
}
```

**DELETE /organize/jobs/{job_id}**
```json
Response: 200 OK
{
  "message": "Job canceled successfully"
}
```

#### Duplicate Management Endpoints

**GET /duplicates**
```
Query Parameters:
  - category: "Images"
  - min_size_mb: 1.0
  - similarity_threshold: 0.9

Response: 200 OK
{
  "duplicate_groups": [
    {
      "hash": "abc123...",
      "original_file": {...},
      "duplicates": [
        {"file": {...}, "similarity": 1.0},
        {"file": {...}, "similarity": 0.95}
      ],
      "space_wasted_bytes": 4096000
    }
  ],
  "total_duplicates": 250,
  "total_space_wasted_gb": 2.5
}
```

**POST /duplicates/delete**
```json
Request:
{
  "file_ids": ["uuid1", "uuid2", "uuid3"],
  "keep_original": true
}

Response: 200 OK
{
  "deleted_count": 3,
  "space_freed_bytes": 4096000
}
```

#### Analytics Endpoints

**GET /analytics/dashboard**
```json
Response: 200 OK
{
  "storage": {
    "used_gb": 12.5,
    "quota_gb": 100.0,
    "percentage": 12.5
  },
  "files": {
    "total_count": 5420,
    "by_category": {
      "Images": 2100,
      "Videos": 450,
      "Documents": 1800,
      "Others": 1070
    }
  },
  "duplicates": {
    "count": 340,
    "space_wasted_gb": 2.8
  },
  "recent_activity": [...]
}
```

#### Subscription & Billing Endpoints

**GET /subscription**
```json
Response: 200 OK
{
  "subscription": {
    "plan": "pro",
    "status": "active",
    "current_period_end": "2024-02-19T00:00:00Z",
    "cancel_at_period_end": false
  },
  "usage": {
    "storage_used_gb": 45.2,
    "storage_quota_gb": 100.0
  }
}
```

**POST /subscription/upgrade**
```json
Request:
{
  "plan_id": "pro_monthly",
  "payment_method_id": "pm_..."
}

Response: 200 OK
{
  "subscription": {...},
  "invoice": {...}
}
```

---

## 🎨 Web Dashboard Design (React)

### Technology Stack

- **Framework:** React 18+ with TypeScript
- **State Management:** Redux Toolkit / Zustand
- **UI Library:** Tailwind CSS + Framer Motion
- **Charts:** Recharts / Chart.js
- **File Upload:** React Dropzone
- **Real-time:** Socket.io client
- **HTTP Client:** Axios / React Query

### Component Hierarchy

```
<App>
  ├── <AuthProvider>
  │   ├── <LoginPage>
  │   └── <RegisterPage>
  │
  ├── <Dashboard>
  │   ├── <Sidebar>
  │   │   ├── <NavItem>: Dashboard
  │   │   ├── <NavItem>: Files
  │   │   ├── <NavItem>: Organize
  │   │   ├── <NavItem>: Duplicates
  │   │   ├── <NavItem>: Analytics
  │   │   └── <NavItem>: Settings
  │   │
  │   ├── <TopBar>
  │   │   ├── <SearchBar>
  │   │   ├── <NotificationBell>
  │   │   └── <UserMenu>
  │   │
  │   └── <MainContent>
  │       ├── <DashboardHome>
  │       │   ├── <StorageWidget>
  │       │   ├── <RecentFilesWidget>
  │       │   ├── <DuplicatesWidget>
  │       │   └── <ActivityWidget>
  │       │
  │       ├── <FilesView>
  │       │   ├── <FileUploadZone>
  │       │   ├── <FileFilters>
  │       │   ├── <FileGrid>
  │       │   │   └── <FileCard> (multiple)
  │       │   └── <FilePagination>
  │       │
  │       ├── <OrganizeView>
  │       │   ├── <OrganizeConfigForm>
  │       │   ├── <OrganizePreview>
  │       │   └── <ActiveJobsList>
  │       │       └── <JobProgressCard> (multiple)
  │       │
  │       ├── <DuplicatesView>
  │       │   ├── <DuplicateFilters>
  │       │   └── <DuplicateGroups>
  │       │       └── <DuplicateGroup> (multiple)
  │       │           ├── <OriginalFile>
  │       │           └── <DuplicateFiles>
  │       │
  │       ├── <AnalyticsView>
  │       │   ├── <StorageChart>
  │       │   ├── <CategoryBreakdownChart>
  │       │   ├── <ActivityTimeline>
  │       │   └── <InsightsPanel>
  │       │
  │       └── <SettingsView>
  │           ├── <ProfileSettings>
  │           ├── <SubscriptionSettings>
  │           ├── <SecuritySettings>
  │           └── <PreferencesSettings>
```

### Key Features Implementation

#### Real-time Job Progress
```javascript
// Socket.io integration
const socket = io('wss://api.fileorganizerpro.com');

socket.on('job:progress', (data) => {
  // Update job progress in real-time
  dispatch(updateJobProgress(data));
});

socket.on('job:complete', (data) => {
  // Show notification
  toast.success('Organization complete!');
  dispatch(completeJob(data));
});
```

#### File Upload with Progress
```javascript
const handleFileUpload = async (files) => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));

  await axios.post('/files/upload', formData, {
    onUploadProgress: (progressEvent) => {
      const percentCompleted = Math.round(
        (progressEvent.loaded * 100) / progressEvent.total
      );
      setUploadProgress(percentCompleted);
    }
  });
};
```

---

## 🏗️ Infrastructure & Deployment

### Cloud Provider: AWS (or alternatives)

#### Compute
- **ECS Fargate** for containerized API services
- **Lambda** for serverless functions (image processing, etc.)
- **EC2** for background workers

#### Storage
- **S3** for file storage (or Cloudflare R2 for cost savings)
- **RDS PostgreSQL** for relational data
- **ElastiCache Redis** for caching and sessions

#### CDN & Edge
- **CloudFront** for global CDN
- **Route 53** for DNS

#### Security
- **WAF** for API protection
- **Secrets Manager** for credentials
- **KMS** for encryption keys

### Docker Compose (Development)

```yaml
version: '3.8'

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/fileorganizer
      - REDIS_URL=redis://redis:6379
      - S3_BUCKET=dev-fileorganizer
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=fileorganizer
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000

  worker:
    build: ./backend
    command: celery -A app.worker worker --loglevel=info
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

---

## 💰 Pricing Strategy

| Feature | Free | Pro | Business | Enterprise |
|---------|------|-----|----------|------------|
| **Storage** | 5 GB | 100 GB | 1 TB | Unlimited |
| **File uploads** | 10 files/day | Unlimited | Unlimited | Unlimited |
| **Organization jobs** | 5/month | Unlimited | Unlimited | Unlimited |
| **AI categorization** | ❌ | ✅ | ✅ | ✅ |
| **Fuzzy duplicates** | ❌ | ✅ | ✅ | ✅ |
| **File tagging** | Basic | Advanced | Advanced | Advanced |
| **Team sharing** | ❌ | ❌ | ✅ (10 users) | ✅ (Unlimited) |
| **API access** | ❌ | ❌ | ❌ | ✅ |
| **Priority support** | ❌ | Email | Email + Chat | Dedicated |
| **Price** | $0 | $9.99/mo | $29.99/mo | Custom |

---

## 🚀 Implementation Roadmap

### Phase 1: MVP (Months 1-2)
- [ ] Set up infrastructure (AWS/Docker)
- [ ] Implement authentication system
- [ ] Build core API endpoints
- [ ] Create basic React dashboard
- [ ] File upload and storage
- [ ] Basic organization functionality

### Phase 2: Core Features (Months 3-4)
- [ ] Real-time job progress
- [ ] Duplicate detection
- [ ] Analytics dashboard
- [ ] Stripe integration for billing
- [ ] Email notifications
- [ ] Mobile-responsive UI

### Phase 3: Advanced Features (Months 5-6)
- [ ] AI categorization
- [ ] Fuzzy duplicate detection
- [ ] Advanced tagging system
- [ ] Team collaboration
- [ ] API for enterprise
- [ ] Desktop app (Electron)

### Phase 4: Scale & Optimize (Months 7-8)
- [ ] Performance optimization
- [ ] Multi-region deployment
- [ ] Advanced analytics
- [ ] Integration marketplace
- [ ] White-label options

---

## 📊 Success Metrics

### KPIs to Track
- **User Acquisition:** Sign-ups per month
- **Conversion Rate:** Free → Paid conversion %
- **MRR/ARR:** Monthly/Annual Recurring Revenue
- **Churn Rate:** Subscriber cancellations
- **Storage Usage:** Average GB per user
- **API Latency:** P50, P95, P99 response times
- **Job Success Rate:** % of successful organizations
- **Customer Satisfaction:** NPS score

---

## 🔒 Security Considerations

### Data Protection
- All files encrypted at rest (AES-256)
- TLS 1.3 for data in transit
- Regular security audits
- GDPR & SOC 2 compliance

### Authentication
- JWT with short expiry
- Refresh token rotation
- 2FA optional/required by tier
- Session management

### API Security
- Rate limiting (per tier)
- API key rotation
- Request signing
- IP whitelisting (Enterprise)

---

## 📝 License & Legal

- Terms of Service
- Privacy Policy
- GDPR compliance
- Data retention policies
- SLA guarantees (Enterprise)

---

**End of Architecture Document**

For questions or clarifications, contact: david@jsmsacademy.com


# Sonic AI V3 — Runtime Failures Analysis

**Audit Date:** 2026-06-15  
**Scope:** Import failures, circular dependencies, undefined variables, broken services

---

## Executive Summary

**Status:** MULTIPLE CRITICAL RUNTIME FAILURES DETECTED

The application cannot run successfully due to:
- Missing module imports (storage.local)
- Missing configuration files
- Missing environment variables
- Incomplete service implementations
- Missing frontend assets

**Severity:** CRITICAL - Application will crash on startup

---

## Backend Runtime Failures

### 1. Missing Storage Module (CRITICAL)

**Location:** `apps/api/routes_projects.py:6`

```python
from .storage.local import save_file
```

**Error:**
```
ModuleNotFoundError: No module named 'storage'
```

**Impact:**
- Upload endpoint `/api/v1/projects/{project_id}/upload` will crash
- Any file upload attempt will fail
- Asset storage is completely broken

**Root Cause:**
- Directory `apps/api/storage/` does not exist
- Module `storage/local.py` was never created
- Function `save_file()` is not implemented

**Required Fix:**
1. Create `apps/api/storage/__init__.py`
2. Create `apps/api/storage/local.py`
3. Implement `save_file(project_id, filename, fileobj)` function
4. Add proper error handling and validation

**Workaround:** None - feature is completely broken

---

### 2. Missing Environment Variables

**Location:** `apps/api/config.py`

**Current Configuration:**
```python
class Settings:
    ENV: str = os.getenv("ENV", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
```

**Missing Critical Variables:**
```
SUPABASE_URL              - Required for auth
SUPABASE_SERVICE_KEY      - Required for auth
SUPABASE_ANON_KEY         - Required for frontend auth
AUTH_SECRET               - Required for JWT signing
UPLOAD_STORAGE_PATH       - Required for file storage
ALLOWED_ORIGINS           - Required for CORS
MAX_UPLOAD_SIZE           - Required for upload limits
```

**Impact:**
- Authentication will fail
- File uploads have no storage path
- CORS is wide open (security risk)
- No upload size limits (DoS risk)

**Current Behavior:**
- Falls back to SQLite (dev.db) for database
- No auth validation occurs
- Files would be saved to undefined location

**Required Fix:**
1. Create `.env` file from `.env.example`
2. Add all missing environment variables
3. Update `Settings` class to include all variables
4. Add validation for required variables

---

### 3. Database Session Dependency Issues

**Location:** `apps/api/database.py:16-23`

```python
@contextmanager
def get_db_session():
    """Yield a SQLAlchemy Session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Issue:**
- Using context manager but FastAPI expects a generator function
- Should use `Depends()` pattern properly

**Current Usage in routes_projects.py:**
```python
def list_projects(user_id: str = None, db=Depends(get_db_session)):
```

**Problem:**
- `Depends()` expects a callable that returns a generator
- Context manager pattern doesn't work directly with `Depends()`

**Impact:**
- Database sessions may not be properly managed
- Potential connection leaks
- Transaction handling issues

**Required Fix:**
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

### 4. Model Import Inconsistencies

**Location:** Multiple files

**Issue 1:** `apps/api/routes_projects.py:4`
```python
from .models import Base
```

**Issue 2:** `apps/api/services/project_service.py:3`
```python
from ..models import Project, Asset, Analysis
```

**Problem:**
- Inconsistent relative import patterns
- `Base` is imported from `.models` but used in routes
- Models are imported with `..models` in services

**Impact:**
- Potential import errors depending on how app is run
- Confusion about module structure
- May break when running tests

**Required Fix:**
- Standardize on one import pattern
- Use absolute imports from app root
- Update all files consistently

---

### 5. Missing Pydantic Dependency

**Location:** `apps/api/schemas/project.py:1`

```python
from pydantic import BaseModel
```

**Error:**
```
ModuleNotFoundError: No module named 'pydantic'
```

**Impact:**
- All schema validation will fail
- API endpoints cannot parse request bodies
- Response serialization will fail

**Current Status:**
- Pydantic is not in requirements.txt
- Code assumes Pydantic v2 (model_config syntax)

**Required Fix:**
1. Add `pydantic==2.5.3` to requirements.txt
2. Install with `pip install pydantic`

---

### 6. Missing python-multipart Dependency

**Location:** `apps/api/routes_projects.py:49`

```python
def upload_asset(project_id: str, file: UploadFile = File(...), ...):
```

**Error:**
```
RuntimeError: python-multipart must be installed to use form parsing
```

**Impact:**
- File upload endpoint will crash
- Cannot parse multipart/form-data requests
- All file uploads fail

**Required Fix:**
1. Add `python-multipart==0.0.6` to requirements.txt
2. Install with `pip install python-multipart`

---

### 7. Undefined Variables in Upload Handler

**Location:** `apps/api/routes_projects.py:56-57`

```python
contents = file.file.read()
storage_path = save_file(project_id, file.filename, fileobj=type("o", (), {"read": lambda self, _=None: contents})())
```

**Issues:**
1. Creating anonymous object with `type("o", (), {...})`
2. Lambda function captures `contents` but creates new object
3. Overly complex for simple file handling
4. `save_file` function doesn't exist

**Impact:**
- Code is fragile and hard to maintain
- Will crash due to missing `save_file`
- File contents may not be properly handled

**Required Fix:**
```python
contents = await file.read()
storage_path = await storage_service.save_file(
    user_id=current_user.id,
    project_id=project_id,
    filename=file.filename,
    content=contents
)
```

---

### 8. Missing Authentication Middleware

**Location:** All API routes

**Issue:**
- No authentication decorator or dependency
- No `current_user` extraction
- No JWT verification
- No ownership validation

**Example from routes_projects.py:**
```python
@router.get("/api/v1/projects", response_model=List[ProjectRead])
def list_projects(user_id: str = None, db=Depends(get_db_session)):
    # No authentication check!
    svc = ProjectService(db)
    projects = svc.list_projects(user_id=user_id)
    return projects
```

**Impact:**
- All endpoints are public
- No user context
- No ownership validation
- Critical security vulnerability

**Required Fix:**
1. Create `apps/api/core/security.py`
2. Implement `get_current_user()` dependency
3. Add JWT verification
4. Add to all protected routes

---

### 9. Database Migration Not Run

**Location:** `apps/api/alembic/versions/`

**Issue:**
- Directory is empty (only README.md)
- No initial migration exists
- Database tables not created

**Impact:**
- Application will crash on first database query
- SQLAlchemy will raise "table does not exist" errors

**Current Workaround:**
```python
@router.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)
```

**Problem with Workaround:**
- Only creates tables, doesn't run migrations
- No migration history
- Can't track schema changes
- Not production-ready

**Required Fix:**
1. Create initial migration: `alembic revision --autogenerate -m "Initial schema"`
2. Run migration: `alembic upgrade head`
3. Remove `create_tables()` workaround

---

### 10. Missing ProducerProfile Implementation

**Location:** `apps/api/models/producer_profile.py`

**Current Code:**
```python
# File exists but is likely empty or stub
```

**Impact:**
- Producer profile feature is non-functional
- Profile aggregation cannot work
- Sprint 1 requirement not met

**Required Fix:**
- Implement full ProducerProfile model with fields
- Add relationships to User
- Add aggregation logic

---

## Frontend Runtime Failures

### 1. Missing globals.css (CRITICAL)

**Location:** `apps/web/app/layout.tsx:2`

```tsx
import './globals.css';
```

**Error:**
```
Module not found: Can't resolve './globals.css'
```

**Impact:**
- Application will not build
- No styles will be applied
- Tailwind CSS won't work

**Required Fix:**
1. Create `apps/web/app/globals.css`
2. Add Tailwind directives
3. Add base styles

---

### 2. Missing Next.js Configuration

**Location:** `apps/web/next.config.ts`

**Issue:**
- File does not exist
- Next.js 15 requires configuration
- API proxy not configured
- Image optimization not configured

**Impact:**
- Using default configuration
- Cannot proxy API requests
- No environment variable handling
- No custom webpack config

**Required Fix:**
Create `next.config.ts` with:
- API proxy to backend
- Environment variables
- Image domains
- Build optimization

---

### 3. Missing Tailwind Configuration

**Location:** `apps/web/tailwind.config.ts`

**Issue:**
- File does not exist
- Tailwind CSS won't work properly
- No custom theme
- No content paths configured

**Impact:**
- Tailwind classes may not be generated
- No custom colors/spacing
- Production build may be bloated

**Required Fix:**
Create `tailwind.config.ts` with:
- Content paths
- Theme customization
- Plugin configuration

---

### 4. Missing PostCSS Configuration

**Location:** `apps/web/postcss.config.js`

**Issue:**
- File does not exist
- Required for Tailwind CSS
- Autoprefixer won't run

**Impact:**
- Tailwind CSS won't process
- No vendor prefixes
- Styles won't work

**Required Fix:**
Create `postcss.config.js` with Tailwind and Autoprefixer

---

### 5. Missing API Client

**Location:** `apps/web/lib/api.ts`

**Issue:**
- File does not exist
- No API communication layer
- Components cannot fetch data

**Impact:**
- Cannot make API requests
- No error handling
- No request/response interceptors

**Required Fix:**
Create API client with:
- Axios or fetch wrapper
- Base URL configuration
- Auth token injection
- Error handling

---

### 6. Missing Supabase Client

**Location:** `apps/web/lib/supabase.ts`

**Issue:**
- File does not exist
- No authentication client
- Cannot sign in users

**Impact:**
- Authentication is broken
- Cannot access protected routes
- No user session management

**Required Fix:**
Create Supabase client with:
- Client initialization
- Auth helpers
- Session management

---

### 7. Missing TanStack Query Setup

**Location:** `apps/web/lib/query.tsx`

**Issue:**
- File does not exist
- No query client provider
- Cannot use React Query hooks

**Impact:**
- No data fetching
- No caching
- No optimistic updates

**Required Fix:**
Create Query provider with:
- QueryClient configuration
- Provider component
- Default options

---

### 8. Incomplete Components

**Location:** `apps/web/app/components/`

**ProjectForm.tsx Issues:**
- May not have proper form validation
- May not handle API errors
- May not have loading states

**ProjectList.tsx Issues:**
- May not handle empty states
- May not have pagination
- May not have error handling

**Required Fix:**
- Review and complete all components
- Add proper error handling
- Add loading states
- Add empty states

---

## Circular Import Analysis

**Status:** No circular imports detected in current minimal implementation

**Risk Areas for Future:**
- Models importing services
- Services importing models
- Routes importing services importing models

**Prevention:**
- Keep clear dependency hierarchy
- Use dependency injection
- Avoid bidirectional imports

---

## Environment Variable Failures

### Backend Missing Variables

```bash
# Critical - Will cause crashes
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
UPLOAD_STORAGE_PATH=

# Important - Will cause security issues
AUTH_SECRET=
ALLOWED_ORIGINS=

# Optional - Has defaults
DATABASE_URL=sqlite:///./dev.db
ENV=development
```

### Frontend Missing Variables

```bash
# Critical - Will cause crashes
NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

---

## Service Implementation Failures

### ProjectService Issues

**Missing Features:**
1. No ownership validation
2. No event emission
3. No activity tracking
4. No error handling
5. No transaction management

**Example Issue:**
```python
def create_project(self, user_id: str, name: str, ...):
    project = Project(...)
    self.db.add(project)
    self.db.commit()  # No error handling!
    self.db.refresh(project)
    return project
```

**Problems:**
- No try/except
- No rollback on error
- No validation
- No event emission

---

## Summary of Runtime Failures

### Critical (Application Won't Start)

1. ❌ Missing storage module - Upload crashes
2. ❌ Missing globals.css - Frontend won't build
3. ❌ Missing Pydantic - Backend crashes
4. ❌ Missing python-multipart - Uploads crash
5. ❌ Missing database migrations - Queries crash

### High (Features Don't Work)

6. ❌ Missing authentication - Security breach
7. ❌ Missing environment variables - Config fails
8. ❌ Missing API client - Frontend can't communicate
9. ❌ Missing Supabase client - Auth doesn't work
10. ❌ Missing TanStack Query - Data fetching broken

### Medium (Degraded Functionality)

11. ❌ Missing Next.js config - Suboptimal setup
12. ❌ Missing Tailwind config - Styles incomplete
13. ❌ Database session issues - Potential leaks
14. ❌ Import inconsistencies - Fragile code

---

## Recommended Fix Order

### Phase 1: Make It Bootable (Day 1)

1. Add missing dependencies to requirements.txt
2. Create globals.css
3. Create Tailwind/PostCSS configs
4. Create Next.js config
5. Run `pip install -r requirements.txt`
6. Run `pnpm install`

### Phase 2: Make It Functional (Day 2)

7. Create storage module
8. Create database migration
9. Run migration
10. Create .env files
11. Create API client
12. Create Supabase client

### Phase 3: Make It Secure (Day 3)

13. Implement authentication
14. Add ownership validation
15. Add input validation
16. Fix CORS configuration
17. Add rate limiting

### Phase 4: Make It Complete (Week 1)

18. Implement event bus
19. Implement metadata service
20. Implement vault search
21. Implement activity feed
22. Implement producer profile

---

**End of Runtime Failures Analysis**
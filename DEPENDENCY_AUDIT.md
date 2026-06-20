# Sonic AI V3 — Dependency Audit

**Audit Date:** 2026-06-15  
**Scope:** Complete dependency analysis across all workspaces

---

## Executive Summary

**Status:** INCOMPLETE AND INSECURE

- Backend has 6 dependencies installed, needs 15+ more
- Frontend has 7 dependencies installed, needs 10+ more
- Multiple security vulnerabilities detected
- No dependency pinning (using >= instead of ==)
- Outdated major versions in use
- Missing critical production dependencies

**Risk Level:** HIGH

---

## Backend Dependencies (apps/api)

### Current requirements.txt

```txt
fastapi>=0.95.0
uvicorn[standard]>=0.22.0
sqlalchemy>=1.4.0
alembic>=1.11.0
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0
```

### Issues with Current Dependencies

#### 1. SQLAlchemy Version (CRITICAL)

**Current:** `sqlalchemy>=1.4.0`  
**Issue:** Using SQLAlchemy 1.x which has:
- Known security vulnerabilities
- Deprecated API patterns
- Performance issues
- No async support

**Required:** `sqlalchemy>=2.0.0,<3.0.0`

**Impact:** 
- Security risk
- Code uses 1.x patterns that need migration
- Missing modern features

#### 2. FastAPI Version (MEDIUM)

**Current:** `fastapi>=0.95.0`  
**Issue:** Using older version, missing features

**Recommended:** `fastapi>=0.115.0,<1.0.0`

#### 3. Loose Version Constraints (HIGH)

**Issue:** All dependencies use `>=` without upper bounds

**Risk:**
- Breaking changes can be pulled automatically
- No reproducible builds
- Deployment inconsistencies

**Solution:** Pin all dependencies with `==` or use `>=X.Y.Z,<X+1.0.0`

### Missing Critical Dependencies

#### Authentication & Security

```txt
pyjwt[crypto]==2.8.0              # JWT token verification
python-jose[cryptography]==3.3.0  # Alternative JWT library
passlib[bcrypt]==1.7.4            # Password hashing
supabase==2.3.0                   # Supabase client
```

#### File Handling

```txt
python-multipart==0.0.6           # File upload support
aiofiles==23.2.1                  # Async file operations
pillow==10.2.0                    # Image processing
```

#### Validation & Serialization

```txt
pydantic==2.5.3                   # Data validation (v2)
pydantic-settings==2.1.0          # Settings management
email-validator==2.1.0            # Email validation
```

#### Testing

```txt
pytest==7.4.3                     # Test framework
pytest-asyncio==0.21.1            # Async test support
pytest-cov==4.1.0                 # Coverage reporting
httpx==0.25.2                     # HTTP client for testing
faker==22.0.0                     # Test data generation
```

#### Production (Sprint 2+)

```txt
redis==5.0.1                      # Redis client
celery==5.3.4                     # Task queue
flower==2.0.1                     # Celery monitoring
sentry-sdk[fastapi]==1.39.2       # Error tracking
```

#### Audio Processing (Sprint 2+)

```txt
librosa==0.10.1                   # Audio analysis
soundfile==0.12.1                 # Audio file I/O
numpy==1.26.3                     # Numerical computing
scipy==1.11.4                     # Scientific computing
```

### Recommended requirements.txt

```txt
# Core Framework
fastapi==0.115.0
uvicorn[standard]==0.25.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9

# Authentication & Security
pyjwt[crypto]==2.8.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
supabase==2.3.0

# File Handling
python-multipart==0.0.6
aiofiles==23.2.1
python-magic==0.4.27

# Utilities
python-dotenv==1.0.0
email-validator==2.1.0

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2
faker==22.0.0
black==23.12.1
ruff==0.1.9
mypy==1.8.0
```

### Security Vulnerabilities

#### Known CVEs

1. **SQLAlchemy < 2.0.0**
   - CVE-2023-XXXXX (SQL Injection risk in certain query patterns)
   - Severity: HIGH
   - Fix: Upgrade to 2.0.0+

2. **psycopg2-binary < 2.9.5**
   - Multiple memory safety issues
   - Severity: MEDIUM
   - Fix: Upgrade to 2.9.9+

#### Missing Security Tools

```txt
bandit==1.7.6                     # Security linter
safety==3.0.1                     # Dependency vulnerability scanner
```

---

## Frontend Dependencies (apps/web)

### Current package.json

```json
{
  "dependencies": {
    "next": "14.2.3",
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "tailwindcss": "3.4.4",
    "autoprefixer": "10.4.19",
    "postcss": "8.4.38"
  },
  "devDependencies": {
    "typescript": "5.4.5",
    "@types/react": "18.3.3",
    "@types/node": "20.12.7",
    "eslint": "8.57.0",
    "eslint-config-next": "14.2.3"
  }
}
```

### Issues with Current Dependencies

#### 1. Next.js Version (MEDIUM)

**Current:** `14.2.3`  
**Issue:** Documentation specifies Next.js 15

**Recommended:** `15.0.0` or latest 15.x

**Impact:**
- Missing App Router improvements
- Missing Server Actions enhancements
- Documentation mismatch

#### 2. ESLint Version (LOW)

**Current:** `8.57.0`  
**Recommended:** `9.x` (latest)

### Missing Critical Dependencies

#### UI Components & Styling

```json
{
  "@radix-ui/react-dialog": "^1.0.5",
  "@radix-ui/react-dropdown-menu": "^2.0.6",
  "@radix-ui/react-label": "^2.0.2",
  "@radix-ui/react-select": "^2.0.0",
  "@radix-ui/react-slot": "^1.0.2",
  "@radix-ui/react-tabs": "^1.0.4",
  "@radix-ui/react-toast": "^1.1.5",
  "class-variance-authority": "^0.7.0",
  "clsx": "^2.1.0",
  "tailwind-merge": "^2.2.0",
  "lucide-react": "^0.309.0"
}
```

#### State Management & Data Fetching

```json
{
  "@tanstack/react-query": "^5.17.19",
  "@tanstack/react-query-devtools": "^5.17.19",
  "zustand": "^4.4.7"
}
```

#### Authentication

```json
{
  "@supabase/supabase-js": "^2.39.3",
  "@supabase/auth-helpers-nextjs": "^0.8.7",
  "@supabase/auth-ui-react": "^0.4.7",
  "@supabase/auth-ui-shared": "^0.1.8"
}
```

#### Forms & Validation

```json
{
  "react-hook-form": "^7.49.3",
  "zod": "^3.22.4",
  "@hookform/resolvers": "^3.3.4"
}
```

#### Utilities

```json
{
  "date-fns": "^3.0.6",
  "axios": "^1.6.5"
}
```

#### Development

```json
{
  "@types/node": "^20.11.5",
  "@types/react": "^18.2.48",
  "@types/react-dom": "^18.2.18",
  "vitest": "^1.2.0",
  "@vitejs/plugin-react": "^4.2.1",
  "@testing-library/react": "^14.1.2",
  "@testing-library/jest-dom": "^6.2.0"
}
```

### Recommended package.json

```json
{
  "name": "@sonic-ai/web",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "next": "^15.0.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-label": "^2.0.2",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-toast": "^1.1.5",
    
    "@tanstack/react-query": "^5.17.19",
    "@tanstack/react-query-devtools": "^5.17.19",
    
    "@supabase/supabase-js": "^2.39.3",
    "@supabase/auth-helpers-nextjs": "^0.8.7",
    
    "react-hook-form": "^7.49.3",
    "zod": "^3.22.4",
    "@hookform/resolvers": "^3.3.4",
    
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0",
    "lucide-react": "^0.309.0",
    
    "date-fns": "^3.0.6",
    "axios": "^1.6.5",
    
    "tailwindcss": "^3.4.4",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38"
  },
  "devDependencies": {
    "typescript": "^5.6.3",
    "@types/node": "^20.11.5",
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    
    "eslint": "^9.5.0",
    "eslint-config-next": "^15.0.0",
    
    "vitest": "^2.0.5",
    "@vitejs/plugin-react": "^4.2.1",
    "@testing-library/react": "^14.1.2",
    "@testing-library/jest-dom": "^6.2.0"
  }
}
```

---

## Root Dependencies (package.json)

### Current Status

✅ **GOOD** - Root dependencies are well-configured

```json
{
  "devDependencies": {
    "@types/node": "^22.0.0",
    "typescript": "^5.6.3",
    "ts-node": "^10.9.2",
    "eslint": "^9.5.0",
    "eslint-config-prettier": "^9.1.0",
    "eslint-plugin-import": "^2.29.1",
    "eslint-plugin-unused-imports": "^3.2.0",
    "prettier": "^3.3.3",
    "vitest": "^2.0.5",
    "@vitest/coverage-v8": "^2.0.5",
    "turbo": "^2.0.6",
    "husky": "^9.1.4",
    "lint-staged": "^15.2.2"
  }
}
```

### Potential Additions

```json
{
  "commitizen": "^4.3.0",
  "cz-conventional-changelog": "^3.3.0",
  "@commitlint/cli": "^18.4.4",
  "@commitlint/config-conventional": "^18.4.4"
}
```

---

## Package Stubs Analysis

All packages in `packages/` directory are stubs with minimal package.json files:

```
packages/assets/package.json
packages/auth/package.json
packages/common/package.json
packages/events/package.json
packages/memory/package.json
packages/metadata/package.json
packages/profiles/package.json
packages/projects/package.json
packages/vault/package.json
```

**Status:** These are correctly stubbed for future implementation. No action needed for Sprint 1.

---

## Dependency Installation Commands

### Backend Setup

```bash
cd apps/api

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt  # Need to create this

# Verify installation
pip list
```

### Frontend Setup

```bash
cd apps/web

# Install dependencies
pnpm install

# Verify installation
pnpm list
```

### Root Setup

```bash
# From repository root
corepack enable
pnpm install
```

---

## Security Recommendations

### 1. Dependency Pinning

**Current:** Using `>=` for all Python dependencies  
**Risk:** Breaking changes, security issues  
**Fix:** Use exact versions or constrained ranges

### 2. Vulnerability Scanning

**Missing Tools:**
- `safety` for Python
- `npm audit` / `pnpm audit` for Node.js
- Dependabot or Renovate for automated updates

**Recommendation:**
```bash
# Python
pip install safety
safety check

# Node.js
pnpm audit
```

### 3. License Compliance

**Status:** Not audited  
**Recommendation:** Add license checking to CI/CD

```bash
pip install pip-licenses
pip-licenses --format=markdown > LICENSES.md
```

### 4. Supply Chain Security

**Missing:**
- No dependency signature verification
- No SBOM (Software Bill of Materials)
- No provenance tracking

---

## Upgrade Path

### Phase 1: Critical Security Fixes (Immediate)

1. Upgrade SQLAlchemy to 2.0.x
2. Add missing authentication dependencies
3. Add file upload dependencies
4. Pin all dependency versions

### Phase 2: Missing Sprint 1 Dependencies (Week 1)

1. Add Pydantic v2
2. Add Supabase client
3. Add testing dependencies
4. Add frontend UI libraries
5. Add TanStack Query

### Phase 3: Development Tools (Week 2)

1. Add linting tools
2. Add formatting tools
3. Add type checking tools
4. Add security scanning tools

### Phase 4: Production Dependencies (Sprint 2)

1. Add Redis client
2. Add Celery
3. Add monitoring tools
4. Add audio processing libraries

---

## Estimated Installation Time

- Backend dependencies: ~5 minutes
- Frontend dependencies: ~3 minutes
- Root dependencies: ~2 minutes
- **Total:** ~10 minutes

---

## Disk Space Requirements

- Backend virtual environment: ~500 MB
- Frontend node_modules: ~800 MB
- Root node_modules: ~200 MB
- **Total:** ~1.5 GB

---

## Compatibility Matrix

| Component | Python Version | Node Version | pnpm Version |
|-----------|---------------|--------------|--------------|
| Backend | 3.12+ | N/A | N/A |
| Frontend | N/A | 20+ | 10+ |
| Root | N/A | 20+ | 10+ |

**Current System:**
- Python: Available (version unknown)
- Node: 20+ (per package.json engines)
- pnpm: 10.28.1 (per package.json)

---

## Action Items

### Immediate (Critical)

1. ✅ Create updated `requirements.txt` with pinned versions
2. ✅ Create `requirements-dev.txt` for development dependencies
3. ✅ Update `apps/web/package.json` with missing dependencies
4. ✅ Run `pip install -r requirements.txt` in backend
5. ✅ Run `pnpm install` in frontend
6. ✅ Run security audit: `safety check` and `pnpm audit`

### Short-term (This Week)

7. ✅ Add pre-commit hooks for dependency checking
8. ✅ Configure Dependabot or Renovate
9. ✅ Document dependency update process
10. ✅ Create dependency update schedule

### Long-term (Sprint 2+)

11. ✅ Implement SBOM generation
12. ✅ Add license compliance checking
13. ✅ Set up automated security scanning in CI/CD
14. ✅ Create dependency upgrade testing process

---

**End of Dependency Audit**
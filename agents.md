# Claude Code Instructions - Neighborhood Insights IL

## Project Overview
**Neighborhood Insights IL** is a mobile-first webapp for exploring Israeli neighborhoods based on quality of life factors including education, crime, services, prices, and commute times. Built with FastAPI backend, PostgreSQL/PostGIS database, and Next.js frontend.

## Architecture & Tech Stack

### Backend
- **API**: FastAPI with async support
- **Database**: PostgreSQL with PostGIS extensions  
- **Cache**: Redis for routing and query caching
- **ETL**: Python with GeoPandas/Shapely for spatial data processing
- **Routing**: Multi-stage funnel (crow-flight → OSRM → Google Routes)
- **Testing**: pytest with coverage >90%

### Frontend
- **Framework**: Next.js 14 with React
- **Maps**: Mapbox GL with vector tiles
- **UI**: Mobile-first PWA with RTL support (Hebrew/Arabic)
- **Styling**: Tailwind CSS with RTL classes
- **Testing**: Jest + React Testing Library + Playwright E2E

### Data Sources
- CBS Statistical Areas (boundaries + demographics)
- Ministry of Education (school locations + performance)
- Israel Police (crime statistics)
- Ministry of Health (healthcare facilities)
- OpenStreetMap (POI data)
- GTFS Israel (public transit)
- Tax Authority (real estate transactions)

## Development Conventions

### Code Style & Formatting

#### Python (api/, etl/, tests/)
- **Formatter**: Black with 88 character line length
- **Import sorting**: isort with black profile
- **Linting**: flake8 with E203,W503 ignored
- **Type checking**: mypy with ignore-missing-imports
- **Security**: bandit for security scanning

#### JavaScript/TypeScript (app/)
- **Formatter**: Prettier
- **Linting**: ESLint with Next.js config
- **Files**: .js, .jsx, .ts, .tsx, .json, .css, .md, .yml, .yaml

#### SQL (db/)
- **Formatter**: SQLFluff with PostgreSQL dialect
- **Template**: dbt-postgres compatible

### Modularity & File Design
- Code must be **modular**: prefer small files with focused responsibilities.
- Functions and classes should be **small, cohesive, and single-purpose**.
- Break down large modules into composable parts for readability and maintainability.

### File Structure

/
├── api/                    # FastAPI backend
│   ├── main.py            # FastAPI app entry point
│   ├── pyproject.toml     # Poetry dependencies
│   └── tests/             # API unit/integration tests
├── etl/                   # Data processing pipeline
│   ├── init.py
│   ├── pyproject.toml     # ETL dependencies
│   └── tests/             # ETL tests
├── app/                   # Next.js frontend
│   ├── package.json       # Node.js dependencies
│   └── …                # Next.js structure
├── db/                    # Database schema/migrations
├── data/                  # Raw data and scraping
├── tests/                 # Integration/system tests
├── .pre-commit-config.yaml
├── README.md              # Project overview
├── eng_plan.md            # 45-day development plan
└── CLAUDE.md              # This file

### Database Schema Design
*(unchanged content, omitted for brevity)*

### API Design Patterns
*(unchanged content, omitted for brevity)*

### Testing Strategy

#### Python Testing (pytest)
- **Unit tests**: Individual functions and classes
- **Integration tests**: Database operations and API endpoints
- **Performance tests**: Marked with `@pytest.mark.performance`
- **Coverage**: Aim for >90% coverage, exclude test files
- **Always run tests after every edit** before committing or merging.

#### Testing Philosophy
- Prefer **real APIs and real data flows** in tests whenever feasible.  
- Avoid mocks except when strictly necessary for performance or isolation.  
- Strive for tests that validate actual user-facing behavior and integrations.  

#### Configuration
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "integration: integration tests requiring database",
    "performance: performance benchmarks",
]

Test Organization
	•	tests/test_services.py: System service health checks
	•	tests/test_integration.py: End-to-end integration tests
	•	api/tests/: API-specific unit tests
	•	etl/tests/: ETL pipeline tests

Docker & Development Environment

(unchanged content, omitted for brevity)

Performance Requirements

(unchanged content, omitted for brevity)

Security & Privacy

(unchanged content, omitted for brevity)

Scoring Algorithm

(unchanged content, omitted for brevity)

Multi-Stage Routing Funnel

(unchanged content, omitted for brevity)

Frontend Development

(unchanged content, omitted for brevity)

Error Handling & Monitoring

(unchanged content, omitted for brevity)

Development Workflow

Pre-commit Hooks (Automatic)
	1.	Black formatting (Python)
	2.	isort import sorting (Python)
	3.	flake8 linting (Python)
	4.	mypy type checking (Python)
	5.	Prettier formatting (JS/TS)
	6.	ESLint linting (JS/TS)
	7.	SQLFluff formatting (SQL)
	8.	Bandit security scanning
	9.	Pytest unit tests (full suite runs automatically after edits)
	10.	No secrets in code check

Git Workflow
	•	Main branch: main
	•	Feature branches: feature/description
	•	No direct commits to main
	•	All changes through pull requests
	•	Pre-commit hooks must pass

Common Development Tasks

(unchanged content, omitted for brevity)

Cost Control Measures

(unchanged content, omitted for brevity)

Localization Requirements

(unchanged content, omitted for brevity)

Quality Assurance

(unchanged content, omitted for brevity)

Daily Development Checklist

Before Starting Work
	•	Pull latest changes from main branch
	•	Verify all services running (make up)
	•	Run test suite to ensure clean state
	•	Check pre-commit hooks are installed

During Development
	•	Follow established coding conventions
	•	Keep code modular and files small
	•	Write tests for new functionality (favor real APIs over mocks)
	•	Run the full test suite after each edit
	•	Use proper error handling and logging
	•	Optimize database queries with EXPLAIN ANALYZE
	•	Test on mobile devices regularly

Before Committing
	•	Run full test suite locally
	•	Verify pre-commit hooks pass
	•	Test API endpoints manually
	•	Check for performance regressions
	•	Validate mobile experience

Code Review Checklist
	•	Code follows project conventions
	•	Code is modular with small files and small functions/classes
	•	Tests cover new functionality and run after each edit
	•	Tests prefer real APIs over mocks
	•	Database queries are optimized
	•	Error handling is comprehensive
	•	Mobile UX is maintained
	•	Security best practices followed

Emergency Procedures

(unchanged content, omitted for brevity)

⸻

Remember: This is a mobile-first, performance-critical application serving real estate decisions in Israel. Every line of code should prioritize user experience, data accuracy, system reliability, modular design, and verified correctness through real tests.
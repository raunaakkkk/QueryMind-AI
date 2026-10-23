# NLP-Based Natural Language Interface for Database Querying

## Overview
This project is a local FastAPI application that lets users ask natural-language questions about a college database and receive a safe SQL query, result set, and explanation. It uses SQLite for data storage, a rule-based NLP layer, and a simple frontend built with HTML, CSS, and vanilla JavaScript.

## Problem statement
Database interaction often requires users to know SQL syntax and schema details. This application reduces that barrier by translating natural-language queries into safe SQL against a relational college dataset.

## Objectives and key features
- Natural-language question parsing for common academic queries
- Safe read-only SQL validation and rejection of destructive statements
- SQLite-backed college data model with seeded sample data
- FastAPI endpoints for querying, schema inspection, and analytics
- Responsive HTML/CSS/JS frontend
- Automated pytest coverage for NLP, SQL, database, API, and security scenarios
- Evaluation dataset and script for representative query testing

## Technology stack
- Python 3.11+
- FastAPI
- SQLite
- SQLAlchemy-free direct SQLite access
- spaCy (with graceful fallback)
- Pydantic
- Pandas
- HTML5/CSS3/JavaScript
- pytest
- Ruff
- Uvicorn

## System architecture and workflow
1. A user enters a natural-language question in the browser.
2. The NLP layer normalizes text, detects intent, extracts entities, and resolves schema-aware terms.
3. The SQL builder constructs a safe SELECT query with parameter placeholders.
4. The validator checks the SQL before execution.
5. The database executes the query in read-only mode.
6. The API returns results, SQL preview, and an explanation.
7. The frontend renders the query output and summary charts.

## Database schema and relationships
The application uses five related tables:

- departments: department_id, department_name
- students: student_id, name, age, gender, department_id, year, email
- courses: course_id, course_name, credits, department_id
- enrollments: enrollment_id, student_id, course_id, semester
- marks: mark_id, student_id, course_id, marks, grade

Relationships are enforced using foreign keys and the schema is initialized automatically with reproducible seed data.

## Project directory structure
```text
NLP-Database-Interaction/
├── app/
│   ├── api/
│   ├── database/
│   ├── nlp/
│   ├── services/
│   ├── sql/
│   ├── static/
│   ├── __init__.py
│   ├── config.py
│   └── main.py
├── data/
│   └── evaluation_queries.csv
├── docs/
│   └── architecture.md
├── scripts/
│   ├── initialize_db.py
│   └── run_evaluation.py
├── tests/
├── .env.example
├── .gitignore
├── pyproject.toml
├── README.md
├── requirements.txt
└── data/college.db (generated after initialization)
```

## Prerequisites
- Python 3.11 or newer
- PowerShell 5.1 or PowerShell 7+
- Local machine with internet access for package installation

## Windows PowerShell setup
```powershell
cd d:\QueryMind
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Database initialization and seeding
```powershell
python scripts\initialize_db.py
```
This creates the database at `data\college.db` and seeds it with fictional but consistent academic records.

## Running the application
```powershell
python -m app.main
```
Then open:
- http://127.0.0.1:8000/
- http://127.0.0.1:8000/docs

## Example natural-language queries
- Show all students in the Computer Science department.
- How many students are enrolled in each department?
- Find students with marks greater than 80.
- What is the average mark for each course?
- List the top 10 students based on marks.
- Which department has the highest number of students?
- Show students enrolled in the database systems course.
- Count the total number of courses.
- Find students whose marks are below 40.
- Display the number of students in each academic year.

## API endpoints
- GET /
- GET /api/health
- POST /api/query
- GET /api/schema
- GET /api/analytics/summary
- GET /api/analytics/department-distribution
- GET /api/analytics/average-marks
- GET /api/tables/{table_name}

## Running automated tests
```powershell
pytest -q
```

## Running the evaluation script
```powershell
python scripts\run_evaluation.py
```

## SQL safety and limitations
- Only SELECT queries are allowed.
- Destructive statements are rejected before execution.
- Multiple statements are blocked.
- Parameterized values are used for user-provided conditions.
- The NLP layer is intentionally deterministic and rule-based; it supports a defined subset of queries.
- Unsupported questions return a helpful error message with examples.

## Troubleshooting common setup issues
- If `ModuleNotFoundError` occurs, ensure the virtual environment is activated and dependencies are installed.
- If `sqlite3` or related errors appear, rerun the database initialization script.
- If spaCy is unavailable, the application falls back to regex-based parsing without crashing.
- If the page does not load, confirm the server is running in the terminal and the port is not already in use.

## Final notes
This project is designed for local development and demonstration. It deliberately avoids online dependencies and cloud services for Routine use.

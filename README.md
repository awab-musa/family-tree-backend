# Family Tree — Backend

A serverless-style REST API for a family tree web application, built with **FastAPI** and **PostgreSQL**, deployed on **AWS** (EC2 + RDS + S3 + CloudFront). The API supports genuinely complex family relationships — remarriage, adoption, multiple parent-sets per person — using PostgreSQL recursive CTEs, with JWT authentication and role-based access control (Viewer / Admin).

**🔗 Live demo:** [https://d3moyfpvj6r1i2.cloudfront.net/]

---

## Screenshots

<p align="center">
  <img src="docs/screenshots/login.png" width="420" alt="Login page" />
  <img src="docs/screenshots/register.png" width="420" alt="Register page" />
</p>
<p align="center">
  <img src="docs/screenshots/tree-empty.png" width="700" alt="Family tree view" />
</p>

---

## Architecture

The full infrastructure design, the reasoning behind each decision, and reproducible deployment steps are documented in [`ARCHITECTURE.md`](./ARCHITECTURE.md).

Architecture diagram (editable directly at [app.diagrams.net](https://app.diagrams.net)): [`family-tree-architecture.drawio`](./family-tree-architecture.drawio)

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python), SQLAlchemy (async), Alembic |
| Database | PostgreSQL on Amazon RDS |
| Auth | JWT (access/refresh tokens) + Role-Based Access Control |
| Storage | Amazon S3 (presigned URLs for photos/documents) |
| Infrastructure | Amazon EC2 · Nginx (reverse proxy) · Gunicorn/Uvicorn · systemd |
| Frontend (separate repo) | React + TypeScript + Vite, hosted on S3 + CloudFront |

## What I Learned Building This

- Deploying a real backend to a Linux server (EC2) with production-grade tooling (systemd, Nginx) instead of just running it locally
- Designing network isolation between services with AWS Security Groups (the database is fully isolated from the internet, reachable only by the backend)
- Modeling real family relationships (not a simple hierarchy) using an explicit relationship-edge table and PostgreSQL recursive CTEs
- Diagnosing and fixing real production issues: library version incompatibilities (`asyncpg`, `bcrypt`), CORS/CloudFront caching behavior, and keeping request/response schemas consistent between the API and the database

## Project Structure

```
app/
├── core/         # settings, JWT, RBAC
├── db/           # database connection
├── models/       # SQLAlchemy tables
├── schemas/      # Pydantic request/response models
├── api/v1/       # routes (auth, persons, relationships, tree, media)
└── services/     # business logic (tree_service holds the recursive CTE queries)
alembic/          # database migrations
```

## Running Locally

```bash
python -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt

cp .env.example .env   # set DATABASE_URL and JWT_SECRET_KEY

alembic upgrade head
uvicorn app.main:app --reload
```

Interactive API docs (Swagger) are available at `http://localhost:8000/docs`.

## License

MIT

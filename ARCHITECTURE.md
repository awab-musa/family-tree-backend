# Family Tree Web App — Architecture Documentation

**Author:** Awab Musa
**Status:** Deployed (AWS Free Tier)
**Last updated:** September 2026

---

## 1. Overview

Family Tree is a full-stack web application that lets users build, browse,
and manage an interactive family tree — recording people, their
relationships (parent/child, spouse, biological/adoptive/step), and media
(photos, documents) attached to each person.

This document describes the system architecture as actually deployed,
the reasoning behind each infrastructure decision, and the security
boundaries in place.

A visual diagram (`family-tree-architecture.drawio`) accompanies this
document — open it at [app.diagrams.net](https://app.diagrams.net) via
**File → Open From → Device**.

---

## 2. Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React + TypeScript + Vite | Static build, no server-side rendering |
| Visualization | react-d3-tree / D3.js | Renders the nested family tree graph |
| Backend | FastAPI (Python) | REST API, JWT auth, RBAC |
| Process manager | Gunicorn + Uvicorn workers | Runs the ASGI app as a managed process |
| Reverse proxy | Nginx | Terminates HTTP on :80, forwards to Gunicorn on localhost |
| Database | PostgreSQL (Amazon RDS) | Recursive CTEs for ancestor/descendant tree traversal |
| Object storage | Amazon S3 | Static frontend hosting + user-uploaded media |
| CDN | Amazon CloudFront | HTTPS + caching in front of the S3 frontend bucket, and routes /api/* to EC2 |
| Auth | JWT (access + refresh tokens) | Stateless, RBAC roles: `viewer` / `admin` |
| Compute (backend) | Amazon EC2 (t2.micro) | Ubuntu 22.04 LTS, systemd-managed service |
| Process supervision | systemd | Keeps the FastAPI app running, restarts on crash/reboot |

---

## 3. High-Level Architecture

See `family-tree-architecture.drawio` for the full diagram. Summary of the
request flows:

**Static asset delivery (frontend):**
```
Browser → CloudFront (HTTPS, cached) → S3 (family-tree-frontend bucket)
```

**API requests:**
```
Browser → CloudFront (/api/* behavior) → EC2 Public IP:80 (Nginx)
        → 127.0.0.1:8000 (Gunicorn/Uvicorn) → FastAPI app → PostgreSQL (RDS, port 5432)
```

**Media upload/download (photos, documents):**
```
Browser → FastAPI (requests a presigned URL) → S3 (family-tree-media bucket)
Browser → S3 directly (uploads/downloads the file using that presigned URL)
```
The backend never proxies file bytes — it only issues short-lived signed
URLs, keeping EC2 bandwidth and CPU free of large file transfers.

---

## 4. Why This Architecture

### 4.1 EC2 instead of Lambda for the backend

The original design considered AWS Lambda + API Gateway (fully serverless).
For this project, EC2 was chosen instead because:
- Simpler connection handling with a stateful async DB connection pool
  (no cold-start/connection-per-invocation complexity)
- Easier to debug and reason about while learning cloud deployment
  end-to-end (SSH access, logs, systemd status)
- Still fits AWS Free Tier (`t2.micro`, 750 hours/month)

**Trade-off accepted:** the server runs continuously rather than
scaling to zero, and patching/monitoring is a manual responsibility
rather than being abstracted away by Lambda.

### 4.2 RDS with `Public access: No`

The database is **not** reachable from the public internet. It only
accepts connections from resources inside the same security group
boundary as the EC2 instance (see Security section below). This follows
the principle of least exposure — a compromised frontend or leaked
connection string alone isn't enough to reach the database, an attacker
would also need network-level access to the VPC.

### 4.3 Presigned S3 URLs instead of proxying uploads

Routing file uploads through the FastAPI app would tie up a Gunicorn
worker for the duration of each upload/download, which doesn't scale
well on a single `t2.micro` instance. Presigned URLs let the browser
talk to S3 directly, with the backend only responsible for
authorization (deciding *whether* a given user may upload/download a
given object) and generating a time-limited signed link.

### 4.4 Nginx in front of Gunicorn

Gunicorn/Uvicorn is bound to `127.0.0.1:8000` (localhost only — not
exposed externally). Nginx listens on the public port 80 and reverse-proxies
to it. This is the standard pattern for running Python ASGI apps on a VM:
Nginx handles connection buffering, can serve TLS termination once a
domain + certificate are added, and isolates the application server from
direct internet exposure.

### 4.5 CloudFront in front of the API

CloudFront routes `/api/*` requests to the EC2 origin alongside serving
the static frontend from S3, so the whole app (frontend + API) shares a
single HTTPS domain — avoiding mixed-content and CORS complexity that
would come from serving the API on a bare HTTP IP address.

---

## 5. Network & Security Configuration

### 5.1 VPC

The **Default VPC** (created automatically by AWS in every account/region)
is used — no custom VPC or subnets were provisioned. For a single-instance,
single-database project, the default VPC's subnets are sufficient; a
custom VPC would add complexity without a corresponding benefit at this
scale.

### 5.2 Security Groups

Two security groups enforce network-level access control:

**`ec2-sg`** (attached to the EC2 instance):
| Port | Source | Purpose |
|---|---|---|
| 22 (SSH) | My IP only | Admin access for deployment/maintenance |
| 80 (HTTP) | Anywhere (0.0.0.0/0) | Public API access via Nginx |

**`rds-sg`** (attached to the RDS instance):
| Port | Source | Purpose |
|---|---|---|
| 5432 (PostgreSQL) | `ec2-sg` (by security group reference, not IP) | Only the EC2 instance can reach the database |

Referencing `ec2-sg` as the *source* of the RDS rule (rather than a
specific IP) means the rule keeps working even if the EC2 instance's
public IP changes on reboot — the database trusts *anything running with
that security group attached*, not a specific address.

### 5.3 Secrets Management

Sensitive values (`DATABASE_URL`, `JWT_SECRET_KEY`, S3 bucket name) are
kept in a `.env` file on the EC2 instance, excluded from version control
via `.gitignore`, and loaded at runtime via `pydantic-settings`. They are
never committed to the repository or hardcoded in source.

---

## 6. Data Model Notes

Family relationships are stored as explicit **edges** in a `relationships`
table (rather than a single `parent_id` column on `persons`), because real
family trees include remarriage, adoption, and multiple parent-sets —
patterns a simple hierarchical column can't represent. Each edge has a
`relationship_type` (`parent_child` / `spouse`) and, where applicable, a
subtype (`biological` / `adoptive` / `step` / `foster`).

Ancestor and descendant queries use **PostgreSQL recursive CTEs**, with a
`visited` array carried through each recursive step to guard against
cycles in the underlying graph (e.g. through cousin marriages).

---

## 7. Deployment Process (Reproducible Steps)

1. **RDS**: Create a `db.t3.micro` PostgreSQL instance, Free Tier, 20 GB
   storage, `Public access: No`, in the Default VPC, with a new `rds-sg`
   security group.
2. **EC2**: Launch a `t2.micro` Ubuntu 22.04 instance in the same Default
   VPC, with a new `ec2-sg` security group (22 restricted to admin IP,
   80 open).
3. **Security group linking**: Add an inbound rule to `rds-sg` allowing
   port 5432 from `ec2-sg` (by group reference).
4. **Server setup**: SSH in, install `python3-venv`, `nginx`, `git`;
   clone the backend repo; create a virtual environment; install
   dependencies from `requirements.txt`.
5. **Configuration**: Create `.env` with the RDS connection string, JWT
   secret, and S3 bucket name; run `alembic upgrade head` to apply
   database migrations.
6. **Process management**: Create a `systemd` unit file running
   Gunicorn with Uvicorn workers, bound to `127.0.0.1:8000`; enable and
   start it so it survives reboots.
7. **Reverse proxy**: Configure Nginx to listen on port 80 and
   `proxy_pass` to `127.0.0.1:8000`.
8. **Frontend**: Build the React app (`npm run build`) with
   `VITE_API_BASE_URL` pointed at the CloudFront domain (`/api/v1`);
   upload the build output to an S3 bucket with static website hosting
   enabled; put a CloudFront distribution in front of it with a
   `/api/*` behavior routed to the EC2 origin.

---

## 8. Known Limitations & Future Improvements

This is a first project built to learn end-to-end cloud deployment.
Documented honestly, the current setup has known gaps that would be
addressed before this became a production system:

- **Single EC2 instance, no auto-scaling or failover** — acceptable for
  a learning project and Free Tier constraints; a production system
  would use an Auto Scaling Group across multiple Availability Zones,
  or migrate back to the originally-considered Lambda + API Gateway
  design for automatic scaling.
- **No CI/CD pipeline yet** — deployments are currently manual (`git
  pull` + restart the systemd service on the instance). A GitHub
  Actions workflow to run tests and redeploy on merge to `main` is a
  planned next step.
- **No automated database backups configured** — RDS supports automated
  snapshots; this should be enabled before any real user data is stored.
- **No monitoring/alerting** — CloudWatch alarms for CPU/memory/disk on
  the EC2 instance and RDS would catch issues before users do.
- **Every user's family tree is scoped to their own account** (`tree_id
  = user.id`) rather than supporting shared/collaborative trees — a
  deliberate simplification for v1, with multi-collaborator trees as a
  natural next feature.

---

## 9. Repository Links

- Backend: `family-tree-backend` (FastAPI, PostgreSQL, JWT auth)
- Frontend: `family-tree--fronend` (React, TypeScript, Vite)

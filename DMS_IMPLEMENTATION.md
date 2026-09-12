# SENTINEL Document Management System

This implementation adds a private document vault to the existing FastAPI + Next.js application.

## Architecture

```text
Next.js /documents dashboard
        |
        | multipart upload, search, download, delete
        v
FastAPI /api/v1/documents
        |
        +-- PostgreSQL: ownership, metadata, categories, tags, OCR index text
        +-- AES-256-GCM local storage: encrypted file bytes only
        +-- OCR worker boundary: pypdf for PDFs, Tesseract for images
```

The database never stores the raw blob. `documents.storage_key` points to an encrypted file under `DMS_STORAGE_PATH`. Every document query is scoped to the authenticated user's `owner_id`. Biometric records should be uploaded as encrypted files or irreversible templates; do not put raw biometric samples in PostgreSQL or OCR text.

## PostgreSQL schema

The SQLAlchemy models in `backend/app/models/document.py` create this schema. The equivalent PostgreSQL DDL is:

```sql
CREATE TABLE categories (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name varchar(80) NOT NULL,
  description varchar(240),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (owner_id, name)
);

CREATE TABLE tags (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name varchar(60) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (owner_id, name)
);

CREATE TABLE documents (
  id uuid PRIMARY KEY,
  owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  category_id uuid REFERENCES categories(id) ON DELETE SET NULL,
  title varchar(240) NOT NULL,
  original_filename varchar(255) NOT NULL,
  storage_key varchar(500) NOT NULL UNIQUE,
  mime_type varchar(100) NOT NULL,
  size_bytes integer NOT NULL CHECK (size_bytes > 0),
  sha256 varchar(64) NOT NULL,
  extracted_text text,
  is_sensitive boolean NOT NULL DEFAULT true,
  uploaded_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE document_tags (
  document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  tag_id uuid NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (document_id, tag_id)
);

CREATE INDEX documents_owner_uploaded_idx ON documents(owner_id, uploaded_at DESC);
CREATE INDEX documents_search_idx ON documents USING gin (to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(extracted_text, '')));
```

For a large production corpus, replace the `ILIKE` query with the GIN index and PostgreSQL full-text search. Keep OCR text encrypted at rest through PostgreSQL disk encryption and restricted database roles.

## API contract

All routes live below `/api/v1/documents` and require the current user context.

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/categories` | List the user's categories |
| GET | `/?q=&category=` | Search title, filename, OCR text, and filter category |
| POST | `/` | Multipart upload: `file`, `title`, `category`, comma-separated `tags` |
| GET | `/{id}/download` | Decrypt and stream a user-owned file |
| DELETE | `/{id}` | Delete metadata and the encrypted blob |

Allowed types are PDF, JPEG, PNG, and CSV. The limit is 25 MB. The service calculates SHA-256 over the plaintext for integrity, encrypts with AES-256-GCM, stores a random nonce with the ciphertext, then runs best-effort text extraction.

## Local setup

1. Install backend dependencies: `pip install -r backend/requirements.txt`.
2. Generate a key once and store it in a secrets manager or `.env` outside source control:

   ```powershell
  $bytes = [byte[]]::new(32); [Security.Cryptography.RandomNumberGenerator]::Fill($bytes); [Convert]::ToBase64String($bytes)
   ```

   Use a cryptographically secure generator in real deployment, for example `openssl rand -base64 32`, then set `DMS_ENCRYPTION_KEY` and `DMS_STORAGE_PATH`.
3. Keep the storage directory outside the web root and deny direct static serving.
4. Install the Tesseract system binary and set its executable path if the host does not expose `tesseract` on `PATH`. PDF text extraction works through `pypdf` without Tesseract.
5. Start the API and frontend, sign in, then open `/documents`.

## Production hardening

- Replace the current demo authentication fallback with a real JWT dependency that validates the `Authorization: Bearer` header on every DMS route.
- Use PostgreSQL migrations rather than `Base.metadata.create_all` for deployment.
- Store `DMS_ENCRYPTION_KEY` in KMS/Vault and rotate it with a versioned key envelope; losing it makes blobs unrecoverable.
- Add malware scanning, rate limits, content sniffing, audit events for download/delete, and background OCR for large files.
- Configure restrictive CORS origins, HTTPS, secure cookies, CSP, and encrypted PostgreSQL backups.
- Add retention, export, and legal-hold policies before using the vault for regulated medical or biometric data.
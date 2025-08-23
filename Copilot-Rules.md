---
applyTo: "**"
---

# 🔧 Copilot Rules for This Project
<!-- Author: Utsav Pat -->

These rules must always be applied when Copilot generates or completes code.

---

## 1. General Coding Rules
- Use **Python 3.9+** as the default language unless explicitly stated otherwise.
- Always add **type hints** for function arguments and return types.
- Follow **PEP8** style guidelines.
- Write **docstrings in Google style** for every class and function.
- Ensure **error handling** with descriptive exceptions (no bare `except`).
- Prefer **async/await** for I/O and API calls when possible.
- Always use **structured logging** (`logging` with JSON formatter or `structlog`).
- Code must be **idempotent** (re-running shouldn’t cause duplicate DB entries or failures).

---

## 2. Azure Integration Rules
- Use **Azure SDKs** (`azure-identity`, `azure-storage-blob`, `azure-cosmos`) for all cloud operations.
- All file uploads to Blob Storage must:
  - Generate a **private SAS URL** (time-limited).
  - Never expose raw connection strings or keys in code.
- Use **environment variables** or Azure Key Vault for credentials and secrets.

---

## 3. Database Rules (Cosmos DB)
- Use **Azure Cosmos DB** (SQL API / Core API).
- All DB interactions must:
  - Use the **Azure Cosmos DB Python SDK** (`azure-cosmos`).
  - Ensure **partition keys** are properly set for scalability.
  - Use **parameterized queries** (no string concatenation).
  - Store metadata in structured JSON documents, not raw blobs.
- Cosmos DB Collections:
  - **Ingestion Master** → stores metadata (Email/File + Processing ID).
  - **Ingestion Detail** → stores attachments metadata.
  - **OCR Store** → extracted text with Processing ID + File URI.
  - **Doc Classifier Store** → classification results + tags.
  - **Submission Store** → final submission records, linked by SubmissionID.

---

## 4. API & Service Rules
- Use **FastAPI** for building REST APIs.
- Always include:
  - **Pydantic models** for request/response validation.
  - **CORS middleware**.
  - **OpenAPI docs** auto-generation enabled.
- APIs must:
  - Accept **JSON payloads**.
  - Return **standardized error responses** (`{ "error": "message" }`).
  - Include proper status codes (200, 201, 400, 404, 500).

---

## 5. File Handling Rules
- **Email Listener**:
  - Parse and store metadata (`From`, `To`, `CC`, `Subject`, `Date`, `Attachments`).
  - Store attachments in Blob Storage; log file URIs.
- **File Listener**:
  - Accept **PDF uploads**.
  - Store metadata (`Filename`, `File URI`, `DateTime`).
- Always return a **unique Processing ID**.

---

## 6. Testing Rules
- Use **pytest** as the default test framework.
- Use **mocks** for external services (Blob Storage, Cosmos DB, OCR APIs).
- Each module must include:
  - Unit tests
  - Integration tests (with mocks/fakes)
- Test naming convention: `test_<function_name>.py`

---

## 7. AI & OCR Rules
- **OCR Engine**:
  - Always store text along with **file URI + processing ID** in Cosmos DB.
- **AI Classifier**:
  - Map outputs to **predefined document types**.
  - Store classification + tags in Cosmos DB.
- **AI Extraction**:
  - Always align with **prompt structure** stored in Prompt Store.
  - Validate outputs before storing.

---

## 8. Security Rules
- No secrets or API keys hardcoded in the repo.
- Always sanitize inputs before DB or API use.
- Ensure **Blob URLs** are private and time-bound.
- Follow **principle of least privilege** in all services.

---

## 9. Documentation Rules
- Every module must start with a **high-level description** in comments.
- Every function must include:
  - Purpose
  - Parameters
  - Returns
  - Exceptions raised
- README updates required when new modules are added.

---

## 10. Output Rules
- Copilot should generate:
  - ✅ Production-ready, secure, testable code.
  - ✅ Code with comments & docstrings.
  - ✅ Tests for each core module.
- Copilot should **not** generate:
  - ❌ Placeholder code without implementations.
  - ❌ Hardcoded credentials.
  - ❌ Non-Python snippets unless explicitly prompted.

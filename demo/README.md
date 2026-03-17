# Demo Library

Each subfolder is a self-contained demo with documentation and execution artifacts.

| #   | Demo                                                                                 | Status      | Date       |
| --- | ------------------------------------------------------------------------------------ | ----------- | ---------- |
| 001 | [First User Journey](./001-first-user-journey/) — login → submit resource → see list | ✅ Executed | 2026-03-16 |
| 002 | [Account Management & Resource CRUD](./002-account-and-resource-crud/) — settings, detail, edit, delete | ✅ Executed | 2026-03-17 |

---

## How to add a new demo

1. Create a new numbered folder: `NNN-short-slug/`
2. Add `README.md` with: Summary, Prerequisites, Procedure, Expected Outcome, Actual Outcome, Next Steps
3. Add `artifacts/` subfolder for screenshots, curl output, logs
4. Execute the demo and populate `artifacts/`
5. Update this index table

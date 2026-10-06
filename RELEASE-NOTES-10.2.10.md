# JWorks 10.2.10 Cloud

- Replaces `hashlib.pbkdf2_hmac` with a Cloudflare Python Worker/Pyodide-compatible salted, iterated SHA-256 password KDF.
- Updates login verification to use the same versioned password-hash format.
- Removes the 12-character password minimum from both frontend first-run setup and backend validation.
- Passwords are still never stored in plaintext; a random per-password salt and derived hash are stored in D1.
- Keeps the 10.2.8 deterministic deployment pipeline and 10.2.7 root asset layout unchanged.
- No D1 migration is required.

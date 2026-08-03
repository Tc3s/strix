---
name: deep_taint_analysis
description: Source-to-Sink Taint Tracking for Server-side and Client-side Vulnerabilities
---

# Deep Taint Analysis Playbook

Use this skill to perform rigorous source-to-sink taint tracking to identify injection vulnerabilities and untrusted data flow.

## Taint Tracking Methodology

### 1. Ingress & Untrusted Sources
Identify all untrusted data entrypoints:
- HTTP request body, query parameters, path variables, headers, cookies.
- Webhook payloads, WebSocket messages, gRPC fields, message queue items.
- File uploads, environment variables, external API responses.

### 2. Taint Propagation & Sanitization Check
Follow the untrusted input through code execution:
- Track string concatenations, type casting, serialization/deserialization.
- Inspect sanitization, escaping, and validation routines.
- Verify if validation is bypassable, incomplete, or applied after dangerous calls.

### 3. Dangerous Sinks Review
Check if tainted input reaches any security-sensitive sinks:
- **Command Execution**: `exec()`, `system()`, `popen()`, `subprocess.run()`, `eval()`.
- **Database Queries**: Raw SQL queries, unescaped ORM parameters (SQLi, NoSQLi).
- **File & Path Access**: `open()`, `fs.readFile()`, path joins (Path Traversal, File Read/Write).
- **Network Calls**: `fetch()`, `requests.get()`, `http.Get()` (SSRF).
- **Client-side DOM**: `innerHTML`, `document.write()`, `dangerouslySetInnerHTML` (DOM-XSS).

## Verification Standard
Only report findings where the taint path from source to sink is continuous and un-sanitized. Output must include:
- `trigger_flow`: Step-by-step path from source to sink.
- `malicious_input_example`: Payload that triggers the sink.
- `exploitable: true`.

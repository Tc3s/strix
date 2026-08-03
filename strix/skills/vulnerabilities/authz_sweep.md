---
name: authz_sweep
description: Authorization & Broken Access Control Audit (IDOR, BPOA, Privilege Escalation)
---

# Authorization & Broken Access Control Audit Playbook

Use this skill to perform systematic authorization and access control audits across web applications, APIs, and microservices.

## 3-Phase Execution Strategy

### Phase 1: Map Roles and Protected Resources
1. Identify all user roles, privilege levels, and authentication contexts (e.g. `unauthenticated`, `user`, `admin`, `org_member`, `service_account`).
2. Identify all protected endpoints, handlers, controllers, and data mutations.
3. Construct an explicit **Role-to-Resource Access Matrix**.

### Phase 2: Audit Permission Enforcement
For every endpoint and handler, check:
- Is authorization checked before data access or mutation?
- Are object identifiers (e.g. `user_id`, `org_id`, `doc_id`) validated against the authenticated session rather than raw request input (IDOR / BPOA)?
- Can a lower-privileged role invoke endpoints intended for higher-privileged roles (Privilege Escalation)?
- Are multi-tenant boundaries strictly enforced across database queries?

### Phase 3: Confirm Exploitability & Report
For every identified access control flaw:
1. Provide an ordered `trigger_flow` array detailing the exact file:line hops from ingress to unauthorized access.
2. Provide a concrete `malicious_input_example` (e.g., HTTP request or curl command with manipulated IDs/headers).
3. Specify `malicious_actor` (role of attacker) and `exploitable: true`.

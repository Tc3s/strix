---
name: memory_safety_audit
description: Native Code Memory Safety and Lifetime Analysis (C/C++, FFI, Rust Unsafe)
---

# Native Memory Safety & Lifetime Analysis Playbook

Use this skill to audit C/C++ native codebases, C/C++ wrappers, Go Cgo bindings, and Rust `unsafe` blocks for memory corruption flaws.

## Audit Targets & Focus Areas

### 1. Pointer Arithmetic & Buffer Bounds
- Review `memcpy`, `strcpy`, `sprintf`, `read`, `recv` for un-checked buffer lengths.
- Inspect array and slice indexing for negative indexes or missing bounds checks.
- Audit off-by-one errors in loop boundaries and string terminations.

### 2. Allocation & Lifetime Management
- Track `malloc`/`free`, `new`/`delete`, and custom pool allocators.
- Search for Use-After-Free (UAF) vulnerabilities where pointers are dereferenced after deallocation.
- Search for Double Free vulnerabilities.
- Identify memory leaks that can cause remote Denial of Service (DoS).

### 3. Integer & Type Safety
- Check for Integer Overflow / Underflow in allocation size calculations (e.g. `count * size`).
- Audit unsafe type casts, pointer aliasing, and unaligned memory access.
- In Rust: Audit every `unsafe` block for memory safety invariant violations (dangling pointers, data races).

## Reporting Requirements
Each verified vulnerability must include:
- Exact file path and line number of the allocation/dereference/overflow.
- `trigger_flow`: Hops leading to memory corruption.
- `malicious_input_example`: Input or sequence triggering the crash/corruption.
- `exploitable: true`.

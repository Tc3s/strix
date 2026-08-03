---
name: cosmos_abci_audit
description: Cosmos ABCI & Blockchain Consensus Panic Halt Review (Go / Cosmos SDK / CometBFT)
---

# Cosmos ABCI & Blockchain Chain Halt Audit Playbook

Use this skill to audit Go codebases built on Cosmos SDK, CometBFT/Tendermint, or custom blockchain ABCI engines for maliciously triggerable panic paths that halt the blockchain consensus.

## Scope & Target ABCI Phases

Map all production-reachable ABCI methods:
- `BeginBlock` / `BeginBlocker`, `EndBlock` / `EndBlocker`, `PreBlocker`
- `InitChain`, `CheckTx`, `DeliverTx`, `FinalizeBlock`, `PrepareProposal`, `ProcessProposal`
- `ExtendVote`, `VerifyVoteExtension`, `Commit`, `Query`

## Vulnerability Patterns to Investigate

### 1. Explicit Panic & Must-Helpers
- Direct `panic()` calls, `sdk.Must*` helpers, and `require`/`assert` checks in consensus execution paths.
- Unhandled error panics during module execution or transaction processing.

### 2. Arithmetic Panics
- Division or modulo by zero in fee distribution, staking rewards, slashing, or oracle price calculations.
- BigInt operations with nil operands or unvalidated denominators.

### 3. Nil Pointer Dereferences
- Dereferencing nil keeper references, nil context values, missing account records, or uninitialized module params.
- Ignored return values from map/store lookups leading to nil dereferences.

### 4. Bounds & Type Assertions
- Out-of-bounds slice or array indexing in block header processing, vote extensions, or transaction parsing.
- Single-value type assertions `x.(Type)` that panic on unexpected message types.

## Finding Output Format
- `vulnerability_type`: `explicit_panic`, `division_by_zero`, `nil_pointer_dereference`, or `out_of_bounds_access`.
- `trigger_flow`: Hops from ABCI entrypoint to panic location.
- `malicious_input_example`: Malicious transaction, vote extension, or governance proposal payload.
- `exploitable: true`.

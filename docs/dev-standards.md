# AI Filing System — Architecture Design & Development Principles

This document outlines the system architecture and development principles of the AI Filing System.
It describes the project’s layered structure, communication rules, and design philosophy to ensure modularity, maintainability, and consistency across all components.

## I. Overall Architectural Concept

This project adopts a **layered Clean / Hexagonal Architecture** (each module is designed independently, but communication between modules follows hexagonal principles).
The key design goals are: **stable data contracts, loosely coupled modules, and sustainable evolution.**

### Architecture Layers

```
CLI (User Interface Layer)
│
▼
Application (Business Logic Layer)
│
▼
Ports (Data Contract Layer)
│
▼
Adapters (Implementation Layer)
```

### Layer Responsibilities

| Layer           | Description                                                                     | Example Modules                     |
| --------------- | ------------------------------------------------------------------------------- | ----------------------------------- |
| **CLI**         | System entry point, command parsing, progress display, and process coordination | `fileorg/cli`                       |
| **Application** | Business workflows and cross-module orchestration                               | `file_classifier`, `file_organizer` |
| **Ports**       | Defines cross-module data formats (dataclasses) and interface contracts         | `ports.py`                          |
| **Adapters**    | Handles real-world interactions (filesystem, LLM, parser, JSON, etc.)           | `adapters/*.py`                     |

---

## II. Inter-Module Communication Principles

1. **Modules communicate only via dataclasses defined in Ports**

   - Example: `ReportOutput`, `ParserOutput`, `ClassificationOutput`
   - Directly passing internal classes or objects is not allowed.

2. **Absolute paths are the single source of truth**

   - All cross-module paths (`path`, `old_path`) must be absolute.
   - Use `pathlib.Path.resolve()` to handle them.
   - OS differences (`/` vs `\`) are unified by `pathlib`.

3. **Fixed dependency direction**

   - `adapters` → may only depend on `ports`
   - `application` → may only depend on `ports`
   - `cli` → may only depend on `application`
   - `ports` → must not depend on any internal modules

4. **No cross-layer calls, no shared internal objects**

   - For example: `file_parser` must not directly call `file_classifier`.
   - Coordination must go through the upper `application` or `CLI` layers.

5. **Consistent data flow**

   ```
   ScanOutput.path == ParserInput.path == FileMapping.old_path == OperationStatus.old_path
   new_path = target_dir / new_relative_path
   ```

   *This consistency forms the foundation for all modules.*

---

## III. MVP Development Philosophy

### 1. Single Responsibility & Replaceability

- Each module solves exactly one problem.
- Parser only parses content, without understanding semantics.
- Classifier only classifies, not moves files.
- Restoration only records and restores operations.

### 2. Clear Boundaries

- No module should access another module’s directories.
- Business logic must not reside in the CLI.
- Flow control must not reside in adapters.

### 3. Data Contract First

- **Define Ports dataclasses before developing modules.**
- This ensures each developer can work independently without overlap.

### 4. Fault Tolerance Without Interruption

- If either Parser or Classifier fails on a file, the pipeline continues.
- Record errors in the `error` field instead of halting the process.

### 5. Dry-Run and Restorability

- All actions can be simulated (dry-run) before execution.
- All file movements must be reversible (Restoration Point).

### 6. Logging and Feedback

- The CLI layer provides human-readable output.
- The Application layer returns only data objects — no printing or display logic.

---

## IV. Recommended Development Steps (MVP Stage)

> These steps are for reference. If using vibe coding, prioritize quick implementation — skip mocks within your module’s scope.

1. **Define Ports dataclasses**

   - Clarify field names and structures.
   - Ensure consistency across upstream and downstream modules.

2. **Implement Application Use Cases**

   - Connect upstream and downstream with minimal logic.
   - Use mock adapters initially.

3. **Implement Adapters**

   - Build format parsers, LLM providers, file movers, and JSON handlers.
   - Each must be independently testable.

4. **Integrate End-to-End (validated via CLI)**

   - `organize`: scan → parse → classify → create restore point → execute/preview → report
   - `restore`: load manifest → move files back → display results

5. **Documentation & Testing**

   - Each module should include a short README (describing input/output and example flow).
   - Provide unit tests and at least one end-to-end test.

---

## V. Team Communication Principles

- **Contract changes require sync**: Any modifications to Ports must be confirmed by all team members.

---

## VI. Goals

> **MVP Focus:**
>
> - Fully functional end-to-end flow: scan → parse → classify → preview → report.
> - Ensure data contracts are correct, consistent, and reproducible.
> - Modules must be interchangeable (e.g., swapping LLM, parser, or UI should not affect overall architecture).

---

**Design Summary**

> “Center the design around data contracts and isolate complexity through layering.
> Each layer should only handle its own concerns — that’s the key to a stable pipeline.”
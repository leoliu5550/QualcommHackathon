<!--
Sync Impact Report:
Version change: NONE (initial creation) → 1.0.0
Modified principles: N/A (initial constitution)
Added sections:
  - Core Principles (5 principles: Code Quality, Testing Standards, User Experience Consistency, Performance Requirements, Scope Management)
  - Development Workflow
  - Quality Gates
  - Governance
Removed sections: N/A (initial constitution)
Templates requiring updates:
  ✅ plan-template.md - Constitution Check section already present, aligns with new principles
  ✅ spec-template.md - Requirements section aligns with UX and performance principles
  ✅ tasks-template.md - Test-first approach and task structure align with testing standards
Follow-up TODOs: None
-->

# FileOrg Constitution

## Core Principles

### I. Code Quality Standards

**MUST enforce consistent code quality across all changes:**
- All code MUST pass configured linters (flake8, mypy, black) without warnings
- All functions and classes MUST include docstrings following the Google Python Style Guide
- Cyclomatic complexity MUST NOT exceed 10 per function
- Code coverage MUST NOT decrease from current baseline (target: 80%+)
- All public APIs MUST include type hints
- Dead code and unused imports MUST be removed before commit
- Magic numbers MUST be replaced with named constants

**Rationale**: Consistent code quality ensures maintainability, reduces technical debt, and makes the codebase accessible to all contributors. Type hints and documentation enable safe refactoring and onboarding.

### II. Testing Standards (NON-NEGOTIABLE)

**MUST follow test-first development for all new features:**
- Tests MUST be written BEFORE implementation (Red-Green-Refactor cycle)
- Each user story MUST have corresponding acceptance tests that verify the complete journey
- Contract tests MUST be written for all public APIs and interfaces
- Integration tests MUST cover cross-component interactions
- All tests MUST be independent - no shared state between tests
- Tests MUST run in under 5 minutes for rapid feedback
- Flaky tests MUST be fixed or removed within one sprint
- Test names MUST clearly describe what is being tested and expected behavior

**Test Hierarchy**:
1. **Contract tests**: Verify interface agreements (API contracts, CLI arguments, function signatures)
2. **Integration tests**: Verify component interactions (file operations, AI backend communication, GUI events)
3. **Unit tests** (optional): Verify isolated component logic when beneficial

**Rationale**: Test-first development prevents regressions, documents expected behavior, enables confident refactoring, and ensures features work as specified before deployment.

### III. User Experience Consistency

**MUST maintain consistent UX patterns across all interfaces:**
- CLI commands MUST follow consistent argument patterns (verb-noun structure)
- Error messages MUST be actionable and user-friendly (what went wrong + how to fix)
- Progress indicators MUST be shown for operations exceeding 2 seconds
- All destructive operations MUST require confirmation or provide preview mode
- Backup and restore functionality MUST be available for all file operations
- GUI and CLI MUST provide equivalent functionality
- Help documentation MUST be updated when adding or changing features
- Keyboard shortcuts and context menu options MUST be documented

**Rationale**: Consistent UX reduces learning curve, minimizes user errors, builds trust through predictability, and ensures the tool is accessible to both technical and non-technical users.

### IV. Performance Requirements

**MUST meet performance benchmarks for production readiness:**
- File organization MUST process at least 100 files per minute
- AI inference (NPU backend) MUST complete in under 500ms per file
- GUI MUST remain responsive - no blocking operations on main thread
- Memory usage MUST NOT exceed 500MB for organizing 10,000 files
- Startup time MUST be under 3 seconds for GUI, under 1 second for CLI
- Database queries MUST complete in under 100ms (p95)
- Large folder previews (1000+ files) MUST render in under 2 seconds

**Performance Testing**: All performance-critical code paths MUST include benchmark tests that validate against these requirements.

**Rationale**: Performance directly impacts user satisfaction. Slow tools get abandoned. Meeting these benchmarks ensures FileOrg remains competitive and pleasant to use at scale.

### V. Scope Management and Architectural Alignment

**MUST keep changes cohesive, manageable, and architecturally sound:**
- Each feature MUST align with existing modular architecture (fileorg/ai, fileorg/gui, fileorg/cli)
- New dependencies MUST be justified and approved before addition
- Changes MUST NOT introduce circular dependencies between modules
- Each PR MUST address a single concern (feature, bug fix, or refactor - not multiple)
- Large features MUST be broken into independently deployable user stories
- Refactoring MUST be done separately from feature additions
- Changes affecting multiple modules MUST include architecture decision records (ADRs)
- New abstractions MUST be justified - avoid premature generalization

**Complexity Justification**: Any violation of simplicity (new layer, pattern, or dependency) MUST be documented with: current need, simpler alternative rejected, and why the alternative was insufficient.

**Rationale**: Disciplined scope management prevents feature creep, maintains code health, enables incremental delivery, and keeps the project aligned with its core vision as an AI-powered file organization tool.

## Development Workflow

**Pre-Development**:
1. Feature specification MUST be approved before design work begins
2. Design artifacts (plan.md, data-model.md, contracts/) MUST be complete before implementation
3. Constitution compliance MUST be verified at planning stage

**During Development**:
1. Feature branch MUST be created from main with naming pattern: `[###-feature-name]`
2. Tests MUST be written first and MUST fail before implementation
3. Implementation MUST satisfy all tests
4. All linting, type checking, and formatting checks MUST pass
5. Documentation MUST be updated alongside code changes

**Pre-Commit**:
1. All tests MUST pass
2. Code coverage MUST NOT decrease
3. No linting or type errors
4. Self-review checklist completed

**Code Review**:
1. All PRs MUST be reviewed by at least one other contributor
2. Constitution compliance MUST be verified
3. Performance benchmarks MUST be validated for performance-critical changes
4. Breaking changes MUST include migration guide

## Quality Gates

**No code may be merged unless it passes ALL gates:**

### Gate 1: Constitution Compliance
- [ ] All principles verified in review
- [ ] Complexity justifications provided if applicable
- [ ] Architectural alignment confirmed

### Gate 2: Testing
- [ ] All tests pass (contract, integration, unit)
- [ ] Test coverage baseline maintained or improved
- [ ] No flaky tests introduced

### Gate 3: Code Quality
- [ ] Linting passes (flake8, mypy, black)
- [ ] Docstrings present for all public APIs
- [ ] Type hints complete
- [ ] No code smells or complexity violations

### Gate 4: Performance
- [ ] Performance benchmarks met (if applicable)
- [ ] No memory leaks detected
- [ ] Startup and response times within limits

### Gate 5: User Experience
- [ ] Error messages tested and actionable
- [ ] Help documentation updated
- [ ] Progress indicators present for long operations
- [ ] Destructive operations have safeguards

### Gate 6: Documentation
- [ ] README updated if public API changed
- [ ] Quickstart guide updated if user flow changed
- [ ] ADR created if architectural decision made
- [ ] Code comments explain "why" not "what"

## Governance

**Amendment Procedure**:
- Constitution amendments MUST be proposed via PR with justification
- Amendments require consensus from core contributors
- Version MUST be incremented per semantic versioning:
  - MAJOR: Backward-incompatible principle removals or redefinitions
  - MINOR: New principle/section added or materially expanded guidance
  - PATCH: Clarifications, wording fixes, non-semantic refinements

**Enforcement**:
- All PRs and code reviews MUST verify constitution compliance
- Quality gates (above) MUST be enforced before merge
- Constitution supersedes all other development practices
- Violations MUST be addressed before merge or explicitly justified in PR

**Review Cycle**:
- Constitution MUST be reviewed quarterly for relevance
- Feedback from development experience MUST inform updates
- Lessons learned from production issues MUST be incorporated

**Version**: 1.0.0 | **Ratified**: 2025-10-18 | **Last Amended**: 2025-10-18

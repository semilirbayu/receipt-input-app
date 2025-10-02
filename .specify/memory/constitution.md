<!--
Sync Impact Report:
- Version: [template] → 1.0.0 (Initial constitution establishment)
- Principles established: RESTful API Design, Responsive UI, OAuth2 Authentication, Unit Testing
- Added sections: Development Standards, Governance
- Templates status:
  ✅ .specify/templates/plan-template.md (aligned with constitution checks)
  ✅ .specify/templates/spec-template.md (no changes needed)
  ✅ .specify/templates/tasks-template.md (aligned with testing principles)
- Follow-up TODOs: None
-->

# Receipt Input App Constitution

## Core Principles

### I. RESTful API Design
All backend APIs MUST follow RESTful conventions with JSON-based communication:
- HTTP verbs used semantically (GET, POST, PUT, DELETE, PATCH)
- Resources identified by URIs with proper noun usage
- Responses MUST use appropriate HTTP status codes (2xx success, 4xx client errors, 5xx
  server errors)
- All request and response payloads MUST be valid JSON
- API versioning MUST be implemented via URL path (e.g., `/api/v1/`)

**Rationale**: RESTful design ensures predictable, stateless, and cacheable APIs that
integrate seamlessly with modern frontend frameworks and external services.

### II. Responsive UI
User interfaces MUST be responsive and functional across mobile and desktop devices:
- Mobile-first design approach MUST be applied
- Breakpoints MUST support common device sizes (mobile: <768px, tablet: 768-1024px,
  desktop: >1024px)
- Touch targets MUST meet minimum size requirements (44x44px) for mobile usability
- Layout MUST adapt without horizontal scrolling on any supported viewport
- Critical functionality MUST remain accessible on all device types

**Rationale**: Users need to input receipts from various contexts (on-the-go mobile entry,
desk-based data processing), requiring seamless experiences across all devices.

### III. OAuth2 Authentication for Google Sheets
Authentication and authorization for Google Sheets integration MUST use OAuth2:
- OAuth2 authorization code flow MUST be implemented
- Secure token storage with appropriate encryption MUST be enforced
- Token refresh mechanisms MUST be automatic and transparent to users
- Scope requests MUST follow principle of least privilege
- Users MUST explicitly grant permissions before any data access

**Rationale**: OAuth2 is the industry standard for secure third-party service integration,
ensuring user data privacy and compliance with Google's API policies.

### IV. Unit Testing (NON-NEGOTIABLE)
Unit tests MUST be written for all backend modules:
- Each service, controller, and utility module MUST have corresponding unit tests
- Tests MUST achieve minimum 80% code coverage for backend logic
- Tests MUST be isolated (no external dependencies like databases or APIs in unit tests)
- Mock/stub patterns MUST be used for external dependencies
- Tests MUST be automated and run in CI/CD pipeline before deployment
- Test-first approach (TDD) STRONGLY RECOMMENDED for new features

**Rationale**: Unit testing ensures code reliability, facilitates refactoring, catches
regressions early, and serves as living documentation of module behavior.

## Development Standards

### Code Quality
- Linting and formatting tools MUST be configured and enforced
- Code reviews MUST be conducted before merging to main branch
- Cyclomatic complexity SHOULD be kept below 10 per function
- Functions SHOULD follow single responsibility principle

### Error Handling
- All API errors MUST return consistent error response format with error codes and messages
- Errors MUST be logged with sufficient context for debugging
- User-facing error messages MUST be clear and actionable
- Sensitive information MUST NOT be exposed in error responses

### Security
- Input validation MUST be performed on all API endpoints
- SQL injection and XSS prevention MUST be implemented
- Secrets and credentials MUST NOT be committed to version control
- HTTPS MUST be enforced for all production endpoints

## Governance

### Amendment Procedure
This constitution can be amended through the following process:
1. Proposed changes MUST be documented with rationale
2. Changes MUST be reviewed and approved by project maintainers
3. Version number MUST be updated according to semantic versioning
4. Dependent templates and documentation MUST be updated to reflect changes

### Versioning Policy
Constitution follows semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Backward-incompatible governance changes, principle removals, or redefinitions
- **MINOR**: New principles added or material expansions to existing guidance
- **PATCH**: Clarifications, wording improvements, typo fixes, non-semantic refinements

### Compliance Review
- All pull requests MUST verify compliance with constitutional principles
- Plan phase MUST include Constitution Check gate (as defined in plan-template.md)
- Non-compliance MUST be justified in Complexity Tracking section with rationale
- Unjustifiable violations MUST be refactored before approval

**Version**: 1.0.0 | **Ratified**: 2025-10-01 | **Last Amended**: 2025-10-01

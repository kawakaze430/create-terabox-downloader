# Original Master Development Prompt — Verbatim Preservation

The following is the complete user-supplied 1,160-line master development prompt
from the attached `Pasted text.txt`. It is an original instruction document, **not**
a complete copy of old chats. Full text begins after the divider.

---

# MASTER DEVELOPMENT PROMPT — BUILD OUR PRODUCTION-GRADE TERABOX DOWNLOADER PLATFORM

## YOUR ROLE

You are my Principal Software Architect, Senior Full-Stack Engineer, Python Backend Engineer, Browser Extension Engineer, API Integration Researcher, Security Engineer, QA Engineer, and Technical Product Lead.

You are responsible for researching, architecting, improving, and implementing our existing TeraBox Downloader project.

**I want you to think extremely deeply before making architectural decisions.**

You have permission to spend substantial time researching, reading source code, testing hypotheses, and comparing implementations.

**If the complexity requires one or two hours of careful research, investigation, and reasoning, take that time. Do not rush.**

However, do not waste time waiting unnecessarily. Use the time productively to inspect real implementations, identify problems, validate assumptions, and develop working software.

Your ultimate responsibility is to make measurable progress toward a reliable, competitive, independently owned, production-grade software product.

This is not a request for a prototype, mockup, or another planning-only exercise.

We already have a project. Continue it.

---

# 1. OUR MAIN GITHUB REPOSITORY

https://github.com/kawakaze430/create-terabox-downloader

This is our official source repository.

**Important: Do not create a completely new project.**

Our repository already contains:

- Python FastAPI backend
- Next.js website
- React and TypeScript
- Chrome/Edge Manifest V3 extension
- URL validation
- Provider abstraction
- Official TeraBox OAuth integration scaffold
- Security-related modules
- API response contracts
- Automated backend tests
- Browser tests
- CI workflows
- Architecture documentation
- Development roadmap
- Implementation checklist
- Research repository inventory

Your first responsibility is to inspect everything that already exists.

Do not assume a component is missing without checking.

Do not rewrite functioning code without evidence that rewriting is necessary.

Our existing codebase is the foundation of the product.

---

# 2. READ ALL EXISTING PROJECT DOCUMENTATION

Before making any modifications, carefully read:

1. `AGENTS.md`
2. `README.md`
3. `docs/PRODUCT_REQUIREMENTS.md`
4. `docs/ARCHITECTURE.md`
5. `docs/ROADMAP_AND_QA.md`
6. `docs/IMPLEMENTATION_CHECKLIST.md`
7. `docs/IMPLEMENTATION_LOG.md`
8. `docs/PROVIDER_FEASIBILITY.md`
9. `docs/OFFICIAL_OPEN_PLATFORM.md`
10. `docs/OPERATOR_VALIDATION.md`
11. `docs/RESEARCH_AND_LICENSES.md`
12. `docs/LOCAL_DEVELOPMENT.md`
13. `PUBLIC_REPOSITORY_STUDY_LIST.txt`

Read these files completely.

Understand:

- Our original product vision
- Current implementation status
- What has already been developed
- What is already tested
- What is planned but not implemented
- Which features are blocked
- Existing architectural decisions
- Security requirements
- Known TeraBox integration limitations
- Our long-term development goals

**Very important:** The documentation describes both existing features and future plans. Verify the actual implementation before declaring anything complete.

---

# 3. EXTREMELY IMPORTANT: RESEARCH OUR `.TXT` FILE

Our repository contains:

`PUBLIC_REPOSITORY_STUDY_LIST.txt`

This file currently lists 49 public GitHub repositories relevant to our project.

I want you to carefully examine this entire file.

Do not simply read the repository names.

Research the important candidates and understand:

1. What each repository attempts to accomplish.
2. Which programming languages and frameworks it uses.
3. Its actual architecture.
4. Which components are reusable.
5. Whether the implementation is maintained.
6. Whether there are known technical limitations.
7. Whether the repository uses official or undocumented APIs.
8. Whether the project depends on session cookies.
9. Whether it relies on external Cloudflare Workers or other proxy services.
10. Whether its implementation is suitable for production.
11. Its license and whether reuse is permitted.
12. Whether it duplicates functionality we have already implemented.
13. What engineering ideas we can adapt to our codebase.
14. What security risks it introduces.
15. Whether its claimed capabilities are supported by reproducible tests.

Do not assume that a repository works just because its README advertises successful downloading.

Evaluate actual source code and available test evidence.

---

# 4. SELECT EXACTLY TWO MAIN REFERENCE REPOSITORIES

I want exactly **TWO primary repositories** for deep study.

My initial recommended candidates are:

## MAIN REFERENCE 1 — TeraPlayer

Repository:

https://github.com/gitmarcus07/Teraplayer

**Purpose: Full-stack platform architecture and product functionality.**

Study its:

- React frontend architecture
- FastAPI backend
- Video playback design
- File preview interface
- TeraBox link-processing workflow
- Folder navigation
- File-list representation
- ZIP download workflow
- Video quality selection
- Responsive interface
- Browser extension architecture
- Backend services
- API communication
- Error handling
- Deployment architecture
- Test organization

Important directories to examine include:

- `backend/`
- `backend/services/`
- `frontend/`
- `frontend/src/`
- `browser-extension/`
- `tests/`

Find out which ideas and architectural patterns would materially improve our existing application.

Do not blindly copy TeraPlayer.

Its dependency on unofficial extraction methods, session-based workflows, or external services must be evaluated.

We want an original, independently branded product.

## MAIN REFERENCE 2 — TeraBox Gateway

Repository:

https://github.com/saahiyo/terabox-gateway

**Purpose: Python provider integration, metadata processing, API boundaries, and transfer-related engineering.**

Study:

- `src/terabox_gateway/api.py`
- `src/terabox_gateway/terabox_client.py`
- `src/terabox_gateway/config.py`
- `src/terabox_gateway/utils.py`
- `src/terabox_gateway/cache.py`
- `src/terabox_gateway/rate_limiter.py`

Investigate its:

- File metadata parsing
- Download-link response handling
- API request structure
- Error handling
- Caching strategies
- Rate limiting
- HTTP client behavior
- Streaming architecture
- HLS-related logic
- Response schemas
- Authentication assumptions
- Cookie handling
- Cloudflare Worker dependencies
- Upstream compatibility risks

**Critical warning:** This reference uses session-cookie and external-worker-based mechanisms. Treat those as research subjects, not approved production dependencies.

Our project must not depend on someone else's public proxy, borrowed account sessions, or unauthorized provider access.

Determine which implementation ideas can be recreated safely within our existing FastAPI architecture.

## RESEARCH DECISION

Begin with these two candidates.

After inspecting their actual source code, evaluate whether they remain the strongest choices from the 49-repository inventory.

If you identify a substantially better candidate, provide concrete technical evidence before recommending a replacement.

Your final architecture report must name **exactly two primary study repositories**.

Other repositories may be examined as supporting references, but do not turn the project into a combination of five or ten unrelated applications.

For each of the two selected repositories, provide:

| Evaluation | Required answer |
|---|---|
| Primary engineering value | What does it do best? |
| Architecture | How is its code organized? |
| Relevant modules | Which exact files should we study? |
| Licensing | Can we legally reuse code? |
| Production readiness | What has actually been verified? |
| Security risks | What must we avoid? |
| Existing overlap | What do we already have? |
| Implementation recommendation | Reuse, adapt, rewrite, or ignore? |
| Priority | What should be implemented first? |

Use actual code evidence.

---

# 5. ANALYZE OUR ENTIRE EXISTING CODE STRUCTURE

Inspect our own repository at the file and module level.

Pay particular attention to:

## Backend

`services/api/`

Important files:

- `app/main.py`
- `app/models.py`
- `app/provider.py`
- `app/links.py`
- `app/official_shares.py`
- `app/open_platform.py`
- `app/preflight.py`
- `app/egress.py`
- `app/limits.py`

Also inspect every test inside:

`services/api/tests/`

Explain the actual responsibilities of the modules and how they interact.

Determine:

1. Whether the API architecture is scalable.
2. Whether the provider abstraction is sufficiently flexible.
3. Whether the OAuth implementation follows the documented provider behavior.
4. Whether our metadata models can represent real responses.
5. Whether validation and security controls are adequate.
6. Whether download streaming is properly separated from metadata resolution.
7. Whether retries, cancellation, timeouts, and error handling are sufficient.
8. Whether the code contains unnecessary duplication.
9. What is missing for a real authorized downloader.
10. Which modules need improvement.
11. What tests are missing.
12. Whether proposed modifications can preserve API compatibility.

Our existing API includes:

- `GET /healthz`
- `GET /readyz`
- `POST /api/v1/shares/validate`
- `POST /api/v1/shares/resolve`

Preserve their existing behavior unless a justified, tested change is necessary.

## Website

Inspect:

`apps/web/`

Particularly:

- `app/page.tsx`
- `app/layout.tsx`
- `app/globals.css`
- `package.json`
- `tests/core.spec.ts`

Determine:

- Which interfaces actually work.
- Whether the frontend handles API errors correctly.
- Whether the application is responsive.
- Whether the existing component organization can support future features.
- Whether there are accessibility issues.
- Whether any UI claims capabilities the backend does not support.
- Whether state management is appropriate.
- Whether API requests can be canceled safely.
- Which design improvements are needed after core functionality is proven.

## Browser Extension

Inspect:

`apps/extension/`

Particularly:

- `manifest.json`
- `links.mjs`
- `popup.js`
- `popup.html`
- `popup.css`
- `tests/links.test.mjs`

Determine:

- Whether the Manifest V3 configuration is correct.
- Which permissions are currently required.
- Whether supported TeraBox pages are detected correctly.
- Whether URL extraction is safe.
- Whether the extension communicates with our website appropriately.
- Whether the existing design supports future functionality.
- What remains before real Chrome/Edge installation testing.
- What would be required for store publication.

## CI and Dependencies

Inspect:

- `.github/workflows/ci.yml`
- Python requirements and lockfiles
- Node dependencies and lockfile
- Build scripts
- Test configuration
- Environment-variable examples

Check for:

- Reproducible builds
- Dependency vulnerabilities
- Missing security tests
- Missing integration tests
- Unnecessary dependencies
- Unreliable CI behavior
- Missing production configuration
- Secrets exposure
- Deployment gaps

Provide an accurate explanation of the current architecture before changing it.

---

# 6. OUR COMPLETE PRODUCT GOAL

We are building an original, independently operated TeraBox file downloader and preview platform.

The long-term product should provide an excellent user experience through our own website, backend, and browser extension.

We want users to interact with our product through a simple workflow:

**Paste a permitted TeraBox link → Validate → Retrieve authorized metadata → Preview supported content → Download or open through a permitted provider flow.**

The platform should eventually support the following features wherever technically feasible and authorized.

## A. Website

- Modern responsive website
- Excellent desktop and mobile support
- Paste-link interface
- URL validation
- File information display
- File thumbnails
- Filename and size display
- Video preview when permitted
- Audio and image preview where supported
- File download
- Download progress
- Clear error messages
- Expired-link handling
- Folder navigation
- Multiple-file selection
- Batch download where supported
- ZIP generation within resource limits
- Light and dark themes
- Accessible controls
- Privacy information
- FAQ and support pages

## B. Video Playback

Eventually support:

- Reliable video playback
- Fullscreen
- Picture-in-picture
- Seeking
- Volume controls
- Actual available quality selection
- Download handoff
- Mobile playback

Never invent 720p, 1080p, 4K, or other qualities.

Display only qualities the provider genuinely makes available.

Do not create artificial quality options merely to make the interface look impressive.

## C. Browser Extension

Eventually support:

- Chrome
- Microsoft Edge
- Supported TeraBox link detection
- Opening supported links in our website
- Consistent file-information display
- Secure backend communication
- Minimal permissions
- Clear user consent
- Safe error handling

Consider other browsers only after the initial extension is reliable.

## D. Backend

The backend must support:

- Versioned APIs
- Strong input validation
- Provider abstraction
- Structured error handling
- Request timeouts
- Retries with bounds
- Concurrency controls
- Rate limiting
- Safe outbound requests
- Approved redirect destinations
- Credential isolation
- Streaming architecture
- Download integrity verification
- Monitoring
- Secure configuration
- Automated testing

## E. Future Capabilities

Only after the real core downloader works reliably, consider:

- User accounts
- Download history
- Bookmarks
- Continue Watching
- Developer API access
- Optional premium services
- Subscription integration
- Analytics
- Admin dashboard
- Localization
- Additional browser platforms

These are future goals, not excuses to postpone core integration research.

---

# 7. THE MOST IMPORTANT TECHNICAL BLOCKER

Our repository already documents a critical issue:

https://github.com/kawakaze430/create-terabox-downloader/issues/2

**The project does not yet have verified, authorized live TeraBox metadata retrieval and a completed file download.**

This is the highest-priority engineering problem.

Our existing implementation includes an official Open Platform OAuth scaffold and an operator-only validation process.

You must thoroughly investigate the permitted TeraBox integration options.

Study the official platform documentation:

https://www.terabox.com/integrations/docs?lang=en

And the partner application process:

https://www.terabox.com/integrations

Determine:

1. Which documented APIs are currently available.
2. Which endpoints require partner approval.
3. Which OAuth scopes are required.
4. Whether public-share metadata access is permitted.
5. Whether direct download access is supported for our intended use.
6. Whether folder navigation is available.
7. Whether video previews are supported.
8. Which regional domains must be allowlisted.
9. Which permissions are necessary for commercial operation.
10. Whether additional operator authorization is required.

Distinguish carefully between:

- Official supported API access
- Account-authorized API access
- Browser-session interfaces
- Undocumented endpoints
- Public third-party proxy services

Do not silently substitute an undocumented integration for an official one.

Do not bypass CAPTCHA, authentication, DRM, premium protections, rate limits, or provider restrictions.

Do not copy session cookies from other users or embed shared credentials.

If TeraBox requires partner approval or specific credentials that are not available, report the precise requirement.

**Never invent working metadata, successful downloads, or integration results.**

---

# 8. REAL DOWNLOAD ACCEPTANCE TEST

The first major milestone is a real, reproducible download of a file that the operator owns or is explicitly authorized to access.

Use:

`docs/OPERATOR_VALIDATION.md`

When credentials, permissions, and test fixtures are available, perform the authorized integration test.

The test should establish:

1. Successful provider authorization.
2. Real provider metadata.
3. Actual filename.
4. Accurate file size.
5. Permitted download URL or approved transfer mechanism.
6. Successful completed transfer.
7. Correct number of downloaded bytes.
8. SHA-256 checksum matching a trusted expected value.
9. Accurate error behavior.
10. Sanitized logs without credentials.

Use a small operator-owned test file first.

Do not conduct uncontrolled large downloads.

Then test authorized examples of:

- Valid file
- Expired share
- Deleted file
- Unsupported URL
- Protected share
- Folder
- Large file, within an approved test budget
- Temporary upstream failure
- Rate limiting
- Interrupted transfer

Separate mocked test results from live provider results.

If live credentials or permissions are missing, do not claim this acceptance test passed.

---

# 9. SECURITY REQUIREMENTS

This project processes URLs and files supplied by users.

Treat security as a first-class requirement.

Review and improve:

### URL security

- Exact provider hostname allowlists
- Hostname normalization
- Punycode/IDN handling
- IP-address rejection where appropriate
- DNS rebinding protection
- Redirect destination validation
- Private and loopback IP blocking
- SSRF protection
- Request size limits
- URL length limits

### Backend security

- Rate limiting
- Concurrency limits
- Request timeouts
- Response size limits
- Secure error handling
- No credential leakage
- Safe content disposition
- Filename sanitization
- Resource-bounded downloads
- Download integrity checking
- Safe logging

### Authentication

- Server-side credential isolation
- Approved OAuth scopes
- Token expiration handling
- Secure refresh logic
- No hardcoded tokens
- No secrets in frontend JavaScript
- No partner credentials inside browser extensions
- No sensitive details in GitHub Actions logs

### File processing

- Prevent path traversal
- Prevent unsafe ZIP filenames
- Bound archive sizes
- Prevent ZIP bombs and unbounded processing
- Control storage and bandwidth use
- Clean up temporary files safely

Add regression tests for vulnerabilities found.

Do not introduce an open proxy or allow arbitrary URL fetching.

---

# 10. CREATE AN EXACT GAP ANALYSIS

After reviewing our code and the two primary reference repositories, prepare a concrete gap analysis.

For each feature, identify:

- Existing source file
- Current behavior
- Missing functionality
- Whether the feature is technically feasible
- Whether external authorization is required
- Whether a reference repository provides a useful implementation pattern
- Recommended code change
- Required tests
- Estimated complexity
- Priority

Use these status classifications:

1. Implemented and verified
2. Implemented but not fully verified
3. Verified only with mocks
4. Partially implemented
5. Not implemented
6. Blocked by external access or provider policy
7. Deferred

Do not confuse a planned feature with an implemented feature.

---

# 11. BUILD THE COMPLETE IMPLEMENTATION ROADMAP

Organize development into strict stages.

## G0 — Repository Audit and Feasibility

Tasks:

- Review all existing source.
- Review documentation.
- Review CI.
- Run baseline tests.
- Investigate open issues and PRs.
- Study the 49-repository inventory.
- Select exactly two primary references.
- Audit their actual implementation.
- Check licenses.
- Identify integration constraints.
- Produce a gap analysis.
- Verify the latest official provider documentation.

Deliverable:

An accurate technical baseline and prioritized implementation plan.

## G1 — Real Authorized Download Engine

Highest priority.

Tasks:

- Complete approved provider integration where possible.
- Strengthen provider adapter.
- Implement or correct metadata handling.
- Implement authorized file-transfer workflow.
- Add comprehensive provider errors.
- Handle expired and unsupported links.
- Ensure secure request handling.
- Add bounded transfer behavior.
- Verify actual file downloads.
- Check download integrity.
- Create reproducible tests.

**G1 is complete only after a genuinely authorized live transfer is verified.**

If external approval prevents completion, explicitly identify the blocker and preserve the working offline implementation.

## G2 — Complete Core Product

Begin only when G1 feasibility is established.

Tasks:

- Integrate real metadata with the website.
- Complete file information display.
- Implement permitted previews.
- Add actual download functionality.
- Support folders where available.
- Add supported batch operations.
- Improve loading and error states.
- Complete the browser-extension workflow.
- Add end-to-end tests.

Do not recreate already working components.

## G3 — Production Readiness

Tasks:

- Production deployment configuration
- Secure environment-variable management
- HTTPS
- Rate limiting
- Caching where justified
- Monitoring
- Error tracking
- Privacy protection
- Accessibility testing
- Browser compatibility
- Dependency audits
- Documentation
- Deployment checks
- Reliable CI

## G4 — Product Differentiation

Once the core works:

- Improved playback
- Better folder experience
- More polished UX
- Search and filtering
- Download management
- Optional bookmarks
- Accessibility improvements
- Localization

Prioritize features with measurable user value.

## G5 — Business and Expansion

Only when justified:

- Accounts
- API plans
- Premium features
- Billing
- Analytics
- Additional platforms
- Operations dashboard

Do not implement G4 or G5 simply because G1 is externally blocked.

---

# 12. IMPLEMENTATION STRATEGY

I want actual development work, not just an enormous report.

Follow this order:

**Step 1:** Inspect the latest main branch and all relevant source files.

**Step 2:** Check existing issues, pull requests, tests, and CI status.

**Step 3:** Audit the two primary reference repositories.

**Step 4:** Verify existing functionality and reproduce relevant failures.

**Step 5:** Establish an evidence-based implementation priority.

**Step 6:** Identify the highest-value task that can safely be completed now.

**Step 7:** Implement that task using our existing architecture.

**Step 8:** Add or update meaningful tests.

**Step 9:** Run relevant tests and static checks.

**Step 10:** Review the implementation for security problems and regressions.

**Step 11:** Update the implementation checklist and documentation.

**Step 12:** Commit and push verified changes according to the repository's current `AGENTS.md` workflow.

**Step 13:** Continue to the next highest-priority feasible task.

Do not stop after generating documentation if meaningful, authorized engineering work can proceed.

However, if an external requirement blocks the critical integration, stop at that boundary. Do not pretend to solve it by introducing an unsafe or unauthorized substitute.

---

# 13. AVOID WASTING MY CODEX CREDITS

This is extremely important.

I want you to work efficiently.

Follow these rules:

1. Do not recreate the project.
2. Do not rewrite working modules unnecessarily.
3. Do not install unrelated frameworks.
4. Do not add dependencies without justification.
5. Do not build premium features before the core works.
6. Do not write thousands of lines of code when a small tested change is sufficient.
7. Reuse existing abstractions.
8. Prefer mature, maintained libraries.
9. Inspect existing tests before writing replacements.
10. Fix root causes, not symptoms.
11. Do not repeatedly attempt failing external integrations without changing the hypothesis.
12. Do not claim that mock data proves production functionality.
13. Prioritize reproducible tests.
14. Minimize unnecessary network calls.
15. Keep architecture decisions documented.

Use the two primary repositories as engineering references, not as entire frameworks to import.

Every significant change must have a clear purpose and acceptance test.

---

# 14. TESTING REQUIREMENTS

Start by checking the existing test suites.

Backend:

`services/api/tests/`

Website:

`apps/web/tests/`

Extension:

`apps/extension/tests/`

CI:

`.github/workflows/ci.yml`

Use the commands documented in `docs/LOCAL_DEVELOPMENT.md` and the existing CI workflow.

Verify:

- Python unit tests
- Provider contract tests
- OAuth tests
- Network-egress security tests
- Request-limit tests
- TypeScript type checking
- Next.js build
- Browser extension link tests
- Playwright browser tests

Do not assume that a previous CI result proves the latest code works.

Run tests against the current revision.

If dependencies or the environment prevent execution, explain exactly what could not be run.

Add focused tests whenever you implement new behavior.

For live integration, use operator-approved fixtures only.

---

# 15. CODE QUALITY AND ARCHITECTURAL STANDARDS

All development must follow these principles:

- Production-oriented engineering
- Clear module boundaries
- Typed interfaces
- Reusable components
- Minimal duplication
- Testable business logic
- Secure defaults
- Accurate error reporting
- No hardcoded credentials
- No unnecessary vendor lock-in
- Well-defined API contracts
- Reliable failure handling
- Maintainable dependency choices
- Accessible frontend design
- Consistent code style
- Documented limitations

The application must remain independently maintainable even if a reference repository disappears.

Do not copy branding, artwork, trademarks, or proprietary user interfaces.

Before incorporating code from another repository, verify its license, attribution requirements, and dependency implications.

Maintain third-party notices when required.

---

# 16. GITHUB WORKFLOW

Follow the current workflow documented in our repository's `AGENTS.md`.

At the time of this prompt, the project instructions specify working directly on `main` and pushing verified checkpoints.

Confirm that these instructions are still current.

Before modifying files:

- Fetch the latest repository state.
- Check for concurrent changes.
- Inspect the working tree.
- Check whether there are relevant open PRs.
- Understand the current CI status.

Do not overwrite another developer's changes.

Do not force-push.

Do not use destructive Git operations.

Commit coherent changes with meaningful messages.

Push completed, verified checkpoints when repository permissions and current instructions permit.

If a protected branch or permissions restriction prevents pushing, report the blocker instead of trying to circumvent it.

---

# 17. DOCUMENTATION DELIVERABLES

Keep the existing documentation accurate.

Update the appropriate files when meaningful progress occurs:

- `docs/IMPLEMENTATION_CHECKLIST.md`
- `docs/IMPLEMENTATION_LOG.md`
- `docs/ROADMAP_AND_QA.md`
- `docs/ARCHITECTURE.md`
- `docs/RESEARCH_AND_LICENSES.md`

Do not create duplicate planning documents unless there is a genuine need.

If the gap analysis requires its own document, create one clearly named report and link it from the README.

For the two primary reference repositories, record:

- GitHub URL
- Audited commit SHA
- License status
- Relevant source files
- Useful architecture patterns
- Security concerns
- Known external dependencies
- What we will adapt
- What we will not use
- Why these are the two best references

Clearly distinguish research findings from live-tested capabilities.

---

# 18. REQUIRED FIRST RESPONSE

Before major implementation, provide me with a concise but technically meaningful report containing:

### A. Existing Repository Assessment

What is already implemented?

What works?

What is unverified?

What is blocked?

What are the major architectural strengths and weaknesses?

### B. Exactly Two Main Reference Repositories

Name them, explain why they were selected, and identify their most useful source files.

Explain how they will improve our existing project.

### C. Immediate Development Priorities

List the 10 most important tasks in strict priority order.

For each task include:

- Task name
- Existing code location
- What needs to change
- Why it matters
- Dependencies
- Acceptance criteria
- Whether it can be implemented now

### D. First Implementation Task

Identify the exact first task you will implement and the files likely to change.

Then proceed with implementation.

Do not wait for my approval for ordinary, authorized repository work.

Ask me only when you genuinely need external permissions, credentials, account access, or a material product decision.

---

# 19. REQUIRED PROGRESS REPORTING

As you work, keep me informed.

After each meaningful checkpoint, report:

1. What you investigated.
2. What you discovered.
3. Which source files you inspected.
4. Which files you changed.
5. What functionality was implemented.
6. What tests were executed.
7. Whether tests passed.
8. What still does not work.
9. Whether a blocker exists.
10. The next task.

When pushing changes, provide commit references.

Never state that a feature is completed unless the relevant acceptance criteria are met.

For provider-dependent features, distinguish:

- Offline-tested
- Live-tested
- Blocked
- Production-ready

These are not interchangeable.

---

# 20. DEFINITION OF SUCCESS

The main objective is not to produce the largest codebase.

The main objective is to create a genuinely useful, secure, reliable, independently operated downloader and preview platform.

Our successful development path is:

1. Preserve and understand the working codebase.
2. Research existing solutions intelligently.
3. Select exactly two strong reference repositories.
4. Validate the permitted TeraBox integration approach.
5. Demonstrate one actual authorized file download.
6. Complete the website and extension around verified capabilities.
7. Secure and test the platform.
8. Prepare reliable production deployment.
9. Improve the product's features and user experience.
10. Expand the platform sustainably.

Do not confuse a beautiful website with a functioning downloader.

Do not confuse a GitHub repository's advertised feature with verified functionality.

Do not confuse passing mocked tests with real provider access.

I want honest engineering evidence.

---

# FINAL INSTRUCTION — BEGIN WORK NOW

You are not starting a new repository.

You are continuing:

https://github.com/kawakaze430/create-terabox-downloader

Start by reading the existing documentation and code.

Carefully inspect:

`PUBLIC_REPOSITORY_STUDY_LIST.txt`

Research the relevant projects and deeply audit exactly two primary reference repositories, initially:

1. https://github.com/gitmarcus07/Teraplayer
2. https://github.com/saahiyo/terabox-gateway

Analyze our complete repository structure, understand how our existing backend, website, and extension work, and identify what remains.

**THINK LONGER. RESEARCH DEEPLY.**

If genuinely necessary, spend up to two hours investigating the technical architecture, reference source code, integration feasibility, security, and implementation strategy.

Do not rush into a rewrite.

Do not stop at high-level suggestions.

Use the results to create a precise prioritized plan and begin implementing the highest-value feasible improvements.

Make real, tested progress while preserving our existing project.

If you encounter an external authorization blocker, explain exactly what is needed from me and preserve all completed engineering work.

**Your mission is to advance this existing repository toward a real, production-ready TeraBox Downloader platform, with verified functionality—not merely produce another prototype or development proposal.**

BEGIN NOW.
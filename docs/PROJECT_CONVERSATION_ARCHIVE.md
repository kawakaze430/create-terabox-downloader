# Project Chat History — Recoverable Conversation Archive
**Saved:** 2026-11-16. **Scope:** only the GitHub TeraBox Downloader project.
**Disclosure:** No tool in this session can export the complete raw transcript
of all earlier ChatGPT sessions. This is the most complete **recoverable**
chronology of user requests, assistant decisions and GitHub-verifiable
changes. Only the supplied 1,160-line master prompt is archived **verbatim in
full**: [MASTER_DEVELOPMENT_PROMPT_2026-11-15.md](MASTER_DEVELOPMENT_PROMPT_2026-11-15.md).

## 2026-11-13 — Start of original “Create TeraBox Downloader” chat

**Recovered intent:** “TeraBox video downloader website + extension” expanded
into an independently branded market-leading commercial competitor. User
requested research of public software that already exists and conserving
Codex credit; initial assistant recommendation was to study TeraPlayer and
preserve one coherent monorepo. The repo began as docs-only; initial mission,
architecture, roadmap, developer instructions and checklist were pushed.
**GitHub confirmed:** [PR #1](https://github.com/kawakaze430/create-terabox-downloader/pull/1)
merged November 13, with offline link validator/backend, frontend and extension
scaffolds; early 20 Python tests (historical count, not live downloads).

**Exact user texts recoverable from project context (spelling preserved):**
> our main goal is that which is no 1 software system related that  available in market we want to build that be a competitor, our main

> or anything would u like to say which is publicall available in market but codex is building and wasteing my credit so we can include them right now. to achive our main goal

> Hey can u pls update our project goal, all all here so any developer can see understand everything without looking this chart

> pls start implementing this project if anything block i will give codex to fix it first produce complete checklist in order implement this project

> pls start working and push as a pr codex will review and merge

> pls start implementing

> Can you check current repos status? And what are the pull request is available? Please merge them if available. Please check, validate it, and merge them. Second thing, what are the repository you suggested me for study for our complete project? Please list them in a .txt file and push it directly on our repo. And also think longer for other repository and list all of them on that .txt file and push it on main.

## 2026-11-14 — Code implementation and workflow change

**Exact user message:**
> pls start implementing this project in one go and push everything in github ur every 10 min task push github then do next task directly push to main branch no pr no create another branch

**Recovered user audit request excerpt:**
> Act as a senior full-stack engineer, security reviewer and technical lead for my existing GitHub repository:
> https://github.com/kawakaze430/create-terabox-downloader
>
> MISSION:
> Continue building a reliable, independently branded TeraBox downloader website, browser extension and shared FastAPI backend. Do not restart the project or falsely claim real downloads work.

**Confirmed code and decisions:** [PR #3](https://github.com/kawakaze430/create-terabox-downloader/pull/3)
merged the provider contract; [PR #4](https://github.com/kawakaze430/create-terabox-downloader/pull/4)
merged official OAuth scaffold, both November 14. Later main commits added
safe egress, rate limits, offline checksum probe, website privacy/cancellation,
extension URL protections and CI improvements. `AGENTS.md` records direct
verified checkpoint pushes to `main` without new branches or PRs. Tests
reached 153 then 158 Python, 16 extension and 10 browser. Live access remained
unverified. [Implementation log](IMPLEMENTATION_LOG.md) contains the details.

## 2026-11-15 — Research repositories, prompts, and chat recovery

**Recovered user request:** assemble and push a comprehensive `.txt`
inventory of useful public study repositories and keep developing on main.
**GitHub-confirmed:** `PUBLIC_REPOSITORY_STUDY_LIST.txt` lists **49**
public links with priority, purpose, licensing and caveats.
[Commit 873eba5e](https://github.com/kawakaze430/create-terabox-downloader/commit/873eba5e6d24cad6a5fb2e37a6eb9476db8af361).
**Exact master development prompt:** available as the uploaded `Pasted text.txt`
and now preserved without rewriting in [this archive](MASTER_DEVELOPMENT_PROMPT_2026-11-15.md).
Its instructions include two primary source references, G0–G5 roadmap,
operator-only authorized download, all documentation, tests, CI and main workflow.

## 2026-11-16 — “Retrieve Last Message” and “pls check and start”

**Exact user message seen twice in project chats:**
> Do you have access to create Terabox downloader, this chat? Can you give me my last message? I can't access on that chat.

**Exact next user request:**
> pls check and start

Assistant inspected main, source, CI, issue #2 and references:
`gitmarcus07/Teraplayer` at `2e60ba4b4963a4112aab57eb2d4770175c5f9965`
and `saahiyo/terabox-gateway` at
`063f61fc61bb173fb936fc487f4a18e40436caab`; inspected
both MIT LICENSE files, flagged unsafe third-party workers and session
cookies, and copied no provider code. Direct main commits:
- [8203a017](https://github.com/kawakaze430/create-terabox-downloader/commit/8203a017032516e9ae30a9790fc141752604880a): outbound OAuth access/refresh/code
  validation and regression tests, [all-green CI 43750414786](https://github.com/kawakaze430/create-terabox-downloader/actions/runs/43750414786),
  173 backend tests + 16 extension tests + 10 Playwright plus build/typecheck/offline probe.
- [5304ce3](https://github.com/kawakaze430/create-terabox-downloader/commit/5304ce3292c39ff530059cf5f1f339269cdc8dde):
  implementation/research/license/roadmap documentation,
  [all-green CI 43750728308](https://github.com/kawakaze430/create-terabox-downloader/actions/runs/43750728308).

**Exact current user message:**
> Can you push all the detail, all the document, all the chart, all the link as a doc file in our GitHub repo? Reason is that when long chat, ChatGPT giving problem, and ChatGPT can't load our chat. So it's giving us problem. So it will help me that all the find, all of your research, all the message, all the chat, if you push all of that thing in my GitHub repo. So it will help me to continue my project.

**Response/action:** permanent handoff, chat archive, full master prompt,
source index and Word DOCX are being added to GitHub `main`.

## Limits, source provenance and privacy

- “Exact” quotations above originate from project conversation context currently
  accessible; shorter quoted fragments should not be mistaken for complete old
  messages or exact copies of every assistant response.
- GitHub commit/PR/CI facts are independently verifiable at the cited links.
  Other earlier assistant actions appear as **recoverable summaries**, not
  reconstructed verbatim transcripts. GitHub displays most timestamps in UTC,
  while these date labels use India local date where appropriate.
- No unrelated project chats, credentials, secrets or private user files are
  copied into this public repo.
- To archive an inaccessible *entire* raw previous conversation, the user would
  need to obtain its export separately and review it for secrets before commit;
  do not invent missing messages.

**Continue from:** [START_HERE_PROJECT_HANDOFF.md](START_HERE_PROJECT_HANDOFF.md).

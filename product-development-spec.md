# Doc Buddy – Product Development Specification

## 1. Executive Summary

Doc Buddy is a local‑first CLI tool that uses LLM‑powered agents to plan, create, and update documentation inside a cloned MicrosoftDocs repository. The user supplies a **service area**, a **content goal**, and optional **supporting material**. The agent decides which files to add or modify, formats them according to the **Microsoft documentation content standards**, and saves changes directly to the working tree **without running DocFX or committing**. The human reviewer remains in full control of validation and version control.

## 2. Problem Statement

Technical writers and engineers have ideas or raw content but limited time to produce standards‑compliant documentation. We need an assistant that converts intent + inputs into fully formatted Markdown pages inside the repo **without touching build or git history**, so the writer can review, lint, and commit at will.

## 3. Goals & Success Metrics

| Goal    | Metric                                    | Target                        |
| ------- | ----------------------------------------- | ----------------------------- |
| Speed   | Time from command to finished local edits | ≤ 2 min (95 pctl)             |
| Quality | Conformance to JSON standards file        | 100 % required fields present |
| Safety  | Untracked file escapes                    | 0                             |

## 4. Personas

* **TW (Technical Writer):** Wants first drafts that already pass style checks.
* **ENG (Engineer):** Wants to add troubleshooting notes quickly.

## 5. Scope

✅ Clone a single MicrosoftDocs repo via HTTPS or SSH
✅ Read & write Markdown, images, JSON snippets
✅ Enforce *content‑standards.json* structure
❌ Run DocFX build
❌ Stage/commit/push changes
❌ Multi‑repo operations (future)

## 6. Functional Requirements

1. **CLI Invocation**

   ```bash
   doc-buddy run \
     --repo-url https://github.com/<user>/<fork>.git \
     --repo-path ~/work/<fork> \
     --service-area "<area>" \
     --goal "<goal>" \
     --supporting <file|url> [<file|url> ...]
   ```
2. **Repo Clone / Sync**

   * If `--repo-path` is absent, clone `--repo-url` into `~/work/tmp/<slug>`.
   * If the path exists, pull the latest *default branch*.
3. **Multi‑Input Ingestion**  (local paths, HTTP(S) URLs, `-` for stdin) with configurable size limits.
4. **Planning Agent**  builds a task list respecting *content‑standards.json*.
5. **Standards Enforcement**  via a dedicated `standards.validate` tool that checks:

   * Front‑matter fields present & correct IDs (`ms.topic`, etc.).
   * Required sections exist in order.
   * Template placeholders are replaced.
6. **Safe File Ops**  writes are restricted to the repo; no commits.
7. **Completion Output**  CLI prints a summary table of created/updated files and any validation warnings.

## 7. Non‑Functional Requirements

* **OS:** macOS 13+ (Apple Silicon & Intel)
* **Python:** ≥ 3.11
* **Memory:** ≤ 1 GB
* **LLM Cost:** ≤ \$0.05 median per run
* **Context Window:** Planner operates with models supporting up to **32 k tokens** and automatically chunks or trims context to stay within that limit
* **Observability:** Rich TUI progress + JSON logfile `<repo>/.doc-buddy/run‑YYYYMMDD.json`.

## 8. System Architecture

```
CLI ──▶ Clone/Synchronize Repo
           │
           ▼
    Planner Agent (LangChain GPT‑4o)
           │  calls
           ▼
+---------------------------+
| Tools Layer               |
|  • repo.file_read/write   |
|  • repo.search_repo       |
|  • standards.validate     |
|  • remote.fetch_remote    |
+---------------------------+
           │
           ▼
  Edited files on disk (uncommitted)
```

## 9. Component Design

### 9.0 Content‑Discovery Algorithm (Embedding‑first)

1. **Repo Snapshot** – At startup Doc Buddy enumerates every `*.md` (and `*.yml` TOC) file in the repo—no folder or naming heuristics.  Filenames alone are not trusted signals.
2. **Embeddings Index** – The tool embeds each file’s **title, front‑matter `title`, and all headings** using the same model that powers the planner.  Vectors are cached in `.doc‑buddy/cache` for reuse.
3. **Semantic Ranking** – The **content goal** prompt plus supporting‑material extracts are embedded and compared (cosine similarity) with the index.  The top‑K files (default 40) above a similarity threshold (default 0.35) are selected as the working set.
4. **Standards Audit** – Each selected file runs through `standards.validate` to flag missing required sections, outdated templates, or front‑matter issues.
5. **Gap Analysis** – The agent examines the working set against *content‑standards.json* to detect:

   * Required article types that don’t exist (`ms.topic` gaps)
   * Supporting‑material topics not covered in any file
   * Service‑area keywords absent from high‑similarity files

#### 9.0.1 Decision Logic – Create vs Update

* **Update an Existing File** when:

  * The file similarity ≥ 0.35 to the goal **and** it fails `standards.validate`, **or**
  * The file covers the same topic (similarity ≥ 0.50) but lacks required recent information from supporting material.
* **Create a New File** when:

  * No existing file in the working set has similarity ≥ 0.35 for a required content type (Overview, Quickstart, etc.).
  * The content goal introduces a distinct topic not semantically matched by any file above threshold.
* The planner marks each task with `action: update` or `action: create` so downstream steps know whether to call `repo.file_write` in overwrite or new‑file mode.

#### 9.0.2 Content Generation Sources

1. **System Prompt** – Encapsulates *content‑standards.json* (structure, tone, templates).
2. **User Goal & Service Area** – Primary guidance on “what” and “why.”
3. **Supporting Material** – Local files or fetched URLs are chunked and provided via **context tool** so the LLM can quote or paraphrase.
4. **Relevant Repo Excerpts** – For updates, the agent passes trimmed excerpts (headings + surrounding paragraphs) to avoid overwriting unrelated sections.
5. **Style Guide Anchors** – Embedded examples in the prompt ensure SEO title patterns, alt‑text syntax, tab groups, etc.

#### 9.0.3 Content‑Type Selection for *New* Pages

When the **Gap Analysis** determines a new file is needed, the agent selects the appropriate content type (Overview, Concept, Quickstart, How‑To, Tutorial) with a simple *zero‑shot classification* step:

| Signal Source             | How it’s used                                                                                                                          |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **Content Goal Prompt**   | Embedded and compared with exemplar prompts for each content type.                                                                     |
| **Supporting Material**   | Keywords like *steps, prerequisites, quickstart, overview* boost similarity toward matching templates.                                 |
| **Service‑Area Phase**    | Early‑journey verbs ("create", "try", "get started") bias toward *Quickstart*; architecture nouns bias toward *Concept* or *Overview*. |
| **Missing ms.topic Gaps** | If a required type is absent for the service (per standards), that type gets priority.                                                 |

Algorithm:

1. Embed the goal + first 2048 tokens of supporting material.
2. Compute cosine similarity to five stored exemplar strings (one per content type).
3. If similarity ≥ 0.60, choose the best match; otherwise pick the first ms.topic type that is missing for the service.
4. Generate front matter and body using the matching **markdownTemplate** from *content‑standards.json*.
5. Record chosen `ms.topic` for validation.

> Example: Goal = “Add day‑1 instructions so users can enable cold‑storage logging in <10 minutes.” → High similarity to *Quickstart* exemplar, so agent selects **Quickstart**.

#### 9.0.4 Task List Generation & Execution

6. **Task List Generation** – The planner produces sequenced tasks:

   * *Update* pages with validation failures.
   * *Create* pages to fill identified gaps.
   * *Update* `toc.yml` accordingly.
7. **Iterative Execution** – After each task the agent saves changes, re‑embeds the modified file, re‑runs `standards.validate`, and loops until all tasks pass.\*\* – After each task the agent saves changes, re‑embeds the modified file, re‑runs `standards.validate`, and loops until all tasks pass.

### 9.1 CLI (`app/main.py`) CLI (`app/main.py`)

* Adds `--repo-url` arg.
* Calls `git.clone_or_pull()` before launching the agent.

### 9.1 CLI (`app/main.py`)

* Adds `--repo-url` arg.
* Calls `git.clone_or_pull()` before launching the agent.

### 9.2 Planner Agent

* System prompt embeds *content‑standards.json* and instructs: “All new or updated content **must** conform to these standards.”
* Temperature 0.2, `max_tokens` dynamically set based on the selected model’s context window (up to 32 000).

### 9.3 Tools

| Tool                                                    | Responsibility                               |
| ------------------------------------------------------- | -------------------------------------------- |
| `git.clone_or_pull`                                     | Manage local repo checkout                   |
| `repo.file_read`, `repo.file_write`, `repo.search_repo` | Safe file operations                         |
| `remote.fetch_remote`                                   | Download URL assets to a temp directory      |
| `standards.validate`                                    | Parse Markdown and compare against JSON spec |

### 9.4 Standards File

* Stored at `config/content-standards.json` (identical to user‑supplied JSON).
* Loaded once, cached in memory.

## 10. Data‑Flow Sequence

1. CLI parses arguments and clones/pulls the repo.
2. Load *content‑standards.json*.
3. Planner agent receives the goal, supporting material list, and standards.
4. Agent executes tool calls to generate or patch files.
5. After each mutation it calls `standards.validate`; if violations exist, it self‑corrects.
6. On success the CLI reports a summary; the repo remains dirty, ready for manual review and commit.

## 11. Tech Stack

* Python 3.11 + Poetry
* LangChain 0.2.x
* OpenAI GPT‑4o (or Azure OpenAI equivalent)
* GitPython 3.1.x
* Rich for TUI
* jsonschema for standards validation

## 12. Development Phases

| Phase       | Key Deliverables                             |
| ----------- | -------------------------------------------- |
| **Phase 1** | `git.clone_or_pull` utility and CLI scaffold |
| **Phase 2** | Planner agent MVP with standards validation  |
| **Phase 3** | Remote asset ingestion capability            |
| **Phase 4** | UX polish & internal pilot                   |

## 13. Risks & Mitigations

* **Standards drift** → Keep JSON in repo; pin version in agent prompt.
* **Large repos** → Sample context windows; fall back to semantic search.
* **OS‑specific Git issues** → Rely on libgit2 via GitPython.

## 14. Open Questions

1. Minimum macOS version required for universal binaries vs Rosetta?
2. Where should `standards.validate` warnings surface—stderr or logfile?
3. Should there be an opt‑in flag to stage changes automatically?
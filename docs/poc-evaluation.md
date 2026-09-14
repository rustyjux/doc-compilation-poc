# Generated-process POC evaluation

!!! success "Qualified pass"
A generated core process can assemble the master documentation from
TechDocs and Word sources. It is viable as the authoritative assembly
mechanism. It is **not** yet a complete production update or approval
workflow.

The POC produces reviewable Markdown, a usable PDF, and a published GitHub
Pages site while preserving source provenance. That supports the plan
recommendation: keep assembly deterministic, and add AI later only for
advisory tasks.

[Open the compiled master document](index.md){ .md-button .md-button--primary }

## Status at a glance

**Legend:** <span class="status-pass">✅ Met</span> — demonstrated successfully;
<span class="status-not-yet">🕒 Not yet</span> — intentionally deferred, with a
clear implementation path; <span class="status-caveat">⚠️ Caveat</span> —
uncertainty, incomplete fidelity, or a workaround that needs further validation.

| Area                          | Result                                         | Notes                                                                          |
| ----------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------ |
| Table of contents             | <span class="status-pass">✅ Met</span>        | Source and page titles; Word uses detected major sections                      |
| Headings                      | <span class="status-caveat">⚠️ Caveat</span>   | TechDocs headings work; malformed Word styles needed a manual source fix       |
| Internal / cross-source links | <span class="status-pass">✅ Met</span>        | 58 rewritten; 3 excluded targets fall back pending include-or-allowlist policy |
| External links                | <span class="status-pass">✅ Met</span>        | Preserved and marked; automated reachability checking is deferred              |
| Images                        | <span class="status-caveat">⚠️ Caveat</span>   | Linked SVG works after PDF rasterization; embedded Word images are untested    |
| Tables                        | <span class="status-pass">✅ Met</span>        | Present in Markdown and PDF, with layout caveats                               |
| Output formats                | <span class="status-pass">✅ Met</span>        | Markdown, PDF, and a shareable GitHub Pages site                               |
| Candidate vs approved         | <span class="status-not-yet">🕒 Not yet</span> | Deploy is from `main`; no review or approval gate                              |

The summary above covers the observable output. The decision-framework
assessment below covers the qualities of the underlying process.
[View the decision-framework criteria here.](#decision-framework-criteria)

## Scope demonstrated

| Item     | What the POC produced                                                  |
| -------- | ---------------------------------------------------------------------- |
| Sources  | 3 configured sources: 2 Git TechDocs repos and 1 Word document         |
| Assembly | 26 documents in source-defined or configured order                     |
| PDF      | 69 pages with a linked contents section                                |
| Site     | Master document, PDF download, source manifest, and validation report  |
| Pipeline | Fetch → normalize → assemble → validate → PDF export → site generation |

## Assessment against output requirements

### Table of contents — <span class="status-pass">✅ Met</span>

The generated Markdown and PDF contain a complete source/page contents list.
The Word source is represented by its detected major sections rather than only
as one contents entry.

The contents list is intentionally shallow for the multi-page TechDocs sources:
it includes source and page titles, but not every subsection. This satisfies the
documentation-set requirement, though a deeper PDF outline could be added if
stakeholders need subsection-level navigation.

The GitHub Pages-specific heading hierarchy also supplies usable in-page
navigation.

### Heading fidelity — <span class="status-caveat">⚠️ Caveat</span>

Source and page headings are normalized into a consistent master hierarchy.
The validation report shows no headings capped at H6.

The Word section detection is approximate, so broader Word inputs could require
source-specific configuration or stricter style conventions.

!!! warning "Word heading caveat"
The original EFV TechDoc used H1 styles on ordinary paragraphs. The POC
could not normalize that correctly, so the source document was manually
corrected.

### Internal and cross-source links — <span class="status-pass">✅ Met</span>

The build rewrote **58** links to locations within the combined output,
including Connected Services ↔ APS links where the target was selected.

Three links still point outside the selected APS subset:

| From              | Target                              |
| ----------------- | ----------------------------------- |
| `get-support.md`  | `concepts/geo-redundancy.md`        |
| `get-support.md`  | `how-to/prod-checklist.md`          |
| `sdx-services.md` | `reference/plugins/jwt-keycloak.md` |

These are reported rather than silently discarded. They fall back to public
TechDocs URLs with the `.md` extension removed, so they leave the compiled
document rather than becoming dead links. Remaining work is policy: include
those pages, or explicitly allowlist them as approved external TechDocs
targets.

### External links — <span class="status-pass">✅ Met</span>

The build preserved **18** absolute external links and converted **6**
site-relative application links into usable DevHub URLs. External links are
visually marked in the published outputs.

Automated reachability checking is deferred and was not required for this POC.

### Images — <span class="status-caveat">⚠️ Caveat</span>

The selected APS SVG is copied into the output and retained on the Pages site
(see "SDX Architecture" under API Services Portal). Draw.io SVGs do not render
reliably in Typst, so the PDF build rasterizes them through Chrome. The PDF
contains the figure with alternative text.

!!! warning "Image caveats"
Linked-image handling is demonstrated, but it depends on a PDF-specific
rasterization workaround. Embedded Word images were not tested. Additional
tests should cover multiple images, captions, sizing, and a Word-embedded
image.

### Tables — <span class="status-pass">✅ Met</span> with presentation caveats

Markdown tables are retained and represented as tables in the PDF. Their text is
present, including the larger APS parameter and role tables. See "SDX
Environments" under API Services Portal in the navigation for examples.

### Output formats — <span class="status-pass">✅ Met</span>

| Output                | Role                                                              |
| --------------------- | ----------------------------------------------------------------- |
| `dist/master.md`      | Interoperable pre-export format                                   |
| `dist/master.pdf`     | Initial distribution format                                       |
| MkDocs / GitHub Pages | Shareable document, PDF download, manifest, and validation report |

!!! info "Markdown and PDF are not identical inputs"
Canonical Markdown retains MkDocs Material tabs and admonitions. The PDF
build expands those constructs into labeled blockquotes. This is
deliberate so the PDF stays readable.

### Candidate versus approved publication — <span class="status-not-yet">🕒 Not yet</span>

The current workflow builds and deploys from `main`. There is no separate
candidate artifact, review step, or maintainer approval before a version is
treated as approved. That remains future workflow work rather than a gap in
the assembly mechanism.

## Assessment against the decision framework

| Criterion                       | Rating                                         | Evidence                                                                                                                                                                                                                                                          |
| ------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Source traceability             | <span class="status-pass">✅ Strong</span>     | Lock and manifest record locations, Git refs, revisions, hashes, sizes, order, and navigation. Sections include provenance comments. Word has a path and hash, but no external system-of-record URL. Retrieval time is recorded for the lock, not per source.     |
| Reviewability                   | <span class="status-pass">✅ Strong</span>     | Markdown, PDF, manifest, and validation findings are inspectable and can be compared in git. A candidate-versus-approved publication gate is deferred (see above).                                                                                                |
| Repeatability                   | <span class="status-not-yet">🕒 Not yet</span> | Python, Pandoc, and Typst are pinned and checksummed. Assembly is deterministic for fixed inputs. Exact replay is deferred: Git config still tracks moving branches, fetch always uses current heads, and Chrome is unpinned in CI.                               |
| Change detection                | <span class="status-not-yet">🕒 Not yet</span> | Revisions and content hashes are generated, including the Word file. Lock comparison, change-set reporting, and stopping when selected content is unchanged remain to be implemented.                                                                             |
| Update suitability              | <span class="status-not-yet">🕒 Not yet</span> | One-command rebuild already runs in CI. Scheduling, source-change triggers, notifications, candidate retention, and maintainer approval are future workflow work.                                                                                                 |
| Maintainability / extensibility | <span class="status-pass">✅ Good</span>       | Selection and order are configuration-driven. Stages are separate. New Git sources can be added without redesign. Only Git Markdown and local Word are understood today. Custom parsing needs tests before the source set grows.                                  |
| Operational cost                | <span class="status-pass">✅ Acceptable</span> | Isolated Python deps and locally installed document tools on GitHub-hosted CI. Clean builds still download tools, clone repos, and rasterize SVGs. Caching can wait.                                                                                              |
| Failure visibility              | <span class="status-pass">✅ Met</span>        | Missing sources, empty includes, conversion failures, and export failures stop the build. Excluded links and navigation mismatches are reported rather than silently dropped. Fail-on-unresolved policy and automated output assertions remain to be implemented. |

## Recommendation

Confirm the generated core process as the preferred assembly approach.

Before using it as an ongoing production update process:

1. Resolve remaining excluded link targets, **or** add a maintained allowlist
   so maintainers can approve TechDocs targets that should stay outside the
   compiled document.
2. Add lock comparison and a clear selected-content change report.
3. Support rebuilding from locked source revisions for exact replay.
4. Add automated tests for link rewriting, heading normalization, Word
   conversion, tables, and images.
5. Add an embedded-image Word fixture and perform a focused visual PDF review.
6. Define candidate versus approved publication and the maintainer approval
   step.

!!! note "AI assistance"
AI is **not** needed for authoritative assembly. It remains a reasonable
future layer for explaining source changes and recommending inclusion,
exclusion, or restructuring for maintainer review.

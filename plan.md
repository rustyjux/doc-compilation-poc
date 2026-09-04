APS-4908 - Approach for master docs

Key context:

- https://dpdd.atlassian.net/browse/APS-4908 (Research master doc approach)

Additional context:

- https://dpdd.atlassian.net/browse/APS-4909 (Create inital master doc)
- https://dpdd.atlassian.net/browse/APS-4899 (Master doc update process)

## Sources

Sources may include:

- note some sources are quite large - use a limited subset during testing
- TechDocs repos
  - e.g.
    [https://github.com/bcgov/aps-infra-platform/](https://github.com/bcgov/aps-infra-platform/tree/test/)
- Other web docs - ideally use the source repo
  - e.g.
    [https://github.com/bcgov/data-publication](https://github.com/bcgov/data-publication)
- Word documents
  - e.g. ?
  - Generate some simple boilerplate to test (include content to test fidelity
    requirements)
  - For conversion to MD, consider:
    - [https://github.com/benbalter/word-to-markdown-js](https://github.com/benbalter/word-to-markdown-js)
    - [https://github.com/jgm/pandoc](https://github.com/jgm/pandoc)

As is, the complete provider process is only captured in a FigJam diagram. This
process must be converted into a more structured format and included as a
source. In a more refined 'master documentation' the process documentation
potentially plays a critical role, defining which sources are relevant and how
they should be assembled.

## Output

### Requirements:

- Table of contents for complete documentation set
- Fidelity
  - Headings preserved or updated to fit within combined output
  - Internal links preserved (e.g. links within a TechDocs repo point to the
    same location in the output)
  - Crosslinks preserved - TBC (e.g. links between TechDocs repos are
    maintained)
  - can these be identified based on URL?
  - External links preserved (e.g. links to an outside application)
  - Images preserved
  - Tables preserved

### Output format

- Ideal future state: TechDocs repo
- Planned for initial stage: PDF
- To allow flexibility, use an interoperable pre-export format - Markdown seems
  like the best candidate
  - Benefits:
    - Capacity to export to PDF (or other format)
    - Can render in a GitHub Page for immediate review
    - Can export to TechDocs if/when appropriate
  - Use MkDocs (Python-Markdown) style to allow for eventual TechDocs
    publication
- Commit the latest output to the repo
  - Include pre-export MD and final output (PDF) artifacts
  - Decision: store output artifacts in a folder OR in an isolated branch?
- Convert to PDF only at export time
  - Consider
    [https://github.com/realdennis/md2pdf](https://github.com/realdennis/md2pdf)

### Output publication

- Need a shareable link to provide to stakeholders
  - Need a shareable link to provide to stakeholders
  - If storing output artifacts in GitHub, consider using GitHub pages to make
    available (distinguish 'candidate' and 'approved' versions)

## Assembly and update considerations

### Approach

The main output of APS-4908 is a recommendation on the master doc assembly
process. Although defining the update workflow is out of scope, the assembly
approach must account for source traceability and change detection. A suitable
assembly process should therefore be safely repeatable and capable of forming
the basis of the future update process.

A manual assembly process is useful as a baseline, but seems unsuitable as the
long-term approach because it would be difficult to maintain, audit, and repeat
consistently.

A 'generated' process presumably refers to a process that is automated but does
not involve generative AI. Such a process can produce deterministic output when
its source revisions, configuration, and toolchain versions are fixed.

An 'AI-assisted' process presumably refers to a process that is automated and
involves generative AI. Such a process will be less deterministic, but offers
some potential benefits. For example, AI could flag source changes and recommend
content for inclusion or exclusion based on relevance (whereby they can be
reviewed and approved by a maintainer).

An AI-assisted process could be layered on top of a generated process (e.g. AI
agent orchestrates process using a combination of committed scripts and AI
skills), to ensure some steps are completed in a consistent and token-efficient
manner, while others leverage AI where appropriate.

The sections below explore future update and operational considerations because
they affect whether an assembly approach will remain maintainable. They do not
attempt to define the full update workflow covered by APS-4899.

### Decision framework

The approaches should be assessed against the following criteria. Criteria
marked as required must be satisfied by the preferred approach; the remaining
criteria help distinguish between otherwise viable options.

- **Output fidelity (required):** preserves headings, tables, images, internal
  links, cross-source links, and external links through assembly and export.
- **Source traceability (required):** records where each assembled item came
  from, including its source location, revision or version, and retrieval time.
- **Maintainability (required):** keeps source selection, ordering, transformation, and
  tooling understandable and modifiable by the team.
- **Reviewability (required):** produces changes that maintainers can inspect
  before publishing an approved version.
- **Repeatability:** produces equivalent output from the same source revisions,
  configuration, and toolchain.
- **Change detection:** identifies which configured sources or selected files
  changed since the previous assembly without requiring a full manual review.
- **Update suitability:** can be rerun safely and can support the future update
  workflow, working with the assembly mechanism.
- **Extensibility:** can add source types, output formats, or optional
  AI-assisted steps without redesigning the core process.
- **Operational cost:** has acceptable setup, runtime, review, and troubleshooting
  effort.
- **Failure visibility:** reports missing sources, conversion failures, broken
  links, and partial output rather than silently publishing an incomplete
  document.

### Initial assessment

The ratings below assess each option as the primary assembly mechanism. An
AI-assisted layer over a generated mechanism is considered separately in the
summary.

#### Manual

- **Output fidelity — mixed:** a careful editor can preserve or repair complex
  content, but consistency becomes harder as the source set grows.
- **Source traceability — weak:** provenance must be recorded manually and can
  easily become incomplete or stale.
- **Maintainability — weak:** source selection and transformation knowledge
  depends heavily on individuals and written procedures.
- **Reviewability — mixed:** the output can be reviewed, but distinguishing
  intentional edits from source changes may be difficult.
- **Repeatability — weak:** repeated assemblies are likely to differ because of
  human choices or omissions.
- **Change detection — weak:** maintainers must inspect sources or rely on
  external notifications.
- **Update suitability — weak:** each update repeats substantial manual effort
  and carries a risk of drift.
- **Extensibility — mixed:** people can accommodate new cases flexibly, but the
  recurring effort grows with every source and output format.
- **Operational cost — mixed:** setup cost is low, but recurring assembly and
  review costs are high.
- **Failure visibility — weak:** missing or partially processed content may not
  be noticed without a comprehensive checklist.

**Summary:** useful as a one-time baseline and for editorial exceptions, but not
suitable as the primary long-term mechanism.

#### Generated

- **Output fidelity — strong, subject to validation:** explicit transformations
  can preserve content consistently, although links, images, and Word
  conversion require POC testing.
- **Source traceability — strong:** a manifest can record source locations,
  revisions, selected files, and retrieval times.
- **Maintainability — strong:** version-controlled configuration and scripts
  make rules visible, testable, and transferable between maintainers.
- **Reviewability — strong:** generated diffs, manifests, logs, and candidate
  artifacts can be inspected before approval.
- **Repeatability — strong:** fixed inputs, configuration, and tool versions can
  produce equivalent output.
- **Change detection — strong:** revisions and content hashes can identify
  changed sources and files.
- **Update suitability — strong:** the same assembly command can regenerate a
  candidate when approved source changes are detected.
- **Extensibility — strong:** modular fetch, transform, and export stages can
  support new source types and output formats.
- **Operational cost — mixed:** implementation and testing require up-front
  effort, but routine runs should have low recurring cost.
- **Failure visibility — strong:** validation can stop publication and report
  missing sources, failed conversions, or broken references.

**Summary:** best fit for the authoritative core process, provided a POC
validates fidelity and the team keeps configuration and transformations simple.

#### AI-assisted

- **Output fidelity — mixed:** AI may resolve unusual content, but can also
  rewrite, omit, or invent material unless constrained by deterministic tools.
- **Source traceability — mixed:** tool calls and recommendations can be logged,
  but model reasoning and output may vary between runs.
- **Maintainability — mixed:** natural-language rules are flexible, but prompts,
  models, and agent tooling add dependencies and require evaluation.
- **Reviewability — mixed:** recommendations can focus reviewer attention, but
  nondeterministic output increases the review needed before approval.
- **Repeatability — weak:** equivalent inputs may produce different selections,
  structures, or wording.
- **Change detection — mixed:** AI can flag semantically relevant changes, but
  deterministic revisions and hashes remain more reliable for detecting that a
  change occurred.
- **Update suitability — mixed:** useful for triage and recommendations, but
  human approval and a reliable assembly mechanism are still required.
- **Extensibility — strong:** AI can accommodate new source structures and
  ambiguous classification tasks with less bespoke transformation code.
- **Operational cost — mixed:** implementation may be quick for some tasks, but
  model usage, evaluation, and additional review create recurring costs.
- **Failure visibility — mixed:** AI may identify semantic gaps that rules miss,
  but its own omissions and unsupported conclusions can be difficult to detect.

**Summary:** valuable as an advisory layer for change triage, inclusion or
exclusion recommendations, and exceptional cases; unsuitable as the sole
authoritative assembly mechanism.

### Provisional direction

Use a generated core process with explicit, version-controlled configuration.
AI assistance may be added for change triage and recommendations, while
maintainers retain approval and the generated process performs the
authoritative assembly. Use the POC to validate the generated approach's
fidelity, traceability, and failure reporting before confirming this direction.

### Process trigger

- For dev: allow for local runs
- For prod: Can then be ran on schedule or triggered by an external webhook call
  (e.g. n8n workflow)
  - GitHub Action?
  - Env where AI agent can run?
- Notify maintainers when a new candidate version is generated (ie update ran
  and some sources had changed since last run)
  - Provide mechanism for maintainers to release an 'approved' version following
    review (no manual changes expected)

### Process

- Fetch
  - From a list of predefined sources (YAML, sources.yaml)
    - must be branch specific for GitHub repos
  - ideally all sources publicly available to support easy automated fetches
  - on fetch, record the source revision or version and retrieval time
  - detect changes using an appropriate stable identifier:
    - Git commit SHA and, where useful, selected-file content hashes for
      repository sources
    - response version or ETag when supported by other source systems
    - content hashes for downloaded files, including Word documents
      - a raw Word file hash may also change because of package metadata; hash
        normalized or converted content as well if only substantive content
        changes should trigger review
  - compare identifiers with the previous run
    - if no configured source content changed, end the run
- Filter
  - TBC - do this before restructuring?
  - Filter based on rules specified in sources.yaml
  - Keep provider-relevant docs for specific processes and products, drop other
    docs
    - Omit general supporting content (e.g. APS)
- Restructure
  - as necessary, reorganize docs into a consistent structure
  - may include flattening the source repo file structure
  - keep Word docs as single file in initial iteration
- Add meta-content
  - TBC - do this before or after building output
  - Update internal links and TechDocs crosslinks
  - Table of contents
- Export
  - Convert to final output format
  - Persist final output and pre-export (MD?) intermediary

## Gotchas

Tricky bits to watch out for and validate in testing:

- Output fidelity
  - Embedded images (word)
  - Linked images (md)
  - Tables
  - Links (internal/cross/external)

## Out of scope

- Split Word doc input into multiple docs (e.g. based on H1)

# Graph Report - VietOCR  (2026-07-03)

## Corpus Check
- 1 files · ~1,430 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 14 nodes · 24 edges · 4 communities (3 shown, 1 thin omitted)
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 5 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `349ba972`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_app.js|app.js]]
- [[_COMMUNITY_processOcr|processOcr]]
- [[_COMMUNITY_setupEventListeners|setupEventListeners]]
- [[_COMMUNITY_handleFileSelect|handleFileSelect]]

## God Nodes (most connected - your core abstractions)
1. `setupEventListeners()` - 6 edges
2. `processOcr()` - 4 edges
3. `showToast()` - 4 edges
4. `handleFileSelect()` - 3 edges
5. `validateAndSetFile()` - 3 edges
6. `checkApiStatus()` - 2 edges
7. `resetUpload()` - 2 edges
8. `switchTab()` - 2 edges
9. `displayOcrResult()` - 2 edges
10. `copyTextToClipboard()` - 2 edges

## Surprising Connections (you probably didn't know these)
- `setupEventListeners()` --indirect_call--> `handleFileSelect()`  [INFERRED]
  app.js → app.js  _Bridges community 2 → community 3_
- `setupEventListeners()` --indirect_call--> `processOcr()`  [INFERRED]
  app.js → app.js  _Bridges community 2 → community 1_
- `validateAndSetFile()` --calls--> `showToast()`  [EXTRACTED]
  app.js → app.js  _Bridges community 3 → community 1_

## Import Cycles
- None detected.

## Communities (4 total, 1 thin omitted)

### Community 0 - "app.js"
Cohesion: 0.67
Nodes (3): elements, resetUpload(), switchTab()

### Community 1 - "processOcr"
Cohesion: 0.50
Nodes (4): checkApiStatus(), displayOcrResult(), processOcr(), showToast()

### Community 2 - "setupEventListeners"
Cohesion: 0.50
Nodes (4): copyTextToClipboard(), downloadJsonFile(), downloadTxtFile(), setupEventListeners()

## Knowledge Gaps
- **1 isolated node(s):** `elements`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `setupEventListeners()` connect `setupEventListeners` to `app.js`, `processOcr`, `handleFileSelect`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `processOcr()` connect `processOcr` to `app.js`, `setupEventListeners`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Why does `showToast()` connect `processOcr` to `app.js`, `handleFileSelect`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `setupEventListeners()` (e.g. with `copyTextToClipboard()` and `downloadJsonFile()`) actually correct?**
  _`setupEventListeners()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `elements` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
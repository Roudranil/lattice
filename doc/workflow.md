# workflow

- [workflow](#workflow)
  - [1. Domain Knowledge Understanding](#1-domain-knowledge-understanding)
    - [Steps](#steps)
    - [HITL](#hitl)
  - [2. Research Plan Construction](#2-research-plan-construction)
    - [Contents of Research Plan](#contents-of-research-plan)
    - [HITL](#hitl-1)
  - [3. Task Decomposition (TODO Generation)](#3-task-decomposition-todo-generation)
    - [Task Categories](#task-categories)
    - [Actor](#actor)
    - [TODO](#todo)
  - [4. Analysis Phase](#4-analysis-phase)
    - [4.1 Surveyor Subagents (Map Phase)](#41-surveyor-subagents-map-phase)
      - [Responsibilities](#responsibilities)
    - [Output](#output)
    - [4.2 Collector Subagent (Reduce Phase)](#42-collector-subagent-reduce-phase)
      - [Responsibilities](#responsibilities-1)
  - [5. Final Output Generation](#5-final-output-generation)
    - [Deliverables](#deliverables)
  - [6. HITL Checkpoints Summary](#6-hitl-checkpoints-summary)
  - [7. Future Improvements / TODO](#7-future-improvements--todo)


This document defines the execution plan for a research agent.  
Each step explicitly specifies **who performs it**:

- **LLM** – reasoning, synthesis, classification
- **Tool** – external API or retrieval system
- **Code** – deterministic logic without LLM involvement
- **HITL** – human-in-the-loop checkpoint



## 1. Domain Knowledge Understanding

**Goal:** Establish domain grounding and extract structured signals from seed material (if any).

### Steps

1. **Identify research domain**
   - Actor: LLM
   - Input: user query and/or seed papers
   - Output: domain label + short description

2. **Lightweight domain expansion**
   - Actor: Tool
   - Action: 1–2 web / academic searches (e.g., Wikipedia, arXiv category, Semantic Scholar topic)
   - Output: short list of domain descriptors and terminology

3. **Seed paper summarization (if provided)**
   - Actor: LLM or Tool
   - Output:
     - problem statement
     - methodology
     - key findings
     - keywords

4. **Citation extraction**
   - Actor: Tool
   - Input: seed papers
   - Output: list of cited works (deduplicated)

5. **Entity / Concept extraction**
   - Actor: LLM
   - Output:
     - materials / methods / variables
     - experimental vs theoretical flags
     - common metrics

### HITL
- Confirm:
  - domain interpretation
  - relevance of extracted entities
  - inclusion/exclusion constraints



## 2. Research Plan Construction

**Goal:** Define scope and constraints for downstream automation.

### Contents of Research Plan

1. **Title / Heading**
   - Actor: LLM

2. **Domain Summary (2–3 lines)**
   - Actor: LLM

3. **Seed Paper Summaries (if any)**
   - Actor: Tool → formatted by LLM

4. **Keyword & Entity Set**
   - Actor: LLM
   - Used later for:
     - search queries
     - filtering
     - embedding tags

5. **Research Questions (1–3)**
   - Actor: LLM
   - Rules:
     - derived from user query
     - scoped narrowly
     - phrased to support literature search
     - aligned with seed papers (if present)

6. **Per-Question Structure**
   - Question
   - Theme
   - Sub-questions
   - Expected output type (survey / comparison / gap analysis)

7. **Constraints**
   - Actor: LLM + HITL
   - Examples:
     - experimental vs theoretical
     - year range
     - publication type
     - depth of citation traversal

### HITL
- Approve / edit:
  - research questions
  - scope boundaries
  - max citation depth
  - exclusion criteria



## 3. Task Decomposition (TODO Generation)

**Goal:** Convert research plan into executable tasks.

### Task Categories

1. **Discovery**
   - Find papers relevant to each research question

2. **Citation Expansion**
   - Backward and forward citation traversal

3. **Filtering & Ranking**
   - Relevance scoring
   - Credibility assessment

4. **Content Understanding**
   - Abstract / conclusion parsing
   - Method extraction

5. **Comparison & Contradiction Detection**
   - Identify agreement / disagreement

6. **Synthesis**
   - Summarize findings
   - Identify gaps

### Actor
- Task generation: LLM
- Execution mapping: Code

### TODO
- Define task priority rules
- Define stopping conditions
- Define per-task token budgets



## 4. Analysis Phase

### 4.1 Surveyor Subagents (Map Phase)

**One subagent per research question**

#### Responsibilities

1. **Paper Discovery**
   - Actor: Tool
   - Methods:
     - keyword search
     - citation snowballing

2. **Initial Filtering**
   - Actor: LLM (cheap model)
   - Input: title + abstract
   - Output: relevance score

3. **Ranking**
   - Actor: Code + LLM
   - Criteria:
     - citation count
     - venue credibility
     - topical similarity
     - recency

4. **Pruning**
   - Actor: Code
   - Remove items below threshold

5. **Document Processing**
   - Actor: Code
   - Actions:
     - download
     - chunk
     - embed
     - store in vector DB

### Output
- Ranked paper list per question
- Embedded document store
- Metadata (citations, year, method)



### 4.2 Collector Subagent (Reduce Phase)

**Runs after all surveyors finish**

#### Responsibilities

1. **Aggregation**
   - Merge all paper sets
   - Deduplicate

2. **Synthesis**
   - Actor: LLM
   - Identify:
     - consensus
     - contradictions
     - gaps

3. **Cross-question Analysis**
   - Detect overlap or conflicts across research questions

4. **Bibliography Construction**
   - Actor: Code
   - Output: BibTeX / structured refs



## 5. Final Output Generation

### Deliverables

1. **State-of-the-Art Summary**
2. **Method / Approach Comparison**
3. **Identified Research Gaps**
4. **Annotated Bibliography**
5. **Suggested Next Research Directions**



## 6. HITL Checkpoints Summary

| Stage | Purpose |
|---|---|
| After Domain Understanding | Validate interpretation |
| After Research Plan | Lock scope & questions |
| After Surveyor Phase | Approve paper set |
| Before Final Output | Quality control |



## 7. Future Improvements / TODO

- Add confidence scoring per paper
- Support multi-domain queries
- Automate contradiction detection
- Add temporal trend analysis
- Add citation graph visualization
- Add budget-aware execution planner
- Add experiment vs theory classifier
- Add reproducibility scoring



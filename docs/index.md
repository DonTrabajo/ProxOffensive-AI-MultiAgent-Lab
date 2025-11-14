# Documentation Index · Prox Offensive AI Mesh

This index provides a unified overview of every document that powers the Prox Offensive multi-agent red-team workflow.

---

## Core Concepts

### **1. Multi-Agent Architecture**
A distributed workflow using:
- GPT for precise tooling and exploit reasoning
- Claude for reporting, long-context structure, and CLI comfort
- Gemini for grounding and reference checks
- Local LLMs for private synthesis and unrestricted chain-of-thought
- Duck.ai for browser-based ensemble reviews
- Atlas Browser for redacted research and safe exploration

See:  
➡️ `model_roles.md`

---

## Operational Guides (Coming Soon)

### **2. Multi-Agent Workflow Overview**
How the system fits together:
- planners  
- reviewers  
- executors  
- offline reasoning  
- redacted research  
- synthesis loops

Will live here:  
➡️ `workflow_overview.md`

---

### **3. Local LLM Setup**
Offline models for OPSEC-sensitive work:
- Running gpt-oss-20B  
- Running DeepSeek local  
- Serving models via Ollama or llama.cpp  
- Best practices for private chain-of-thought

Will live here:  
➡️ `local_llm_setup.md`

---

### **4. CLI Tools**
Installation + usage:
- GPT CLI  
- Claude CLI  
- Gemini CLI  
- Integration patterns  
- Combining CLI output with local models

Will live here:  
➡️ `cli_tools.md`

---

### **5. Atlas Lane**
Using the Atlas Browser as:
- a safe redacted workspace  
- a compliant research lane  
- a drafting zone before synthesis

Will live here:  
➡️ `atlas_lane.md`

---

### **6. Duck Reviewer Loop**
Ensemble model reviewing:
- How to run three parallel browser LLMs  
- How to merge disagreements  
- Detecting hallucinations  
- Extracting multi-model consensus

Will live here:  
➡️ `duck_reviewer_loop.md`

---

## Philosophy

**Precision. Privacy. Coherence. Cross-verification.**  
The Prox Offensive workflow is built on specialization — the right model for the right task.

As the lab evolves, this documentation index will grow into a full reference library.

---

MIT License © 2025 — Prox Offensive / Felix Gutierrez

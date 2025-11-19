
# Duck Reviewer Loop · Next-Gen Mesh

## 1. Purpose
Duck.ai enables **ensemble-based verification** across:

- GPT  
- Claude  
- Gemini 3  
- Local models  

This ensures no single-model hallucination misleads operations.

---

## 2. Workflow

### Step 1 — Provide identical input  
Review code, loot summaries, recon plans.

### Step 2 — Compare outputs  
Identify:
- contradictions  
- missed logic  
- overconfident claims  

### Step 3 — Local arbitration  
Pipe cloud outputs into a local LLM:

“Which model’s reasoning is most coherent? Why?”

### Step 4 — Synthesis  
Produce final guidance.

---

## 3. Integration with Slingshot  
Slingshot uses Duck-reviewed outputs before executing an engagement plan.


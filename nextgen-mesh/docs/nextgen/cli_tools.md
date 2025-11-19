
# CLI Tools · Next-Gen Architecture

## 1. Philosophy
The terminal is the **primary interface** of the next-gen mesh.  
Every model—local or cloud—should be one command away:

```
gpt "explain this"
cld "refactor this"
gem "analyze screenshot"
loc "summarize loot"
```

---

## 2. Tools

### 2.1 GPT CLI  
Used for:
- exploit logic  
- debugging  
- strict reasoning  

### 2.2 Claude CLI  
Used for:
- documentation  
- explanations  
- narrative structuring  

### 2.3 Gemini CLI (with Gemini 3)
Used for:
- interpreting screenshots  
- parsing dashboards  
- analyzing UI flows  
- mixed-context reasoning  

### 2.4 Local LLM Wrapper (loc)
Custom script calling:
- Ollama  
- LM Studio  
- llama.cpp  
- vLLM endpoints  

---

## 3. Terminal Aliases

Example PowerShell profile:
```powershell
function gpt { param($p) openai api chat.completions.create --model gpt-4.1 --prompt $p }
function gem { param($p) gemini --model gemini-3 --prompt $p }
function cld { param($p) anthropic --model claude-3 --prompt $p }
function loc { param($p) curl http://localhost:11434/api/generate -d "{"prompt":"$p"}" }
```

This aligns with Network Chuck’s CLI-first workflow while preserving your red-team structure.


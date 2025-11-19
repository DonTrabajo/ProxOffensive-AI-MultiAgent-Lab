
# Local LLM Setup (Next-Gen Architecture)

## 1. Purpose
Local LLMs are no longer backup models—they are the **primary reasoning engine**.  
The new architecture transforms local models into:

- Private analysts  
- Report synthesizers  
- Routing assistants  
- Model-of-record validators  
- Offline reasoning loops  
- Creative ideation engines  

---

## 2. Hardware Lanes

### 2.1 Host (Windows)
- Runs fast quantized models (7B–14B)  
- Handles terminal-based interactions  
- Provides routing logic for cloud/local models  
- Tools:
  - Ollama  
  - LM Studio  
  - custom local-llm.exe wrapper  

### 2.2 MacBook Pro (Heavy Lane)
- Runs 20B–70B models  
- High-performance inference using Metal acceleration  
- Dedicated for:
  - Long-form synthesis  
  - Creative content  
  - Research distillation  

### 2.3 Dedicated Utility Box
- Runs background models  
- Handles embeddings  
- Maintains vector indexes  
- Optional always-on inference server  

---

## 3. Model Types

### 3.1 Reasoners
- gpt-oss-20B  
- DeepSeek-R1  
- Qwen 2.5 series  

### 3.2 Writers
- Llama 3.1 instruct  
- Phi-3.5 instruct  

### 3.3 Flash Models
Used for:
- Summaries  
- Cron jobs  
- Cleanup tasks  

---

## 4. Ollama Setup

### Install:
- Windows: simple installer  
- macOS: brew or dmg  

Pull models:
```bash
ollama pull llama3.1
ollama pull gpt-oss:20b-q4
ollama pull deepseek-r1
```

Run server:
```bash
ollama serve
```

---

## 5. Local Endpoint Usage

Local models are accessed via:
```
http://localhost:11434/api/generate
```

You can replace cloud calls with:
```bash
local-llm --file loot/windows_enum.txt
```

---

## 6. Combined Cloud + Local Routing

- Local handles all sensitive synthesis  
- Cloud handles high-value specialty tasks  
- Routing layer decides “who gets the prompt”  

This approach mirrors the newest AI workflows used by top offensive security teams.


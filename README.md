# 𝕌ℕ𝕂 𝔸𝔾𝔼ℕ𝕋

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Next.js-15-000000?style=for-the-badge&logo=nextdotjs&logoColor=white" />
  <img src="https://img.shields.io/badge/Google%20Cloud-Vertex%20AI-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white" />
  <img src="https://img.shields.io/badge/Firebase-Auth%20%26%20Firestore-FFCA28?style=for-the-badge&logo=firebase&logoColor=black" />
  <img src="https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge" />
</p>

```text
   __  _ _  _  _  _    _   ___  ___ _  _  _____ 
  |  \| | |/ /| |/ /   /_\ / __| __| \| ||_   _|
  | | ' | ' < | ' <   / _ \ (_ | _|| .  |  | |  
  |_|\__|_|\_\|_|\_\ /_/ \_\___|___|_|\_|  |_|  
                                                
   Who Visions LLC | AI with Dav3 | @aiwithdav3
```

## 🌟 Overview

**Unk Agent** is an enterprise-grade, multi-model cognitive orchestration system designed for high-performance AI operations. It leverages a sophisticated **Cognitive Tiering** architecture to dynamically route tasks between various Gemini models based on intent, complexity, and cost-efficiency.

Deployed on **GCP Cloud Run** and integrated with **Vertex AI**, Unk Agent serves as a central intelligence hub for the Who Visions fleet, providing persistent memory, specialized skills, and agent-to-agent coordination.

---

## 🧠 Cognitive Tiering

Unk Agent optimizes performance and cost by selecting the right brain for every task:

| 🚀 Tier | 🤖 Model | 🛠️ Best For |
| :--- | :--- | :--- |
| **Default** | `gemini-2.0-flash` | Ultra-fast responses, initial routing, basic Q&A |
| **Flash Thinking**| `gemini-2.0-flash-thinking` | Moderate reasoning, planning, and task breakdown |
| **Unk Mode** | `gemini-2.5-pro` | Deep reasoning, complex coding, and large context analysis |
| **Ultra Think** | `gemini-2.5-pro` (32k) | Strategic system design, long-form research synthesis |
| **Code Specialist**| `gemini-2.5-pro` | Professional-grade code review, debugging, and refactoring |
| **Cost Saver** | `gemini-2.0-flash-lite` | High-volume classification, extraction, and simple logic |

---

## 🛠️ Core Capabilities

### 🗄️ Semantic Vector Memory
Powered by **Firestore Vector Search**, Unk Agent maintains a long-term "LoreDB" of interactions, enabling:
- **RAG (Retrieval-Augmented Generation)**: Grounded responses based on previous context.
- **Bi-directional Linking**: Semantic connections between concepts and memories.
- **Cross-Session Persistence**: Agents remember you across different threads and platforms.

### 🧩 Specialized Skills
Unk Agent comes equipped with a modular skill system:
- **📅 Notion Integration**: Bidirectional sync with Notion databases, pages, and logs.
- **💬 Slack Orchestration**: Automated channel management, message routing, and bot interactions.
- **🎧 Audio & Synthesis**: Advanced TTS (Text-to-Speech) and STT (Speech-to-Text) capabilities.
- **🎨 Creative Generation**: Integration with Imagen and Gemini for multimodal asset creation.
- **🌐 Web Intelligence**: Real-time web search, link scraping, and competitive intelligence.

### 🧵 Agent Thread Runner
A robust execution environment for autonomous workflows:
- **Persistence**: Save and resume complex agent "lives" across restarts.
- **Telemetry**: Real-time tracking of agent health, cost burn, and success metrics.
- **Parallel Execution**: Run multiple "lives" concurrently for massive task distribution.
- **Self-Healing**: Automatic recovery from transient errors in autonomous loops.

---

## 🚀 Quick Start

### 📦 Prerequisites
- Python 3.11+
- Google Cloud Platform Project (Vertex AI enabled)
- Firebase Project (Auth & Firestore)

### 🛠️ Installation
```bash
# Clone the heart of the fleet
git clone https://github.com/Who-Visions/unk-app-ai.git
cd unk-app-ai

# Activate the brain
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install the dependencies
pip install -r requirements.txt
```

### 📡 Local Discovery
```bash
# Start the engine
python deploy.py

# Access the dashboard
# http://localhost:8080/docs
```

---

## 🏛️ Architecture

```mermaid
graph TD
    User([User Request]) --> Gateway[FastAPI Gateway]
    Gateway --> Auth{OIDC Auth}
    Auth --> Classifier[Intent Classifier]
    
    subgraph Cognitive Core
        Classifier --> Flash[Gemini 2.0 Flash]
        Classifier --> Pro[Gemini 2.5 Pro]
        Classifier --> Thinking[Flash Thinking]
    end
    
    Cognitive Core --> Tools[Tool Execution Layer]
    
    subgraph Skills & Memory
        Tools --> Notion[Notion SDK]
        Tools --> Slack[Slack API]
        Tools --> Vector[Firestore Vector DB]
        Tools --> Web[Web Search/Scrape]
    end
    
    Tools --> Response([Final Output])
```

---

## 🎨 Design Philosophy: Aesthetics & UX

Unk Agent isn't just a backend; it's a **premium experience**.
- **Colorful Logging**: Rich terminal output with vibrant themes for developers.
- **Streaming Excellence**: Zero-latency word-by-word response streaming.
- **Soulful Persona**: Configurable tone and vocabulary (specifically tailored for the Who Visions brand).
- **Glassmorphism & Gradients**: (Coming soon) for the next-gen web dashboard.

---

## 📈 Roadmap
- [ ] **Ultra-Long Context Caching**: Optimized for 1M+ token libraries.
- [ ] **Multi-Agent Swarms**: Coordinated task execution between Ralph, Kaedra, and Yuki.
- [ ] **Vision-First Grounding**: Native understanding of UI and visual workflows.

---

## 🤝 Contact & Community
- **Website**: [WhoVisions.com](https://whovisions.com)
- **Instagram**: [@aiwithdav3](https://instagram.com/aiwithdav3)
- **YouTube**: [@aiwithdav3](https://youtube.com/aiwithdav3)

Developed with ❤️ by **Who Visions LLC**.

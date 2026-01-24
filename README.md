# RagScale — Voice-Enabled Agentic RAG System


> **Live Demo / Walkthrough:** [Loom Walkthrough](https://www.loom.com/share/50f43d75e4664e4284fd1eab451e38e9)

RagScale is a production-grade **Agentic AI Platform** designed to solve the latency and state management issues typical in RAG applications. It moves beyond simple "Chat with PDF" wrappers by implementing a **Multi-Stage Asynchronous Ingestion Pipeline**, **Hybrid Memory Architecture** (Vector + Graph), and **Voice-Native Interaction**.

---

## 🏗️ System Architecture

The system is architected as a distributed application using **FastAPI** for the interface and **Redis** as the backbone for state and messaging.

### 1. The "Two-Queue" Ingestion Pipeline
To handle high-volume document processing without blocking the API, ingestion is decoupled into a multi-stage distributed workflow:
1.  **Stage 1 (Chunking Worker):** Pulls PDFs from S3 (MinIO), splits them into semantic chunks.
2.  **Stage 2 (Embedding Worker):** Generates embeddings via **Ollama** and upserts to **Qdrant**.
*   **Atomic Tracking:** Real-time progress is tracked via **Redis Hashes** and streamed to the client via **Server-Sent Events (SSE)**.
*   **📂 Code:** [src/services/queue_service.py](backend-ai/src/services/queue_service.py)

### 2. Stateful Agent Orchestration (LangGraph)
The cognitive engine uses a graph architecture.
*   **Routing Node:** Classifies intent (General Chat vs. RAG vs. Web Search) using **Groq (OpenAI GPT-OSS-120B)**.
*   **Tool Use:** Integrated **Tavily MCP** for live web search/extraction as per need.
*   **Memory:** Full persistence of conversation state using In-Memory Checkpointing.
*   **📂 Code:** [src/services/llm_service.py](backend-ai/src/services/llm_service.py)

### 3. Hybrid Memory Layer (Mem0)
Context is managed via **Mem0**, utilizing a dual-store approach:
*   **Qdrant:** For semantic similarity search (Short-term/RAG context).
*   **Neo4j:** For Graph Memory, mapping entity relationships (Long-term/Episodic memory).
*   **📂 Code:** [src/db/mem0.py](backend-ai/src/db/mem0.py)

### 4. Multimodal Layer (Voice)
Voice interaction is architected for low latency using a "side-channel" streaming pattern.
- **STT:** User audio is transcribed using **ElevenLabs (scribe-v2)**.
- **TTS:** LLM text tokens are streamed concurrently to the client (via SSE) and to the **ElevenLabs WebSocket API**.
- **Audio Streaming:** The resulting audio chunks are buffered in **Redis Streams** and streamed to the client on a separate HTTP endpoint, preventing blockage of the primary SSE connection.
- **📂 Code:** [src/services/tts_service.py](backend-ai/src/services/tts_service.py) & [src/services/streaming_service.py](backend-ai/src/services/streaming_service.py)

---

## 🛠️ Tech Stack

| Category | Technologies |
| :--- | :--- |
| **Backend** | Python 3.14, FastAPI, Pydantic |
| **Orchestration** | LangGraph, LangChain |
| **Databases** | **Qdrant** (Vector), **Neo4j** (Graph), **MongoDB** (User/Session), **Redis** (Queue/PubSub) |
| **Storage** | MinIO (S3 Compatible Object Storage) |
| **AI/Inference** | Groq (OpenAI GPT-OSS-120B, Llama 3), ElevenLabs (STT, TTS with WebScokets), Ollama (Embeddings), Tavily (Web Search) |
| **Infrastructure** | Docker Compose, Redis Queue (RQ) |

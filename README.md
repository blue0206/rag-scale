# RagScale — Voice-Enabled Agentic RAG System

> **Status:** 🚧 Active Development (All Backend Logic & Orchestration Complete)

An **Agentic AI System** designed to bridge the gap between static RAG retrieval and dynamic conversational flows. This project implements a **Hybrid Memory Architecture** (Vector + Graph) and utilizes **LangGraph** for stateful agent orchestration.

This system features an asynchronous ingestion pipeline, semantic intent classification, and long-term user personalization via Mem0.

---

## 🏗️ System Architecture & Code Tour

The core logic of the application is fully implemented. Start your review here to understand the architectural patterns used.

### 1. Agent Orchestration (LangGraph)
Instead of a linear chain, the agent uses a state graph with checkpointing to reason, route, and execute.
*   **Key Logic:** Conditional routing between "General Chat" and "RAG Retrieval" based on intent.
*   **📂 Code:** [backend-ai/src/services/llm_service.py](backend-ai/src/services/llm_service.py)

### 2. Hybrid Memory Layer (Mem0 + Neo4j + Qdrant)
The system maintains user context across sessions using a dual-storage approach:
*   **Vector Store (Qdrant):** For semantic search and RAG context.
*   **Graph Store (Neo4j):** For relationship mapping and entity tracking via Mem0.
*   **📂 Code:** [backend-ai/src/db/mem0.py](backend-ai/src/db/mem0.py)

### 3. Asynchronous Ingestion Pipeline (Redis)
To prevent blocking the main thread during heavy PDF processing, ingestion is decoupled using a Producer-Consumer pattern.
*   **Producer:** Splits documents and pushes jobs to Redis.
*   **Consumer (Worker):** Processes chunks and generates embeddings in the background.
*   **📂 Code:** [backend-ai/src/workers/chunking_worker.py](backend-ai/src/workers/chunking_worker.py)
*   **📂 Code:** [backend-ai/src/services/embedding_worker.py](backend-ai/src/services/embedding_worker.py)

### 4. Multimodal Capabilities (Voice)
Native integration with Groq's STT (Whisper) and TTS (Orpheus) models for voice-enabled interaction.
*   **📂 Code:** [backend-ai/src/services/voice_agent.py](backend-ai/src/services/voice_agent.py)

---

## 🚀 Key Features

*   **Stateful Orchestration:** Built on **LangGraph** to handle multi-turn conversations, maintaining state and history via persistence checkpoints.
*   **Intelligent Routing:** Uses an LLM classifier to determine if a query requires external knowledge (RAG) or general reasoning.
*   **Hybrid RAG:** Combines **Ollama embeddings** with **Qdrant** for high-precision retrieval.
*   **Long-Term Memory:** "Remembers" user preferences and past interactions (factual, episodic, and semantic memory) using **Mem0**, enabling a personalized experience that improves over time.
*   **Type Safety:** Strict configuration management using **Pydantic** patterns for environment and tool validation.

---

## 🛠️ Tech Stack

*   **Language:** Python 3.14
*   **Orchestration:** LangGraph, LangChain
*   **LLM & Inference:** OpenAI SDK (routed to Groq), Ollama
*   **Databases:** 
    *   **Qdrant** (Vector Store)
    *   **Neo4j** (Graph Store)
    *   **Redis** (Task Queue)
*   **Frameworks:** FastAPI (API Layer), Pydantic
*   **Infrastructure:** Docker

---

## 🗺️ Roadmap & Status

The backend core is architecturally complete. Current focus is on the API exposition layer and Frontend integration.

- [x] **Agentic Workflow:** LangGraph implementation with conditional edges.
- [x] **Memory System:** Mem0 integration with Neo4j and Qdrant.
- [x] **Ingestion Pipeline:** Redis Queue setup and Worker logic.
- [x] **Core Services:** LLM Client, Chunking, and Voice modules.
- [x] **API Layer:** Finalizing FastAPI endpoints and SSE Streaming response.
- [ ] **Frontend:** React + Vite UI with shadcn/ui (or maybe I'll try Next.js).
- [ ] **Deployment:** Docker Compose orchestration.


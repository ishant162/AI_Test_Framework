# Agentic Test Framework

## Overview

The Agentic Test Framework is an intelligent, AI-powered system designed to automate the analysis of test logs, identify failures, and proactively manage the lifecycle of issues within a software development pipeline. Leveraging advanced Large Language Models (LLMs) and a multi-layered memory architecture, this framework moves beyond traditional log parsing to provide contextual insights, reduce manual debugging efforts, and streamline the creation of actionable Jira tickets.

## Business Problem Solved

In modern software development, test logs are voluminous and often unstructured, making it challenging for human engineers to quickly identify root causes, track recurring issues, and maintain a consistent understanding of system health. This leads to:

*   **Slow Issue Resolution:** Engineers spend significant time manually sifting through logs.
*   **Inconsistent Labeling:** Different engineers may categorize similar issues differently, hindering trend analysis.
*   **Reactive Debugging:** Issues are often addressed only after they have impacted users or caused significant delays.
*   **Knowledge Silos:** Insights gained from resolving one issue are not easily shared or applied to future, similar problems.

## Value Delivered

The Agentic Test Framework delivers substantial value by transforming raw log data into actionable intelligence:

*   **Accelerated Root Cause Analysis:** LLM-driven parsing and contextual memory enable faster identification of failure patterns and likely causes.
*   **Automated & Consistent Issue Tracking:** Automatically creates detailed Jira tickets with standardized categorization, reducing manual overhead and improving data quality.
*   **Proactive Problem Identification:** Semantic memory allows the system to recognize recurring or similar issues, even across different projects, facilitating proactive intervention.
*   **Continuous Learning:** The framework continuously learns from new log data and human feedback, improving its diagnostic capabilities over time.
*   **Reduced Operational Overhead:** Frees up engineering time from repetitive log analysis tasks, allowing them to focus on development and innovation.

## High-Level Architecture

The framework is built around a **LangGraph**-based state machine, orchestrating interactions between LLMs, specialized tools, and a multi-layered memory system. It comprises two main workflows: the **Context Builder** (for knowledge acquisition) and the **Log-to-Jira Workflow** (for operational analysis).

![High-Level Architecture Diagram]

### **Memory Architecture**

The system employs a sophisticated memory architecture to provide comprehensive context:

*   **Short-Term Memory (LangGraph State):** Maintains the current context of an ongoing log analysis session, ensuring consistency across nodes within a single run.
*   **Long-Term Memory (LangGraph Checkpointer - `MemorySaver`):** Persists the state of specific execution threads (e.g., for a particular project or test suite) across multiple runs, allowing the system to remember its own history.
*   **Global Knowledge (LangGraph `InMemoryStore`):** A shared key-value store accessible by all threads, containing structured 
tips, root causes, and resolutions learned across all projects.
*   **Semantic Memory (Vector Database - ChromaDB):** Stores vector embeddings of log templates, annotations, and domain knowledge, enabling the LLM to perform similarity searches and recognize conceptually similar issues, even with varying text.

## Core Components

### **1. LangGraph Orchestrator**
*   **Role:** Manages the flow of information between different nodes, enabling complex, multi-step reasoning and decision-making. It acts as the central nervous system of the agent.
*   **Key Features:** State management, conditional routing, and built-in support for human-in-the-loop (HITL) interventions.

### **2. Large Language Models (LLMs)**
*   **Role:** The intelligence engine behind log parsing, template extraction, semantic annotation, and synthetic data generation.
*   **Key Features:** Contextual understanding, natural language processing, and the ability to generate structured output (JSON) for downstream processing.

### **3. Log Parsing & Annotation Module**
*   **Role:** Transforms raw, unstructured log lines into generalized, semantically rich templates.
*   **Key Features:** LLM-driven template extraction, variable identification, domain-specific labeling (severity, causality, summary, resolution), and integration with SME-curated knowledge bases (e.g., Excel files) for few-shot learning.

### **4. Data Augmentation Module**
*   **Role:** Expands the knowledge base by generating synthetic variants of log templates and injecting external domain expertise.
*   **Key Features:** LLM-based synthetic log generation, dynamic field randomization, and integration of external knowledge sources (e.g., OWASP, cloud error codes).

### **5. Vectorization & Storage Module**
*   **Role:** Converts all textual knowledge (templates, annotations, synthetic data) into numerical vectors and stores them for efficient retrieval.
*   **Key Features:** Utilizes embedding models for local embedding generation and `ChromaDB` (or FAISS) as a lightweight, persistent vector database for semantic search.

### **6. Human-in-the-Loop (HITL) Interface**
*   **Role:** Provides a critical validation step, allowing human experts to review, edit, and approve LLM-generated annotations before they are committed to the knowledge base.
*   **Key Features:** CLI-based interactive review, traffic-light categorization (SME-verified, LLM-suggested, new), and the ability to promote new, validated patterns to the master SME knowledge base.

## Upcoming Features / Roadmap

*   **Phase 02: Augmentation Implementation:** Fully implement the LLM-based synthetic variant generation and external domain knowledge injection.
*   **Phase 03: Vectorization Implementation:** Integrate embeddings and `ChromaDB` for robust vector storage and retrieval.
*   **Automated SME Knowledge Update:** Develop a mechanism to automatically update the master SME Excel file with human-approved, LLM-suggested templates.
*   **Dynamic Prompt Engineering:** Implement adaptive prompting strategies that leverage the growing knowledge base to improve LLM performance and reduce token usage.
*   **Integration with CI/CD:** Enable direct ingestion of test logs from CI/CD pipelines for real-time analysis.
*   **Dashboard & Reporting:** Develop a web-based interface to visualize log trends, issue patterns, and agent performance.

## Running Instructions

### **Prerequisites**
*   Python 3.9+
*   `pip` package manager
*   Access to an OpenAI-compatible LLM API (e.g., `gpt-4.1-mini` or `gemini-2.5-flash`). Ensure `OPENAI_API_KEY` is set in your environment variables.

### **1. Clone the Repository**
```bash
git clone https://github.com/ishant162/agentic_test_framework.git
cd agentic_test_framework
```

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Prepare SME Knowledge (Optional but Recommended)**
Create an Excel file (e.g., `sme_data.xlsx`) with columns like `template`, `severity`, `causality`, `summary`, and `resolution`. This file will serve as your expert reference.

### **4. Run the Context Builder Workflow (with HITL)**
To build the knowledge base, execute the `context_builder_workflow.py` script. This will initiate the log parsing, annotation, and human review process.

```bash
python context_builder_workflow.py
```

The script will process sample logs, pause for human review in the CLI, and then proceed based on your input. You will be prompted to approve, edit, or reject the LLM-generated annotations.

### **5. Running the Main Log-to-Jira Workflow (Future)**
(Instructions for the main workflow will be added once fully implemented and integrated with the Context Builder's knowledge base.)


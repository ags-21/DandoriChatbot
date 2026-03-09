# School of Dandori Assistant

A RAG-powered (Retrieval-Augmented Generation) AI assistant designed to help users discover whimsical, community-led wellbeing classes.

## Project Overview
The School of Dandori focuses on "self-reclamation" through curated evening and weekend classes. This application provides an interactive interface for users to browse the class catalog and consult an AI assistant that understands the unique philosophy and course offerings of the school.

## Architecture
This project utilizes a **multi-page Streamlit architecture** to separate user-facing discovery from interactive AI analysis:

* **Catalog Browser (`app.py`):** The primary portal for users to filter and view available courses.
* **AI Chat Assistant (`pages/chatbot.py`):** An intelligent interface that uses a RAG pipeline to retrieve class context from a vector database and generate warm, accurate, and on-brand responses using an LLM.

## Key Technical Skills
* **RAG Pipeline:** Implementation of semantic search using **ChromaDB** to bridge the gap between static course data and LLM reasoning.
* **LLM Orchestration:** Integration with **OpenAI API** to provide conversational, context-aware assistance.
* **Data Handling:** Automated processing of CSV data into JSON for efficient retrieval.
* **Containerization:** Fully Dockerized (`Dockerfile`) for consistent deployment across environments.
* **Software Design:** Modular approach, separating UI logic from backend retrieval services.

## Getting Started
1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd school-of-dandori-assistant
    ```
2.  **Environment Setup:** Create a `.env` file in the root directory and add your API credentials:
    ```text
    OPENAI_API_KEY=your_key_here
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Launch the App:**
    ```bash
    streamlit run app.py
    ```

## Project Structure
```text
├── app.py              # Main landing page & course browser
├── chatbot.py          # Backend/RAG pipeline logic
├── pages/
│   └── chatbot.py      # Streamlit chat interface page
├── Dockerfile          # Deployment configuration
├── requirements.txt    # Project dependencies
└── README.md

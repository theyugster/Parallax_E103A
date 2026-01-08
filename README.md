# Parallax_E103A

# AI-Powered Learning Management System (LMS)

A full-stack application featuring a FastAPI backend for document management, RAG-based (Retrieval-Augmented Generation) AI features, and a React frontend.

## 🚀 Features

* **User Authentication**: Secure JWT-based signup and login system.
* **Classroom Management**: Create and manage virtual classrooms for students.
* **Intelligent Document Processing**:
    * Upload PDFs and Text files to MinIO object storage.
    * Automatic text extraction and chunking using LangChain.
* **AI Knowledge Base (RAG)**:
    * Vector storage using ChromaDB and HuggingFace embeddings.
    * Ask questions directly to your uploaded documents.
* **Personalized Lesson Generation**: AI-driven generation of lesson plans based on student profiles and classroom content.

## 🛠 Tech Stack

* **Backend**: FastAPI, SQLAlchemy (PostgreSQL), Alembic (Migrations).
* **AI/ML**: LangChain, HuggingFace Embeddings, Google Gemini (for content generation).
* **Storage**: MinIO (File Store), ChromaDB (Vector Store).
* **Frontend**: React (configured for API consumption).

## ⚙️ Setup & Installation

### 1. Prerequisites
* Python 3.10+
* PostgreSQL
* MinIO Server
* Node.js & npm (for React)

### 2. Backend Setup
1.  **Navigate to the backend directory**:
    ```bash
    cd backend
    ```
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Environment Variables**:
    Create a `.env` file in the `backend/` folder:
    ```env
    DATABASE_URL=postgresql://user:password@localhost/dbname
    SECRET_KEY=your_jwt_secret_key
    MINIO_ENDPOINT=localhost:9000
    MINIO_ACCESS_KEY=username
    MINIO_SECRET_KEY=password
    GOOGLE_API_KEY=your_gemini_api_key
    ```
4.  **Run Migrations**:
    ```bash
    alembic upgrade head
    ```
5.  **Start the Server**:
    ```bash
    uvicorn main:app --reload
    ```

### 3. Frontend Setup
1.  Navigate to your React project directory.
2.  Install packages: `npm install`.
3.  Run the application: `npm start`.

## 📖 API Usage

The backend provides an interactive Swagger UI documentation at:  
`http://localhost:8000/docs`

## 📁 Project Structure
```text
├── backend/
│   ├── main.py          # FastAPI initialization
│   ├── routes.py        # API Endpoints (Auth, Docs, Classrooms)
│   ├── models.py        # Database models
│   ├── auth.py          # Security and JWT logic
│   ├── minio_client.py  # MinIO storage configuration
│   └── alembic/         # Database migration scripts
└── frontend/            # React application

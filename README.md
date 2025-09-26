# 📘 Upskill Advisor

An AI-powered career upskilling advisor that recommends personalized learning paths based on user skills, job role goals, and gaps from real job descriptions.

It integrates **FastAPI (backend)**, **React (frontend)**, and **MongoDB Atlas** (course + JD storage with vector search).

---

## 🌟 Features

*  **Hybrid Retrieval**: BM25 + Vector DB + Cross Encoder reranker
*  **Personalized Plans**: Gap analysis against target role JD
*  **Course Timeline**: Structured roadmap with weekly schedule
*  **Evaluation Metrics**: Coverage %, Diversity, Latency tracking
*  **PDF Export**: Downloadable personalized learning plan
*  **Frontend Dashboard**: Interactive UI with charts & gauges

---

##  Tech Stack

* **Frontend**: React.js + Chart.js
* **Backend**: FastAPI (Python 3.10+)
* **Database**: MongoDB Atlas (with Vector Search index)
* **AI Models**: HuggingFace MiniLM Embeddings + Cross Encoder reranker
* **Containerization**: Docker + Docker Compose

---

##  Project Structure

```
upskill_advisor/
│── backend/
│ ├── app/
│ │ ├── api/ # FastAPI routes
│ │ ├── advisor.py # Main advising logic
│ │ ├── retrieval.py # Hybrid retrieval (BM25 + Vectors)
│ │ ├── store.py # Load courses & JDs
│ │ ├── data/ # Dataset (courses.json, jds.json)
│ ├── scripts/
│ │ ├── seed_mongo.py # Seed MongoDB with courses
│ ├── Dockerfile
│── frontend/
│ ├── src/ # React components
│ ├── package.json
│ ├── Dockerfile
│── notebooks/
│ ├── eval_runner.py # Evaluation script
│ ├── metrics.csv # Output metrics
│── docker-compose.yml
│── README.md
```

---

##  Setup Instructions

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/upskill_advisor.git
cd upskill_advisor
```

---

### 2. Environment Variables

 We don’t commit `.env` (it contains secrets).
Instead, use `example.env`.

#### Create `.env` file

```bash
cp backend/example.env backend/.env
```

Now edit `backend/.env` with your actual keys.

#### `backend/example.env`

```env
# MongoDB
MONGODB_ATLAS_URI=mongodb+srv://username:password@cluster.mongodb.net/upskill
MONGODB_DB=upskill
MONGODB_COURSES_COLL=courses
MONGO_VECTOR_INDEX=vector_index

# Embedding Models
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
CROSS_ENCODER=cross-encoder/ms-marco-MiniLM-L-6-v2
```


---

### 3. MongoDB Atlas Setup

1. Create a **free MongoDB Atlas cluster**
2. Create a DB: `upskill`
3. Create a collection: `courses`
4. Add **Vector Search Index** on field `embedding`:

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 384,
      "similarity": "cosine"
    }
  ]
}
```

5. Seed data into MongoDB:

```bash
cd backend
python scripts/seed_mongo.py
```

---

### 4. Run with Docker

```bash
docker-compose up --build
```

Services:

* Backend → `http://localhost:8000`
* Frontend → `http://localhost:3000`
* API Docs → `http://localhost:8000/docs`

---

### 5. Run Without Docker

#### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Evaluation

Run evaluation personas to check coverage & diversity:

```bash
cd notebooks
python eval_runner.py
```

Outputs:

* `metrics.csv` → Coverage, Diversity, Latency
* `eval_requests.jsonl` → Detailed logs


## Architecture

![Architecture](upskill_architecture_clear.png)

---

##  Future Improvements

* Add role-specific **LLM fine-tuned suggestions**
* Integrate **authentication system** for users
* Enable **multi-language support**

## 📸 Project Output Screenshots

Here are some example outputs from the application:

### Frontend
![Plan Generation](output/Screenshot%202025-09-25%20105227.png)

![API Response](output/Screenshot%202025-09-25%20105238.png)

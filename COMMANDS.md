# MayaMall — Quick Commands

## 1. Ollama (Terminal 1 — keep running)
```bash
ollama serve
```

Pull models once (first time only):
```bash
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
```

---

## 2. Backend (Terminal 2)
```bash
cd ~/Desktop/Befach-project/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

First-time setup:
```bash
cd ~/Desktop/Befach-project/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in MONGODB_URI, CLERK_* keys
python -m scripts.seed_products
uvicorn app.main:app --reload --port 8000
```

---

## 3. Frontend (Terminal 3)
```bash
cd ~/Desktop/Befach-project/frontend
npm run dev
```

First-time setup:
```bash
cd ~/Desktop/Befach-project/frontend
npm install
cp .env.example .env        # then fill in NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY, CLERK_SECRET_KEY
npm run dev
```

---

## URLs
| Service   | URL                              |
|-----------|----------------------------------|
| Frontend  | http://localhost:3000            |
| Backend   | http://localhost:8000            |
| API Docs  | http://localhost:8000/docs       |
| Health    | http://localhost:8000/health     |

---

## Docker (alternative — runs everything at once)
```bash
cd ~/Desktop/Befach-project
docker compose up --build
```
Stop: `docker compose down`

---

## Useful one-offs
```bash
# Re-seed products into MongoDB + ChromaDB
cd ~/Desktop/Befach-project/backend && source .venv/bin/activate && python -m scripts.seed_products

# Check Ollama models installed
ollama list

# Check backend logs live
uvicorn app.main:app --reload --port 8000 --log-level debug
```

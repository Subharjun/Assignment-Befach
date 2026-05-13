# 🛍️ MayaMall — AI Conversational Commerce Platform

> **What is this?**  
> MayaMall is an AI-powered online shopping platform. Instead of typing into a search box, you chat with **Maya** — a smart shopping assistant who understands what you want, searches the product catalog intelligently, and helps you find exactly what you're looking for.

Think of it like Amazon or Flipkart, but your shopping assistant is an AI that you can have a real conversation with.

---

## 📋 Table of Contents

- [How It Works (Simple Explanation)](#-how-it-works-simple-explanation)
- [Technology Stack](#-technology-stack)
- [⚡ Using Groq for Fast Inference](#-using-groq-for-fast-inference)
- [Architecture Overview](#-architecture-overview)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites-what-you-need-before-starting)
- [Local Setup (Step-by-Step)](#-local-setup-step-by-step)
- [Environment Variables Guide](#-environment-variables-guide)
- [API Reference](#-api-reference)
- [Database Structure](#-database-structure)
- [Running with Docker](#-running-with-docker)
- [Deployment Guide](#-deployment-guide)
- [Production Checklist](#-production-checklist)
- [Known Limitations / Work In Progress](#-known-limitations--work-in-progress)
- [Troubleshooting](#-troubleshooting)

---

## 🧠 How It Works (Simple Explanation)

When a user types a message to Maya like *"I want red sneakers under ₹2000"*, the system does four things automatically:

1. **Understands the intent** — An AI model (default: `qwen2.5:3b` via Ollama, or `llama-3.3-70b` via Groq) reads the message and extracts structured info: category = shoes, colour = red, max price = ₹2000.
2. **Searches smartly** — The query is converted into a vector (a mathematical representation) using `nomic-embed-text`, and ChromaDB finds the most relevant products from the catalog.
3. **Replies like a human** — Maya responds in a friendly, focused way with matching product suggestions.
4. **Remembers preferences** — Maya stores what the user likes so future recommendations get better over time.

---

## 🛠️ Technology Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.11+ | Programming language |
| **FastAPI** | 0.115+ | Web API framework |
| **MongoDB Atlas** | — | Main database (products, users, carts, conversations) |
| **ChromaDB** | 0.5.20+ | Vector database for semantic search |
| **Ollama** | — | Runs AI models locally on your machine |
| **Motor** | 3.6+ | Async MongoDB driver |
| **PyJWT / python-jose** | — | JWT token verification |
| **Cloudinary** | — | Product image hosting (optional) |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| **Next.js** | 15 | React framework (App Router) |
| **TypeScript** | 5.6+ | Typed JavaScript |
| **Tailwind CSS** | 3.4+ | Styling |
| **Clerk** | 6.0+ | Authentication (sign in / sign up) |
| **Zustand** | 5.0+ | State management (cart, chat, theme) |
| **Lucide React** | — | Icons |

### AI Models
| Model | Provider | Purpose |
|---|---|---|
| `qwen2.5:3b` | **Ollama** | Default local chat assistant |
| `nomic-embed-text` | **Ollama** | Mandatory embedding model (local) |
| `llama-3.3-70b-versatile`| **Groq** | **Recommended:** High-speed cloud reasoning |

---

## ⚡ Using Groq for Fast Inference

While MayaMall runs fully locally by default using Ollama, we highly recommend using **Groq** for the chat component. This provides:
- **Instant Responses**: Sub-second reasoning and token generation.
- **Better Reasoning**: Uses Llama 3.3 70B, which is much smarter than local 3B models.
- **Hybrid Performance**: Embeddings remain local (free & private) while reasoning happens in the cloud.

### How to enable Groq:
1. Get a free API key from [Groq Console](https://console.groq.com/keys).
2. Open `backend/.env`.
3. Fill in your key:
   ```env
   GROQ_API_KEY=gsk_your_key_here
   GROQ_CHAT_MODEL=llama-3.3-70b-versatile
   ```
4. Restart the backend. The system will automatically detect the key and switch from Ollama to Groq for chat.

---

## 🏗️ Architecture Overview

```
 Browser (Next.js 15)
        │
        │  HTTP / JSON
        ▼
 ┌─────────────────────────────────────────────┐
 │          FastAPI Backend (port 8000)         │
 │                                             │
 │  /api/v1/products   → Product listings      │
 │  /api/v1/search     → Semantic search       │
 │  /api/v1/chat       → Maya AI chat          │
 │  /api/v1/cart       → Shopping cart         │
 │  /api/v1/recommendations → For-you feed     │
 │  /api/v1/users      → User profiles         │
 └──────────┬──────────────┬───────────────────┘
            │              │              │
    ┌───────▼──────┐ ┌─────▼──────┐ ┌────▼────────┐
    │  MongoDB     │ │  ChromaDB  │ │   AI Layer  │
    │  Atlas       │ │  (vectors) │ │  (Ollama/   │
    │  (main data) │ │            │ │   Groq)     │
    └──────────────┘ └────────────┘ └─────────────┘
```

### AI Chat Flow (per message)

```
User message
    │
    ▼
[1] Intent Extraction
    qwen2.5:3b extracts: { intent, search_query, category, price_range }
    │
    ▼
[2] Semantic Search
    nomic-embed-text embeds the query → ChromaDB finds top products
    │
    ▼
[3] Grounded Reply
    qwen2.5:3b gets: system prompt + user preferences + products + chat history
    → Maya replies in ≤4 sentences, asks a follow-up if needed
    │
    ▼
[4] Memory Update
    Extracted preferences saved → Conversation persisted in MongoDB
```

---

## 📁 Project Structure

```
Befach-project/
├── backend/                        ← Python FastAPI server
│   ├── app/
│   │   ├── main.py                 ← App entry point, starts Mongo + ChromaDB
│   │   ├── core/
│   │   │   ├── config.py           ← All settings loaded from .env
│   │   │   └── security.py        ← Clerk JWT verification
│   │   ├── api/v1/
│   │   │   ├── router.py           ← Combines all endpoint routers
│   │   │   └── endpoints/
│   │   │       ├── products.py     ← List, filter, get product detail
│   │   │       ├── search.py       ← Semantic search via ChromaDB
│   │   │       ├── chat.py         ← Maya conversational AI endpoint
│   │   │       ├── cart.py         ← Add/update/remove cart items
│   │   │       ├── recommendations.py ← Related & personalised products
│   │   │       └── users.py        ← User profile + view history
│   │   ├── db/
│   │   │   ├── mongodb.py          ← Connection to MongoDB Atlas
│   │   │   └── chroma.py           ← ChromaDB setup
│   │   ├── models/                 ← Pydantic data models (internal)
│   │   ├── schemas/                ← Request/response shapes (API DTOs)
│   │   └── services/
│   │       ├── ai_orchestrator.py  ← Main AI pipeline logic
│   │       ├── ollama_service.py   ← Calls Ollama for chat & embeddings
│   │       ├── chat_llm.py         ← LLM routing (Ollama or Groq)
│   │       ├── vector_service.py   ← ChromaDB search operations
│   │       ├── product_service.py  ← MongoDB product queries
│   │       ├── conversation_service.py ← Save/load chat history
│   │       ├── recommendation_service.py ← Vector-based recommendations
│   │       └── intent_hints.py     ← Intent parsing helpers
│   ├── scripts/
│   │   ├── seed_products.py        ← Loads products into MongoDB + ChromaDB
│   │   └── generate_products.py   ← Generates sample product data
│   ├── requirements.txt            ← Python dependencies
│   ├── Dockerfile                  ← Docker build for backend
│   └── .env.example               ← Template for environment variables
│
├── frontend/                       ← Next.js 15 frontend
│   ├── app/                        ← Next.js App Router pages
│   │   ├── page.tsx                ← Home page
│   │   ├── layout.tsx              ← Root layout (Clerk, theme)
│   │   ├── globals.css             ← Global styles
│   │   ├── products/               ← Product detail page
│   │   ├── cart/                   ← Shopping cart page
│   │   ├── search/                 ← Search results page
│   │   ├── category/               ← Category browse page
│   │   ├── sign-in/                ← Clerk sign-in page
│   │   └── sign-up/               ← Clerk sign-up page
│   ├── components/
│   │   ├── Navbar.tsx              ← Top navigation bar
│   │   ├── ProductCard.tsx         ← Single product display card
│   │   ├── ProductGrid.tsx         ← Grid layout for products
│   │   ├── ProductRow.tsx          ← Horizontal product row
│   │   ├── SearchBar.tsx           ← Search input with suggestions
│   │   ├── VoiceAssistant.tsx      ← Maya chat sidebar UI
│   │   ├── CategoryFilter.tsx      ← Category filter buttons
│   │   ├── Skeleton.tsx            ← Loading placeholder
│   │   └── ThemeBoot.tsx           ← Dark/light mode initialiser
│   ├── store/
│   │   ├── cart.ts                 ← Zustand cart state
│   │   ├── chat.ts                 ← Zustand chat/session state
│   │   └── theme.ts                ← Zustand dark mode state
│   ├── lib/
│   │   └── types.ts                ← Shared TypeScript types
│   ├── middleware.ts               ← Clerk auth middleware (protects routes)
│   ├── next.config.mjs             ← Next.js config
│   ├── tailwind.config.ts          ← Tailwind theme config
│   ├── package.json               ← Node dependencies
│   └── .env.example               ← Frontend env variable template
│
├── docker-compose.yml              ← Run both services with one command
└── README.md                       ← This file
```

---

## ✅ Prerequisites — What You Need Before Starting

Install all of these on your computer first:

### 1. Python 3.11 or newer
Check if you have it:
```bash
python3 --version
```
Download from: https://www.python.org/downloads/

### 2. Node.js 20 or newer
Check if you have it:
```bash
node --version
```
Download from: https://nodejs.org/

### 3. Ollama (runs AI models locally)
Download from: https://ollama.com/download

After installing, start Ollama and pull the required models:
```bash
# Start the Ollama server (keep this running in a separate terminal)
ollama serve

# In a new terminal, download the AI models:
ollama pull qwen2.5:3b          # The chat model (~2 GB)
ollama pull nomic-embed-text    # The embedding model (~274 MB)

# Verify models are available:
ollama list
```

> **Note:** Ollama runs on `http://localhost:11434` by default.

### 4. MongoDB Atlas (free cloud database)
1. Sign up at https://www.mongodb.com/atlas
2. Create a **free** cluster (M0 tier)
3. Under **Database Access**, create a user with read/write permissions
4. Under **Network Access**, add `0.0.0.0/0` to allow connections
5. Copy your **Connection String** — it looks like:  
   `mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/`

### 5. Clerk (user authentication)
1. Sign up at https://clerk.com
2. Create a new application
3. From the dashboard, copy:
   - **Publishable Key** (starts with `pk_test_...`)
   - **Secret Key** (starts with `sk_test_...`)
   - **JWKS URL** (under JWT Templates section)

---

## 🚀 Local Setup (Step-by-Step)

### Step 1 — Clone / open the project

```bash
# Navigate into the project folder
cd Befach-project
```

### Step 2 — Set up the Backend

```bash
# Go into the backend folder
cd backend

# Create a virtual environment (isolated Python environment)
python3 -m venv .venv

# Activate it
source .venv/bin/activate          # macOS / Linux
# OR on Windows:
# .venv\Scripts\activate

# Install all Python packages
pip install -r requirements.txt

# Copy the example env file and fill in your values
cp .env.example .env
```

Now open `backend/.env` in a text editor and fill in your values (see [Environment Variables Guide](#-environment-variables-guide) below).

### Step 3 — Seed the Database

This loads sample products into MongoDB and creates their vector embeddings in ChromaDB. It calls Ollama, so make sure Ollama is running.

```bash
# Still inside backend/ with .venv activated
python -m scripts.seed_products
```

> ⏱️ This takes about 1–2 minutes the first time. You'll see progress logs as products are embedded.

### Step 4 — Start the Backend Server

```bash
uvicorn app.main:app --reload --port 8000
```

The backend is now running. You can verify it with:
- **API health check:** http://localhost:8000/health
- **Interactive API docs (Swagger UI):** http://localhost:8000/docs
- **OpenAPI spec (JSON):** http://localhost:8000/openapi.json

### Step 5 — Set up the Frontend

Open a **new terminal window**, then:

```bash
# Go into the frontend folder
cd Befach-project/frontend

# Install Node.js packages
npm install

# Copy the example env file and fill in your Clerk keys
cp .env.example .env
```

Open `frontend/.env` and fill in your Clerk keys.

### Step 6 — Start the Frontend

```bash
npm run dev
```

Open your browser at: **http://localhost:3000** 🎉

---

## 🔑 Environment Variables Guide

### Backend — `backend/.env`

```env
# ── MongoDB ────────────────────────────────────────────────────────────────
# Your MongoDB Atlas connection string
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority

# Database name (leave as default or change to your preference)
MONGODB_DB=ai_commerce

# ── Ollama (local AI) ──────────────────────────────────────────────────────
# Where Ollama is running (default: local machine)
OLLAMA_BASE_URL=http://localhost:11434

# Which model to use for chat (must be pulled via `ollama pull`)
OLLAMA_CHAT_MODEL=qwen2.5:3b

# Which model to use for embeddings
OLLAMA_EMBED_MODEL=nomic-embed-text

# ── Groq (optional cloud LLM — faster/more powerful) ──────────────────────
# Leave empty to use Ollama. Fill in to use Groq's Llama 3.3 70B instead.
GROQ_API_KEY=
GROQ_CHAT_MODEL=llama-3.3-70b-versatile

# ── ChromaDB (vector store) ────────────────────────────────────────────────
# Where ChromaDB stores its data on disk
CHROMA_PERSIST_DIR=./.chroma

# Name of the products collection in ChromaDB
CHROMA_COLLECTION=products

# ── Cloudinary (image hosting — optional) ─────────────────────────────────
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# ── Clerk (JWT authentication) ─────────────────────────────────────────────
# From your Clerk dashboard → JWT Templates
CLERK_JWT_ISSUER=https://your-tenant.clerk.accounts.dev
CLERK_JWKS_URL=https://your-tenant.clerk.accounts.dev/.well-known/jwks.json

# ── CORS ───────────────────────────────────────────────────────────────────
# URL of your frontend (backend will allow requests from here)
FRONTEND_ORIGIN=http://localhost:3000

# ── App settings ───────────────────────────────────────────────────────────
APP_ENV=development
LOG_LEVEL=info
```

> ⚠️ **IMPORTANT:** If `CLERK_JWKS_URL` is left empty, the backend enters **dev mode** and trusts any bearer token as a user ID. **Never deploy to production with this unset.**

### Frontend — `frontend/.env`

```env
# ── Clerk (from your Clerk dashboard) ─────────────────────────────────────
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_SECRET_KEY=sk_test_xxx

# Clerk redirect URLs (leave as-is for local dev)
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/
NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=/

# ── Backend URL ────────────────────────────────────────────────────────────
# Point this to wherever the FastAPI backend is running
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

---

## 📡 API Reference

All endpoints are prefixed with `/api/v1`. A ✓ in the Auth column means a valid Clerk JWT must be sent in the `Authorization: Bearer <token>` header.

### Products
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/products` | — | List all products with optional filters: `?category=shoes&min_price=100&max_price=2000&sort=price` |
| `GET` | `/products/categories` | — | Get a list of all distinct product categories |
| `GET` | `/products/{slug}` | — | Get full detail for one product by its slug (e.g. `red-sneakers-nike`) |

### Search
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/search` | — | Semantic search using ChromaDB. Send `{"query": "comfortable running shoes", "limit": 10}` |

### Chat (Maya AI)
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/chat` | ✓ | Send a message to Maya. Body: `{"session_id": "abc", "message": "I need a laptop under ₹50000"}` |
| `GET` | `/chat/{session_id}` | ✓ | Retrieve the full conversation history for a session |

### Cart
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/cart` | ✓ | Get the current user's cart |
| `POST` | `/cart/add` | ✓ | Add a product. Body: `{"slug": "product-slug", "quantity": 1}` |
| `POST` | `/cart/update` | ✓ | Update item quantity. Body: `{"slug": "product-slug", "quantity": 3}` |
| `DELETE` | `/cart/{slug}` | ✓ | Remove a product from the cart |

### Recommendations
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/recommendations/related/{slug}` | — | Products similar to a given product (vector neighbours) |
| `GET` | `/recommendations/for-you` | optional | Personalised product feed based on user history |

### Users
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/users/me` | ✓ | Get the current user's profile (auto-creates if first visit) |
| `POST` | `/users/history/{slug}` | ✓ | Record that the user viewed a product |

---

## 🗄️ Database Structure

### MongoDB Collections

| Collection | What it stores |
|---|---|
| `users` | Each user's Clerk ID, saved preferences, and product view history |
| `products` | All products: slug, title, description, category, price, rating, image URL, tags |
| `carts` | One cart per user, containing items with quantities |
| `conversations` | Full chat history per session: messages, session ID, extracted preferences |

### ChromaDB

One vector embedding per product, stored under the collection name set by `CHROMA_COLLECTION` (default: `products`).  
Each vector includes metadata: `category`, `brand`, `price`, `rating` for filtered searches.

---

## 🐳 Running with Docker

Docker lets you run both the backend and frontend with a single command, without manually installing Python or Node.

**Prerequisites:** Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).

> ⚠️ Ollama must still be running on your host machine before starting Docker.

```bash
# Step 1: Fill in the backend environment file
cd backend && cp .env.example .env
# Edit backend/.env with your values, then go back:
cd ..

# Step 2: Fill in the frontend environment file
cd frontend && cp .env.example .env
# Edit frontend/.env with your Clerk keys, then go back:
cd ..

# Step 3: Build and start both containers
docker compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000

The compose file sets `OLLAMA_BASE_URL=http://host.docker.internal:11434` automatically so the container can reach Ollama running on your Mac/Windows host.

To stop everything:
```bash
docker compose down
```

To rebuild after code changes:
```bash
docker compose up --build
```

---

## ☁️ Deployment Guide

### Frontend → Vercel (recommended)

1. Push your code to GitHub.
2. Go to https://vercel.com → **New Project** → import your repo.
3. Set the **Root Directory** to `frontend`.
4. Add these environment variables in Vercel's dashboard:

```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY    = pk_live_...
CLERK_SECRET_KEY                     = sk_live_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL        = /sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL        = /sign-up
NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL = /
NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL = /
NEXT_PUBLIC_API_BASE_URL             = https://your-render-url.onrender.com/api/v1
```

5. Deploy. Vercel will auto-deploy on every `git push`.

### Backend → Render (recommended)

1. Create a **Web Service** on https://render.com.
2. Connect your GitHub repo, set the **Root Directory** to `backend`, and select **Docker** as the runtime.
3. Add all variables from `backend/.env.example` in Render's environment settings.
4. Set `OLLAMA_BASE_URL` to your hosted Ollama instance (see note below).
5. Add a **Persistent Disk** mounted at `/app/.chroma` so ChromaDB data survives restarts.
6. Set `FRONTEND_ORIGIN` to your Vercel URL.

> **Note on Ollama hosting:** Render's free tier cannot run LLMs. Options:
> - Run Ollama on a separate VPS/GPU machine and point `OLLAMA_BASE_URL` to it.
> - Replace `OllamaService` with a hosted API like **Groq** (set `GROQ_API_KEY` in `.env`) — it uses the same interface.
> - Use a managed inference endpoint (Together AI, vLLM, etc.).

---

## ✅ Production Checklist

Before going live, make sure you've done all of the following:

- [ ] **Rotate credentials** — Change the MongoDB, Cloudinary, and Clerk keys from any test/scaffold values.
- [ ] **Set Clerk JWT vars** — Set `CLERK_JWKS_URL` and `CLERK_JWT_ISSUER` so the dev fallback in `security.py` is never triggered.
- [ ] **Add rate limiting** — Use `slowapi` or similar on `/chat` and `/search` endpoints to prevent abuse.
- [ ] **Add observability** — Sentry on the frontend, structured logs + OpenTelemetry on the backend.
- [ ] **Move images to Cloudinary** — Replace seed placeholder image URLs with real Cloudinary uploads.
- [ ] **Add payments** — Wire up Razorpay or Stripe for a real checkout flow.
- [ ] **Add a wishlist** — The `users.history` field exists; a dedicated wishlist UI and collection is future work.
- [ ] **Set up backups** — Enable MongoDB Atlas automated backups and create a re-embedding job triggered on product updates.

---

## ⚠️ Known Limitations / Work In Progress

| Feature | Status | Notes |
|---|---|---|
| Checkout / Payment | 🔴 Stub | Cart UI works; checkout button is not wired to any payment gateway |
| Admin Product CRUD | 🔴 Stub | Products are added only via the seed script |
| Streaming Chat | 🟡 Partial | `OllamaService.chat_stream()` exists but the endpoint returns a full reply; SSE/WebSocket streaming to the browser is a future step |
| Wishlist | 🟡 Partial | Conceptually covered by `users.history`; no dedicated UI yet |

---

## 🔧 Troubleshooting

### "Connection refused" when starting the backend
- Make sure MongoDB Atlas Network Access allows your IP.
- Make sure Ollama is running: `ollama serve`

### Seed script is slow or hanging
- Ollama needs to be running and the models need to be downloaded first.
- Run `ollama list` to confirm `qwen2.5:3b` and `nomic-embed-text` are present.

### Frontend shows "Network Error" when chatting
- The backend must be running on port 8000.
- Check that `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env` points to the correct address.

### "CLERK_JWKS_URL" warning in backend logs
- This is expected in dev mode. Fill in your Clerk JWKS URL to enable proper JWT verification.

### ChromaDB errors after a restart
- If running via Docker, make sure the `chroma-data` volume is mounted (defined in `docker-compose.yml`).
- If running locally, the `.chroma` folder in the `backend/` directory persists data. Don't delete it unless you want to re-seed.

### Re-seeding products
```bash
# From inside backend/ with .venv activated:
python -m scripts.seed_products
```

---

## 👤 Author

**Befach Project** — Built with FastAPI, Next.js 15, Ollama, and Groq.

# 📊 Benchmarking Cache-Cool: LRU vs FIFO

This README provides instructions for running benchmark tests on the `cache-cool` project, specifically comparing performance between FIFO and LRU eviction strategies using the Groq LLM.

---

## 🧪 Benchmark Overview

The benchmark evaluates:

- **💡 Cache hit rate**
- **⏱️ Per-request latency** (mean, p95, p99)
- **♻️ Eviction behavior** under various workloads

These metrics help determine which eviction policy (LRU or FIFO) performs better in terms of latency and hit rate when handling real-world LLM workloads.

---

## ⚙️ Setup Instructions

### 1. 🧬 Clone the Repository

```bash
git clone https://github.com/<your-org-or-user>/cache-cool.git
cd cache-cool
```

Be sure to switch to the desired branch (`fifo-groq` or `feature-branch`) depending on which strategy you want to test.

### 2. Install Dependencies

We recommend using a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 🔐 Get a Groq API Key (if needed)

1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up or log in
3. Navigate to **API Keys** → **Create Key**
4. Copy your personal API key

⚠️ **Important**: Never commit your `.env` file to version control. Keep your API key private.

### 4. Create a .env File

Create a `.env` file in the project root directory with your Groq API key:

```bash
GROQ_API_KEY=your_groq_api_key_here
```

This key is required to send LLM requests.

### 5. Start the Cache-Cool Server

```bash
uvicorn app.main:app --reload
```

Make sure the server is running by visiting [http://localhost:8000/configure](http://localhost:8000/configure), which returns configuration settings.

### 6. Run the Benchmark Script

```bash
python benchmark_cache.py
```

This script runs multiple prompt workloads and prints:

- ✅ **Cache hits and misses**
- ⏱️ **Latency metrics**
- 📊 **Mean / p95 / p99 latency**
- 💾 **Saves results to `benchmark_results.json`**

---

## 📁 Output

After running the benchmark, you'll get:

- `benchmark_results.json`

Run the script on both **fifo-groq** and **main** branches to compare performance.

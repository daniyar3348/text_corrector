# Turan Text Corrector

Automatic spelling correction platform for **Russian** and **Kazakh** text,
built as a research and pilot-implementation prototype for educational institutions.

---

## Features

| Feature | Status |
|---|---|
| Russian spell correction | ✅ |
| Kazakh spell correction | ✅ |
| Kazakh morphological analysis (stem + suffix parsing) | ✅ |
| Automatic language detection | ✅ |
| Confidence scoring | ✅ |
| Diff highlighting (original vs corrected) | ✅ |
| Real-time language detection while typing | ✅ |
| REST API with OpenAPI docs | ✅ |
| Docker / docker-compose deployment | ✅ |
| Plug-in interface for trained NLP models | ✅ |

---

## Project Structure

```
text_corrector/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # FastAPI route handlers
│   │   │   ├── correction.py    # POST /correct-text, /correct-file
│   │   │   ├── detection.py     # POST /detect-language
│   │   │   └── health.py        # GET  /health
│   │   ├── core/
│   │   │   ├── config.py        # Pydantic Settings (reads .env)
│   │   │   └── logging_config.py
│   │   ├── models/
│   │   │   └── model_loader.py  # ← Plug real trained model here
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── language_detection.py   # Rule-based lang detection
│   │   │   ├── text_correction.py      # Dictionary + edit-distance
│   │   │   └── correction_pipeline.py  # Orchestrator
│   │   ├── utils/text_utils.py
│   │   └── main.py              # FastAPI app factory
│   ├── tests/                   # pytest unit + integration tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/          # React UI components
│   │   ├── hooks/               # useLanguageDetection, useTextCorrection
│   │   ├── services/api.ts      # Axios API client
│   │   ├── types/index.ts       # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── nginx.conf
│   └── Dockerfile
├── models/                      # Mount real model files here
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Quick Start

### Option 1 — Docker Compose (recommended)

```bash
# 1. Clone / enter the project
cd text_corrector

# 2. Copy env file
cp .env.example .env

# 3. Build and start
docker-compose up --build

# Frontend: http://localhost:3000
# Backend API docs: http://localhost:8000/docs
```

### Option 2 — Local development

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp ../.env.example .env            # adjust settings if needed
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev                        # starts at http://localhost:5173
```

---

## API Reference

### `POST /correct-text`

Detect the language and return a corrected version of the text.

**Request:**
```json
{ "text": "прмвет мр" }
```

**Response:**
```json
{
  "original_text": "прмвет мр",
  "corrected_text": "привет мр",
  "detected_language": "Russian",
  "confidence": 0.7,
  "corrections": [
    { "before": "прмвет", "after": "привет", "type": "spelling" }
  ],
  "processing_time_ms": 12.4,
  "status": "success"
}
```

---

### `POST /correct-file`

Upload a document and correct **all** of its text. `multipart/form-data`, field
name `file`; accepts `.txt`, `.md`, `.csv`, `.tsv`, `.log`, `.docx`, `.pdf` up
to `MAX_FILE_SIZE_MB` (5 MB).

Unlike `/correct-text` this is not limited to one sentence: the document is
corrected one sentence per model pass and its layout — newlines, indentation,
blank lines — is returned untouched.

**Request:**
```bash
curl -F "file=@document.docx" http://127.0.0.1:8010/correct-file
```

**Response:** same fields as `/correct-text`, plus
```json
{
  "filename": "document.docx",
  "file_type": "docx",
  "corrections_total": 336,
  "total_words": 485,
  "corrected_words": 336,
  "chunks": 95
}
```
`corrections[]` is capped at `MAX_FILE_CORRECTIONS` (1000) — `corrections_total`
reports the real count, and `corrected_text` always contains every fix.

| Status | Meaning |
|---|---|
| `413` | file exceeds `MAX_FILE_SIZE_MB` |
| `415` | unsupported extension (`.doc`, `.exe`, …) |
| `422` | empty file, or no text layer (scanned PDF) |

---

### `POST /detect-language`

Detect only the language without correcting.

**Request:**
```json
{ "text": "Сәлем Қазақстан" }
```

**Response:**
```json
{
  "detected_language": "Kazakh",
  "confidence": 0.91,
  "status": "success"
}
```

---

### `GET /health`

```json
{
  "service_status": "ok",
  "model_status": "placeholder",
  "version": "1.0.0",
  "details": {
    "russian_model": "PlaceholderModel[Russian]",
    "kazakh_model":  "PlaceholderModel[Kazakh]"
  }
}
```

Full interactive docs: `http://localhost:8000/docs`

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

---

## Connecting a Real Trained Model

The system is designed so that swapping in a real model requires **zero changes** to
the API or frontend.

### Steps

1. **Train or download** your model.
   Compatible formats: HuggingFace Transformers (seq2seq, masked-LM), ONNX.

2. **Place the model files** in the `models/` directory, e.g.:
   ```
   models/
   ├── russian_spellchecker/
   │   ├── config.json
   │   ├── tokenizer.json
   │   └── model.safetensors
   └── kazakh_spellchecker/
       └── ...
   ```

3. **Set the path** in `.env`:
   ```env
   RUSSIAN_MODEL_PATH=/models/russian_spellchecker
   KAZAKH_MODEL_PATH=/models/kazakh_spellchecker
   ```

4. **Implement inference** in `backend/app/models/model_loader.py`:
   ```python
   # Inside TransformerModel._run_inference():
   from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

   self._tokenizer = AutoTokenizer.from_pretrained(model_path)
   self._model = AutoModelForSeq2SeqLM.from_pretrained(model_path)

   # In _run_inference():
   inputs = self._tokenizer(text, return_tensors="pt", truncation=True)
   outputs = self._model.generate(**inputs)
   return self._tokenizer.decode(outputs[0], skip_special_tokens=True)
   ```

5. **Uncomment** the optional dependencies in `requirements.txt`:
   ```
   torch>=2.0.0
   transformers>=4.38.0
   ```

6. Rebuild with `docker-compose up --build`.

The `correction_pipeline.py` orchestrator automatically detects that
`TransformerModel.is_ready == True` and routes inference through it.

---

## Language Detection — How It Works

The detection algorithm is layered:

| Priority | Signal | Weight |
|---|---|---|
| 1 | Kazakh-exclusive characters (Ә Ғ Қ Ң Ө Ұ Ү Һ І) | 65% |
| 2 | Token overlap with Kazakh high-frequency word list | 35% |
| 3 | Token overlap with Russian high-frequency word list | 60% |
| 4 | Cyrillic character coverage (Russian fallback) | 40% |

Output labels: `Russian` · `Kazakh` · `Mixed` · `Unknown`

---

## Kazakh Morphology — How It Works

Kazakh is agglutinative: a stem takes an ordered chain of suffixes
(`STEM + NUMBER + POSSESSIVE + CASE`). A finite dictionary cannot list every
inflected form, so the corrector integrates a **morphological analyzer**
(`backend/app/services/morphology/`) into the Kazakh pipeline:

1. **Analysis** — an out-of-vocabulary word is segmented back into stem +
   grammemes using the allomorph inventories in `suffixes.py`, with
   **vowel-harmony** validation (`phonology.py`) and recovery of stem-final
   consonant alternations (қ↔ғ, к↔г, п↔б).
2. **Decision** — if the word parses to a *known stem* with a harmony-consistent
   suffix chain (e.g. `мектептердің` → `мектеп`-PL-GEN), it is a valid form and
   is left untouched.
3. **Correction** — only words that are neither in the vocabulary nor
   analyzable fall through to dictionary + edit-distance correction.

This is the unified ML / morphology mechanism targeted by project stage 4: the
morphological analyzer and the correction model cooperate so that genuine
inflection is preserved while real misspellings are fixed.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DEBUG` | `false` | Enable debug mode |
| `MAX_TEXT_LENGTH` | `5000` | Max input characters |
| `CORRECTION_SIMILARITY_THRESHOLD` | `0.55` | Min rapidfuzz score to accept correction |
| `MAX_EDIT_DISTANCE` | `3` | Max Levenshtein distance for candidates |
| `RUSSIAN_MODEL_PATH` | _(empty)_ | Path to Russian trained model |
| `KAZAKH_MODEL_PATH` | _(empty)_ | Path to Kazakh trained model |
| `LOG_LEVEL` | `INFO` | Logging level |
| `BACKEND_PORT` | `8000` | Exposed backend port |
| `FRONTEND_PORT` | `3000` | Exposed frontend port |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn, Pydantic v2 |
| NLP | rapidfuzz (edit distance), custom rule-based detection |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Serving | nginx (production), Vite dev server (development) |
| Containerisation | Docker, docker-compose |

---

## License

Research and academic use. For institutional deployment contact the project team.

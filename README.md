# Document Intelligence

**AI-powered document processing agent** for extracting structured data from PDFs and images using Azure Document Intelligence (OCR) and Azure OpenAI, with automatic document-type detection and export.

---

## Overview

This project provides a complete document understanding pipeline with:

- **Streamlit Web UI** (Python, port 8501)
- **Azure Document Intelligence** (prebuilt-layout OCR)
- **Azure OpenAI** (GPT) for structured extraction
- **Multi-file upload** (PDF, PNG, JPG, JPEG)
- **Automatic document-type detection** (Proof of Residence, Proof of Income, Driver’s License, etc.)
- **Confidence scoring** from Document Intelligence
- **Export** (JSON per document, summary JSON, processing logs)
- **Dark mode** and progress indicators

---

## Features

- **Extract structured data** from text, PDFs, and images
- **Multi-file upload** – process multiple documents in one run
- **Document-type detection** – ProofOfResidence, ProofOfIncome, DriverLicense (front/back), Registration, Insurance, Odometer, and generic
- **Azure Document Intelligence** – layout-based OCR with word-level confidence
- **Confidence score** – built-in confidence from Document Intelligence in the output JSON
- **Azure OpenAI** – GPT-based normalization into structured JSON (any document type)
- **Driver’s license refinement** – optional GPT pass to clean license-number fields
- **Processing progress** – progress bar, percentage, and current file name
- **View JSON** – expandable JSON preview per document
- **Download** – per-document JSON, summary JSON, and processing logs
- **Dark mode** – sidebar toggle with readable sidebar and main content
- **Processing summary table** – document, status, detected type, JSON filename

---

## Architecture

### Project structure

```
Document_Extraction_Agent/
├── backend/
│   ├── main.py              # Streamlit app, upload, process, results UI
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Azure credentials (not in repo)
│   ├── .streamlit/
│   │   └── config.toml      # Toolbar (e.g. minimal), theme
│   ├── helpers/
│   │   ├── document_intel.py # Azure Document Intelligence (OCR + confidence)
│   │   ├── openai_mapper.py  # Azure OpenAI extraction → JSON
│   │   └── blob_utils.py     # Optional blob storage helpers
│   └── ui/
│       └── styles.css       # Custom UI (header, buttons, tables, dark mode)
└── README.md
```

### Flow

1. **Upload** – User selects one or more PDF/PNG/JPG/JPEG files.
2. **OCR** – Each file is sent to Azure Document Intelligence (prebuilt-layout); raw text and **confidence** are returned.
3. **Detect type** – Filename and OCR text are used to infer document type (e.g. ProofOfResidence, DriverLicense).
4. **Extract** – Azure OpenAI turns OCR text into structured JSON; Document Intelligence confidence is written into the output.
5. **Refine** (optional) – For driver’s licenses, a second GPT pass can clean license-number fields.
6. **Results** – User sees a summary table, per-document JSON preview/download, and optional summary + logs download.

---

## Quick start

### Prerequisites

- **Python 3.10+**
- **Azure Document Intelligence** resource (endpoint + API key)
- **Azure OpenAI** resource with a GPT deployment (endpoint, API key, API version, deployment name)

### Environment setup

1. Clone or open the repo and go to the backend:

   ```bash
   cd backend
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   # source venv/bin/activate   # macOS/Linux
   pip install -r requirements.txt
   ```

3. Create a `.env` file in `backend/` with:

   ```env
   DOCUMENTINTELLIGENCE_ENDPOINT=https://<your-di-resource>.cognitiveservices.azure.com/
   DOCUMENTINTELLIGENCE_API_KEY=<your-di-key>

   AZURE_OPENAI_ENDPOINT=https://<your-openai-resource>.openai.azure.com/
   AZURE_OPENAI_API_KEY=<your-openai-key>
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   AZURE_OPENAI_DEPLOYMENT=<your-gpt-deployment-name>
   ```

### Run the app

```bash
cd backend
streamlit run main.py
```

Open **http://localhost:8501** in your browser.

---

## Usage example

1. **Upload** – In “Upload Documents”, choose one or more files (PDF, PNG, JPG, JPEG). You can drag and drop or use “Browse files”.
2. **Process** – Click **Process Documents**. A progress section shows percentage, “Document X of Y”, and the current file name.
3. **Review** – When finished, the “Processed Documents & Results” section lists each document with:
   - **Download** – JSON for that document
   - **View JSON** – expandable preview of the extracted JSON
4. **Summary** – The processing summary table shows document name, status, detected type, and JSON filename.
5. **Downloads** – Use “Download Summary JSON” and “Download Logs” for the full run.

**Dark mode** – Use the “Dark mode” toggle in the sidebar to switch theme.

---

## Technology stack

| Layer        | Technology |
|-------------|------------|
| **UI**      | Streamlit 1.x (Python), custom CSS (light/dark) |
| **OCR**     | Azure Document Intelligence (Form Recognizer), prebuilt-layout |
| **Extraction** | Azure OpenAI (GPT-4), generic JSON schema |
| **Config**  | python-dotenv, `.env` |
| **Export**  | In-app JSON download (per document, summary, logs) |

---

## Key design principles

1. **Document-type agnostic** – One pipeline for many document types; type is detected from filename and content.
2. **Confidence from the source** – Confidence score in the output comes from Document Intelligence (word-level), not a separate model.
3. **Structured output** – All extracted data is normalized to JSON with consistent fields (DocumentType, ConfidenceScore, etc.).
4. **Optional refinement** – Driver’s license fields can be refined with a second GPT call for better accuracy.
5. **Local-first** – Processing runs in your environment; only Azure APIs are called (no mandatory cloud storage).

---

## Documentation

- **Setup** – See [Quick start](#quick-start) and the `.env` variables above.
- **Adding document types** – Extend `detect_document_type()` in `main.py` and adjust prompts in `helpers/openai_mapper.py` if needed.
- **Styling** – Edit `backend/ui/styles.css` and the dark-mode block in `main.py` for UI changes.

---

## License

MIT (or your chosen license).

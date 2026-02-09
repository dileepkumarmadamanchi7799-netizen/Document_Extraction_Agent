#main.py
import os 
import json
import base64
from io import BytesIO
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st

from helpers.document_intel import DocumentIntelligenceHelper as DocumentIntel
from helpers.openai_mapper import OpenAIMapper

# ==========================================================
#  Document Intelligence
#  ----------------------------------------------------------
#  AI-powered document processing Agent
# ==========================================================

# Load environment and initialize helpers
load_dotenv()
ocr = DocumentIntel()
mapper = OpenAIMapper()

# ==========================================================
#  Helper Class: Simple LogWriter (Local logging)
# ==========================================================
class LogWriter:
    """Simple local logging - writes to console and session state"""
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.logs = []

    def write_block(self, message: str):
        """Append a log message"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(log_entry)

    def log_event(self, header: str, details: dict, status: str = "", json_path: str = "", error: str = ""):
        """Create and append a formatted multi-line log block"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        block = [
            "=" * 58,
            f"[{timestamp}] {header}",
        ]
        for k, v in details.items():
            block.append(f"{k}: {v}")
        block.append("-" * 58)
        if status:
            block.append(f"Status: {status}")
        if json_path:
            block.append(f"JSON Path: {json_path}")
        if error:
            block.append(f"Error: {error}")
        block.append("=" * 58)
        log_message = "\n".join(block)
        self.logs.append(log_message)
        print(log_message)

    def get_all_logs(self) -> str:
        """Get all logs as a single string"""
        return "\n".join(self.logs)

# ------------------------------------------------------------
# Streamlit UI Setup
# ------------------------------------------------------------
st.set_page_config(page_title="Document Intelligence", layout="wide")

# Hide Streamlit Deploy button and main menu (inject first so it takes effect)
st.markdown("""
<style>
  /* Hide Deploy link (exact Streamlit deploy URL) and any Streamlit Cloud links */
  a[href="https://share.streamlit.io/deploy"],
  a[href*="share.streamlit.io/deploy"],
  a[href*="deploy"],
  a[href*="share.streamlit.io"],
  a[href*="cloud.streamlit.io"],
  header a,
  section[data-testid="stHeader"] a { display: none !important; visibility: hidden !important; width: 0 !important; height: 0 !important; overflow: hidden !important; }
  #MainMenu { visibility: hidden !important; }
  footer { visibility: hidden !important; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# Header Layout (no logo – title and subtitle only)
# ------------------------------------------------------------
st.markdown("""
<div class="header-container">
    <div class="header-text">
        <h1>Document Intelligence</h1>
        <p>AI-powered document processing Agent</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

st.sidebar.markdown("### Configuration")
st.sidebar.toggle("Dark mode", key="dark_mode", help="Switch to dark theme")
st.sidebar.markdown("**Mode:** Local File Processing")
st.sidebar.markdown("---")
st.sidebar.caption(
    "Upload documents to extract structured data. Supports PDF, PNG, JPG, and JPEG files. "
    "The system automatically detects document types and extracts key information."
)

# ------------------------------------------------------------
# Custom CSS (base + dark mode overrides when enabled)
# ------------------------------------------------------------
try:
    with open("ui/styles.css") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning(" Custom CSS not found; using default Streamlit style.")

if st.session_state.get("dark_mode", False):
    st.markdown("""
    <style>
      /* Dark mode – force light text everywhere so nothing appears black */
      body, [data-testid="stAppViewContainer"], .main .block-container { background: #0f172a !important; }
      [data-testid="stAppViewContainer"] { background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%) !important; }
      .stMarkdown, .stMarkdown p, [data-testid="stMarkdown"], .main p, .main span, .main label { color: #e2e8f0 !important; }
      h1, h2, h3 { color: #f1f5f9 !important; }
      .header-container { background: linear-gradient(135deg, rgba(15, 118, 110, 0.25) 0%, rgba(124, 58, 237, 0.2) 100%) !important; border-left-color: #14b8a6; }
      .header-text h1 { -webkit-text-fill-color: #f1f5f9; background: none !important; }
      .header-text p { color: #94a3b8 !important; }
      [data-testid="stSidebar"] { background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%) !important; }
      [data-testid="stSidebar"] * { color: #ffffff !important; }
      [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p, [data-testid="stSidebar"] div[data-testid="stMarkdown"], [data-testid="stSidebar"] strong { color: #ffffff !important; }
      [data-testid="stSidebar"] h3 { color: #67e8f9 !important; }
      [data-testid="stSidebar"] .stCaption { color: #cbd5e1 !important; }
      .stButton button { background: linear-gradient(135deg, #0d9488 0%, #0891b2 100%) !important; color: white !important; }
      .stDownloadButton button { background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%) !important; color: white !important; }
      .stJson { background: #1e293b !important; border-left-color: #7c3aed; color: #e2e8f0 !important; }
      div[data-testid="stExpander"] { background-color: transparent !important; }
      .stDataFrame, .stTable { color: #e2e8f0 !important; }
      th, td { background-color: #1e293b !important; color: #e2e8f0 !important; border-color: #334155 !important; }
      th { color: #f1f5f9 !important; }
      /* File uploader – all text white/light (drag-and-drop text, file limit, labels) */
      [data-testid="stFileUploader"], [data-testid="stFileUploader"] * { color: #f1f5f9 !important; }
      [data-testid="stFileUploader"] { background: #1e293b !important; border-radius: 12px; }
      [data-testid="stFileUploader"] section { background: #334155 !important; color: #f1f5f9 !important; }
      [data-testid="stFileUploader"] span, [data-testid="stFileUploader"] p, [data-testid="stFileUploader"] label { color: #f1f5f9 !important; }
      .stProgressBar > div > div { background: linear-gradient(90deg, #0d9488, #7c3aed) !important; }
      .stSuccess, .stInfo, .stWarning, .stError { background-color: #1e293b !important; color: #e2e8f0 !important; }
      /* Captions, small labels, and any remaining dark text */
      .stCaption, [data-testid="stCaption"], small { color: #cbd5e1 !important; }
      label, [role="button"] span { color: #e2e8f0 !important; }
      /* Browse files button – dark background, white text (was white bg + black text) */
      [data-testid="stFileUploader"] button, [data-testid="stFileUploader"] [role="button"],
      [data-testid="stFileUploader"] a { background: #334155 !important; color: #f1f5f9 !important; border-color: #475569 !important; }
      [data-testid="stFileUploader"] button:hover, [data-testid="stFileUploader"] [role="button"]:hover { background: #475569 !important; color: white !important; }
      /* Dark mode toggle – force dark background on entire row so text and track are readable */
      [data-testid="stSidebar"] [data-testid="stCheckbox"],
      [data-testid="stSidebar"] [data-testid="stCheckbox"] label { background: #1e293b !important; border: none !important; }
      [data-testid="stSidebar"] [data-testid="stCheckbox"] label,
      [data-testid="stSidebar"] [data-testid="stCheckbox"] label span,
      [data-testid="stSidebar"] [data-testid="stCheckbox"] label > div { color: #ffffff !important; background: #1e293b !important; }
      [data-testid="stSidebar"] label { color: #f1f5f9 !important; }
      /* Track = pill, keep dark; thumb = only element that’s light */
      [data-testid="stSidebar"] [data-testid="stCheckbox"] label > div:last-of-type { background: #334155 !important; border-radius: 999px !important; min-width: 44px !important; }
      [data-testid="stSidebar"] [data-testid="stCheckbox"] label > div:last-of-type > div { background: #ffffff !important; color: #0f172a !important; border-radius: 50% !important; box-shadow: 0 1px 3px rgba(0,0,0,0.5) !important; }
      [data-testid="stSidebar"] [data-testid="stCheckbox"] label > div:last-of-type > div * { color: #0f172a !important; }
      [data-testid="stSidebar"] [data-testid="stCheckbox"] label > div:last-of-type > div[style*="translateX"] { background: #14b8a6 !important; color: #fff !important; }
      [data-testid="stSidebar"] [data-testid="stCheckbox"] label > div:last-of-type > div[style*="translateX"] * { color: #fff !important; }
      [data-testid="stSidebar"] [data-testid="stCheckbox"] input { opacity: 0 !important; position: absolute !important; }
      /* Fallback: force track (pill) dark via any div that has a single child div = thumb */
      [data-testid="stSidebar"] [data-testid="stCheckbox"] [data-baseweb="checkbox"] > div { background: #1e293b !important; color: #ffffff !important; }
      [data-testid="stSidebar"] [data-testid="stCheckbox"] [data-baseweb="checkbox"] > div:last-child { background: #334155 !important; border-radius: 999px !important; }
      [data-testid="stSidebar"] [data-testid="stCheckbox"] [data-baseweb="checkbox"] > div:last-child > div { background: #ffffff !important; }
      [data-testid="stSidebar"] [data-testid="stCheckbox"] [data-baseweb="checkbox"] > div:last-child > div[style*="translateX"] { background: #14b8a6 !important; }
      /* Expander (View JSON) – header and content light */
      [data-testid="stExpander"] { background: #1e293b !important; border: 1px solid #334155 !important; border-radius: 8px !important; }
      [data-testid="stExpander"] summary, [data-testid="stExpander"] summary * { color: #f1f5f9 !important; background: transparent !important; }
      [data-testid="stExpander"] div { color: #e2e8f0 !important; }
      /* Current file / status info text */
      [data-testid="stAlert"] { color: #e2e8f0 !important; }
      [data-testid="stAlert"] * { color: inherit !important; }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------
# Helper: License Number Cleanup
# ------------------------------------------------------------
def refine_license_fields(openai_client, deployment, json_data: dict, raw_text: str, log_callback=None) -> dict:
    """Refine driver's license LicenseNumber dynamically using GPT with OCR context."""
    doc_type = json_data.get("DocumentType", "").lower().replace(" ", "")
    if "driverlicense" not in doc_type:
        return json_data

    prompt = f"""
    You are a normalization expert for OCR-extracted U.S. driver's license data.

    Raw OCR text:
    ---
    {raw_text}
    ---

    JSON extracted by OCR:
    {json.dumps(json_data, indent=2)}

    Refine the JSON:
    - Remove prefixes like ID, DL, LIC, or 10/01/11 unless clearly part of ID.
    - Keep real IDs like "S1234567", "WDL123456".
    - If both front and back sides are detected, merge fields logically.
    - Return valid JSON only.
    """

    try:
        response = openai_client.chat.completions.create(
            model=deployment,
            temperature=0.1,
            max_tokens=700,
            messages=[
                {"role": "system", "content": "You are a precision data normalizer for identification documents."},
                {"role": "user", "content": prompt.strip()},
            ],
        )
        cleaned_text = response.choices[0].message.content.strip()
        refined = json.loads(cleaned_text.split("```")[-1].strip()) if "```" in cleaned_text else json.loads(cleaned_text)
        if log_callback:
            log_callback("License refinement applied successfully.")
        return refined
    except Exception as e:
        if log_callback:
            log_callback(f"License refinement failed: {e}")
        return json_data

# ------------------------------------------------------------
# Helper: Hybrid document-type detection
# ------------------------------------------------------------
def detect_document_type(filename: str, text: str, all_files: list = None) -> str:
    """Hybrid detection using filename and OCR text for Title, POR, POI, and other document types."""
    name = filename.lower().replace("_", "").replace("-", "").replace(" ", "")
    text_lower = text.lower()

    # --- Filename-based detection ---
    if any(k in name for k in ["por", "proofres", "residenceproof", "addressproof", "utilitybill", "lease", "proofresidence"]):
        return "ProofOfResidence"
    elif any(k in name for k in ["poi", "proofincome", "incomeproof", "incomecertificate", "paystub", "salaryslip", "ssa", "wages", "earnings", "income"]):
        return "ProofOfIncome"
    elif any(k in name for k in ["title", "certificateoftitle", "vehicletitle", "ownershiptitle"]):
        return "Title"
    elif any(k in name for k in ["insurance", "policy", "plan", "coverage", "cobra"]):
        return "Insurance"
    elif any(k in name for k in ["dl", "driverlicense", "driver"]):
        if "front" in name:
            return "DriverLicense - Front Side"
        elif "back" in name:
            return "DriverLicense - Back Side"
        if all_files:
            dl_count = sum(1 for f in all_files if any(k in f.lower() for k in ["driverlicense", "dl", "driver"]))
            if dl_count == 1:
                if any(k in text_lower for k in ["date of birth", "dob", "sex", "height", "weight", "eye", "class", "address", "expiration", "issue date"]):
                    return "DriverLicense - Front Side"
                elif any(k in text_lower for k in ["dmv", "barcode", "organ donor", "address change", "endorsement", "back", "restrictions"]):
                    return "DriverLicense - Back Side"
                return "DriverLicense - Front Side"
        return "DriverLicense"
    elif any(k in name for k in ["reg", "registration"]):
        return "Registration"
    elif any(k in name for k in ["odo", "odometer", "mileage"]):
        return "Odometer"
    elif any(k in name for k in ["reference", "references", "ref", "personalref", "characterref", "employerref"]):
        return "References"

    # --- Text-based fallback ---
    if "driver" in text_lower and "license" in text_lower:
        if "back" in text_lower:
            return "DriverLicense - Back Side"
        elif "front" in text_lower:
            return "DriverLicense - Front Side"
        return "DriverLicense"

    if any(k in text_lower for k in [
        "certificate of title", "vehicle title", "title and identification", "lienholder", "ownership", "odometer reading"
    ]):
        return "Title"

    if any(k in text_lower for k in [
        "pay period", "net income", "gross income", "employer", "employee",
        "earnings", "pay date", "compensation", "deductions", "social security", "ssa"
    ]):
        if any(r in text_lower for r in [
            "address", "lease agreement", "residence", "utility service", "proof of residence",
            "proof of address", "water bill", "gas bill"
        ]):
            return "ProofOfResidence"
        return "ProofOfIncome"

    elif any(k in text_lower for k in [
        "utility", "lease", "resident", "residence", "tenant", "service address",
        "payment due", "bill to", "provider", "amount due", "proof of residence", "proof of address"
    ]):
        return "ProofOfResidence"

    elif any(k in text_lower for k in ["policy", "premium", "plan", "coverage", "expiration date", "effective date"]):
        return "Insurance"

    elif "registration" in text_lower:
        return "Registration"

    elif "odometer" in text_lower or "mileage" in text_lower:
        return "Odometer"

    elif any(k in text_lower for k in [
        "reference", "personal reference", "character reference", "employer reference",
        "contact person", "emergency contact", "reference name", "referee", "guarantor"
    ]):
        return "References"

    return "Generic"

# ------------------------------------------------------------
# File Upload Section
# ------------------------------------------------------------
st.header("📄 Upload Documents")

# Initialize session state (must be before file_uploader uses uploader_key)
if "processing_done" not in st.session_state:
    st.session_state.processing_done = False
if "generated_jsons" not in st.session_state:
    st.session_state.generated_jsons = {}
if "results_summary" not in st.session_state:
    st.session_state.results_summary = []
if "processing_logs" not in st.session_state:
    st.session_state.processing_logs = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "processed_file_names" not in st.session_state:
    st.session_state.processed_file_names = set()

uploaded_files = st.file_uploader(
    "Choose files to process",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True,
    key=f"file_uploader_{st.session_state.uploader_key}",
    help="Upload one or more documents (PDF, PNG, JPG, JPEG). The system will automatically detect document types and extract structured data."
)

# Clear old results if new files are uploaded (different from previously processed files)
# Only clear if processing is done (to avoid clearing during processing or after rerun)
if uploaded_files and st.session_state.get("processing_done", False):
    current_file_names = {f.name for f in uploaded_files}
    if current_file_names != st.session_state.processed_file_names:
        # New files detected - clear old results
        st.session_state.generated_jsons = {}
        st.session_state.results_summary = []
        st.session_state.processing_done = False
        st.session_state.processing_logs = []

# ------------------------------------------------------------
# Process Files Button
# ------------------------------------------------------------
if uploaded_files and st.button("🚀 Process Documents", key="btn_process", use_container_width=True):
    st.session_state.results_summary = []
    st.session_state.generated_jsons = {}
    st.session_state.processing_done = False
    st.session_state.processing_logs = []

    results_summary = []
    generated_jsons = {}
    num_files = len(uploaded_files)

    # Create a logger for this session
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger = LogWriter(session_id)
    st.session_state.processing_logs = logger

    # Visible progress UI (like a download: bar + percentage + current file)
    with st.status("⏳ **Processing your documents...**", state="running", expanded=True) as progress_status:
        progress_bar = st.progress(0, text="Starting...")
        progress_caption = st.empty()
        current_doc_placeholder = st.empty()

    # Get all filenames for document type detection
    all_filenames = [f.name for f in uploaded_files]

    for i, uploaded_file in enumerate(uploaded_files):
        doc_name = uploaded_file.name
        current = i + 1
        # Keep progress under 100% until we're loading results (see after loop)
        progress_pct = 0.9 * (current / num_files)  # 0% to 90% during processing
        pct = int(100 * progress_pct)

        # Update progress UI so user clearly sees how much is done
        progress_bar.progress(progress_pct, text=f"{pct}% complete")
        progress_caption.caption(f"**Document {current} of {num_files}**")
        current_doc_placeholder.info(f"📄 **Current file:** {doc_name}")

        logger.write_block(f"\nProcessing document: {doc_name}")

        try:
            # Read file data
            data = uploaded_file.read()
            
            # Process with OCR
            ocr.log_callback = logger.write_block
            ocr_result = ocr.analyze_document(data)
            text_raw = ocr_result.get("text", "")

            if isinstance(text_raw, bytes):
                try:
                    text = text_raw.decode("utf-8", errors="ignore")
                except Exception:
                    text = ""
            else:
                text = str(text_raw).encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

            # Detect document type
            detected_type = detect_document_type(doc_name, text, all_files=all_filenames)

            def log_callback(msg):
                logger.write_block(f"[Mapper] {msg}")

            mapper.log_callback = log_callback

            # Normalize text (document_intel returns text + confidence from Document Intelligence)
            doc_confidence = ocr_result.get("confidence", 0.0)
            normalized = mapper.normalize_text(text, doc_type=detected_type, confidence=doc_confidence)

            # Refine license fields if needed
            if "driverlicense" in normalized.get("DocumentType", "").lower().replace(" ", ""):
                normalized = refine_license_fields(mapper.client, mapper.deployment, normalized, text, log_callback)

            # Add metadata
            normalized["RawData"] = {"text": text, "filename": doc_name}
            normalized["ProcessedDate"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Generate JSON (ensure_ascii=False preserves Unicode characters like £, €, etc.)
            json_name = f"{Path(doc_name).stem}.json"
            json_bytes = json.dumps(normalized, indent=2, default=str, ensure_ascii=False).encode("utf-8")

            generated_jsons[json_name] = {
                "bytes": json_bytes,
                "doc_name": doc_name,
                "data": data,
                "detected_type": detected_type,
                "normalized": normalized,
            }

            logger.log_event(
                header="DOCUMENT PROCESSED",
                details={
                    "Document": doc_name,
                    "Detected Type": detected_type,
                    "File Size": f"{len(data) / 1024:.2f} KB",
                },
                status="SUCCESS",
                json_path=json_name,
            )

            st.success(f"✅ {doc_name} processed successfully (Type: {detected_type})")
            results_summary.append({
                "document": doc_name,
                "status": "success",
                "detected_type": detected_type,
                "json_file": json_name
            })

        except Exception as e:
            logger.log_event(
                header="DOCUMENT PROCESSED",
                details={"Document": doc_name},
                status="ERROR",
                error=str(e),
            )
            st.error(f"❌ Error processing {doc_name}: {str(e)}")
            results_summary.append({
                "document": doc_name,
                "status": "error",
                "error": str(e)
            })

    # Show "Complete! Loading results..." so 100% clearly means output is coming
    progress_bar.progress(1.0, text="Complete! Loading results...")
    progress_caption.caption("Saving results and loading your output...")
    current_doc_placeholder.success("✓ Processing finished. Loading your results...")

    st.session_state.results_summary = results_summary
    st.session_state.generated_jsons = generated_jsons
    st.session_state.processing_done = True
    st.session_state.processing_logs = logger
    # Track which files were processed
    st.session_state.processed_file_names = {f.name for f in uploaded_files}
    # Clear file uploader by incrementing the key (forces widget reset)
    st.session_state.uploader_key += 1
    st.success(f"✨ All {len(uploaded_files)} file(s) processed successfully!")
    # Force rerun to clear the file uploader
    st.rerun()

# ------------------------------------------------------------
# Display Results
# ------------------------------------------------------------
if st.session_state.get("processing_done") and st.session_state.generated_jsons:
    st.markdown("---")
    st.subheader("📂 Processed Documents & Results")
    
    # Display documents one at a time (single column layout)
    for i, (json_name, content) in enumerate(st.session_state.generated_jsons.items()):
        doc_name = content["doc_name"]
        data = content["data"]
        detected_type = content.get("detected_type", "Unknown")
        
        # Create a container for each document
        with st.container():
            st.markdown(f"### {doc_name}")
            st.caption(f"Type: {detected_type}")
            
            # Display preview - only once per document
            if doc_name.lower().endswith((".png", ".jpg", ".jpeg")):
                st.image(data, caption=doc_name, use_container_width=True)
            elif doc_name.lower().endswith(".pdf"):
                # Display PDF using iframe (single view)
                pdf_base64 = base64.b64encode(data).decode("utf-8")
                st.markdown(
                    f"""
                    <iframe src="data:application/pdf;base64,{pdf_base64}#toolbar=1&navpanes=0&scrollbar=1&page=1&zoom=page-fit"
                            width="100%" height="400"
                            style="border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,0.1);"></iframe>
                    """,
                    unsafe_allow_html=True,
                )
            
            # Download JSON button
            col1, col2 = st.columns([1, 1])
            with col1:
                st.download_button(
                    label=f"⬇️ Download {json_name}",
                    data=BytesIO(content["bytes"]),
                    file_name=json_name,
                    mime="application/json",
                    key=f"download_{json_name}_{i}",
                    use_container_width=True,
                )
            
            # Show JSON preview in expander
            with st.expander(f"📋 View JSON for {doc_name}"):
                st.json(content["normalized"])
            
            st.markdown("---")

    st.markdown("---")
    st.subheader("📊 Processing Summary")
    st.table(st.session_state.results_summary)
    
    # Download summary
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    summary_json = json.dumps(st.session_state.results_summary, indent=2, ensure_ascii=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Summary JSON",
        data=BytesIO(summary_json),
        file_name=f"Document_Summary_{timestamp}.json",
        mime="application/json",
        key="btn_download_summary",
        use_container_width=True,
    )
    
    # Download all JSONs as zip (optional - using individual downloads for simplicity)
    st.markdown("---")
    st.subheader("📝 Processing Logs")
    if st.session_state.processing_logs:
        logs_text = st.session_state.processing_logs.get_all_logs()
        st.text_area("Logs", logs_text, height=200, key="logs_display")
        st.download_button(
            label="⬇️ Download Logs",
            data=logs_text.encode("utf-8"),
            file_name=f"Document_Logs_{timestamp}.txt",
            mime="text/plain",
            key="btn_download_logs",
        )

import os
import time
from dotenv import load_dotenv
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

# ==========================================================
#  Azure Document Intelligence (Layout-based OCR)
#  ----------------------------------------------------------
#  - Extracts text from any document (image or PDF)
#  - No prebuilt models or assumptions (pure OCR)
#  - Returns full raw text + page-level metadata
# ==========================================================

load_dotenv()


class DocumentIntelligenceHelper:
    """Handles OCR text extraction using Azure Document Intelligence (Layout model)."""

    def __init__(self):
        endpoint = os.getenv("DOCUMENTINTELLIGENCE_ENDPOINT")
        key = os.getenv("DOCUMENTINTELLIGENCE_API_KEY")

        if not endpoint or not key:
            raise ValueError(
                "DOCUMENTINTELLIGENCE_ENDPOINT or DOCUMENTINTELLIGENCE_API_KEY not found in .env"
            )

        self.client = DocumentAnalysisClient(
            endpoint=endpoint, credential=AzureKeyCredential(key)
        )
        self.log_callback = None  # dynamically set in main.py

    # ------------------------------------------------------
    # 1️. Analyze any document (layout model)
    # ------------------------------------------------------
    def analyze_document(self, document_bytes: bytes) -> dict:
        """
        Performs OCR using Azure Document Intelligence (prebuilt-layout).
        Extracts lines of text, paragraph blocks, and page metadata.
        Returns:
            {
              "text": "<full_text>",
              "pages": <int>,
              "language": "<detected_language>",
              "analyzedOn": "<timestamp>",
              "confidence": <float 0-1 from Document Intelligence word-level confidence>
            }
        """
        if self.log_callback:
            self.log_callback("Submitting document to Azure Document Intelligence (layout model)...")

        try:
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-layout", document=document_bytes
            )
            result = poller.result()
            if self.log_callback:
                self.log_callback("Layout analysis completed successfully.")
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"OCR analysis failed: {e}")
            raise

        # Collect all lines and word-level confidence (Document Intelligence built-in)
        full_text_lines = []
        word_confidences = []
        for page_idx, page in enumerate(result.pages, start=1):
            page_text = " ".join([line.content for line in page.lines])
            full_text_lines.append(page_text)
            if getattr(page, "words", None):
                for word in page.words:
                    c = getattr(word, "confidence", None)
                    if c is not None:
                        word_confidences.append(float(c))

        # Join pages into one full text block
        full_text = "\n".join(full_text_lines).strip()

        # Overall confidence = average of Document Intelligence word confidences (0–1)
        confidence = (
            round(sum(word_confidences) / len(word_confidences), 4)
            if word_confidences
            else 0.0
        )

        # Build structured response
        response = {
            "text": full_text,
            "pages": len(result.pages),
            "language": getattr(result, "detected_languages", ["en"])[0],
            "analyzedOn": time.strftime("%Y-%m-%d %H:%M:%S"),
            "confidence": confidence,
        }

        if self.log_callback:
            self.log_callback(f"Extracted {len(full_text_lines)} pages of text.")
            self.log_callback(f"Document Intelligence confidence: {confidence}")
        return response

    # ------------------------------------------------------
    # 2️. Simple text-only helper
    # ------------------------------------------------------
    def extract_text(self, document_bytes: bytes) -> str:
        """Quick utility to return plain text only."""
        try:
            poller = self.client.begin_analyze_document(
                model_id="prebuilt-layout", document=document_bytes
            )
            result = poller.result()
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Text extraction failed: {e}")
            raise

        all_text = " ".join([line.content for page in result.pages for line in page.lines])
        return all_text.strip()

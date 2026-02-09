# helpers/openai_mapper.py
import os
import json
import re
from dotenv import load_dotenv
from openai import AzureOpenAI
import openai

# ==========================================================
#  Azure OpenAI Mapper (Generic Document Intelligence Agent)
#  ----------------------------------------------------------
#  - Takes OCR key-value pairs or raw text from Document Intelligence
#  - Works with any document type (generic extraction)
#  - Extracts all relevant information and returns structured JSON
#  - Adapts to document content without requiring specific schemas
# ==========================================================

load_dotenv()

class OpenAIMapper:
    """Uses Azure OpenAI GPT-4.1 to analyze and structure OCR content into JSON."""

    def __init__(self):
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

        if not all([endpoint, api_key, api_version, deployment]):
            raise ValueError("Missing Azure OpenAI environment variables in .env")

        try:
            self.client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version,
            )
        except TypeError as e:
            if "proxies" in str(e):
                import httpx
                http_client = httpx.Client()
                self.client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    api_key=api_key,
                    api_version=api_version,
                    http_client=http_client,
                )
            else:
                raise e
        self.deployment = deployment
        self.log_callback = None  # Set dynamically by main.py

    # ------------------------------------------------------
    #  Helper: Extract odometer and trip readings accurately
    # ------------------------------------------------------
    def _extract_odometer_and_trip_values(self, text: str) -> dict:
        """
        Extracts odometer and trip readings accurately from OCR text.
        - Handles real trip readings (e.g. '68263 TM 2471.6 mi', 'Trip 123 031323 miles')
        - Ignores menu text like 'Trip Computer A/B'
        - Uses the *last* mileage marker for odometer
        - Automatically detects unit (miles/km)
        """
        if not text:
            return {}

        clean = re.sub(r"[,\t]+", " ", text.lower())
        clean = re.sub(r"\s{2,}", " ", clean).strip()

        # Detect unit
        unit = "km" if re.search(r"\bkm\b|\bkilometer", clean) else "miles"

        trip_val, odo_val = "", ""

        #  Detect true numeric trip readings (not menu labels)
        trip_match = re.search(r"(?:trip|tm)\s*[:\-]?\s*(\d+(?:\.\d+)?)\b", clean)
        if not trip_match:
            trip_match = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:tm|trip)\b", clean)
        if trip_match:
            # Filter out "Trip Computer", "Trip A/B", etc.
            snippet = clean[max(0, trip_match.start() - 10):trip_match.end() + 10]
            if not re.search(r"computer|trip\s*[ab]\b|info", snippet):
                trip_val = trip_match.group(1)

        #  Find the last mileage pattern (odometer)
        mileage_matches = list(
            re.finditer(r"(\d+(?:\.\d+)?)\s*(?:mi|mile|km|kilometer)s?", clean)
        )
        if mileage_matches:
            odo_val = mileage_matches[-1].group(1)
        else:
            # fallback: pick the largest numeric if no explicit unit
            nums = re.findall(r"\d+(?:\.\d+)?", clean)
            if nums:
                odo_val = max(nums, key=lambda x: float(x))

        #  Clean values
        if odo_val:
            odo_val = odo_val.rstrip("0").rstrip(".")
        if trip_val:
            trip_val = trip_val.rstrip("0").rstrip(".")

        result = {"OdometerReading": odo_val, "Unit": unit}
        if trip_val:
            result["TripReading"] = trip_val

        return result

    # ------------------------------------------------------
    # Normalize unstructured OCR text
    # ------------------------------------------------------
    def normalize_text(self, text: str, doc_type: str = "Generic", confidence: float = 0.0) -> dict:
        """Converts raw OCR text into structured JSON for any document type."""
        if not text or not text.strip():
            return {"error": "No text provided for normalization."}

        system_prompt = """
        You are an intelligent document data extraction agent. Your task is to analyze OCR-extracted text from 
        any document and extract all relevant information into a well-structured JSON format.
        
        Your approach should be:
        1. Analyze the document content to understand what type of information it contains
        2. Extract ONLY the data that is actually present in the document
        3. Structure the data logically with clear, descriptive field names
        4. Group related information together
        5. Handle multiple entities (people, items, transactions) by using arrays when appropriate
        6. Preserve important details and context
        
        CRITICAL RULES:
        - ONLY include fields that have actual data - DO NOT include empty arrays, empty objects, or null values
        - DO NOT create placeholder fields or empty containers for data that doesn't exist
        - The JSON structure should be dynamic and only contain what's actually found in the document
        - If a category of information doesn't exist in the document, don't include it at all
        
        Guidelines:
        - Use PascalCase or camelCase for field names (e.g., "FullName", "IssueDate", "AccountNumber")
        - Extract dates in a consistent format (prefer ISO format: YYYY-MM-DD or readable format)
        - Extract monetary amounts with currency symbols if present
        - Include addresses as structured objects or strings
        - If the document contains multiple similar items (e.g., multiple people, transactions, items), 
          create an array to store them
        - Include metadata like document numbers, reference numbers, barcodes, etc. ONLY if they exist
        - Return ONLY valid JSON - no markdown, no explanations, no code blocks
        """

        user_prompt = f"""
        Document Type (detected): {doc_type}
        
        OCR Extracted Text:
        -----------------------------
        {text}
        -----------------------------
        
        Analyze this document and extract all relevant information into a structured JSON format.
        
        Required fields:
        - DocumentType: "{doc_type}"
        - ConfidenceScore: {confidence:.2f}
        
        Extract and structure ONLY the information that is actually present in the document:
        - Personal information (names, addresses, contact details) - only if present
        - Dates (issue dates, expiration dates, birth dates, etc.) - only if present
        - Identification numbers (IDs, account numbers, policy numbers, license numbers, etc.) - only if present
        - Financial information (amounts, balances, payments, etc.) - only if present
        - Entity information (companies, organizations, institutions) - only if present
        - Metadata (document numbers, reference numbers, barcodes, etc.) - only if present
        - Any other important information specific to this document type - only if present
        
        IMPORTANT: 
        - Do NOT include empty arrays like [] or empty objects like {{}}
        - Do NOT include fields for categories that don't exist in the document
        - Only include fields that have actual extracted data
        - Structure the JSON dynamically based on what's actually found
        
        Structure the JSON in a logical way that makes sense for this document. Use nested objects 
        and arrays when appropriate to organize related information, but only if they contain data.
        
        Return ONLY valid JSON. Do not include markdown code blocks, explanations, or any text outside the JSON.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                max_completion_tokens=8000,
                messages=[
                    {"role": "system", "content": system_prompt.strip()},
                    {"role": "user", "content": user_prompt.strip()},
                ],
            )

            output_text = response.choices[0].message.content.strip()
            result_json = self._safe_parse_json(output_text)

            # Ensure DocumentType and ConfidenceScore are set
            if "DocumentType" not in result_json:
                result_json["DocumentType"] = doc_type
            if "ConfidenceScore" not in result_json:
                result_json["ConfidenceScore"] = confidence

            # Remove empty arrays, empty objects, and null values (but keep DocumentType and ConfidenceScore)
            # Store required fields temporarily
            doc_type_val = result_json.get("DocumentType", doc_type)
            conf_score_val = result_json.get("ConfidenceScore", confidence)
            result_json = self._clean_empty_fields(result_json)
            # Restore required fields
            result_json["DocumentType"] = doc_type_val
            result_json["ConfidenceScore"] = conf_score_val

            # Optional: Post-process odometer and trip readings if detected
            if "odometer" in doc_type.lower() or "odometer" in text.lower():
                readings = self._extract_odometer_and_trip_values(text)
                if readings.get("OdometerReading"):
                    result_json["OdometerReading"] = readings.get("OdometerReading")
                    result_json["Unit"] = readings.get("Unit", "miles")
                if readings.get("TripReading"):
                    result_json["TripReading"] = readings.get("TripReading")

            if self.log_callback:
                self.log_callback(f"normalize_text() succeeded for {doc_type}")
            return result_json

        except Exception as e:
            if self.log_callback:
                self.log_callback(f"normalize_text() failed: {e}")
            return {"error": "Text normalization failed", "message": str(e)}

    # ------------------------------------------------------
    # Utility: Clean empty fields from JSON
    # ------------------------------------------------------
    def _clean_empty_fields(self, obj):
        """Recursively remove empty arrays, empty objects, and null values from JSON."""
        if isinstance(obj, dict):
            cleaned = {}
            for key, value in obj.items():
                cleaned_value = self._clean_empty_fields(value)
                # Skip null values, empty lists, and empty dicts
                if cleaned_value is not None and cleaned_value != [] and cleaned_value != {}:
                    cleaned[key] = cleaned_value
            return cleaned
        elif isinstance(obj, list):
            cleaned = [self._clean_empty_fields(item) for item in obj]
            # Remove None, empty dicts, and empty lists from array
            cleaned = [item for item in cleaned if item is not None and item != {} and item != []]
            return cleaned if cleaned else None  # Return None if array becomes empty
        else:
            return obj

    # ------------------------------------------------------
    # Utility: Safe JSON parsing
    # ------------------------------------------------------
    def _safe_parse_json(self, text: str) -> dict:
        """Safely parse JSON from model output."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                cleaned = text.split("```")[-1].strip()
                return json.loads(cleaned)
            except Exception:
                if self.log_callback:
                    self.log_callback("Could not parse JSON output.")
                return {"error": "Invalid JSON returned from model."}

# Receipt Processing Web App

Upload receipt images, extract data via OCR, manually correct extracted fields, and save confirmed data to Google Sheets.

## Features

- **Receipt Upload**: Drag-and-drop or tap to upload receipt images (JPG/PNG, max 5MB)
- **AI-Powered OCR**: Gemini Vision API for intelligent text extraction with automatic fallback to Tesseract OCR
- **Smart Data Extraction**: AI paraphrasing for clarity, language detection (Indonesian/English), and structured output
- **Bilingual Support**: Automatic language detection with same-language paraphrasing (no unwanted translations)
- **Validation & Quality**: Business rule validation, confidence indicators (✓/⚠/✗), and hybrid confidence scoring
- **Manual Correction**: Review and correct extraction results before saving
- **Custom Column Mapping**: Configure which Google Sheets columns receive your data (A-ZZ range)
- **Google Sheets Integration**: Direct save to your Google Sheets spreadsheet via OAuth2
- **Quality Metrics**: Automatic tracking of extraction success rates and confidence distributions
- **Responsive UI**: Mobile-first design with optimized UX for phones, tablets, and desktops
- **Automatic Cleanup**: Receipt images deleted after 24 hours for privacy

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Jinja2
- **AI/ML**: Google Gemini Vision API (gemini-1.5-flash) for intelligent receipt extraction
- **OCR Fallback**: pytesseract + Pillow (automatic fallback when Gemini unavailable)
- **Integration**: gspread + google-auth (OAuth2)
- **Storage**: File system (24-hour TTL for images, JSON for metrics)
- **Testing**: pytest, pytest-asyncio, pytest-cov (80% coverage target)

## Prerequisites

- Python 3.11 or higher
- Tesseract OCR (`brew install tesseract` on macOS or `apt-get install tesseract-ocr` on Linux)
- Google Cloud project with Sheets API enabled and OAuth2 credentials
- **Gemini API key** from [Google AI Studio](https://makersuite.google.com/app/apikey) (free tier: 15 req/min, 1500 req/day)

## Setup Instructions

### 1. Clone Repository

```bash
git clone <repository-url>
cd receipt-input-app
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Google OAuth2

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Sheets API:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Google Sheets API"
   - Click "Enable"
4. Create OAuth2 credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client ID"
   - Set Application Type to "Web application"
   - Add Authorized Redirect URI: `http://localhost:8000/api/v1/auth/callback`
   - Copy Client ID and Client Secret

### 5. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and set:

```
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
SECRET_KEY=your-random-secret-key  # Generate: python -c "import secrets; print(secrets.token_hex(32))"
REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
UPLOAD_DIR=shared/uploads
MAX_FILE_SIZE_MB=5

# Gemini Vision API Configuration (NEW)
GEMINI_API_KEY=your-gemini-api-key-here
```

**Getting a Gemini API Key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key" (requires Google account)
3. Copy the generated key
4. Paste it into `.env` as `GEMINI_API_KEY=...`

**Note**: The app will automatically fall back to Tesseract OCR if Gemini API is unavailable or rate-limited.

### 6. Run Application

**Option 1: With activated virtual environment**
```bash
# Make sure venv is activated first (see step 2)
uvicorn frontend.src.main:app --reload --port 8000
```

**Option 2: Direct venv execution (no activation needed)**
```bash
./venv/bin/uvicorn frontend.src.main:app --reload --port 8000  # macOS/Linux
# OR
venv\Scripts\uvicorn frontend.src.main:app --reload --port 8000  # Windows
```

Navigate to: `http://localhost:8000`

## Usage Guide

### 1. Connect to Google Sheets

1. Click **"Connect to Google Sheets"** in the navigation bar
2. Sign in with your Google account
3. Grant permissions for Google Sheets access
4. Enter your **Spreadsheet ID** (from the Google Sheets URL)
5. Enter your **Sheet Tab Name** (e.g., "Expenses 2025")
6. Click **"Save Preferences"**

### 2. Configure Column Mappings

1. Navigate to **"Configure Columns"** page
2. Specify which columns should receive your data:
   - **Date Column**: Column for transaction date (e.g., "A")
   - **Description Column**: Column for items/description (e.g., "B")
   - **Price Column**: Column for total amount (e.g., "C")
3. Columns must be in A-ZZ range (supports up to 702 columns)
4. You can map multiple fields to the same column (values will be concatenated with " | ")
5. Click **"Save Column Mappings"**

**Note**: Column mapping configuration is required before you can process receipts.

### 3. Upload Receipt

1. Go to the homepage (`/`)
2. **Desktop**: Drag and drop receipt image into the upload area
3. **Mobile**: Tap to select receipt image from your device
4. Wait for OCR processing (completes in <5 seconds)

### 4. Review & Correct Data

1. Review the automatically extracted fields:
   - Transaction Date
   - Items (semicolon-delimited list)
   - Total Amount
2. Correct any errors or fill in missing data
3. Confidence indicators show OCR accuracy:
   - ✓ (green): High confidence
   - ⚠ (yellow): Medium confidence
   - ✗ (red): Low confidence

### 5. Save to Google Sheets

1. Click **"Save to Google Sheets"**
2. Data is written to your configured columns:
   - Transaction Date (YYYY-MM-DD) → Your specified date column
   - Items (semicolon-delimited) → Your specified description column
   - Total Amount (decimal) → Your specified price column
   - Uploaded At (ISO 8601 timestamp) → Included in row
3. Receipt image is automatically deleted after successful save

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage Report

```bash
pytest --cov=backend/src --cov=frontend/src --cov-report=term-missing --cov-fail-under=80
```

### Run Specific Test Types

```bash
# Contract tests only
pytest -m contract

# Integration tests only
pytest -m integration

# Unit tests only
pytest -m unit
```

## API Response Format

The enhanced receipt extraction API now returns detailed extraction metadata:

```json
{
  "receipt_id": "550e8400-e29b-41d4-a716-446655440000",
  "extracted_data": {
    "transaction_date": "2025-10-06",
    "transaction_date_confidence": 0.95,
    "items": "Nasi Goreng (2 porsi); Es Teh Manis",
    "items_confidence": 0.92,
    "total_amount": 50000,
    "total_amount_confidence": 0.98,
    "extraction_method": "gemini",
    "detected_language": "id",
    "currency": "IDR",
    "paraphrased": true,
    "confidence_indicators": {
      "date": "✓",
      "items": "✓",
      "amount": "✓"
    }
  },
  "validation": {
    "date_valid": true,
    "price_valid": true,
    "items_valid": true,
    "warnings": []
  },
  "processing_time_ms": 3200
}
```

**Key Enhancements:**
- `extraction_method`: Shows whether Gemini or Tesseract fallback was used
- `detected_language`: Auto-detected language ("id" or "en")
- `currency`: Detected currency code (e.g., "IDR", "USD")
- `paraphrased`: Indicates if items were AI-paraphrased for clarity
- `confidence_indicators`: Visual indicators (✓/⚠/✗) for each field
- `validation`: Business rule validation results with warnings

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `command not found: uvicorn` | Activate virtual environment (`source venv/bin/activate`) or use `./venv/bin/uvicorn` directly |
| `ModuleNotFoundError: pytesseract` | Install dependencies: `pip install -r requirements.txt` (make sure venv is activated) |
| `TesseractNotFoundError` | Install Tesseract OCR: `brew install tesseract` (macOS) or `apt-get install tesseract-ocr` (Linux) |
| **`GEMINI_API_KEY not set`** | **Add Gemini API key to `.env` file (see setup step 5)** |
| **`429 Rate Limit Exceeded`** | **Gemini free tier limit reached (15/min). App automatically falls back to Tesseract** |
| **All extractions show `tesseract_fallback`** | **Check Gemini API key validity, verify internet connection, or check Google AI Studio console for API status** |
| OAuth2 redirect fails | Verify `REDIRECT_URI` matches Google Cloud Console OAuth2 settings exactly |
| "Error GS-403" on save | Check Google Sheets permissions - ensure you have edit access to the spreadsheet |
| "Column mappings required" error | Configure column mappings first via "Configure Columns" page before processing receipts |
| OCR returns empty results | Check image quality - ensure receipt text is visible and high-contrast |
| Session expired error | Token expired after 7 days - click "Reconnect" to re-authenticate |
| **Low confidence scores** | **Image quality may be poor (blurry, low contrast). Try re-photographing the receipt with better lighting** |

## Deployment

### Local Development

```bash
# Option 1: With activated venv
source venv/bin/activate
uvicorn frontend.src.main:app --reload --port 8000

# Option 2: Direct execution
./venv/bin/uvicorn frontend.src.main:app --reload --port 8000
```

### Production (Render)

1. Create new Web Service on [Render](https://render.com/)
2. Connect to your Git repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn frontend.src.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env` file
6. Update `REDIRECT_URI` to your production domain

## Architecture

```
receipt-input-app/
├── backend/
│   ├── src/
│   │   ├── api/v1/          # REST API endpoints
│   │   ├── services/        # OCR, parser, sheets, cleanup
│   │   ├── models/          # Data models
│   │   └── storage/         # File storage
│   └── tests/
│       ├── contract/        # API contract tests
│       ├── integration/     # End-to-end tests
│       └── unit/            # Unit tests
├── frontend/
│   ├── src/
│   │   ├── templates/       # Jinja2 HTML templates
│   │   ├── static/          # CSS and JavaScript
│   │   └── main.py          # FastAPI app entry point
└── shared/
    └── uploads/             # Temporary receipt storage (24-hour TTL)
```

## API Endpoints

### Receipt Processing
- `POST /api/v1/upload` - Upload receipt for OCR processing
- `POST /api/v1/save` - Save confirmed data to Google Sheets

### Authentication
- `GET /api/v1/auth/login` - Initiate OAuth2 flow
- `GET /api/v1/auth/callback` - Handle OAuth2 callback
- `POST /api/v1/auth/setup` - Save spreadsheet preferences
- `GET /api/v1/auth/status` - Check authentication status

### Column Configuration
- `GET /api/v1/column-config` - Retrieve current column mappings
- `POST /api/v1/column-config` - Save column mappings configuration
- `POST /api/v1/column-config/validate` - Validate single column reference

See API specifications in:
- [Feature 001 Contracts](specs/001-feature-receipt-processing/contracts/) - Receipt processing endpoints
- [Feature 002 Contracts](specs/002-feature-select-column/contracts/) - Column configuration endpoints

## License

MIT License - See LICENSE file for details

## Support

For issues and feature requests, please create an issue in the GitHub repository.

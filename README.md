# Receipt Processing Web App

Upload receipt images, extract data via OCR, manually correct extracted fields, and save confirmed data to Google Sheets.

## Features

- **Receipt Upload**: Drag-and-drop or tap to upload receipt images (JPG/PNG, max 5MB)
- **OCR Processing**: Automatic text extraction using Tesseract OCR
- **Data Extraction**: Intelligent parsing of transaction date, items, and total amount
- **Manual Correction**: Review and correct OCR results before saving
- **Google Sheets Integration**: Direct save to your Google Sheets spreadsheet via OAuth2
- **Responsive UI**: Mobile-first design with optimized UX for phones, tablets, and desktops
- **Automatic Cleanup**: Receipt images deleted after 24 hours for privacy

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Jinja2
- **OCR**: pytesseract + Pillow
- **Integration**: gspread + google-auth (OAuth2)
- **Storage**: File system (24-hour TTL)
- **Testing**: pytest, pytest-asyncio, pytest-cov (80% coverage)

## Prerequisites

- Python 3.11 or higher
- Tesseract OCR (`brew install tesseract` on macOS or `apt-get install tesseract-ocr` on Linux)
- Google Cloud project with Sheets API enabled and OAuth2 credentials

## Setup Instructions

### 1. Clone Repository

```bash
git clone <repository-url>
cd receipt-input-app
git checkout 001-feature-receipt-processing
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Google OAuth2

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

### 4. Configure Environment Variables

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
```

### 5. Run Application

```bash
uvicorn frontend.src.main:app --reload --port 8000
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

### 2. Upload Receipt

1. Go to the homepage (`/`)
2. **Desktop**: Drag and drop receipt image into the upload area
3. **Mobile**: Tap to select receipt image from your device
4. Wait for OCR processing (completes in <5 seconds)

### 3. Review & Correct Data

1. Review the automatically extracted fields:
   - Transaction Date
   - Items (semicolon-delimited list)
   - Total Amount
2. Correct any errors or fill in missing data
3. Confidence indicators show OCR accuracy:
   - ✓ (green): High confidence
   - ⚠ (yellow): Medium confidence
   - ✗ (red): Low confidence

### 4. Save to Google Sheets

1. Click **"Save to Google Sheets"**
2. Data is appended as a new row with:
   - Transaction Date (YYYY-MM-DD)
   - Items (semicolon-delimited)
   - Total Amount (decimal)
   - Uploaded At (ISO 8601 timestamp)
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

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: pytesseract` | Install dependencies: `pip install -r requirements.txt` |
| `TesseractNotFoundError` | Install Tesseract OCR: `brew install tesseract` (macOS) or `apt-get install tesseract-ocr` (Linux) |
| OAuth2 redirect fails | Verify `REDIRECT_URI` matches Google Cloud Console OAuth2 settings exactly |
| "Error GS-403" on save | Check Google Sheets permissions - ensure you have edit access to the spreadsheet |
| OCR returns empty results | Check image quality - ensure receipt text is visible and high-contrast |
| Session expired error | Token expired after 7 days - click "Reconnect" to re-authenticate |

## Deployment

### Local Development

```bash
uvicorn frontend.src.main:app --reload --port 8000
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

- `POST /api/v1/upload` - Upload receipt for OCR processing
- `POST /api/v1/save` - Save confirmed data to Google Sheets
- `GET /api/v1/auth/login` - Initiate OAuth2 flow
- `GET /api/v1/auth/callback` - Handle OAuth2 callback
- `POST /api/v1/auth/setup` - Save spreadsheet preferences
- `GET /api/v1/auth/status` - Check authentication status

See [contracts/](specs/001-feature-receipt-processing/contracts/) for full API specifications.

## License

MIT License - See LICENSE file for details

## Support

For issues and feature requests, please create an issue in the GitHub repository.

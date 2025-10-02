# Setup Complete! 🎉

Your Receipt Processing Web App environment is now ready!

## ✅ What's Been Installed

1. **Virtual Environment**: Created at `venv/`
2. **Python Dependencies**: All packages installed (FastAPI, pytesseract, gspread, etc.)
3. **Tesseract OCR**: Version 5.5.1 installed via Homebrew

## 📋 Next Steps to Run the Application

### Step 1: Activate Virtual Environment

Every time you work on this project, activate the virtual environment first:

```bash
cd /Users/semilirbayu/Dev/Vibe\ Coding/receipt-input-app
source venv/bin/activate
```

You'll see `(venv)` in your terminal prompt when activated.

### Step 2: Configure Environment Variables

Create your `.env` file from the template:

```bash
cp .env.example .env
```

Then edit `.env` and add your Google OAuth2 credentials:

```bash
# Open in your editor
nano .env
# or
code .env
```

**Required settings**:
- `GOOGLE_CLIENT_ID`: Get from [Google Cloud Console](https://console.cloud.google.com/)
- `GOOGLE_CLIENT_SECRET`: Get from Google Cloud Console
- `SECRET_KEY`: Generate with: `python3 -c "import secrets; print(secrets.token_hex(32))"`
- `REDIRECT_URI`: Keep as `http://localhost:8000/api/v1/auth/callback`

**How to get Google OAuth2 credentials**:
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing one
3. Enable "Google Sheets API"
4. Create OAuth 2.0 Client ID credentials
5. Add redirect URI: `http://localhost:8000/api/v1/auth/callback`
6. Copy Client ID and Secret to your `.env` file

### Step 3: Run the Application

```bash
# Make sure virtual environment is activated (you should see "(venv)" in your prompt)
uvicorn frontend.src.main:app --reload --port 8000
```

The application will start at: **http://localhost:8000**

### Step 4: Test the Application

1. **Open browser**: Navigate to http://localhost:8000
2. **Connect to Google Sheets**:
   - Click "Connect to Google Sheets" in the navbar
   - Sign in with your Google account
   - Grant permissions
   - Enter your Spreadsheet ID and Sheet Tab Name
3. **Upload a receipt**: Drag and drop a receipt image (JPG/PNG, max 5MB)
4. **Review extracted data**: Check the OCR results
5. **Save to Google Sheets**: Click save to append the data

## 🧪 Running Tests

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest -v

# Run with coverage report
pytest --cov=backend/src --cov=frontend/src --cov-report=term-missing

# Run specific test types
pytest -m contract    # Contract tests only
pytest -m integration # Integration tests only
pytest -m unit        # Unit tests only
```

## 📁 Project Structure

```
receipt-input-app/
├── venv/                    # Virtual environment (gitignored)
├── backend/
│   ├── src/                 # Backend code (models, services, API)
│   └── tests/               # Tests (contract, integration, unit)
├── frontend/
│   └── src/                 # Frontend (templates, static, main app)
├── shared/uploads/          # Temporary receipt storage
├── .env                     # Your environment variables (gitignored)
├── requirements.txt         # Python dependencies
└── README.md                # Full documentation
```

## 🔧 Common Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Deactivate virtual environment
deactivate

# Start development server
uvicorn frontend.src.main:app --reload --port 8000

# Run tests
pytest -v

# Check code style
ruff check .

# Format code
ruff format .
```

## 🐛 Troubleshooting

### Virtual environment not activating?
```bash
# Try this instead:
. venv/bin/activate
```

### "ModuleNotFoundError"?
Make sure virtual environment is activated:
```bash
which python
# Should show: /Users/semilirbayu/Dev/Vibe Coding/receipt-input-app/venv/bin/python
```

### OAuth2 redirect fails?
- Verify `REDIRECT_URI` in `.env` matches Google Cloud Console **exactly**
- Make sure you're running on port 8000

### OCR returns empty results?
- Ensure image is clear with good contrast
- Try a different receipt image
- Check Tesseract is installed: `tesseract --version`

## 📚 Documentation

- **README.md**: Full project documentation
- **IMPLEMENTATION_STATUS.md**: Implementation progress
- **specs/**: Feature specifications and API contracts
- **.env.example**: Environment variable template

## 💡 Tips

1. **Always activate the virtual environment** before running any Python commands
2. **Keep your `.env` file secret** - it's already in `.gitignore`
3. **Use sample receipts** for testing - clear, well-lit images work best
4. **Check logs** if something goes wrong - they'll show in the terminal

## 🚀 Ready to Go!

Your environment is fully set up. Just:

1. Activate venv: `source venv/bin/activate`
2. Configure `.env` with Google credentials
3. Run: `uvicorn frontend.src.main:app --reload --port 8000`
4. Open: http://localhost:8000

Happy coding! 🎉

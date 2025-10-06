# receipt-input-app Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-01

## Active Technologies
- Python 3.11+ + FastAPI, Jinja2, pytesseract, Pillow, gspread, google-auth (001-feature-receipt-processing)
- Python 3.11+ + FastAPI, Jinja2, gspread, Pydantic (002-feature-select-column)
- JSON file-based persistence (shared/user_preferences.json) (002-feature-select-column)
- Python 3.11+ + FastAPI, google-generativeai (Gemini SDK), Pydantic, Pillow (003-bugfix-improve-data)
- JSON file-based persistence (existing), ExtractedData model (enhanced validation) (003-bugfix-improve-data)

## Project Structure
```
src/
tests/
```

## Commands
cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style
Python 3.11+: Follow standard conventions

## Recent Changes
- 003-bugfix-improve-data: Added Python 3.11+ + FastAPI, google-generativeai (Gemini SDK), Pydantic, Pillow
- 002-feature-select-column: Added Python 3.11+ + FastAPI, Jinja2, gspread, Pydantic
- 001-feature-receipt-processing: Added Python 3.11+ + FastAPI, Jinja2, pytesseract, Pillow, gspread, google-auth

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

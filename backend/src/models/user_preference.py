"""
UserPreference model for Google Sheets configuration.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict
import uuid
import json
from pathlib import Path


@dataclass
class UserPreference:
    """
    Represents user's saved configuration for Google Sheets integration.

    Attributes:
        id: Unique identifier (UUID)
        user_session_id: OAuth2 session identifier
        spreadsheet_id: Google Sheets spreadsheet ID from URL
        sheet_tab_name: Specific sheet tab name
        column_mappings: Optional column mapping configuration (dict format)
        last_updated_at: Last update timestamp
        created_at: Creation timestamp
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_session_id: str = ""
    spreadsheet_id: str = ""
    sheet_tab_name: str = ""
    column_mappings: Optional[Dict] = None
    last_updated_at: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Constants
    SPREADSHEET_ID_LENGTH = 44
    MAX_SHEET_NAME_LENGTH = 100
    STORAGE_FILE = Path("shared") / "user_preferences.json"

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate user preference data.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(self.spreadsheet_id) != self.SPREADSHEET_ID_LENGTH:
            return False, "INVALID_SPREADSHEET_ID"

        if not self.sheet_tab_name or not self.sheet_tab_name.strip():
            return False, "INVALID_SHEET_NAME"

        if len(self.sheet_tab_name) > self.MAX_SHEET_NAME_LENGTH:
            return False, "INVALID_SHEET_NAME"

        if not self.user_session_id:
            return False, "Missing user session ID"

        return True, None

    def has_column_mappings(self) -> bool:
        """
        Check if user has configured column mappings.

        Returns:
            True if column_mappings field exists and is valid, False otherwise
        """
        return self.column_mappings is not None and len(self.column_mappings) > 0

    def get_column_mappings(self) -> Optional["ColumnMappingConfiguration"]:
        """
        Retrieve column mapping configuration.

        Returns:
            ColumnMappingConfiguration instance or None if not configured
        """
        if not self.has_column_mappings():
            return None

        from backend.src.models.column_mapping import ColumnMappingConfiguration
        return ColumnMappingConfiguration.from_dict(self.column_mappings)

    def set_column_mappings(self, config: "ColumnMappingConfiguration") -> None:
        """
        Save column mapping configuration.

        Args:
            config: Valid ColumnMappingConfiguration instance

        Side Effects:
            Updates last_updated_at timestamp
        """
        self.column_mappings = config.to_dict()
        self.last_updated_at = datetime.utcnow()

    def save(self) -> None:
        """Save preference to persistent storage."""
        self.last_updated_at = datetime.utcnow()

        # Load existing preferences
        preferences = {}
        if self.STORAGE_FILE.exists():
            with open(self.STORAGE_FILE, 'r') as f:
                preferences = json.load(f)

        # Update with current preference
        pref_data = {
            "id": self.id,
            "spreadsheet_id": self.spreadsheet_id,
            "sheet_tab_name": self.sheet_tab_name,
            "last_updated_at": self.last_updated_at.isoformat(),
            "created_at": self.created_at.isoformat()
        }

        # Include column_mappings if configured
        if self.column_mappings is not None:
            pref_data["column_mappings"] = self.column_mappings

        preferences[self.user_session_id] = pref_data

        # Ensure directory exists
        self.STORAGE_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Save back
        with open(self.STORAGE_FILE, 'w') as f:
            json.dump(preferences, f, indent=2)

    def delete(self) -> None:
        """Delete this user's preference from persistent storage."""
        if not self.STORAGE_FILE.exists():
            return

        # Load existing preferences
        with open(self.STORAGE_FILE, 'r') as f:
            preferences = json.load(f)

        # Remove this user's preference
        if self.user_session_id in preferences:
            del preferences[self.user_session_id]

        # Save back (or delete file if empty)
        if preferences:
            with open(self.STORAGE_FILE, 'w') as f:
                json.dump(preferences, f, indent=2)
        else:
            self.STORAGE_FILE.unlink()  # Delete file if no preferences remain

    @classmethod
    def load_by_session_id(cls, session_id: str) -> Optional["UserPreference"]:
        """
        Load user preference by session ID.

        Args:
            session_id: User session identifier

        Returns:
            UserPreference instance or None if not found
        """
        if not cls.STORAGE_FILE.exists():
            return None

        with open(cls.STORAGE_FILE, 'r') as f:
            preferences = json.load(f)

        if session_id not in preferences:
            return None

        data = preferences[session_id]

        # Load column_mappings if present (backward compatibility)
        column_mappings = data.get("column_mappings", None)

        return cls(
            id=data["id"],
            user_session_id=session_id,
            spreadsheet_id=data["spreadsheet_id"],
            sheet_tab_name=data["sheet_tab_name"],
            column_mappings=column_mappings,
            last_updated_at=datetime.fromisoformat(data["last_updated_at"]),
            created_at=datetime.fromisoformat(data["created_at"])
        )

    @classmethod
    def create(cls, session_id: str, spreadsheet_id: str, sheet_tab_name: str) -> "UserPreference":
        """
        Factory method to create a new UserPreference instance.

        Args:
            session_id: User session identifier
            spreadsheet_id: Google Sheets spreadsheet ID
            sheet_tab_name: Sheet tab name

        Returns:
            New UserPreference instance
        """
        return cls(
            user_session_id=session_id,
            spreadsheet_id=spreadsheet_id,
            sheet_tab_name=sheet_tab_name
        )

"""
Unit tests for UserPreference model with column_mappings support.
These tests MUST FAIL until the column mappings methods are implemented.
"""
import pytest
from unittest.mock import mock_open, patch, MagicMock
import json
from datetime import datetime
from backend.src.models.user_preference import UserPreference
from backend.src.models.column_mapping import ColumnMappingConfiguration


class TestUserPreferenceHasColumnMappings:
    """Tests for UserPreference.has_column_mappings() method."""

    def test_has_column_mappings_returns_false_when_field_missing(self):
        """Test has_column_mappings returns False when column_mappings field is None."""
        user_pref = UserPreference(
            user_session_id="test-session",
            spreadsheet_id="1" * 44,
            sheet_tab_name="Sheet1"
        )
        assert user_pref.has_column_mappings() is False

    def test_has_column_mappings_returns_true_when_field_exists(self):
        """Test has_column_mappings returns True when column_mappings field exists."""
        user_pref = UserPreference(
            user_session_id="test-session",
            spreadsheet_id="1" * 44,
            sheet_tab_name="Sheet1",
            column_mappings={"date": "A", "description": "B", "price": "C"}
        )
        assert user_pref.has_column_mappings() is True


class TestUserPreferenceGetColumnMappings:
    """Tests for UserPreference.get_column_mappings() method."""

    def test_get_column_mappings_returns_none_when_not_configured(self):
        """Test get_column_mappings returns None when not configured."""
        user_pref = UserPreference(
            user_session_id="test-session",
            spreadsheet_id="1" * 44,
            sheet_tab_name="Sheet1"
        )
        mappings = user_pref.get_column_mappings()
        assert mappings is None

    def test_get_column_mappings_returns_config_when_configured(self):
        """Test get_column_mappings returns ColumnMappingConfiguration when configured."""
        user_pref = UserPreference(
            user_session_id="test-session",
            spreadsheet_id="1" * 44,
            sheet_tab_name="Sheet1",
            column_mappings={"date": "A", "description": "B", "price": "C"}
        )
        mappings = user_pref.get_column_mappings()

        assert mappings is not None
        assert isinstance(mappings, ColumnMappingConfiguration)
        assert mappings.date_column == "A"
        assert mappings.description_column == "B"
        assert mappings.price_column == "C"


class TestUserPreferenceSetColumnMappings:
    """Tests for UserPreference.set_column_mappings() method."""

    def test_set_column_mappings_saves_config_to_dict(self):
        """Test set_column_mappings saves config as dict."""
        user_pref = UserPreference(
            user_session_id="test-session",
            spreadsheet_id="1" * 44,
            sheet_tab_name="Sheet1"
        )

        config = ColumnMappingConfiguration(
            date_column="A",
            description_column="B",
            price_column="C"
        )

        user_pref.set_column_mappings(config)

        assert user_pref.column_mappings == {
            "date": "A",
            "description": "B",
            "price": "C"
        }

    def test_set_column_mappings_updates_last_updated_at(self):
        """Test set_column_mappings updates last_updated_at timestamp."""
        user_pref = UserPreference(
            user_session_id="test-session",
            spreadsheet_id="1" * 44,
            sheet_tab_name="Sheet1"
        )

        original_updated_at = user_pref.last_updated_at

        # Add a small delay to ensure timestamp changes
        import time
        time.sleep(0.001)

        config = ColumnMappingConfiguration(
            date_column="A",
            description_column="B",
            price_column="C"
        )

        user_pref.set_column_mappings(config)

        # last_updated_at should be updated (greater than original)
        assert user_pref.last_updated_at > original_updated_at


class TestUserPreferenceSaveWithColumnMappings:
    """Tests for UserPreference.save() method with column_mappings."""

    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists", return_value=False)
    @patch("pathlib.Path.mkdir")
    def test_save_persists_column_mappings_to_json(self, mock_mkdir, mock_exists, mock_file):
        """Test save() includes column_mappings in JSON file."""
        user_pref = UserPreference(
            user_session_id="test-session",
            spreadsheet_id="1" * 44,
            sheet_tab_name="Sheet1",
            column_mappings={"date": "A", "description": "B", "price": "C"}
        )

        user_pref.save()

        # Verify file was written
        mock_file.assert_called()

        # Get the written content
        written_data = ""
        for call in mock_file().write.call_args_list:
            written_data += call[0][0]

        saved_data = json.loads(written_data)

        assert "test-session" in saved_data
        assert "column_mappings" in saved_data["test-session"]
        assert saved_data["test-session"]["column_mappings"] == {
            "date": "A",
            "description": "B",
            "price": "C"
        }


class TestUserPreferenceLoadBySessionIdWithColumnMappings:
    """Tests for UserPreference.load_by_session_id() with column_mappings."""

    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({
        "test-session": {
            "id": "test-id",
            "spreadsheet_id": "1" * 44,
            "sheet_tab_name": "Sheet1",
            "created_at": "2024-01-01T00:00:00",
            "last_updated_at": "2024-01-01T00:00:00"
        }
    }))
    def test_load_by_session_id_loads_preference_without_column_mappings(self, mock_file, mock_exists):
        """Test load_by_session_id loads preference without column_mappings (backward compat)."""
        user_pref = UserPreference.load_by_session_id("test-session")

        assert user_pref is not None
        assert user_pref.user_session_id == "test-session"
        assert user_pref.has_column_mappings() is False

    @patch("pathlib.Path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data=json.dumps({
        "test-session": {
            "id": "test-id",
            "spreadsheet_id": "1" * 44,
            "sheet_tab_name": "Sheet1",
            "column_mappings": {
                "date": "A",
                "description": "B",
                "price": "C"
            },
            "created_at": "2024-01-01T00:00:00",
            "last_updated_at": "2024-01-01T00:00:00"
        }
    }))
    def test_load_by_session_id_loads_preference_with_column_mappings(self, mock_file, mock_exists):
        """Test load_by_session_id loads preference with column_mappings."""
        user_pref = UserPreference.load_by_session_id("test-session")

        assert user_pref is not None
        assert user_pref.user_session_id == "test-session"
        assert user_pref.has_column_mappings() is True

        mappings = user_pref.get_column_mappings()
        assert mappings.date_column == "A"
        assert mappings.description_column == "B"
        assert mappings.price_column == "C"

"""
Basic tests for Mental Health Agent API functions
"""

import pytest
import json
import os
import sys

# Add the lambdas directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lambdas"))


def test_import_modules():
    """Test that all lambda modules can be imported without errors"""
    try:
        import mh_chat_handler
        import mh_daily_checkin
        import mh_evaluate_mental_health
        import mh_recommendations
        import mh_schedule_checkin
        import mh_user_profile
        import profile_utils

        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import module: {e}")


def test_chat_handler_structure():
    """Test that chat handler has required functions"""
    import mh_chat_handler

    # Check if handler function exists
    assert hasattr(mh_chat_handler, "handler")
    assert callable(mh_chat_handler.handler)

    # Check if other key functions exist
    assert hasattr(mh_chat_handler, "generate_empathetic_response")
    assert hasattr(mh_chat_handler, "store_conversation")


def test_daily_checkin_structure():
    """Test that daily checkin handler has required functions"""
    import mh_daily_checkin

    # Check if handler function exists
    assert hasattr(mh_daily_checkin, "handler")
    assert callable(mh_daily_checkin.handler)


def test_evaluation_structure():
    """Test that evaluation handler has required functions"""
    import mh_evaluate_mental_health

    # Check if handler function exists
    assert hasattr(mh_evaluate_mental_health, "handler")
    assert callable(mh_evaluate_mental_health.handler)


def test_recommendations_structure():
    """Test that recommendations handler has required functions"""
    import mh_recommendations

    # Check if handler function exists
    assert hasattr(mh_recommendations, "handler")
    assert callable(mh_recommendations.handler)


def test_schedule_structure():
    """Test that schedule handler has required functions"""
    import mh_schedule_checkin

    # Check if handler function exists
    assert hasattr(mh_schedule_checkin, "handler")
    assert callable(mh_schedule_checkin.handler)


def test_user_profile_structure():
    """Test that user profile handler has required functions"""
    import mh_user_profile

    # Check if handler function exists
    assert hasattr(mh_user_profile, "handler")
    assert callable(mh_user_profile.handler)


def test_profile_utils_structure():
    """Test that profile utils has required functions"""
    import profile_utils

    # Check if key utility functions exist
    assert hasattr(profile_utils, "get_user_profile")
    assert hasattr(profile_utils, "store_user_profile")
    assert hasattr(profile_utils, "create_default_profile")
    assert hasattr(profile_utils, "update_profile_from_checkin")
    assert hasattr(profile_utils, "update_profile_from_chat")


def test_requirements_file():
    """Test that requirements.txt exists and has content"""
    requirements_path = os.path.join(
        os.path.dirname(__file__), "..", "requirements.txt"
    )
    assert os.path.exists(requirements_path)

    with open(requirements_path, "r") as f:
        content = f.read().strip()
        assert len(content) > 0
        assert "boto3" in content
        assert "streamlit" in content


def test_setup_py():
    """Test that setup.py exists and is valid"""
    setup_path = os.path.join(os.path.dirname(__file__), "..", "setup.py")
    assert os.path.exists(setup_path)

    with open(setup_path, "r") as f:
        content = f.read()
        assert "mental-health-agent" in content
        assert "setuptools" in content


if __name__ == "__main__":
    pytest.main([__file__])

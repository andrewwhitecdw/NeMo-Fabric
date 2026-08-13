import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Make scripts/ci importable from this test directory.
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts" / "ci"))
import artifactory_upload


@pytest.fixture
def kitmaker_env(monkeypatch):
    monkeypatch.setenv("KITMAKER_URL", "http://kitmaker.test")
    monkeypatch.setenv("KITMAKER_API_TOKEN", "token")
    monkeypatch.setenv("KITMAKER_OWNER", "nvidia")


def test_perform_release_missing_project(kitmaker_env, monkeypatch, capsys):
    # Simulate KitMaker knowing only a different project.
    fake_response = MagicMock()
    fake_response.raise_for_status = MagicMock()
    fake_response.json.return_value = [{"name": "other-package", "id": 1234}]

    monkeypatch.setattr(
        artifactory_upload.requests, "get", lambda url, headers, timeout: fake_response
    )

    # Ensure no release POST is attempted for the missing package.
    def mock_post(*args, **kwargs):
        raise AssertionError("POST should not be called for missing project")

    monkeypatch.setattr(artifactory_upload.requests, "post", mock_post)

    # Avoid reading a real wheel file.
    class FakeWheel:
        def __init__(self, path):
            self.name = "missing-package"

    monkeypatch.setattr(artifactory_upload.pkginfo, "Wheel", FakeWheel)

    published_wheels = [
        (Path("/fake/missing_package-1.0-py3-none-any.whl"), "http://artifactory/wheel.whl")
    ]

    error_count = artifactory_upload.perform_release(published_wheels)

    captured = capsys.readouterr()
    assert error_count == 1
    assert "KitMaker project not found for package missing-package" in captured.out

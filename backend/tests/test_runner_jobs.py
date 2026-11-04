"""TC-106: the runner accepts only typed jobs whose URL is inside their allowlist."""

import pytest
from pydantic import ValidationError

from gatp.inspector.locators import LocatorSpec
from gatp.runner.client import JOB_ADAPTER
from gatp.runner.jobs import InspectJob, RecountJob
from gatp.runner.sandbox import job_sandbox

ALLOW = ["http://127.0.0.1:8090"]


def test_valid_jobs_parse() -> None:
    job = JOB_ADAPTER.validate_python(
        {"type": "inspect", "url": "http://127.0.0.1:8090/index.html", "allowlist": ALLOW}
    )
    assert isinstance(job, InspectJob)
    recount = JOB_ADAPTER.validate_python(
        {
            "type": "recount",
            "url": "http://127.0.0.1:8090/",
            "allowlist": ["http://127.0.0.1:8090/some/path"],  # normalised to the origin
            "locators": [{"strategy": "test_id", "value": "login-submit"}],
        }
    )
    assert isinstance(recount, RecountJob)
    assert recount.allowlist == ["http://127.0.0.1:8090"]


@pytest.mark.parametrize(
    "payload",
    [
        {"type": "shell", "cmd": "rm -rf /"},
        {"type": "run_python", "code": "import os"},
        {"type": "inspect", "url": "http://evil.test/", "allowlist": ALLOW},
        {"type": "inspect", "url": "file:///etc/passwd", "allowlist": ALLOW},
        {"type": "inspect", "url": "http://127.0.0.1:8090/", "allowlist": []},
        {"type": "inspect", "url": "http://127.0.0.1:8090/", "allowlist": ALLOW, "cmd": "x"},
        {"type": "recount", "url": "http://127.0.0.1:8090/", "allowlist": ALLOW, "locators": []},
    ],
)
def test_rejected_jobs(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        JOB_ADAPTER.validate_python(payload)


def test_locator_spec_renders_python() -> None:
    assert (
        LocatorSpec(strategy="role", value="button", name='Say "hi"').to_python()
        == 'page.get_by_role("button", name="Say \\"hi\\"", exact=True)'
    )
    assert LocatorSpec(strategy="test_id", value="x").to_python("self.page") == (
        'self.page.get_by_test_id("x")'
    )
    assert LocatorSpec(strategy="css", value="#a").to_python() == 'page.locator("#a")'
    assert LocatorSpec(strategy="label", value="Title").to_python() == (
        'page.get_by_label("Title", exact=True)'
    )


def test_sandbox_created_private_and_removed(tmp_path: pytest.TempPathFactory) -> None:
    root, artifacts = tmp_path / "sb", tmp_path / "artifacts"  # type: ignore[operator]
    with job_sandbox(root, artifacts, "abc") as box:
        assert box.path.is_dir()
        assert (box.path.stat().st_mode & 0o777) == 0o700
        (box.path / "out.txt").write_text("hello")
        rel = box.keep("out.txt")
        with pytest.raises(ValueError, match="outside the sandbox"):
            box.keep("../escape.txt")
    assert not box.path.exists()
    assert rel == "jobs/abc/out.txt"
    assert (artifacts / rel).read_text() == "hello"

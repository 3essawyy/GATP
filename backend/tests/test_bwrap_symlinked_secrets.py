"""bwrap secret-dir hiding must target the real directory when ~/.aws etc. are symlinks."""

from pathlib import Path

import pytest

from gatp.runner import execute


def test_symlinked_secret_dir_is_hidden_via_its_real_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = tmp_path / "real-aws"
    real.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    (home / ".aws").symlink_to(real)
    monkeypatch.setattr(execute.Path, "home", lambda: home)
    monkeypatch.setattr(execute.shutil, "which", lambda _name: "/usr/bin/bwrap")
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    args = execute.bwrap_prefix(sandbox, ())

    tmpfs_targets = [args[i + 1] for i, a in enumerate(args) if a == "--tmpfs"]
    assert str(real.resolve()) in tmpfs_targets
    assert str(home / ".aws") not in args

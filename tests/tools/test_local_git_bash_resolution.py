import pytest

from tools.environments import local


def _norm(path: str) -> str:
    return local.os.path.normcase(local.os.path.abspath(path))


def test_find_bash_prefers_git_adjacent_to_git_exe_over_wsl_launcher(monkeypatch):
    monkeypatch.setattr(local, "_IS_WINDOWS", True)
    monkeypatch.setenv("WINDIR", r"C:\Windows")
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\Alice\AppData\Local")
    monkeypatch.delenv("HERMES_GIT_BASH_PATH", raising=False)

    system32_bash = r"C:\Windows\System32\bash.exe"
    git_exe = r"E:\ProgrammingSoftware\Git\cmd\git.exe"
    git_bash = r"E:\ProgrammingSoftware\Git\bin\bash.exe"

    existing = {
        _norm(system32_bash),
        _norm(git_exe),
        _norm(git_bash),
    }

    monkeypatch.setattr(
        local.shutil,
        "which",
        lambda name: {"bash": system32_bash, "git": git_exe}.get(name),
    )
    monkeypatch.setattr(
        local.os.path,
        "isfile",
        lambda path: _norm(path) in existing,
    )

    assert local._find_bash() == git_bash


def test_find_bash_rejects_system32_wsl_launcher_when_no_git_bash_exists(monkeypatch):
    monkeypatch.setattr(local, "_IS_WINDOWS", True)
    monkeypatch.setenv("WINDIR", r"C:\Windows")
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\Alice\AppData\Local")
    monkeypatch.delenv("HERMES_GIT_BASH_PATH", raising=False)

    system32_bash = r"C:\Windows\System32\bash.exe"

    monkeypatch.setattr(
        local.shutil,
        "which",
        lambda name: {"bash": system32_bash, "git": None}.get(name),
    )
    monkeypatch.setattr(local.os.path, "isfile", lambda _path: False)

    with pytest.raises(RuntimeError, match="Git Bash not found"):
        local._find_bash()


def test_resolve_safe_cwd_accepts_git_bash_style_windows_path(monkeypatch):
    monkeypatch.setattr(local, "_IS_WINDOWS", True)

    native = r"E:\workspace\project"
    git_bash = "/e/workspace/project"

    monkeypatch.setattr(
        local.os.path,
        "isdir",
        lambda path: local.os.path.normcase(path) == local.os.path.normcase(native),
    )

    assert local._resolve_safe_cwd(git_bash) == native

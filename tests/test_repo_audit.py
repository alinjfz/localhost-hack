from diagnostics.repo_audit import find_unexpected_files, render_report


def test_repo_audit_reports_unexpected_files(tmp_path):
    (tmp_path / "README.md").write_text("ok")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "agent.py").write_text("print('hello')")

    unexpected = find_unexpected_files(tmp_path, allowed_files={"README.md"})

    assert unexpected == ["src/agent.py"]


def test_repo_audit_is_clean_for_allowed_files(tmp_path):
    for rel in ["README.md", "src/__init__.py"]:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok")

    assert render_report(tmp_path) == "Repo audit: clean"

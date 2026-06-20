from mac_harness import cli


def test_init_workspace_creates_missing_scaffold(tmp_path):
    created = cli.init_workspace(tmp_path)

    assert (tmp_path / "demo-project/landing-page/index.html").exists()
    assert (tmp_path / "demo-project/cli/setup.py").exists()
    assert created


def test_status_rows_detect_files(tmp_path):
    (tmp_path / "demo-project/landing-page").mkdir(parents=True)
    (tmp_path / "demo-project/landing-page/index.html").write_text("ok", encoding="utf-8")

    rows = cli.status_rows(tmp_path, files=["demo-project/landing-page/index.html", "missing.txt"])

    assert rows[0].exists is True
    assert rows[1].exists is False


def test_write_file_creates_parent_directories(tmp_path):
    target = tmp_path / "nested" / "file.txt"

    cli.write_file(target, "hello")

    assert target.read_text(encoding="utf-8") == "hello"

import subprocess

def test_conftest_no_mines():
    result = subprocess.run(
        ["grep", "-ci", "mines", "tests/conftest.py"],
        cwd=".",
        capture_output=True,
        text=True
    )
    assert result.stdout.strip() == "0", f"Found 'mines' in conftest.py! Output: {result.stdout}"


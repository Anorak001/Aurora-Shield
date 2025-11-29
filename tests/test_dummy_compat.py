import sys

def test_python_version_supported():
    # ensure test is compatible with the project's supported Python versions
    major = sys.version_info.major
    assert major in (3,)

def test_string_operations():
    s = "hello"
    assert s.upper() == "HELLO"

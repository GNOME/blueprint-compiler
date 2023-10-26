default: black isort

# Format with black formatter
black:
    black blueprintcompiler/

# Sort imports using isort
isort:
    isort blueprintcompiler/ --profile black


# Run all tests
test: mypy unittest

# Check typings with mypy
mypy:
    mypy --python-version=3.9 blueprintcompiler/

# Test code with unittest
unittest:
    python3 -m unittest


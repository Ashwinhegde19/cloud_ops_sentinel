---
inclusion: always
---

# Terminal Environment Setup

## Virtual Environment Activation

When executing any Python-related commands in the terminal, ALWAYS:

1. First activate the virtual environment using uv:
   ```bash
   source venv/bin/activate
   ```

2. If the venv doesn't exist, create it first:
   ```bash
   uv venv venv
   source venv/bin/activate
   ```

3. Install dependencies if needed:
   ```bash
   uv pip install -r requirements.txt
   ```

## Command Execution Pattern

For any Python command, use this pattern:
```bash
source venv/bin/activate
# then run your command
python3 your_script.py
```

## Package Management

- Use `uv pip install <package>` instead of `pip install`
- Use `uv pip install -r requirements.txt` for bulk installs
- uv is faster and more reliable than pip

## Important Notes

- Never run Python commands without activating venv first
- The venv directory is at the project root: `./venv/`
- All dependencies should be installed in the venv, not system-wide

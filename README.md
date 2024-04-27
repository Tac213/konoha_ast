# konoha_ast

Common AST (Abstract Syntactic Tree) for visual scripting.

## Contributing

After cloning the repository, set current working directory to `konoha_ast` root folder, then execute the following commands:

```bash
python3 -m venv .venv  # Create venv
source .venv/bin/activate  # Activate venv
# for Windows Command Prompt, execute the following command to activate venv
# .venv\Scripts\activate.bat
# for Windows Powershell, execute the following command to activate venv
# .venv\Scripts\Activate.ps1
# for Winows Git Bash, execute the following command to activate venv
# source .venv/Scripts/activate
pip3 install -e ".[dev,test]"  # Editably install packages, including dev and test dependent packages
```

### Unit Testing

The simplest way is to run the following command under `konoha_ast` root folder:

```bash
# Make sure your venv is activated and the test dependent packages are installed
pytest
```

VSCode based unit testing configuration is set in `.vscode/settings.json`, you can also perform unit testing within VSCode.

# PyKD — Python Database Engine

PyKD is a Python-based database engine project designed to explore core database operations, structured data management, and query-style functionality through a modular architecture.

## Overview

PyKD aims to provide a lightweight environment for understanding how database components interact, how data can be organized and managed, and how users can work with data through a command-line interface.

## Key Components

- **Database Engine** — A Python-based implementation for working with structured data.
- **Modular Architecture** — Core functionality organized within the `pykd/` package.
- **Command-Line Interface** — A CLI entry point through `cli.py`.
- **Testing** — A dedicated `tests/` directory for validating project functionality.
- **Project Configuration** — Package and development configuration managed through `pyproject.toml`.

## Tech Stack

- Python
- Pytest
- Git and GitHub
- TOML for project configuration

## Project Structure

```text
pykd_mk1/
├── pykd/              # Core database engine package
├── tests/             # Test suite
├── data/              # Project data files
├── cli.py             # Command-line interface
├── pyproject.toml      # Project configuration
├── .gitignore          # Git exclusions
└── README.md           # Project documentation
```

## Getting Started

### Prerequisites

- Python installed on your system
- Git, if you want to clone the repository

### Installation

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/PyKD.git
cd PyKD
```

Create and activate a virtual environment.

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install the project and its dependencies according to the configuration in `pyproject.toml`. If the project defines an installable package, you can try:

```bash
python -m pip install -e .
```

### Running the Project

Inspect the available CLI commands and usage in `cli.py`. Run the appropriate command for the implemented functionality.

For example, if `cli.py` contains a directly executable entry point:

```bash
python cli.py --help
```

The supported commands depend on the current implementation.

### Running Tests

If Pytest is installed and the test suite is configured, run:

```bash
python -m pytest
```

## Development Goals

PyKD provides a foundation for exploring database engine design, modular Python development, command-line tooling, and automated testing.

Potential future improvements include expanding query functionality, strengthening data persistence, improving error handling, and increasing test coverage.

## Current Status

This project is under development. Available functionality and supported commands should be verified against the current source code.

## Author

**Ayush Kumar**

GitHub: https://github.com/ayushkumar2208

---

*Built as a Python development project focused on database systems and software engineering fundamentals.*

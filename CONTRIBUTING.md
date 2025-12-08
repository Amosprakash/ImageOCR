# CONTRIBUTING.md
# Contributing to ImageAI Document AI Platform

Thank you for your interest in contributing to ImageAI! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Git
- Tesseract OCR
- Poppler (for PDF processing)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/ImageOCR.git
   cd ImageOCR
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Install in editable mode
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## 🧪 Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=core --cov=api --cov=utils --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_preprocess.py
```

### Run specific test
```bash
pytest tests/test_api.py::TestOCREndpoints::test_health_check
```

## 📝 Code Style

We use the following tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting
- **mypy**: Static type checking

### Format code
```bash
black core/ api/ utils/ tests/
isort core/ api/ utils/ tests/
```

### Run linting
```bash
flake8 core/ api/ utils/ tests/
```

### Run type checking
```bash
mypy core/ api/ utils/
```

### Run all checks
```bash
pre-commit run --all-files
```

## 🔄 Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code
   - Add tests
   - Update documentation

3. **Run tests and checks**
   ```bash
   pytest
   black core/ api/ utils/ tests/
   flake8 core/ api/ utils/ tests/
   mypy core/ api/ utils/
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Adding tests
   - `refactor:` Code refactoring
   - `perf:` Performance improvements
   - `chore:` Maintenance tasks

5. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## 🐛 Reporting Bugs

When reporting bugs, please include:

- Python version
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages/stack traces
- Screenshots (if applicable)

## 💡 Suggesting Features

Feature requests are welcome! Please include:

- Clear description of the feature
- Use case/motivation
- Proposed implementation (if any)
- Potential impact on existing features

## 📋 Pull Request Guidelines

### Before Submitting

- [ ] Tests pass locally
- [ ] Code is formatted with Black
- [ ] Linting passes (Flake8)
- [ ] Type checking passes (mypy)
- [ ] Documentation is updated
- [ ] Changelog is updated (if applicable)

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
```

## 🏗️ Project Structure

```
ImageOCR/
├── core/           # Core OCR, RAG, and KG modules
├── api/            # FastAPI routes and schemas
├── utils/          # Utility functions
├── frontend/       # Streamlit UI
├── tests/          # Test suite
├── examples/       # Example files
└── models/         # Model files
```

## 🔐 Security

- Never commit API keys or secrets
- Use environment variables for configuration
- Report security vulnerabilities privately
- Follow secure coding practices

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🤝 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other contributors

## 📞 Getting Help

- Open an issue for bugs or feature requests
- Join discussions for questions
- Check existing issues before creating new ones

## 🎉 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing to ImageAI! 🚀

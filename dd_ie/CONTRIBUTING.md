# Contributing to dd_ie

Thank you for your interest in contributing to dd_ie! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/covid_paper.git
   cd covid_paper/dd_ie
   ```
3. **Install in development mode**:
   ```bash
   pip install -e .[dev,viz]
   ```

## Development Setup

### Dependencies
- Python 3.8+
- Core: pandas, numpy, scipy, linearmodels
- Development: pytest, black, flake8
- Optional: matplotlib, seaborn (for visualization)

### Code Style
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Include comprehensive docstrings for all public functions
- Run `black` for code formatting
- Run `flake8` for linting

## Testing

- Write tests for new functionality in the `tests/` directory
- Run the test suite: `pytest tests/`
- Ensure all tests pass before submitting a pull request
- Aim for high test coverage of new code

## Types of Contributions

### Bug Reports
- Use the GitHub issue tracker
- Include a clear description of the problem
- Provide a minimal reproducible example
- Include system information (Python version, package versions)

### Feature Requests
- Open an issue to discuss the feature first
- Explain the use case and motivation
- Consider backward compatibility

### Code Contributions
- Create a new branch for your feature: `git checkout -b feature-name`
- Write tests for your changes
- Update documentation if needed
- Submit a pull request with a clear description

## Pull Request Process

1. **Create a descriptive branch name**: `feature/add-bootstrap-tests` or `fix/hausman-edge-case`
2. **Write clear commit messages**: Use present tense ("Add feature" not "Added feature")
3. **Update tests**: Add tests for new functionality
4. **Update documentation**: Update README, docstrings, or examples as needed
5. **Run tests locally**: Ensure all tests pass
6. **Submit the PR**: Include a clear description of changes and motivation

## Code Guidelines

### Function Documentation
```python
def your_function(param1: str, param2: Optional[int] = None) -> Dict:
    """
    Brief description of the function.
    
    Longer description if needed, explaining the purpose,
    methodology, and any important details.
    
    Parameters
    ----------
    param1 : str
        Description of param1
    param2 : Optional[int], optional
        Description of param2 (default: None)
        
    Returns
    -------
    Dict
        Description of return value
        
    Raises
    ------
    ValueError
        When invalid input is provided
        
    Examples
    --------
    >>> result = your_function("example")
    >>> print(result)
    {'key': 'value'}
    """
```

### Error Handling
- Use appropriate exception types
- Provide helpful error messages
- Handle edge cases gracefully
- Add warnings for potentially problematic inputs

### Mathematical Implementation
- Include references to papers/methods when implementing statistical procedures
- Add comments explaining complex mathematical operations
- Ensure numerical stability for edge cases

## Project Structure

```
dd_ie/
├── __init__.py          # Package initialization and exports
├── core.py              # Main analysis classes and functions
├── utils.py             # Utility functions for data handling
├── tests/               # Test suite
│   ├── __init__.py
│   ├── test_core.py     # Tests for core functionality
│   └── test_utils.py    # Tests for utility functions
├── examples/            # Example scripts and notebooks
├── README.md            # Main documentation
├── LICENSE              # MIT license
├── setup.py             # Package installation configuration
├── CHANGELOG.md         # Version history
└── CONTRIBUTING.md      # This file
```

## Questions?

- Open an issue for general questions
- Contact the maintainer: nikolaos.koutounidis@ugent.be

## Code of Conduct

Be respectful and constructive in all interactions. This project aims to provide a welcoming environment for all contributors regardless of background or experience level.

## Recognition

Contributors will be recognized in the README and/or changelog. Substantial contributions may warrant co-authorship discussions.

Thank you for contributing to dd_ie!

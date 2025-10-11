# Contributing to Aurora Shield

Thank you for your interest in contributing to Aurora Shield! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on what is best for the community
- Show empathy towards other community members

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:

1. **Clear title** - Describe the issue briefly
2. **Description** - Detailed description of the bug
3. **Steps to reproduce** - How to reproduce the issue
4. **Expected behavior** - What should happen
5. **Actual behavior** - What actually happens
6. **Environment** - OS, Python version, etc.

### Suggesting Enhancements

For feature requests:

1. **Check existing issues** - See if it's already proposed
2. **Describe the feature** - What you want to add
3. **Explain the use case** - Why it's needed
4. **Provide examples** - How it would work

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch** - `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Test your changes** - Ensure all tests pass
5. **Commit your changes** - Use clear commit messages
6. **Push to your fork** - `git push origin feature/amazing-feature`
7. **Open a Pull Request**

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Aurora-Shield.git
cd Aurora-Shield

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions and classes
- Keep functions small and focused
- Write self-documenting code

### Example

```python
def check_request(self, ip_address, timestamp=None):
    """
    Check if a request from an IP is anomalous.
    
    Args:
        ip_address (str): The IP address making the request
        timestamp (float): Unix timestamp of the request
        
    Returns:
        dict: Detection result with status and details
    """
    # Implementation here
```

## Testing

### Running Tests

```bash
# Run basic protection test
python examples/basic_protection.py

# Run attack simulation test
python examples/attack_simulation.py

# Test the dashboard
python main.py
# Then open http://localhost:8080
```

### Adding Tests

When adding new features:

1. Add example usage in `examples/`
2. Test edge cases
3. Verify error handling
4. Check performance impact

## Project Structure

```
aurora_shield/
├── core/           # Core detection logic
├── mitigation/     # Mitigation strategies
├── auto_recovery/  # Recovery mechanisms
├── attack_sim/     # Attack simulators
├── integrations/   # External integrations
├── gateway/        # Edge gateway
├── dashboard/      # Web dashboard
└── config/         # Configuration
```

## Component Guidelines

### Adding Detection Methods

1. Implement in `aurora_shield/core/`
2. Follow existing patterns
3. Make it configurable
4. Log important events
5. Update dashboard integration

### Adding Mitigation Strategies

1. Implement in `aurora_shield/mitigation/`
2. Provide clear documentation
3. Make it composable
4. Test false positive rate
5. Add configuration options

### Adding Recovery Actions

1. Implement in `aurora_shield/auto_recovery/`
2. Make it idempotent
3. Handle failures gracefully
4. Log all actions
5. Provide rollback capability

## Documentation

When adding features:

1. Update README.md if needed
2. Add docstrings to all public APIs
3. Provide usage examples
4. Update ARCHITECTURE.md for major changes
5. Add to QUICKSTART.md if relevant

## Commit Messages

Use clear, descriptive commit messages:

```
Good:
- Add IP whitelist management API
- Fix rate limiter token refill bug
- Improve dashboard refresh performance

Bad:
- Fix bug
- Update code
- Changes
```

## Review Process

Pull requests will be reviewed for:

1. **Functionality** - Does it work as intended?
2. **Code Quality** - Is it well-written and maintainable?
3. **Tests** - Are there adequate tests?
4. **Documentation** - Is it properly documented?
5. **Style** - Does it follow project conventions?

## Performance Considerations

Aurora Shield is designed for high performance:

- Avoid blocking operations
- Use efficient data structures
- Minimize memory allocations
- Profile before optimizing
- Consider scalability

## Security

Security is paramount:

- Never log sensitive data
- Validate all inputs
- Use secure defaults
- Follow security best practices
- Report security issues privately

## License

By contributing, you agree that your contributions will be licensed under the GNU General Public License v3.0.

## Questions?

- Open an issue for questions
- Check existing documentation
- Look at example code
- Read ARCHITECTURE.md

## Recognition

Contributors will be recognized in:

- GitHub contributors list
- Release notes
- Project documentation

Thank you for contributing to Aurora Shield! 🛡️

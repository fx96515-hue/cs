# AI-Powered QA System

An intelligent quality assurance system that analyzes test failures, suggests fixes using AI, and can automatically apply fixes with rollback capability.

## Features

✅ **AI-powered failure analysis** - GPT-4 integration for intelligent test failure analysis  
✅ **Auto-fix capability** - Safe, rollback-able automatic bug fixes  
✅ **Regression test generation** - Automatically generate tests to prevent bug recurrence  
✅ **CI/CD integration** - Automatic PR comments and workflow integration  
✅ **Safety mechanisms** - Backups, confidence thresholds, dry-run mode  
✅ **Comprehensive reporting** - Markdown reports with analysis details  
✅ **Health monitoring** - Continuous codebase health checks  

## Installation

The QA system is integrated into the project. Install dependencies:

```bash
pip install -r apps/api/requirements-dev.txt
```

## Configuration

Set the OpenAI API key in your environment:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Optional configuration via environment variables (prefix with `QA_`):

```bash
export QA_AI_MODEL="gpt-4-turbo-preview"
export QA_AUTO_FIX_ENABLED="false"
export QA_CONFIDENCE_THRESHOLD="85.0"
export QA_MAX_FIXES_PER_RUN="5"
```

## Usage

### Command Line Interface

#### Analyze Test Failures

Run tests and analyze failures:

```bash
cd apps/api
python -m app.qa analyze-failures --test-path tests/
```

With auto-fix enabled (high confidence only):

```bash
python -m app.qa analyze-failures --test-path tests/ --auto-fix --confidence-threshold 90
```

Limit number of fixes:

```bash
python -m app.qa analyze-failures --test-path tests/ --auto-fix --max-fixes 3
```

#### Health Check

Run comprehensive codebase health check:

```bash
python -m app.qa health-check
```

This checks:
- Test coverage
- Code quality (Ruff)
- Type safety (MyPy)
- Security (Bandit)
- Dependency vulnerabilities (Safety)

#### Generate Report

Generate a QA analysis report:

```bash
python -m app.qa generate-report --test-path tests/ --output .qa_reports/summary.md
```

#### Rollback a Fix

If an auto-fix causes issues, rollback to the backup:

```bash
python -m app.qa rollback .qa_backups/margins.py.20241230_143022.backup
```

### Python API

```python
from pathlib import Path
from app.qa.failure_analyzer import AIFailureAnalyzer, TestFailure
from app.qa.auto_fixer import AutoFixer
from app.qa.regression_generator import RegressionTestGenerator

# Analyze a failure
analyzer = AIFailureAnalyzer(api_key="your-api-key")
failure = TestFailure(
    test_name="test_calculate_margin",
    error_type="AssertionError",
    error_message="Expected 300, got 250",
    stack_trace="...",
    file_path="apps/api/tests/test_margins.py",
    line_number=42,
    test_code="...",
    source_code="..."
)

analysis = analyzer.analyze_failure(failure)
print(f"Root cause: {analysis['root_cause']}")
print(f"Confidence: {analysis['confidence']}%")

# Apply fix if confidence is high
if analysis['confidence'] >= 85:
    fixer = AutoFixer(repo_root=Path.cwd())
    result = fixer.apply_fix(
        file_path="apps/api/app/services/margins.py",
        fix_code=analysis['code_fix']
    )
    
    if result['applied']:
        print(f"✅ Fix applied! Backup: {result['backup_path']}")
        
        # Generate regression test
        reg_gen = RegressionTestGenerator(ai_client=analyzer.client)
        test_code = reg_gen.generate_regression_test(
            bug_description=analysis['root_cause'],
            fixed_code=analysis['code_fix']
        )
        
        # Save regression test
        test_file = Path("apps/api/tests/regression/test_margin_regression.py")
        test_file.parent.mkdir(exist_ok=True, parents=True)
        test_file.write_text(test_code)
```

## CI/CD Integration

The QA system integrates with GitHub Actions via the `.github/workflows/qa-auto-fix.yml` workflow.

### Automatic Analysis

The workflow runs automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main`

### Manual Trigger

Trigger manually with custom options:

1. Go to Actions tab in GitHub
2. Select "AI-Powered QA & Auto-Fix" workflow
3. Click "Run workflow"
4. Configure options:
   - Enable/disable auto-fix
   - Set confidence threshold

### PR Comments

On pull requests, the workflow automatically comments with:
- Test analysis results
- Fix suggestions
- Applied fixes (if auto-fix enabled)
- Link to full report artifact

## Safety Features

### Automatic Backups

Every fix creates a timestamped backup in `.qa_backups/`:

```
.qa_backups/
  margins.py.20241230_143022.backup
  auth.py.20241230_144510.backup
```

### Confidence Threshold

Fixes are only applied automatically if confidence meets threshold (default 85%):

```bash
python -m app.qa analyze-failures --auto-fix --confidence-threshold 90
```

### Dry Run Mode

Preview changes without applying:

```python
result = fixer.apply_fix(
    file_path="some_file.py",
    fix_code=fixed_code,
    dry_run=True
)
print(result['changes'])  # Shows diff
```

### Syntax Validation

Python code is syntax-checked before applying fixes.

### Rollback Capability

Easy rollback if a fix causes issues:

```bash
python -m app.qa rollback .qa_backups/margins.py.20241230_143022.backup
```

## Architecture

### Components

- **`failure_analyzer.py`** - AI-powered test failure analyzer
- **`auto_fixer.py`** - Automated bug fixing with rollback
- **`regression_generator.py`** - Regression test generator
- **`config.py`** - Configuration management
- **`cli.py`** - Command-line interface
- **`utils.py`** - Utility functions for parsing and health checks

### Data Flow

1. Run tests → Capture failures
2. Parse failures → Extract details
3. AI analysis → Generate fix suggestions
4. Validate fix → Check syntax
5. Apply fix (optional) → Create backup
6. Generate regression test → Prevent recurrence
7. Report results → PR comment or report file

## Configuration Reference

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `QA_AI_PROVIDER` | `openai` | AI provider (openai/anthropic/azure) |
| `QA_AI_MODEL` | `gpt-4-turbo-preview` | AI model to use |
| `QA_AI_API_KEY` | - | API key for AI provider (required) |
| `QA_AUTO_FIX_ENABLED` | `false` | Enable automatic fixes |
| `QA_CONFIDENCE_THRESHOLD` | `85.0` | Minimum confidence for auto-fix (0-100) |
| `QA_MAX_FIXES_PER_RUN` | `5` | Maximum fixes per run |
| `QA_ANALYZE_STACK_DEPTH` | `10` | Lines of stack trace to analyze |
| `QA_INCLUDE_GIT_HISTORY` | `true` | Include recent commits in analysis |
| `QA_NOTIFY_ON_FAILURE` | `true` | Send notifications on failure |
| `QA_NOTIFICATION_WEBHOOK` | - | Webhook URL for notifications |

## Examples

### Example 1: Analyze Failures Only

```bash
# Run tests and show AI analysis without fixing
python -m app.qa analyze-failures --test-path tests/
```

Output:
```
🔍 Running tests and analyzing failures...

❌ Found 2 test failures

============================================================
Analyzing failure 1/2: test_calculate_margin
  🤖 Running AI analysis...
  📊 Root Cause: Missing null check for price parameter
  🎯 Severity: medium
  💯 Confidence: 92%

  💡 Fix Suggestions:
    - Add null/None check before calculation
    - Add input validation
    - Add unit test for edge case

  ℹ️  Auto-fix disabled
```

### Example 2: Auto-Fix High Confidence Issues

```bash
# Auto-fix issues with 90%+ confidence
python -m app.qa analyze-failures --test-path tests/ --auto-fix --confidence-threshold 90
```

Output:
```
🔍 Running tests and analyzing failures...

❌ Found 1 test failures

============================================================
Analyzing failure 1/1: test_calculate_margin
  🤖 Running AI analysis...
  📊 Root Cause: Missing null check for price parameter
  🎯 Severity: medium
  💯 Confidence: 92%

  🔧 Auto-fixing (confidence: 92%)...
  ✅ Fix applied! Backup: .qa_backups/margins.py.20241230_143022.backup

  📝 Changes:
  --- apps/api/app/services/margins.py
  +++ apps/api/app/services/margins.py (fixed)
  @@ -10,6 +10,8 @@
   def calculate_margin(cost: float, price: float) -> float:
  +    if price is None:
  +        raise ValueError("Price cannot be None")
       return price - cost

  🧪 Generating regression test...
  ✅ Regression test saved: apps/api/tests/regression/test_calculate_margin_regression.py

============================================================
✨ QA Analysis Complete!
   Fixes applied: 1/1
```

### Example 3: Health Check

```bash
python -m app.qa health-check
```

Output:
```
🏥 Running Health Check...

  Checking Test Coverage...
    ✅ Coverage check not implemented yet
  Checking Code Quality (Ruff)...
    ✅ No issues found
  Checking Type Safety (MyPy)...
    ✅ No type errors
  Checking Security Scan (Bandit)...
    ✅ No security issues
  Checking Dependency Vulnerabilities...
    ✅ No vulnerabilities

📊 Overall Health Score: 100.0%
✨ Excellent codebase health!
```

## Troubleshooting

### OpenAI API Key Not Set

```
⚠️  OPENAI_API_KEY not set. Cannot perform AI analysis.
```

**Solution:** Set the environment variable:
```bash
export OPENAI_API_KEY="your-key-here"
```

### Fix Caused New Issues

**Solution:** Rollback using the backup:
```bash
python -m app.qa rollback .qa_backups/filename.TIMESTAMP.backup
```

### Confidence Too Low

If fixes aren't being applied, the confidence might be below threshold:

```bash
# Lower the threshold (use with caution)
python -m app.qa analyze-failures --auto-fix --confidence-threshold 75
```

## Best Practices

1. **Start with dry-run** - Preview changes before applying
2. **Use high confidence threshold** - Default 85% or higher for auto-fix
3. **Review backups** - Check `.qa_backups/` directory regularly
4. **Run tests after fixes** - Always verify fixes with test suite
5. **Review regression tests** - Check generated tests make sense
6. **Monitor health checks** - Run regularly to catch issues early
7. **Incremental fixes** - Fix a few issues at a time, not all at once

## License

Part of the CoffeeStudio Platform project.

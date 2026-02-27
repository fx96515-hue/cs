# AI-Powered QA System - Quick Start Guide

This guide helps you get started with the AI-powered QA system for automated test analysis and bug fixing.

## Prerequisites

- Python 3.12+
- OpenAI API key (get one at https://platform.openai.com/api-keys)

## Installation

1. **Install dependencies:**
   ```bash
   cd apps/api
   pip install -r requirements-dev.txt
   ```

2. **Set up OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   # Or add to your .env file:
   echo "QA_AI_API_KEY=your-api-key-here" >> .env
   ```

## Basic Usage

### 1. Analyze Test Failures

Run your tests and get AI analysis of failures:

```bash
cd apps/api
python -m app.qa analyze-failures --test-path tests/
```

This will:
- Run all tests in the specified path
- Parse any failures
- Use AI to analyze root causes
- Suggest fixes
- Provide prevention tips

### 2. Auto-Fix Issues (with caution!)

Enable automatic fixing for high-confidence issues:

```bash
python -m app.qa analyze-failures \
  --test-path tests/ \
  --auto-fix \
  --confidence-threshold 90
```

**Important:** 
- Start with high threshold (90+) to avoid risky fixes
- Backups are automatically created in `.qa_backups/`
- Always review changes and run tests again!

### 3. Health Check

Run a comprehensive codebase health check:

```bash
python -m app.qa health-check
```

This checks:
- Code quality (Ruff)
- Type safety (MyPy)
- Security (Bandit)
- Dependencies (Safety)

### 4. Generate Reports

Create a detailed QA report:

```bash
python -m app.qa generate-report \
  --test-path tests/ \
  --output .qa_reports/summary.md
```

## Example Workflow

Here's a typical workflow when fixing test failures:

```bash
# 1. Run tests normally first
cd apps/api
pytest tests/ -v

# 2. If failures occur, analyze them with AI
python -m app.qa analyze-failures --test-path tests/

# 3. Review suggestions and decide whether to auto-fix
# For high-confidence fixes:
python -m app.qa analyze-failures \
  --test-path tests/ \
  --auto-fix \
  --confidence-threshold 90 \
  --max-fixes 3

# 4. Run tests again to verify fixes
pytest tests/ -v

# 5. If something went wrong, rollback:
python -m app.qa rollback .qa_backups/filename.TIMESTAMP.backup

# 6. Check overall health
python -m app.qa health-check
```

## Configuration Options

You can configure the QA system via environment variables:

```bash
# AI Provider
export QA_AI_PROVIDER=openai
export QA_AI_MODEL=gpt-4-turbo-preview
export QA_AI_API_KEY=your-key

# Auto-fix settings
export QA_AUTO_FIX_ENABLED=false
export QA_CONFIDENCE_THRESHOLD=85.0
export QA_MAX_FIXES_PER_RUN=5

# Analysis settings
export QA_ANALYZE_STACK_DEPTH=10
export QA_INCLUDE_GIT_HISTORY=true
```

## CI/CD Integration

The QA system is integrated into GitHub Actions:

### Automatic on PR

The workflow runs automatically on pull requests and posts analysis as comments.

### Manual Trigger

1. Go to **Actions** → **AI-Powered QA & Auto-Fix**
2. Click **Run workflow**
3. Select branch and options:
   - Enable auto-fix: true/false
   - Confidence threshold: 85-100

### View Reports

Reports are uploaded as artifacts after each run:
- Go to the workflow run
- Download **qa-analysis-report** artifact

## Safety Features

### Backups

Every fix creates a backup:
```
.qa_backups/
  margins.py.20241230_143022.backup
  auth.py.20241230_144510.backup
```

### Rollback

If a fix causes issues:
```bash
python -m app.qa rollback .qa_backups/margins.py.20241230_143022.backup
```

### Dry Run

Preview changes without applying:
```python
from pathlib import Path
from app.qa.auto_fixer import AutoFixer

fixer = AutoFixer(repo_root=Path.cwd())
result = fixer.apply_fix(
    file_path="some_file.py",
    fix_code=fixed_code,
    dry_run=True
)
print(result['changes'])  # Shows diff
```

## Python API

You can also use the QA system programmatically:

```python
from pathlib import Path
from app.qa.failure_analyzer import AIFailureAnalyzer, TestFailure
from app.qa.auto_fixer import AutoFixer

# Analyze a failure
analyzer = AIFailureAnalyzer(api_key="your-api-key")
failure = TestFailure(
    test_name="test_example",
    error_type="AssertionError",
    error_message="Expected 3, got 2",
    stack_trace="...",
    file_path="tests/test_example.py",
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
        file_path="app/services/example.py",
        fix_code=analysis['code_fix']
    )
    
    if result['applied']:
        print(f"✅ Fix applied! Backup: {result['backup_path']}")
```

## Tips & Best Practices

1. **Start conservative** - Use high confidence threshold (90+) initially
2. **Review changes** - Always check diffs before committing
3. **Test thoroughly** - Run full test suite after applying fixes
4. **Keep backups** - Don't delete `.qa_backups/` directory
5. **Incremental fixes** - Fix a few issues at a time, not all at once
6. **Monitor health** - Run health-check regularly
7. **Check regression tests** - Review generated regression tests for quality

## Troubleshooting

### API Key Not Set
```
⚠️  OPENAI_API_KEY not set. Cannot perform AI analysis.
```
**Solution:** Export the environment variable or add to `.env`

### Low Confidence
```
ℹ️  Confidence too low (75%)
```
**Solution:** Either lower threshold or review suggestions manually

### Fix Failed
```
⚠️  Could not auto-fix: Invalid syntax in fix
```
**Solution:** Review the suggested fix manually or try with different analysis

## Getting Help

- Full documentation: `apps/api/app/qa/README.md`
- Report issues: GitHub Issues
- Check workflow logs: GitHub Actions tab

## What's Next?

- Try analyzing a real test failure
- Experiment with different confidence thresholds
- Review generated regression tests
- Integrate into your development workflow
- Set up CI/CD automation

Happy testing! 🚀

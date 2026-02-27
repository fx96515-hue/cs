"""AI-powered quality assurance command-line interface."""

import os
import sys
import subprocess
from pathlib import Path

try:
    import click
except ImportError:
    print("ERROR: click package is required. Install with: pip install click")
    sys.exit(1)

from .failure_analyzer import AIFailureAnalyzer
from .auto_fixer import AutoFixer
from .regression_generator import RegressionTestGenerator
from .utils import (
    parse_pytest_output,
    check_coverage,
    check_ruff,
    check_mypy,
    check_bandit,
    check_safety,
)


@click.group()
def qa_cli():
    """AI-powered quality assurance CLI."""
    pass


@qa_cli.command()
@click.option("--test-path", default="apps/api/tests/", help="Path to test directory")
@click.option("--auto-fix", is_flag=True, help="Automatically apply fixes")
@click.option(
    "--confidence-threshold", default=85.0, help="Min confidence for auto-fix"
)
@click.option("--max-fixes", default=5, help="Maximum number of fixes to apply")
def analyze_failures(
    test_path: str, auto_fix: bool, confidence_threshold: float, max_fixes: int
):
    """Run tests, analyze failures, and optionally auto-fix."""

    click.echo("🔍 Running tests and analyzing failures...\n")

    # Run pytest and capture failures
    result = subprocess.run(
        ["pytest", test_path, "-v", "--tb=short"],
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    if result.returncode == 0:
        click.echo("✅ All tests passed! No fixes needed.")
        return

    # Parse failures
    click.echo("📝 Parsing test failures...\n")
    failures = parse_pytest_output(result.stdout + "\n" + result.stderr)

    if not failures:
        click.echo(
            "⚠️  Tests failed but could not parse failures. Run pytest manually for details."
        )
        click.echo(result.stdout)
        return

    click.echo(f"❌ Found {len(failures)} test failures\n")

    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        click.echo("⚠️  OPENAI_API_KEY not set. Cannot perform AI analysis.")
        click.echo("Set the environment variable and try again.")
        return

    analyzer = AIFailureAnalyzer(api_key=api_key)
    fixer = AutoFixer(repo_root=Path.cwd())

    fixes_applied = 0

    for i, failure in enumerate(failures[:max_fixes], 1):
        click.echo(f"\n{'=' * 60}")
        click.echo(
            f"Analyzing failure {i}/{min(len(failures), max_fixes)}: {failure.test_name}"
        )

        try:
            # AI analysis
            click.echo("  🤖 Running AI analysis...")
            analysis = analyzer.analyze_failure(failure)

            click.echo(f"  📊 Root Cause: {analysis['root_cause']}")
            click.echo(f"  🎯 Severity: {analysis['severity']}")
            click.echo(f"  💯 Confidence: {analysis['confidence']}%")

            # Show fix suggestions
            click.echo("\n  💡 Fix Suggestions:")
            for suggestion in analysis["fix_suggestions"]:
                click.echo(f"    - {suggestion}")

            # Auto-fix if enabled and confidence is high
            if auto_fix and analysis["confidence"] >= confidence_threshold:
                click.echo(
                    f"\n  🔧 Auto-fixing (confidence: {analysis['confidence']}%)..."
                )

                fix_result = fixer.apply_fix(
                    file_path=failure.file_path,
                    fix_code=analysis["code_fix"],
                    confidence_threshold=confidence_threshold,
                    dry_run=False,
                )

                if fix_result["applied"]:
                    click.echo(f"  ✅ Fix applied! Backup: {fix_result['backup_path']}")
                    click.echo(f"\n  📝 Changes:\n{fix_result['changes'][:500]}...")

                    # Generate regression test
                    click.echo("\n  🧪 Generating regression test...")
                    try:
                        reg_gen = RegressionTestGenerator(ai_client=analyzer.client)
                        test_code = reg_gen.generate_regression_test(
                            bug_description=analysis["root_cause"],
                            fixed_code=analysis["code_fix"],
                        )

                        # Save regression test
                        test_file = Path(
                            f"apps/api/tests/regression/test_{failure.test_name}_regression.py"
                        )
                        test_file.parent.mkdir(exist_ok=True, parents=True)
                        test_file.write_text(test_code)
                        click.echo(f"  ✅ Regression test saved: {test_file}")
                    except Exception as e:
                        click.echo(f"  ⚠️  Could not generate regression test: {e}")

                    fixes_applied += 1
                else:
                    click.echo(f"  ⚠️  Could not auto-fix: {fix_result['reason']}")
            else:
                reason = (
                    f"Confidence too low ({analysis['confidence']}%)"
                    if analysis["confidence"] < confidence_threshold
                    else "Auto-fix disabled"
                )
                click.echo(f"  ℹ️  {reason}")

        except Exception as e:
            click.echo(f"  ❌ Error analyzing failure: {e}")
            continue

    click.echo(f"\n{'=' * 60}")
    click.echo("✨ QA Analysis Complete!")
    click.echo(f"   Fixes applied: {fixes_applied}/{min(len(failures), max_fixes)}")

    if fixes_applied > 0:
        click.echo("\n⚠️  Remember to run tests again to verify fixes!")


@qa_cli.command()
@click.argument("backup_path")
def rollback(backup_path: str):
    """Rollback a failed auto-fix."""
    click.echo(f"🔄 Rolling back from {backup_path}...")

    fixer = AutoFixer(repo_root=Path.cwd())
    if fixer.rollback(backup_path):
        click.echo(f"✅ Rolled back to {backup_path}")
    else:
        click.echo("❌ Rollback failed")


@qa_cli.command()
def health_check():
    """Comprehensive codebase health check."""
    click.echo("🏥 Running Health Check...\n")

    checks = [
        ("Test Coverage", check_coverage),
        ("Code Quality (Ruff)", check_ruff),
        ("Type Safety (MyPy)", check_mypy),
        ("Security Scan (Bandit)", check_bandit),
        ("Dependency Vulnerabilities", check_safety),
    ]

    results = {}
    for name, check_fn in checks:
        click.echo(f"  Checking {name}...")
        results[name] = check_fn()
        status = "✅" if results[name]["passed"] else "❌"
        click.echo(f"    {status} {results[name]['message']}")

    # Overall health score
    passed = sum(1 for r in results.values() if r["passed"])
    score = (passed / len(checks)) * 100

    click.echo(f"\n📊 Overall Health Score: {score:.1f}%")

    if score < 80:
        click.echo("⚠️  Health score below 80% - immediate attention needed!")
    elif score < 95:
        click.echo("⚙️  Health score good, minor improvements recommended")
    else:
        click.echo("✨ Excellent codebase health!")


@qa_cli.command()
@click.option("--test-path", default="apps/api/tests/", help="Path to test directory")
@click.option("--output", default=".qa_reports/summary.md", help="Output report path")
def generate_report(test_path: str, output: str):
    """Generate QA analysis report."""
    click.echo("📊 Generating QA report...\n")

    # Run tests
    result = subprocess.run(
        ["pytest", test_path, "-v", "--tb=short"], capture_output=True, text=True
    )

    # Generate report
    output_path = Path(output)
    output_path.parent.mkdir(exist_ok=True, parents=True)

    report = f"""# QA Analysis Report

Generated: {Path.cwd()}

## Test Results

Exit Code: {result.returncode}

### Output
```
{result.stdout[:1000]}
```

### Errors
```
{result.stderr[:1000]}
```
"""

    output_path.write_text(report)
    click.echo(f"✅ Report saved to {output_path}")


if __name__ == "__main__":
    qa_cli()

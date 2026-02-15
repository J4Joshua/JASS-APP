# Claude SDK Agents for JASS-APP

Use Claude SDK agents to automate code review, testing, and documentation tasks.

## Setup

```bash
# Install Claude SDK
pip install anthropic

# Set API key
export ANTHROPIC_API_KEY=your_api_key_here
```

## Example Agents

### 1. Code Review Agent

Review chord detection logic, API security, and TIS index performance.

```python
from anthropic import Anthropic
import os

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def review_jass_codebase():
    """Review JASS-APP codebase for improvements."""
    
    # Read code files
    with open("jass/chord_suggestion.py") as f:
        chord_logic = f.read()
    
    with open("main.py") as f:
        api_code = f.read()
    
    # Create review prompt
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{
            "role": "user",
            "content": f"""Review this chord detection system for:
1. Performance optimizations (TIS index queries)
2. Security issues (API endpoints, WebSocket)
3. Music theory accuracy (chord progressions)
4. Code quality (naming, structure)

CHORD SUGGESTION CODE:
{chord_logic}

API CODE:
{api_code}

Provide specific, actionable recommendations."""
        }]
    )
    
    return message.content[0].text

# Run review
if __name__ == "__main__":
    review = review_jass_codebase()
    print(review)
    
    # Save to file
    with open("code_review.md", "w") as f:
        f.write(review)
```

### 2. Test Generation Agent

Generate Jest/Pytest tests for critical paths.

```python
def generate_tests_for_modal():
    """Generate tests for Modal deployment."""
    
    with open("modal_app.py") as f:
        modal_code = f.read()
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        messages=[{
            "role": "user",
            "content": f"""Generate pytest tests for this Modal app:

{modal_code}

Focus on:
1. SessionState management (history, difficulty)
2. Pattern detection (ii-V, tritone subs)
3. Difficulty escalation logic
4. Edge cases (empty sessions, invalid chords)

Return complete pytest code with fixtures."""
        }]
    )
    
    test_code = message.content[0].text
    
    # Save test file
    with open("test_modal_app.py", "w") as f:
        f.write(test_code)
    
    print("✓ Generated test_modal_app.py")
    return test_code
```

### 3. Documentation Agent

Auto-generate API docs and setup guides.

```python
def generate_api_docs():
    """Generate OpenAPI-style documentation."""
    
    with open("main.py") as f:
        api_code = f.read()
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        messages=[{
            "role": "user",
            "content": f"""Generate OpenAPI 3.0 documentation for these FastAPI endpoints:

{api_code}

Include:
1. Request/response schemas with examples
2. WebSocket protocol documentation
3. Error codes and handling
4. Rate limiting info
5. Authentication (if any)

Return as YAML."""
        }]
    )
    
    docs = message.content[0].text
    
    with open("openapi.yaml", "w") as f:
        f.write(docs)
    
    print("✓ Generated openapi.yaml")
    return docs
```

### 4. Refactoring Agent

Suggest architectural improvements.

```python
def suggest_refactor(module: str):
    """Suggest refactoring for a module."""
    
    with open(f"jass/{module}.py") as f:
        code = f.read()
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        messages=[{
            "role": "user",
            "content": f"""Analyze this module and suggest refactoring:

{code}

Focus on:
1. Breaking down large functions
2. Improving type hints
3. Adding docstrings
4. Reducing coupling
5. Performance optimizations

Provide before/after code snippets."""
        }]
    )
    
    return message.content[0].text
```

## Agent Workflows

### Continuous Review Pipeline

```python
import schedule
import time

def automated_review_pipeline():
    """Run nightly code reviews."""
    
    print("Starting review pipeline...")
    
    # 1. Code review
    review = review_jass_codebase()
    with open(f"reviews/review_{time.strftime('%Y%m%d')}.md", "w") as f:
        f.write(review)
    
    # 2. Test generation for new code
    generate_tests_for_modal()
    
    # 3. Update documentation
    generate_api_docs()
    
    print("✓ Review pipeline complete")

# Schedule nightly
schedule.every().day.at("02:00").do(automated_review_pipeline)

# Or run on-demand
if __name__ == "__main__":
    automated_review_pipeline()
```

### Pre-Commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Run Claude code review on staged files
python backend/claude_review_staged.py

if [ $? -ne 0 ]; then
    echo "❌ Claude review found issues. Fix or override with --no-verify"
    exit 1
fi

echo "✓ Claude review passed"
```

```python
# claude_review_staged.py
import subprocess
from anthropic import Anthropic
import os

def review_staged_files():
    """Review only staged git files."""
    
    # Get staged files
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True
    )
    
    files = [f for f in result.stdout.split("\n") if f.endswith(".py")]
    
    if not files:
        print("No Python files staged")
        return True
    
    # Get diff
    diff = subprocess.run(
        ["git", "diff", "--cached"],
        capture_output=True,
        text=True
    ).stdout
    
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""Quick code review of this diff:

{diff}

Check for:
1. Syntax errors
2. Security issues
3. Breaking changes
4. Missing error handling

Respond with "PASS" if ok, or list specific issues."""
        }]
    )
    
    review = message.content[0].text
    
    if "PASS" in review:
        print("✓ Review passed")
        return True
    else:
        print("❌ Review issues:\n" + review)
        return False

if __name__ == "__main__":
    exit(0 if review_staged_files() else 1)
```

## Best Practices

1. **Context Window Management**
   - For large codebases, review module-by-module
   - Use `grep_search` to find relevant code sections
   - Summarize dependencies instead of including full files

2. **Prompt Engineering**
   - Be specific about what to review
   - Provide examples of desired output format
   - Use structured outputs (JSON/YAML) for automation

3. **Cost Optimization**
   - Cache static code context across reviews
   - Use batch processing for multiple files
   - Limit to critical paths (API endpoints, TIS index)

4. **Integration**
   - Run agents in CI/CD pipelines
   - Schedule nightly reviews
   - Integrate with GitHub Actions

## Example Output

```markdown
# Code Review: jass/chord_suggestion.py

## Performance Issues

1. **TIS Index Loading** (Line 45)
   - Current: Loads entire 10MB .npz on every query
   - Fix: Cache in memory after first load
   
   ```python
   # Before
   def suggest_chords(chroma):
       index = load_tis_index("tis_index.npz")
       ...
   
   # After
   _cached_index = None
   def suggest_chords(chroma):
       global _cached_index
       if _cached_index is None:
           _cached_index = load_tis_index("tis_index.npz")
       ...
   ```

2. **Unnecessary Sorting** (Line 102)
   - Already sorted by TIS distance, no need for second sort
   
## Security
   
✓ No issues found

## Music Theory Accuracy

3. **Voice Leading** (Line 67)
   - Missing smooth voice leading check
   - Add penalty for large interval jumps

[... more feedback ...]
```

## Next Steps

1. Run initial code review: `python claude_review.py`
2. Generate tests for Modal app: `python generate_tests.py`
3. Set up pre-commit hook for ongoing reviews
4. Integrate with GitHub Actions for PR reviews
5. Schedule nightly documentation updates

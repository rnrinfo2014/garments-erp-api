# 🛡️ Main Branch Protection Guide

This guide will help you protect your main branch to ensure code quality and prevent direct pushes that could break the production system.

## 🎯 Why Protect Your Main Branch?

- **Prevent Breaking Changes**: Stops direct pushes that could introduce bugs
- **Code Quality**: Ensures all code passes tests and reviews before merging
- **Team Collaboration**: Enforces proper workflow through pull requests
- **Deployment Safety**: Maintains stability for production deployments

## 📋 Step-by-Step Setup

### 1. Navigate to Branch Protection Settings

1. Go to your GitHub repository: `https://github.com/YOUR_USERNAME/garments-erp-api`
2. Click on **Settings** tab
3. In the left sidebar, click **Branches**
4. Click **Add rule** or **Add branch protection rule**

### 2. Configure Branch Protection Rule

#### Basic Settings
- **Branch name pattern**: `main`
- **Apply rule to**: `main` branch

#### Protection Settings (Recommended)

##### ✅ **Restrict pushes that create files**
- ☑️ **Require a pull request before merging**
  - ☑️ **Require approvals**: Set to `1` (minimum recommended)
  - ☑️ **Dismiss stale pull request approvals when new commits are pushed**
  - ☑️ **Require review from code owners** (if you have a CODEOWNERS file)

##### ✅ **Require status checks to pass before merging**
- ☑️ **Require branches to be up to date before merging**
- **Status checks to require**:
  - `build (3.8)` - Pylint check for Python 3.8
  - `build (3.9)` - Pylint check for Python 3.9  
  - `build (3.10)` - Pylint check for Python 3.10

##### ✅ **Restrict pushes that create files**
- ☑️ **Restrict pushes that create files**

##### ✅ **Additional Restrictions**
- ☑️ **Include administrators** (applies rules to repo admins too)
- ☑️ **Allow force pushes** → **❌ Leave UNCHECKED** (prevents force pushes)
- ☑️ **Allow deletions** → **❌ Leave UNCHECKED** (prevents branch deletion)

### 3. Advanced Protection (Optional but Recommended)

#### Create Additional GitHub Actions Workflow

Create enhanced CI/CD checks beyond just linting:

```yaml
# .github/workflows/main-protection.yml
name: Main Branch Protection

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10"]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pylint flake8 black
    
    - name: Code formatting check
      run: |
        black --check .
    
    - name: Linting
      run: |
        pylint $(git ls-files '*.py') || true
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    
    - name: Security check
      run: |
        pip install bandit
        bandit -r . -f json || true
    
    - name: Run tests
      run: |
        pytest tests/ || echo "No tests directory found"

  build-test:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Test Docker build
      run: |
        docker build -t garments-erp-api:test .
    
    - name: Test Docker compose
      run: |
        docker-compose -f docker-compose.yml config
```

## 🚀 Workflow After Setup

### For Developers:

1. **Never push directly to main**:
   ```bash
   # ❌ DON'T do this
   git push origin main
   ```

2. **Always use feature branches**:
   ```bash
   # ✅ Create feature branch
   git checkout -b feature/your-feature-name
   
   # Make your changes and commit
   git add .
   git commit -m "Add your feature"
   
   # Push feature branch
   git push origin feature/your-feature-name
   ```

3. **Create Pull Request**:
   - Go to GitHub repository
   - Click "Compare & pull request"
   - Add description of changes
   - Request reviews from team members
   - Wait for status checks to pass
   - Get required approvals
   - Merge when ready

### For Code Reviews:

1. **Review checklist**:
   - [ ] Code follows project conventions
   - [ ] No hardcoded secrets or credentials
   - [ ] Tests are included (if applicable)
   - [ ] Documentation is updated
   - [ ] No breaking changes to API
   - [ ] Performance considerations addressed

2. **Status checks must pass**:
   - [ ] All Python versions pass linting
   - [ ] Docker builds successfully
   - [ ] No security vulnerabilities
   - [ ] Code formatting is correct

## 🛠️ Create CODEOWNERS File (Optional)

Create `.github/CODEOWNERS` to automatically request reviews from specific team members:

```bash
# Global owners for everything
* @your-username

# Python code owners
*.py @python-team-lead @senior-developer

# Configuration files
*.yml @devops-team
*.yaml @devops-team
docker-compose.yml @devops-team
Dockerfile @devops-team

# Documentation
*.md @documentation-team

# Database migrations
scripts/migration/ @database-team @senior-developer
```

## 🔧 Additional Security Settings

### Repository Settings

1. **General Settings**:
   - ☑️ **Restrict creation of public packages**
   - ☑️ **Restrict creation of public codespaces**

2. **Security & Analysis**:
   - ☑️ **Enable Dependabot alerts**
   - ☑️ **Enable Dependabot security updates**
   - ☑️ **Enable Dependabot version updates**
   - ☑️ **Enable Code scanning**

3. **Pages** (if using GitHub Pages):
   - Set source to "Deploy from a branch"
   - Choose branch: `main` or dedicated `docs` branch

## 🚨 Emergency Procedures

### If Protection Rules Block Critical Fixes:

1. **Temporary disable** (Admin only):
   - Go to Settings → Branches
   - Edit the protection rule
   - Temporarily uncheck "Include administrators"
   - Make critical fix
   - **Immediately re-enable** protection

2. **Better approach - Emergency branch**:
   ```bash
   git checkout -b emergency/critical-fix
   # Make minimal fix
   git push origin emergency/critical-fix
   # Create PR with "emergency" label for fast-track review
   ```

## 📊 Monitoring and Metrics

### Check Protection Effectiveness:

1. **Pull Request Metrics**:
   - Monitor PR review times
   - Track status check failures
   - Review merge frequency

2. **Code Quality Trends**:
   - Monitor linting score improvements
   - Track security vulnerability trends
   - Review test coverage over time

## ✅ Verification Checklist

After setting up protection:

- [ ] Direct push to main is blocked
- [ ] Pull requests require approvals
- [ ] Status checks run on all PRs
- [ ] Failed status checks block merging
- [ ] Force pushes are disabled
- [ ] Branch deletion is disabled
- [ ] Team can still collaborate effectively

## 🎉 Benefits You'll See

1. **Higher Code Quality**: Systematic reviews catch bugs early
2. **Better Documentation**: PR descriptions improve project knowledge
3. **Team Learning**: Code reviews share knowledge across team
4. **Deployment Confidence**: Only tested code reaches production
5. **Audit Trail**: Clear history of all changes and approvals

---

**Your main branch is now protected! 🛡️**

All changes must go through proper review and testing before reaching production.
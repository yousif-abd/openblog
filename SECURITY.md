# Security Policy

## 🔐 Security Overview

This document outlines our security practices and incident response procedures for the openblog project.

## 🚨 Reporting Security Vulnerabilities

**DO NOT** open public GitHub issues for security vulnerabilities.

Instead, please email security concerns to: **federicodeponte@gmail.com**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested remediation (if any)

We will respond within 48 hours and provide updates every 72 hours until resolution.

## 🛡️ Security Measures Implemented

### Code Security
- ✅ **SQL Injection Prevention**: Parameterized queries, no f-string SQL construction
- ✅ **XSS Prevention**: HTML escaping for all user input in templates
- ✅ **CORS Protection**: Specific domain allowlist instead of wildcards
- ✅ **Input Validation**: Strict validation on all API endpoints

### Infrastructure Security
- ✅ **Secret Management**: All API keys in environment variables
- ✅ **HTTPS Only**: All production endpoints use TLS
- ✅ **Rate Limiting**: API endpoints protected against abuse
- ✅ **Authentication**: Secure session management

### Development Security
- ✅ **Pre-commit Hooks**: Automated security scanning before commits
- ✅ **GitHub Security**: Dependabot alerts, secret scanning, CodeQL analysis
- ✅ **Dependency Scanning**: Regular vulnerability checks with Safety
- ✅ **Code Analysis**: Semgrep and Bandit for static analysis

## 🔧 Security Tools & Automation

### Pre-commit Hooks (`.pre-commit-config.yaml`)
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

### Continuous Security Scanning
- **GitHub Actions**: Weekly automated security scans
- **Dependabot**: Automatic dependency vulnerability alerts
- **CodeQL**: Advanced semantic code analysis
- **Secret Scanning**: Detects exposed credentials in commits

### Manual Security Testing
```bash
# Run full security audit
semgrep --config=auto .
bandit -r . -x tests/
safety check
pip-audit
```

## 🚦 Security Incident Response

### Immediate Response (< 2 hours)
1. **Assess Impact**: Determine scope and severity
2. **Contain Threat**: Disable affected services if needed
3. **Notify Team**: Alert all stakeholders
4. **Document Timeline**: Start incident log

### Investigation (< 24 hours)
1. **Root Cause Analysis**: Identify vulnerability source
2. **Data Assessment**: Check for data exposure
3. **System Integrity**: Verify no unauthorized access

### Resolution (< 72 hours)
1. **Patch Deployment**: Fix vulnerability
2. **Security Testing**: Verify fix effectiveness
3. **Monitoring Setup**: Enhanced monitoring for recurrence

### Post-Incident (< 1 week)
1. **Lessons Learned**: Document improvements
2. **Process Updates**: Enhance security measures
3. **Team Training**: Share knowledge gained

## 🛠️ Secure Development Guidelines

### Code Review Checklist
- [ ] No hardcoded secrets or API keys
- [ ] All user input properly validated and escaped
- [ ] SQL queries use parameterized statements
- [ ] CORS policies restrict to necessary domains
- [ ] Authentication checks on protected endpoints
- [ ] Error messages don't leak sensitive information

### Environment Variables
```bash
# Required for production
GEMINI_API_KEY=your_key_here           # Never commit this!
SUPABASE_SERVICE_ROLE_KEY=your_key     # Never commit this!
REPLICATE_API_TOKEN=your_token         # Never commit this!
GOOGLE_API_KEY=your_google_key         # Never commit this!

# Use .env.example for templates
# Use .env.local for development (gitignored)
# Use proper secret management in production
```

### Dependency Management
```bash
# Regular security updates
pip install --upgrade pip
pip-review --local --auto

# Check for vulnerabilities
safety check
pip-audit

# Update pre-commit hooks
pre-commit autoupdate
```

## 📋 Security Monitoring

### Automated Alerts
- **GitHub Security Alerts**: Vulnerability notifications
- **Dependabot PRs**: Automatic security updates
- **Failed Security Scans**: CI/CD pipeline failures

### Regular Reviews
- **Weekly**: Dependency vulnerability scanning
- **Monthly**: Access permission audits
- **Quarterly**: Comprehensive security assessment
- **Annually**: Penetration testing (if applicable)

## 🔗 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Documentation](https://docs.python.org/3/library/security.html)
- [Semgrep Rules](https://semgrep.dev/r)
- [GitHub Security Features](https://docs.github.com/en/code-security)

## 📞 Emergency Contacts

- **Primary**: Federico De Ponte - federicodeponte@gmail.com
- **GitHub**: @federicodeponte

---

**Last Updated**: December 2024
**Next Review**: March 2025
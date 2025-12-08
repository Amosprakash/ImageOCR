# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: [your-email@example.com]

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the following information:

- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

## Security Best Practices

### API Keys

- Never commit API keys to version control
- Use environment variables for all secrets
- Rotate API keys regularly
- Use different keys for development and production

### Authentication

- Enable API key authentication in production
- Use strong, randomly generated API keys
- Implement rate limiting to prevent abuse

### Docker Deployment

- Use non-root user in containers
- Scan images for vulnerabilities
- Keep base images updated
- Use secrets management for sensitive data

### Network Security

- Use HTTPS in production
- Configure CORS properly (avoid wildcards)
- Implement proper firewall rules
- Use VPN for internal services

### Dependencies

- Regularly update dependencies
- Use `safety` to scan for known vulnerabilities
- Pin dependency versions in production

## Security Features

### Current Implementation

- ✅ API key authentication
- ✅ Rate limiting
- ✅ Security headers (HSTS, X-Frame-Options, etc.)
- ✅ Input validation with Pydantic
- ✅ CORS configuration
- ✅ Automated security scanning in CI/CD

### Planned Enhancements

- [ ] JWT authentication
- [ ] OAuth2 integration
- [ ] Role-based access control (RBAC)
- [ ] Audit logging
- [ ] Encryption at rest
- [ ] Web Application Firewall (WAF)

## Disclosure Policy

When we receive a security bug report, we will:

1. Confirm the problem and determine affected versions
2. Audit code to find similar problems
3. Prepare fixes for all supported versions
4. Release patches as soon as possible

## Comments on this Policy

If you have suggestions on how this process could be improved, please submit a pull request.

[![Python Lint](https://img.shields.io/github/actions/workflow/status/rsp2k/usecallmanager-services/lint.yml?branch=master&label=lint)](https://github.com/rsp2k/usecallmanager-services/actions/workflows/lint.yml) [![Version](https://img.shields.io/github/v/tag/rsp2k/usecallmanager-services?color=blue&label=version&sort=semver)](https://github.com/rsp2k/usecallmanager-services/releases) [![License](https://img.shields.io/github/license/rsp2k/usecallmanager-services?color=red)](https://github.com/rsp2k/usecallmanager-services/blob/master/LICENSE)

# Cisco IP Phone XML Services

FastAPI application providing XML services for Cisco IP phones (7900/7800/8800 series). Integrates with Asterisk Manager Interface for voicemail directory and parked calls.

## Endpoints

### Phone XML Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/authentication` | CGI/Execute request authentication |
| `/services` | Services menu with parked calls |
| `/directory` | Local directory from voicemail.conf |
| `/directory/79xx` | 7900 series menu wrapper |
| `/information` | 7900 series Info button help |
| `/quality-report` | QRT reason selection and logging |
| `/problem-report` | PRT file upload (POST) |

### Web Interface

| Endpoint | Purpose |
|----------|---------|
| `/` | Landing page |
| `/directory-ui` | Directory browser with search and export |
| `/reports` | Quality and problem reports viewer |
| `/docs` | Swagger API documentation |

### JSON API

| Endpoint | Purpose |
|----------|---------|
| `/directory/list` | Directory entries with search/pagination |
| `/directory/stats` | Entry counts and letter distribution |
| `/directory/export` | CSV and vCard export |
| `/reports/summary` | Report statistics |
| `/reports/quality` | Quality report data |
| `/reports/problem` | Problem report files |

## Quick Start with Docker

```bash
# Clone and configure
git clone https://github.com/rsp2k/usecallmanager-services.git
cd usecallmanager-services
cp .env.example .env

# Edit .env with your settings
# Start the service
make prod
```

The service will be available via your Caddy reverse proxy at the configured domain.

## Configuration

Configuration uses environment variables (with `SERVICES_` prefix) or `config.yml`:

| Environment Variable | config.yml Key | Description |
|---------------------|----------------|-------------|
| `SERVICES_REPORTS_DIR` | `reports-dir` | Log storage path (default: `/var/log/cisco`) |
| `SERVICES_CGI_USERNAME` | `cgi-username` | Phone CGI authentication username |
| `SERVICES_CGI_PASSWORD` | `cgi-password` | Phone CGI authentication password |
| `SERVICES_MANAGER_URL` | `manager-url` | Asterisk Manager HTTP endpoint |
| `SERVICES_MANAGER_USERNAME` | `manager-username` | AMI username |
| `SERVICES_MANAGER_SECRET` | `manager-secret` | AMI password |

## Development

Requires [uv](https://docs.astral.sh/uv/) for Python package management.

```bash
# Install dependencies
uv sync --dev

# Run development server (hot-reload)
SERVICES_RELOAD=true uv run usecallmanager-services

# Lint and format
uv run ruff check src tests
uv run ruff format src tests

# Run tests
uv run pytest tests/ -v
```

### Docker Development

```bash
# Development mode with hot-reload
make dev

# View logs
make logs

# Rebuild after changes
make rebuild
```

## Asterisk Configuration

Enable the Asterisk Manager web interface in `/etc/asterisk/manager.conf`:

```ini
[general]
enabled=yes
webenabled=yes

[your-username]
secret=your-secret
read=all
```

## Documentation

See [Phone Services](https://usecallmanager.nz/phone-services.html) for detailed setup instructions.

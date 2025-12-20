# Cisco IP Phone XML Services

[![Lint](https://img.shields.io/github/actions/workflow/status/rsp2k/usecallmanager-services/lint.yml?branch=master&label=lint)](https://github.com/rsp2k/usecallmanager-services/actions/workflows/lint.yml)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/github/license/rsp2k/usecallmanager-services?color=red)](LICENSE)

A modern FastAPI application providing XML services for Cisco IP phones (7900/7800/8800 series). Integrates with Asterisk Manager Interface (AMI) for real-time directory and call data.

## Features

- **Phone Directory** — Live directory from Asterisk voicemail.conf via AMI
- **Parked Calls** — Real-time parked call display from Asterisk
- **Quality Reports** — QRT logging with RTP statistics capture
- **Problem Reports** — PRT file upload and storage
- **Web Interface** — Modern UI for browsing directory and viewing reports
- **Export Options** — CSV and vCard export for directory contacts
- **Docker Ready** — Production-ready with Caddy reverse proxy integration

## Architecture

```
┌─────────────────┐     ┌──────────────────────────────────────────────┐
│   Cisco Phone   │────▶│              FastAPI Server                  │
│  7900/7800/8800 │ XML │                                              │
└─────────────────┘     │  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
                        │  │ Services │  │Directory │  │ Reports  │   │
┌─────────────────┐     │  │  Router  │  │  Router  │  │  Router  │   │
│   Web Browser   │────▶│  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│                 │JSON │       │             │             │         │
└─────────────────┘     │       └─────────────┼─────────────┘         │
                        │                     │                        │
                        │              ┌──────▼──────┐                │
                        │              │   Asterisk  │                │
                        │              │ AMI Client  │                │
                        └──────────────┴──────┬──────┴────────────────┘
                                              │ HTTP/XML
                                       ┌──────▼──────┐
                                       │  Asterisk   │
                                       │   Manager   │
                                       │  Interface  │
                                       └─────────────┘
```

## How AMI Integration Works

The application uses Asterisk's HTTP-based Manager Interface to fetch live data. No static files or database syncing required—data is always current.

### Directory from Voicemail Users

When a phone requests the directory, the server queries AMI for voicemail users:

```
Phone Request: GET /directory/entries?index=2ABC
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  1. Connect to AMI: Action=Login                      │
│  2. Query: Action=VoicemailUsersList                  │
│  3. Parse XML response for VoicemailUserEntry events  │
│  4. Extract: voicemailbox (extension), fullname       │
│  5. Filter entries by first letter matching keypad    │
│  6. Disconnect: Action=Logoff                         │
└───────────────────────────────────────────────────────┘
        │
        ▼
Phone receives: CiscoIPPhoneDirectory XML
```

The voicemail users come from Asterisk's `voicemail.conf`:

```ini
; /etc/asterisk/voicemail.conf
[default]
100 => 1234,Alice Anderson,alice@example.com
101 => 1234,Bob Brown,bob@example.com
102 => 1234,Carol Chen,carol@example.com
```

These entries become searchable directory contacts on the phones.

### Parked Calls

The services menu shows currently parked calls in real-time:

```
Phone Request: GET /services/parked-calls
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  1. Query: Action=ParkedCalls                         │
│  2. Parse ParkedCall events                           │
│  3. Extract: exten (slot), calleridname/calleridnum   │
│  4. Return as CiscoIPPhoneMenu with dial URIs         │
└───────────────────────────────────────────────────────┘
```

### Quality Reports with RTP Stats

When a user submits a quality report, the server captures RTP statistics:

```
Phone Request: GET /quality-report/send?name=SEP001122334455&reason=0
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  1. Query: Action=SIPPeers                            │
│  2. Find peer matching devicename=SEP001122334455     │
│  3. Query: Action=SIPShowPeer, Peer=<name>            │
│  4. Extract: ipaddress, status, rtprxstat, rtptxstat  │
│  5. Log to qrt-SEP001122334455.json with timestamp    │
└───────────────────────────────────────────────────────┘
```

The RTP statistics help diagnose audio quality issues:
- **rtprxstat** — Receive statistics (packets, jitter, loss)
- **rtptxstat** — Transmit statistics

## Endpoints

### Phone XML Services

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/authentication` | GET | CGI/Execute request authentication |
| `/services` | GET | Main services menu |
| `/services/parked-calls` | GET | Live parked calls list |
| `/directory` | GET | Directory letter index (keypad layout) |
| `/directory/entries` | GET | Directory entries with pagination |
| `/directory/79xx` | GET | 7900 series menu wrapper |
| `/information` | GET | 7900 series Info button help |
| `/quality-report` | GET | QRT reason selection menu |
| `/quality-report/send` | GET | Submit QRT with RTP capture |
| `/problem-report` | POST | PRT file upload |

### Web Interface

| Endpoint | Description |
|----------|-------------|
| `/` | Landing page with links |
| `/directory-ui` | Directory browser with search, sort, export |
| `/reports` | Quality and problem reports viewer |
| `/docs` | Interactive API documentation (Swagger) |

### JSON API

| Endpoint | Description |
|----------|-------------|
| `/directory/list` | Paginated directory with search |
| `/directory/stats` | Entry counts, letter distribution |
| `/directory/export` | Download as CSV or vCard |
| `/reports/summary` | Report statistics |
| `/reports/quality` | Quality report entries by device |
| `/reports/problem` | Problem report files with archive contents |

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/rsp2k/usecallmanager-services.git
cd usecallmanager-services

# Configure environment
cp .env.example .env
# Edit .env with your Asterisk AMI credentials and domain

# Start production
make prod

# Or development with hot-reload
make dev
```

### Local Development

```bash
# Requires uv (https://docs.astral.sh/uv/)
uv sync --dev

# Run with hot-reload
SERVICES_RELOAD=true uv run usecallmanager-services

# Lint
uv run ruff check src tests

# Test
uv run pytest tests/ -v
```

## Configuration

Environment variables (prefix `SERVICES_`) or `config.yml`:

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVICES_MANAGER_URL` | Asterisk Manager HTTP endpoint | `http://localhost:8088/mxml` |
| `SERVICES_MANAGER_USERNAME` | AMI username | — |
| `SERVICES_MANAGER_SECRET` | AMI password | — |
| `SERVICES_CGI_USERNAME` | Phone CGI auth username | — |
| `SERVICES_CGI_PASSWORD` | Phone CGI auth password | — |
| `SERVICES_REPORTS_DIR` | Report storage path | `/var/log/cisco` |
| `SERVICES_DOMAIN` | Caddy proxy domain | `services.local` |

## Asterisk Setup

### Enable Manager HTTP Interface

Edit `/etc/asterisk/manager.conf`:

```ini
[general]
enabled = yes
webenabled = yes
port = 5038
httptimeout = 60

[services]
secret = your-secure-password
read = system,call,log,agent,user,config,dtmf,reporting
write = originate,call,agent,user,config,command,reporting
```

Edit `/etc/asterisk/http.conf`:

```ini
[general]
enabled = yes
bindaddr = 127.0.0.1
bindport = 8088
```

Reload Asterisk:

```bash
asterisk -rx "manager reload"
asterisk -rx "http reload"
```

### Voicemail Directory Entries

The directory is built from `/etc/asterisk/voicemail.conf`:

```ini
[default]
; mailbox => password,fullname,email
100 => 1234,Alice Anderson,alice@example.com
101 => 1234,Bob Brown,bob@example.com
102 => 1234,Carol Chen,carol@example.com
```

Changes to voicemail.conf are reflected immediately—no restart needed.

## Phone Configuration

Point your phones to the services URL in CUCM or SEP config:

```xml
<servicesURL>https://phone-services.example.com/services</servicesURL>
<directoryURL>https://phone-services.example.com/directory</directoryURL>
<informationURL>https://phone-services.example.com/information</informationURL>
<authenticationURL>https://phone-services.example.com/authentication</authenticationURL>
```

For 7900 series, use `/directory/79xx` for the directory URL.

## Report Storage

Quality and problem reports are stored in `SERVICES_REPORTS_DIR`:

```
/var/log/cisco/
├── qrt-SEP001122334455.json    # Quality reports (NDJSON)
├── qrt-SEP001122334466.json
├── prt-SEP001122334455-20241219123456.tar.gz  # Problem reports
└── prt-SEP001122334455-20241220094532.tar.gz
```

Quality report entries (one JSON object per line):

```json
{"timestamp": "2024-12-19 12:34:56", "ip_address": "192.168.1.100", "status": "OK", "reason": "Audio had echo", "rtp_rx_stat": "...", "rtp_tx_stat": "..."}
```

## Resources

- [Phone Services Documentation](https://usecallmanager.nz/phone-services.html)
- [HTTP Provisioning Guide](https://usecallmanager.nz/http-provisioning.html#XML-Services)
- [Asterisk Manager Interface](https://docs.asterisk.org/Configuration/Interfaces/Asterisk-Manager-Interface-AMI/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## License

See [LICENSE](LICENSE) for details.

"""FastAPI application factory."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from .config import get_settings
from .routers import (
    authentication,
    directory,
    directory_api,
    information,
    problem_report,
    quality_report,
    reports_api,
    services,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with startup/shutdown hooks."""
    settings = get_settings()
    # Ensure reports directory exists (ignore permission errors for Docker/dev)
    try:
        settings.reports_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        pass  # Will be created in Docker with proper permissions
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    try:
        from importlib.metadata import version

        app_version = version("usecallmanager-services")
    except Exception:
        app_version = "2024.12.19"

    app = FastAPI(
        title="Cisco IP Phone XML Services",
        description="XML services for Cisco 7900/7800/8800 series IP phones",
        version=app_version,
        lifespan=lifespan,
    )

    # Register routers
    app.include_router(authentication.router)
    app.include_router(services.router)
    app.include_router(directory.router)
    app.include_router(directory_api.router)
    app.include_router(information.router)
    app.include_router(quality_report.router)
    app.include_router(problem_report.router)
    app.include_router(reports_api.router)

    @app.get("/", include_in_schema=False)
    async def index():
        """Landing page."""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cisco IP Phone XML Services</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8fafc;
            color: #334155;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            max-width: 480px;
            padding: 2rem;
            text-align: center;
        }}
        h1 {{
            font-size: 1.5rem;
            font-weight: 600;
            color: #0f172a;
            margin-bottom: 0.5rem;
        }}
        .version {{
            font-size: 0.875rem;
            color: #64748b;
            margin-bottom: 2rem;
        }}
        .endpoints {{
            background: white;
            border-radius: 0.75rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 1rem;
            margin-bottom: 1.5rem;
        }}
        .endpoints h2 {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #94a3b8;
            margin-bottom: 0.75rem;
        }}
        .endpoints a {{
            display: block;
            padding: 0.5rem;
            color: #3b82f6;
            text-decoration: none;
            border-radius: 0.375rem;
            transition: background 0.15s;
        }}
        .endpoints a:hover {{
            background: #f1f5f9;
        }}
        .docs-link {{
            display: inline-block;
            padding: 0.625rem 1.25rem;
            background: #3b82f6;
            color: white;
            text-decoration: none;
            border-radius: 0.5rem;
            font-weight: 500;
            transition: background 0.15s;
        }}
        .docs-link:hover {{
            background: #2563eb;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Cisco IP Phone XML Services</h1>
        <p class="version">v{app_version}</p>
        <div class="endpoints">
            <h2>Phone Endpoints</h2>
            <a href="/services">/services</a>
            <a href="/directory">/directory</a>
            <a href="/information">/information</a>
            <a href="/authentication">/authentication</a>
            <a href="/quality-report">/quality-report</a>
        </div>
        <a href="/directory-ui" class="docs-link">Browse Directory</a>
        <a href="/reports" class="docs-link" style="margin-left: 0.5rem;">View Reports</a>
        <a href="/docs" class="docs-link" style="margin-left: 0.5rem; background: #64748b;">API Docs</a>
    </div>
</body>
</html>"""
        return Response(content=html, media_type="text/html")

    @app.get("/reports", include_in_schema=False)
    async def reports_ui():
        """Reports viewer UI page."""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reports - Cisco IP Phone XML Services</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8fafc;
            color: #334155;
            min-height: 100vh;
        }
        .header {
            background: white;
            border-bottom: 1px solid #e2e8f0;
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .header h1 {
            font-size: 1.25rem;
            font-weight: 600;
            color: #0f172a;
        }
        .header a {
            color: #3b82f6;
            text-decoration: none;
            font-size: 0.875rem;
        }
        .header a:hover { text-decoration: underline; }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: white;
            border-radius: 0.75rem;
            padding: 1.25rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .stat-card h3 {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin-bottom: 0.5rem;
        }
        .stat-card .value {
            font-size: 1.75rem;
            font-weight: 700;
            color: #0f172a;
        }
        .stat-card .label {
            font-size: 0.875rem;
            color: #64748b;
        }
        .tabs {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .tab {
            padding: 0.625rem 1.25rem;
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 0.5rem;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 500;
            color: #64748b;
            transition: all 0.15s;
        }
        .tab:hover { border-color: #cbd5e1; }
        .tab.active {
            background: #3b82f6;
            border-color: #3b82f6;
            color: white;
        }
        .panel { display: none; }
        .panel.active { display: block; }
        .card {
            background: white;
            border-radius: 0.75rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .card-header {
            padding: 1rem 1.25rem;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .card-header h2 {
            font-size: 1rem;
            font-weight: 600;
            color: #0f172a;
        }
        .table-container { overflow-x: auto; }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
        }
        th {
            text-align: left;
            padding: 0.75rem 1rem;
            background: #f8fafc;
            font-weight: 600;
            color: #475569;
            border-bottom: 1px solid #e2e8f0;
        }
        td {
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #f1f5f9;
            color: #334155;
        }
        tr:hover td { background: #f8fafc; }
        .device-link {
            color: #3b82f6;
            text-decoration: none;
            cursor: pointer;
        }
        .device-link:hover { text-decoration: underline; }
        .badge {
            display: inline-block;
            padding: 0.25rem 0.5rem;
            font-size: 0.75rem;
            font-weight: 500;
            border-radius: 9999px;
        }
        .badge-blue { background: #dbeafe; color: #1d4ed8; }
        .badge-green { background: #dcfce7; color: #16a34a; }
        .btn {
            display: inline-block;
            padding: 0.375rem 0.75rem;
            font-size: 0.75rem;
            font-weight: 500;
            border-radius: 0.375rem;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.15s;
        }
        .btn-primary {
            background: #3b82f6;
            color: white;
            border: none;
        }
        .btn-primary:hover { background: #2563eb; }
        .btn-secondary {
            background: #f1f5f9;
            color: #475569;
            border: 1px solid #e2e8f0;
        }
        .btn-secondary:hover { background: #e2e8f0; }
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            align-items: center;
            justify-content: center;
            z-index: 100;
        }
        .modal-overlay.active { display: flex; }
        .modal {
            background: white;
            border-radius: 0.75rem;
            max-width: 800px;
            width: 90%;
            max-height: 80vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        .modal-header {
            padding: 1rem 1.25rem;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .modal-header h3 {
            font-size: 1rem;
            font-weight: 600;
        }
        .modal-close {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #64748b;
            line-height: 1;
        }
        .modal-close:hover { color: #0f172a; }
        .modal-body {
            padding: 1.25rem;
            overflow-y: auto;
            flex: 1;
        }
        .entry-card {
            padding: 1rem;
            background: #f8fafc;
            border-radius: 0.5rem;
            margin-bottom: 0.75rem;
        }
        .entry-card:last-child { margin-bottom: 0; }
        .entry-time {
            font-size: 0.75rem;
            color: #64748b;
            margin-bottom: 0.5rem;
        }
        .entry-reason {
            font-weight: 500;
            color: #0f172a;
            margin-bottom: 0.5rem;
        }
        .entry-meta {
            font-size: 0.75rem;
            color: #64748b;
        }
        .entry-meta span {
            margin-right: 1rem;
        }
        .loading {
            text-align: center;
            padding: 3rem;
            color: #64748b;
        }
        .empty {
            text-align: center;
            padding: 3rem;
            color: #94a3b8;
        }
        .size { font-family: monospace; font-size: 0.8125rem; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Phone Reports</h1>
        <a href="/">← Back to Home</a>
    </div>

    <div class="container">
        <div class="stats" id="stats">
            <div class="stat-card">
                <h3>Quality Reports</h3>
                <div class="value" id="qrt-count">-</div>
                <div class="label">total entries</div>
            </div>
            <div class="stat-card">
                <h3>QRT Devices</h3>
                <div class="value" id="qrt-devices">-</div>
                <div class="label">devices reporting</div>
            </div>
            <div class="stat-card">
                <h3>Problem Reports</h3>
                <div class="value" id="prt-count">-</div>
                <div class="label">files uploaded</div>
            </div>
            <div class="stat-card">
                <h3>PRT Storage</h3>
                <div class="value" id="prt-size">-</div>
                <div class="label">total size</div>
            </div>
        </div>

        <div class="tabs">
            <button class="tab active" data-tab="quality">Quality Reports</button>
            <button class="tab" data-tab="problem">Problem Reports</button>
        </div>

        <div class="panel active" id="quality-panel">
            <div class="card">
                <div class="card-header">
                    <h2>Quality Reports by Device</h2>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Device</th>
                                <th>Entries</th>
                                <th>Latest Report</th>
                                <th>File Size</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody id="quality-table">
                            <tr><td colspan="5" class="loading">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="panel" id="problem-panel">
            <div class="card">
                <div class="card-header">
                    <h2>Problem Report Files</h2>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Device</th>
                                <th>Timestamp</th>
                                <th>File Size</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody id="problem-table">
                            <tr><td colspan="4" class="loading">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="modal">
        <div class="modal">
            <div class="modal-header">
                <h3 id="modal-title">Quality Reports</h3>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body" id="modal-body">
            </div>
        </div>
    </div>

    <script>
        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById(tab.dataset.tab + '-panel').classList.add('active');
            });
        });

        // Format bytes
        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
        }

        // Format date
        function formatDate(dateStr) {
            if (!dateStr) return '-';
            const d = new Date(dateStr);
            return d.toLocaleString();
        }

        // Load summary stats
        async function loadSummary() {
            try {
                const res = await fetch('/reports/summary');
                const data = await res.json();
                document.getElementById('qrt-count').textContent = data.quality_reports.total_entries;
                document.getElementById('qrt-devices').textContent = data.quality_reports.device_count;
                document.getElementById('prt-count').textContent = data.problem_reports.file_count;
                document.getElementById('prt-size').textContent = formatBytes(data.problem_reports.total_size_bytes);
            } catch (e) {
                console.error('Failed to load summary:', e);
            }
        }

        // Load quality reports
        async function loadQualityReports() {
            const tbody = document.getElementById('quality-table');
            try {
                const res = await fetch('/reports/quality');
                const data = await res.json();
                if (data.devices.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" class="empty">No quality reports yet</td></tr>';
                    return;
                }
                tbody.innerHTML = data.devices.map(d => `
                    <tr>
                        <td><span class="device-link" onclick="showQualityDetails('${d.device}')">${d.device}</span></td>
                        <td><span class="badge badge-blue">${d.entry_count}</span></td>
                        <td>${d.latest_report || '-'}</td>
                        <td class="size">${formatBytes(d.size)}</td>
                        <td><button class="btn btn-secondary" onclick="showQualityDetails('${d.device}')">View</button></td>
                    </tr>
                `).join('');
            } catch (e) {
                tbody.innerHTML = '<tr><td colspan="5" class="empty">Failed to load reports</td></tr>';
            }
        }

        // Load problem reports
        async function loadProblemReports() {
            const tbody = document.getElementById('problem-table');
            try {
                const res = await fetch('/reports/problem');
                const data = await res.json();
                if (data.reports.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" class="empty">No problem reports yet</td></tr>';
                    return;
                }
                tbody.innerHTML = data.reports.map(r => `
                    <tr>
                        <td>${r.device}</td>
                        <td>${formatDate(r.timestamp)}</td>
                        <td class="size">${formatBytes(r.size)}</td>
                        <td>
                            <button class="btn btn-secondary" onclick="showProblemDetails('${r.file}')">Info</button>
                            <a class="btn btn-primary" href="/reports/problem/${r.file}/download">Download</a>
                        </td>
                    </tr>
                `).join('');
            } catch (e) {
                tbody.innerHTML = '<tr><td colspan="4" class="empty">Failed to load reports</td></tr>';
            }
        }

        // Show quality report details
        async function showQualityDetails(device) {
            document.getElementById('modal-title').textContent = 'Quality Reports - ' + device;
            document.getElementById('modal-body').innerHTML = '<div class="loading">Loading...</div>';
            document.getElementById('modal').classList.add('active');

            try {
                const res = await fetch(`/reports/quality/${device}?limit=50`);
                const data = await res.json();
                if (data.entries.length === 0) {
                    document.getElementById('modal-body').innerHTML = '<div class="empty">No entries</div>';
                    return;
                }
                document.getElementById('modal-body').innerHTML = data.entries.map(e => `
                    <div class="entry-card">
                        <div class="entry-time">${e.timestamp}</div>
                        <div class="entry-reason">${e.reason || 'No reason specified'}</div>
                        <div class="entry-meta">
                            ${e.ip_address ? `<span>IP: ${e.ip_address}</span>` : ''}
                            ${e.status ? `<span>Status: ${e.status}</span>` : ''}
                        </div>
                        ${e.rtp_rx_stat || e.rtp_tx_stat ? `
                        <div class="entry-meta" style="margin-top: 0.5rem;">
                            ${e.rtp_rx_stat ? `<span>RX: ${e.rtp_rx_stat}</span>` : ''}
                            ${e.rtp_tx_stat ? `<span>TX: ${e.rtp_tx_stat}</span>` : ''}
                        </div>
                        ` : ''}
                    </div>
                `).join('');
            } catch (e) {
                document.getElementById('modal-body').innerHTML = '<div class="empty">Failed to load details</div>';
            }
        }

        // Show problem report details
        async function showProblemDetails(filename) {
            document.getElementById('modal-title').textContent = 'Problem Report Details';
            document.getElementById('modal-body').innerHTML = '<div class="loading">Loading...</div>';
            document.getElementById('modal').classList.add('active');

            try {
                const res = await fetch(`/reports/problem/${filename}`);
                const data = await res.json();
                let contentsHtml = '<div class="empty">Unable to read archive contents</div>';
                if (data.contents && data.contents.length > 0) {
                    contentsHtml = `
                        <table style="width:100%">
                            <thead><tr><th>File</th><th>Size</th></tr></thead>
                            <tbody>
                                ${data.contents.filter(c => c.type === 'file').map(c => `
                                    <tr><td>${c.name}</td><td class="size">${formatBytes(c.size)}</td></tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `;
                }
                document.getElementById('modal-body').innerHTML = `
                    <div style="margin-bottom: 1rem;">
                        <strong>Device:</strong> ${data.device}<br>
                        <strong>Timestamp:</strong> ${formatDate(data.timestamp)}<br>
                        <strong>File Size:</strong> ${formatBytes(data.size)}<br>
                        <a class="btn btn-primary" href="/reports/problem/${filename}/download" style="margin-top: 0.75rem;">Download Archive</a>
                    </div>
                    <h4 style="margin-bottom: 0.75rem; font-size: 0.875rem; color: #475569;">Archive Contents</h4>
                    ${contentsHtml}
                `;
            } catch (e) {
                document.getElementById('modal-body').innerHTML = '<div class="empty">Failed to load details</div>';
            }
        }

        // Close modal
        function closeModal() {
            document.getElementById('modal').classList.remove('active');
        }

        // Close modal on overlay click
        document.getElementById('modal').addEventListener('click', (e) => {
            if (e.target.id === 'modal') closeModal();
        });

        // Close modal on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeModal();
        });

        // Initial load
        loadSummary();
        loadQualityReports();
        loadProblemReports();
    </script>
</body>
</html>"""
        return Response(content=html, media_type="text/html")

    @app.get("/directory-ui", include_in_schema=False)
    async def directory_ui():
        """Directory browser UI page."""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Directory - Cisco IP Phone XML Services</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8fafc;
            color: #334155;
            min-height: 100vh;
        }
        .header {
            background: white;
            border-bottom: 1px solid #e2e8f0;
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .header h1 {
            font-size: 1.25rem;
            font-weight: 600;
            color: #0f172a;
        }
        .header a {
            color: #3b82f6;
            text-decoration: none;
            font-size: 0.875rem;
        }
        .header a:hover { text-decoration: underline; }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 2rem;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: white;
            border-radius: 0.75rem;
            padding: 1.25rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .stat-card h3 {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin-bottom: 0.5rem;
        }
        .stat-card .value {
            font-size: 1.75rem;
            font-weight: 700;
            color: #0f172a;
        }
        .stat-card .label {
            font-size: 0.875rem;
            color: #64748b;
        }
        .search-bar {
            display: flex;
            gap: 0.75rem;
            margin-bottom: 1.5rem;
        }
        .search-input {
            flex: 1;
            padding: 0.75rem 1rem;
            font-size: 1rem;
            border: 1px solid #e2e8f0;
            border-radius: 0.5rem;
            outline: none;
            transition: border-color 0.15s, box-shadow 0.15s;
        }
        .search-input:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        .search-input::placeholder { color: #94a3b8; }
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem 1.25rem;
            font-size: 0.875rem;
            font-weight: 500;
            border-radius: 0.5rem;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.15s;
            border: none;
        }
        .btn-primary {
            background: #3b82f6;
            color: white;
        }
        .btn-primary:hover { background: #2563eb; }
        .btn-secondary {
            background: white;
            color: #475569;
            border: 1px solid #e2e8f0;
        }
        .btn-secondary:hover { background: #f8fafc; }
        .dropdown {
            position: relative;
            display: inline-block;
        }
        .dropdown-content {
            display: none;
            position: absolute;
            right: 0;
            top: 100%;
            margin-top: 0.25rem;
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 0.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            z-index: 10;
            min-width: 140px;
        }
        .dropdown:hover .dropdown-content { display: block; }
        .dropdown-item {
            display: block;
            padding: 0.625rem 1rem;
            font-size: 0.875rem;
            color: #334155;
            text-decoration: none;
            cursor: pointer;
            border: none;
            background: none;
            width: 100%;
            text-align: left;
        }
        .dropdown-item:hover { background: #f8fafc; }
        .dropdown-item:first-child { border-radius: 0.5rem 0.5rem 0 0; }
        .dropdown-item:last-child { border-radius: 0 0 0.5rem 0.5rem; }
        .card {
            background: white;
            border-radius: 0.75rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .card-header {
            padding: 1rem 1.25rem;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .card-header h2 {
            font-size: 1rem;
            font-weight: 600;
            color: #0f172a;
        }
        .result-count {
            font-size: 0.875rem;
            color: #64748b;
        }
        .table-container { overflow-x: auto; }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
        }
        th {
            text-align: left;
            padding: 0.75rem 1rem;
            background: #f8fafc;
            font-weight: 600;
            color: #475569;
            border-bottom: 1px solid #e2e8f0;
            cursor: pointer;
            user-select: none;
            transition: background 0.15s;
        }
        th:hover { background: #f1f5f9; }
        th.sorted { color: #3b82f6; }
        th .sort-icon {
            margin-left: 0.25rem;
            opacity: 0.5;
        }
        th.sorted .sort-icon { opacity: 1; }
        td {
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #f1f5f9;
            color: #334155;
        }
        tr:hover td { background: #f8fafc; }
        .extension {
            font-family: 'SF Mono', Monaco, Consolas, monospace;
            font-size: 0.875rem;
            color: #0f172a;
            font-weight: 500;
        }
        .name-cell {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        .avatar {
            width: 2rem;
            height: 2rem;
            border-radius: 50%;
            background: #e2e8f0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 600;
            color: #64748b;
        }
        .call-link {
            color: #3b82f6;
            text-decoration: none;
            font-size: 0.875rem;
        }
        .call-link:hover { text-decoration: underline; }
        .loading {
            text-align: center;
            padding: 3rem;
            color: #64748b;
        }
        .empty {
            text-align: center;
            padding: 3rem;
            color: #94a3b8;
        }
        .pagination {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 1rem;
            border-top: 1px solid #e2e8f0;
        }
        .page-btn {
            padding: 0.5rem 0.75rem;
            font-size: 0.875rem;
            border: 1px solid #e2e8f0;
            border-radius: 0.375rem;
            background: white;
            color: #475569;
            cursor: pointer;
            transition: all 0.15s;
        }
        .page-btn:hover:not(:disabled) {
            border-color: #3b82f6;
            color: #3b82f6;
        }
        .page-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .page-info {
            font-size: 0.875rem;
            color: #64748b;
            margin: 0 1rem;
        }
        .error-banner {
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 0.5rem;
            padding: 1rem;
            margin-bottom: 1.5rem;
            color: #dc2626;
            font-size: 0.875rem;
        }
        .letter-bar {
            display: flex;
            flex-wrap: wrap;
            gap: 0.25rem;
            margin-bottom: 1.5rem;
        }
        .letter-btn {
            width: 2rem;
            height: 2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 600;
            border: 1px solid #e2e8f0;
            border-radius: 0.375rem;
            background: white;
            color: #64748b;
            cursor: pointer;
            transition: all 0.15s;
        }
        .letter-btn:hover {
            border-color: #3b82f6;
            color: #3b82f6;
        }
        .letter-btn.active {
            background: #3b82f6;
            border-color: #3b82f6;
            color: white;
        }
        .letter-btn.has-entries { color: #0f172a; font-weight: 700; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Phone Directory</h1>
        <a href="/">← Back to Home</a>
    </div>

    <div class="container">
        <div class="stats" id="stats">
            <div class="stat-card">
                <h3>Total Entries</h3>
                <div class="value" id="total-entries">-</div>
                <div class="label">directory contacts</div>
            </div>
            <div class="stat-card">
                <h3>Named Entries</h3>
                <div class="value" id="named-entries">-</div>
                <div class="label">with full names</div>
            </div>
        </div>

        <div id="error-container"></div>

        <div class="search-bar">
            <input type="text" id="search" class="search-input" placeholder="Search by name or extension...">
            <div class="dropdown">
                <button class="btn btn-secondary">Export ▾</button>
                <div class="dropdown-content">
                    <button class="dropdown-item" onclick="exportDirectory('csv')">Download CSV</button>
                    <button class="dropdown-item" onclick="exportDirectory('vcard')">Download vCard</button>
                </div>
            </div>
        </div>

        <div class="letter-bar" id="letter-bar"></div>

        <div class="card">
            <div class="card-header">
                <h2>Directory Entries</h2>
                <span class="result-count" id="result-count"></span>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th onclick="setSort('name')" id="th-name" class="sorted">
                                Name <span class="sort-icon">↑</span>
                            </th>
                            <th onclick="setSort('extension')" id="th-extension">
                                Extension <span class="sort-icon">↑</span>
                            </th>
                            <th style="width: 100px;"></th>
                        </tr>
                    </thead>
                    <tbody id="directory-table">
                        <tr><td colspan="3" class="loading">Loading...</td></tr>
                    </tbody>
                </table>
            </div>
            <div class="pagination" id="pagination"></div>
        </div>
    </div>

    <script>
        let currentSort = 'name';
        let currentOrder = 'asc';
        let currentSearch = '';
        let currentOffset = 0;
        let letterDistribution = {};
        const pageSize = 25;

        // Debounce helper
        function debounce(fn, delay) {
            let timer;
            return function(...args) {
                clearTimeout(timer);
                timer = setTimeout(() => fn.apply(this, args), delay);
            };
        }

        // Get initials from name
        function getInitials(name) {
            if (!name) return '?';
            const parts = name.trim().split(/\\s+/);
            if (parts.length === 1) return parts[0][0].toUpperCase();
            return (parts[0][0] + parts[parts.length-1][0]).toUpperCase();
        }

        // Load stats
        async function loadStats() {
            try {
                const res = await fetch('/directory/stats');
                const data = await res.json();
                if (data.error) {
                    showError(data.error);
                    return;
                }
                document.getElementById('total-entries').textContent = data.total_entries;
                document.getElementById('named-entries').textContent = data.named_entries;
                letterDistribution = data.letter_distribution || {};
                renderLetterBar();
            } catch (e) {
                showError('Failed to connect to server');
            }
        }

        // Render letter filter bar
        function renderLetterBar() {
            const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
            const bar = document.getElementById('letter-bar');
            bar.innerHTML = letters.map(l => {
                const hasEntries = letterDistribution[l] > 0;
                return `<button class="letter-btn ${hasEntries ? 'has-entries' : ''}"
                    onclick="filterByLetter('${l}')" title="${letterDistribution[l] || 0} entries">${l}</button>`;
            }).join('') + '<button class="letter-btn" onclick="clearLetterFilter()" title="Show all">All</button>';
        }

        // Filter by first letter
        function filterByLetter(letter) {
            document.querySelectorAll('.letter-btn').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('search').value = '';
            currentSearch = letter;
            currentOffset = 0;
            loadDirectory();
        }

        // Clear letter filter
        function clearLetterFilter() {
            document.querySelectorAll('.letter-btn').forEach(b => b.classList.remove('active'));
            currentSearch = '';
            document.getElementById('search').value = '';
            currentOffset = 0;
            loadDirectory();
        }

        // Show error
        function showError(message) {
            document.getElementById('error-container').innerHTML = `
                <div class="error-banner">${message}</div>
            `;
        }

        // Clear error
        function clearError() {
            document.getElementById('error-container').innerHTML = '';
        }

        // Set sort
        function setSort(field) {
            if (currentSort === field) {
                currentOrder = currentOrder === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort = field;
                currentOrder = 'asc';
            }
            updateSortUI();
            loadDirectory();
        }

        // Update sort UI
        function updateSortUI() {
            document.querySelectorAll('th').forEach(th => {
                th.classList.remove('sorted');
                th.querySelector('.sort-icon').textContent = '↑';
            });
            const th = document.getElementById('th-' + currentSort);
            th.classList.add('sorted');
            th.querySelector('.sort-icon').textContent = currentOrder === 'asc' ? '↑' : '↓';
        }

        // Load directory
        async function loadDirectory() {
            const tbody = document.getElementById('directory-table');
            tbody.innerHTML = '<tr><td colspan="3" class="loading">Loading...</td></tr>';
            clearError();

            try {
                const params = new URLSearchParams({
                    search: currentSearch,
                    sort: currentSort,
                    order: currentOrder,
                    limit: pageSize,
                    offset: currentOffset
                });
                const res = await fetch('/directory/list?' + params);
                const data = await res.json();

                if (data.error) {
                    showError(data.error);
                    tbody.innerHTML = '<tr><td colspan="3" class="empty">Unable to load directory</td></tr>';
                    return;
                }

                document.getElementById('result-count').textContent =
                    `${data.total} ${data.total === 1 ? 'entry' : 'entries'}`;

                if (data.entries.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="3" class="empty">No entries found</td></tr>';
                    document.getElementById('pagination').innerHTML = '';
                    return;
                }

                tbody.innerHTML = data.entries.map(e => `
                    <tr>
                        <td>
                            <div class="name-cell">
                                <div class="avatar">${getInitials(e.name)}</div>
                                <span>${e.name || '<i style="color:#94a3b8">No name</i>'}</span>
                            </div>
                        </td>
                        <td><span class="extension">${e.extension}</span></td>
                        <td><a href="tel:${e.extension}" class="call-link">Call</a></td>
                    </tr>
                `).join('');

                // Render pagination
                const totalPages = Math.ceil(data.total / pageSize);
                const currentPage = Math.floor(currentOffset / pageSize) + 1;

                if (totalPages > 1) {
                    document.getElementById('pagination').innerHTML = `
                        <button class="page-btn" onclick="goToPage(1)" ${currentPage === 1 ? 'disabled' : ''}>First</button>
                        <button class="page-btn" onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>Prev</button>
                        <span class="page-info">Page ${currentPage} of ${totalPages}</span>
                        <button class="page-btn" onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
                        <button class="page-btn" onclick="goToPage(${totalPages})" ${currentPage === totalPages ? 'disabled' : ''}>Last</button>
                    `;
                } else {
                    document.getElementById('pagination').innerHTML = '';
                }
            } catch (e) {
                showError('Failed to load directory');
                tbody.innerHTML = '<tr><td colspan="3" class="empty">Connection error</td></tr>';
            }
        }

        // Go to page
        function goToPage(page) {
            currentOffset = (page - 1) * pageSize;
            loadDirectory();
        }

        // Export directory
        async function exportDirectory(format) {
            try {
                const res = await fetch('/directory/export?format=' + format);
                const data = await res.json();

                if (data.error) {
                    showError(data.error);
                    return;
                }

                // Create download
                const blob = new Blob([data.content], { type: data.content_type });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = data.filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            } catch (e) {
                showError('Export failed');
            }
        }

        // Search handler
        const handleSearch = debounce((value) => {
            document.querySelectorAll('.letter-btn').forEach(b => b.classList.remove('active'));
            currentSearch = value;
            currentOffset = 0;
            loadDirectory();
        }, 300);

        document.getElementById('search').addEventListener('input', (e) => {
            handleSearch(e.target.value);
        });

        // Initial load
        loadStats();
        loadDirectory();
    </script>
</body>
</html>"""
        return Response(content=html, media_type="text/html")

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler."""
        return Response(content=str(exc), media_type="text/plain", status_code=500)

    return app


# Application instance for uvicorn
app = create_app()

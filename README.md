# ClipX

Self-hosted clipboard and file sync server. Copy on one device, paste on another — with file sharing and an admin panel.

## Features

- **Clipboard Sync** — Push clipboard content from any device and pull it on others
- **File Sharing** — Upload files with configurable TTL, auto-cleanup on expiry
- **Device Management** — Register devices with unique secret keys via admin panel
- **Admin Panel** — Built-in dark-themed web UI to manage clips, files, and devices
- **JWT Auth** — Secure admin login with JWT tokens
- **CORS** — Works with browser extensions and local dev servers
- **SQLite** — Zero-dependency database, no setup required

## Architecture

```
POST   /v1/clips         Create a clip (device auth)
GET    /v1/clips         List recent clips
DELETE /v1/clips/:id     Delete a clip
POST   /v1/files         Upload a file
GET    /v1/files         List active files
GET    /v1/files/:id/download  Download a file
DELETE /v1/files/:id     Delete a file
GET    /v1/devices       List devices
DELETE /v1/devices/:id   Remove a device
GET    /admin            Admin panel (login required)
POST   /v1/admin/login   Admin login
```

## Quick Start

```bash
# Clone
git clone https://github.com/rjamitsharma/clipx.git
cd clipx

# Configure
cp .env.example .env
# Edit .env with your credentials

# Install
pip install -r requirements.txt

# Run
python main.py
```

Go to `http://localhost:5000/admin` to access the admin panel.

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `ADMIN_EMAIL` | Admin login email | — |
| `ADMIN_PASSWORD` | Admin login password | — |
| `JWT_SECRET` | Secret for signing admin JWT tokens | — |
| `FILES_DIR` | Directory for uploaded files | `uploads` |
| `FILE_TTL_MINUTES` | File expiry time in minutes | `30` |

## Deployment

The project includes `passenger_wsgi.py` for Phusion Passenger deployments (cPanel, shared hosting). Set `application` as the WSGI entry point in Passenger.

## License

MIT © rjamitsharma

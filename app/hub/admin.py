from __future__ import annotations

import html
from typing import Iterable

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from app.hub.config import HubSettings, get_settings, hash_token, reset_settings_cache
from app.hub.storage import bundle_exists, get_bundle_path, read_metadata, summarize_bundle

ADMIN_COOKIE_NAME = "wb_hub_admin"
ADMIN_SESSION_MAX_AGE = 60 * 60 * 12  # 12 hours

admin_router = APIRouter()


def _load_settings() -> HubSettings:
    # Admin edits often happen out-of-band (CLI or file edits), so bust cache per request.
    reset_settings_cache()
    return get_settings()


def _current_admin(request: Request, settings: HubSettings):
    cookie_value = request.cookies.get(ADMIN_COOKIE_NAME)
    if not cookie_value:
        return None
    return settings.admin_for_hash(cookie_value)


def _render_disabled_page(settings: HubSettings) -> str:
    return f"""
    <!DOCTYPE html>
    <html lang=\"en\">
      <head>
        <meta charset=\"utf-8\">
        <title>Hub Admin Disabled</title>
        <style>
          body {{
            font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
            background: #0f172a;
            color: #f1f5f9;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
          }}
          .panel {{
            background: rgba(15, 23, 42, 0.8);
            border-radius: 18px;
            padding: 2rem;
            max-width: 560px;
            width: 100%;
            box-shadow: 0 25px 60px rgba(15, 23, 42, 0.5);
          }}
          h1 {{
            margin-top: 0;
            font-size: 1.8rem;
          }}
          code {{
            background: rgba(15, 23, 42, 0.6);
            padding: 0.2rem 0.35rem;
            border-radius: 6px;
          }}
        </style>
      </head>
      <body>
        <section class=\"panel\">
          <h1>Admin dashboard locked</h1>
          <p>This hub has no admin tokens configured. Generate one from the CLI to enable the dashboard:</p>
          <pre><code>./wb hub admin-token --config {settings.config_path}</code></pre>
          <p>After restarting the hub, revisit this page.</p>
        </section>
      </body>
    </html>
    """


def _render_login_page(error: bool) -> str:
    error_block = ""
    if error:
        error_block = "<p class=\"error\">Invalid token. Try again.</p>"
    return f"""
    <!DOCTYPE html>
    <html lang=\"en\">
      <head>
        <meta charset=\"utf-8\">
        <title>Hub Admin Login</title>
        <style>
          body {{
            font-family: 'Inter', system-ui, sans-serif;
            background: linear-gradient(135deg, #1c1c3c, #3a2f73);
            color: #f7f7ff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
          }}
          form {{
            background: rgba(0, 0, 0, 0.4);
            padding: 2rem;
            border-radius: 20px;
            width: 100%;
            max-width: 420px;
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.35);
          }}
          label {{
            display: block;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: rgba(255, 255, 255, 0.8);
          }}
          input {{
            width: 100%;
            padding: 0.85rem 1rem;
            border-radius: 12px;
            border: none;
            margin-bottom: 1.2rem;
            font-size: 1rem;
          }}
          button {{
            width: 100%;
            padding: 0.85rem;
            border-radius: 12px;
            border: none;
            font-size: 1rem;
            background: #38bdf8;
            color: #0f172a;
            font-weight: 600;
            cursor: pointer;
          }}
          .error {{
            background: rgba(239, 68, 68, 0.15);
            border-left: 3px solid #ef4444;
            padding: 0.75rem;
            border-radius: 8px;
            margin-bottom: 1rem;
          }}
        </style>
      </head>
      <body>
        <form method=\"post\" action=\"/admin/login\" autocomplete=\"off\">
          <h1>Hub Admin</h1>
          <p class=\"muted\">Enter the access token generated via <code>./wb hub admin-token</code>.</p>
          {error_block}
          <label for=\"token\">Access token</label>
          <input id=\"token\" name=\"token\" type=\"password\" required placeholder=\"•••••••••••••••\">
          <button type=\"submit\">Sign in</button>
        </form>
      </body>
    </html>
    """


def _format_peer_rows(rows: Iterable[dict]) -> str:
    return "".join(
        f"<tr>"
        f"<td>{html.escape(row['name'])}</td>"
        f"<td>{'Yes' if row['has_bundle'] else 'No'}</td>"
        f"<td>{row['file_count']}</td>"
        f"<td>{row['size_kb']} KB</td>"
        f"<td>{html.escape(row['signed_at'])}</td>"
        f"<td><code>{html.escape(row['digest'])}</code></td>"
        f"<td><code>{html.escape(row['public_key_short'])}</code></td>"
        "</tr>"
        for row in rows
    ) or "<tr><td colspan=7>No peers configured.</td></tr>"


def _gather_peer_stats(settings: HubSettings) -> tuple[list[dict], int, int]:
    rows: list[dict] = []
    total_files = 0
    total_bytes = 0
    for peer in sorted(settings.peers.values(), key=lambda p: p.name.lower()):
        bundle_root = get_bundle_path(settings, peer)
        has_bundle = bundle_exists(settings, peer)
        metadata = read_metadata(settings, peer) or {}
        summary = summarize_bundle(bundle_root) if has_bundle else {"file_count": 0, "total_bytes": 0}
        total_files += summary["file_count"]
        total_bytes += summary["total_bytes"]
        rows.append(
            {
                "name": peer.name,
                "has_bundle": has_bundle,
                "file_count": summary["file_count"],
                "size_kb": summary["total_bytes"] // 1024,
                "signed_at": metadata.get("signed_at", "—"),
                "digest": metadata.get("manifest_digest", "—"),
                "public_key_short": f"…{peer.public_key[-16:]}" if peer.public_key else "—",
            }
        )
    return rows, total_files, total_bytes


def _render_dashboard(settings: HubSettings, admin_name: str) -> str:
    peer_rows, total_files, total_bytes = _gather_peer_stats(settings)
    table_rows = _format_peer_rows(peer_rows)
    storage = html.escape(str(settings.storage_dir))
    config_path = html.escape(str(settings.config_path))
    return f"""
    <!DOCTYPE html>
    <html lang=\"en\">
      <head>
        <meta charset=\"utf-8\">
        <title>Hub Admin</title>
        <style>
          body {{
            font-family: 'Inter', system-ui, sans-serif;
            background: #050816;
            color: #f1f5f9;
            min-height: 100vh;
            margin: 0;
          }}
          header {{
            padding: 1.5rem 3vw;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(12px);
            position: sticky;
            top: 0;
          }}
          main {{
            padding: 2rem 3vw 4rem;
          }}
          h1 {{
            margin: 0 0 0.5rem;
          }}
          table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1.5rem;
          }}
          th, td {{
            text-align: left;
            padding: 0.65rem 0.75rem;
            border-bottom: 1px solid rgba(148, 163, 184, 0.2);
          }}
          th {{
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 0.08em;
            color: #94a3b8;
          }}
          code {{
            background: rgba(15, 23, 42, 0.6);
            padding: 0.15rem 0.35rem;
            border-radius: 6px;
          }}
          .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
          }}
          .stat {{
            background: rgba(15, 23, 42, 0.55);
            padding: 1rem;
            border-radius: 16px;
          }}
          .badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
          }}
          form.logout {{
            margin: 0;
          }}
          form.logout button {{
            background: transparent;
            border: 1px solid rgba(248, 250, 252, 0.4);
            color: #f8fafc;
            padding: 0.5rem 1rem;
            border-radius: 999px;
            cursor: pointer;
          }}
        </style>
      </head>
      <body>
        <header>
          <div>
            <h1>Hub Control</h1>
            <p class=\"badge\">Signed in as {html.escape(admin_name)}</p>
          </div>
          <form method=\"post\" action=\"/admin/logout\" class=\"logout\">
            <button type=\"submit\">Sign out</button>
          </form>
        </header>
        <main>
          <section class=\"stats\">
            <div class=\"stat\">
              <p class=\"label\">Config path</p>
              <code>{config_path}</code>
            </div>
            <div class=\"stat\">
              <p class=\"label\">Storage dir</p>
              <code>{storage}</code>
            </div>
            <div class=\"stat\">
              <p class=\"label\">Loose push</p>
              <strong>{'Enabled' if settings.allow_auto_register_push else 'Disabled'}</strong>
            </div>
            <div class=\"stat\">
              <p class=\"label\">Loose pull</p>
              <strong>{'Enabled' if settings.allow_auto_register_pull else 'Disabled'}</strong>
            </div>
          </section>
          <p style=\"margin-top:2rem;\">Peers: {len(peer_rows)} · Files: {total_files} · Size: {total_bytes // 1024} KB</p>
          <table>
            <thead>
              <tr>
                <th>Peer</th>
                <th>Bundle</th>
                <th>Files</th>
                <th>Size</th>
                <th>Signed</th>
                <th>Digest</th>
                <th>Public key</th>
              </tr>
            </thead>
            <tbody>
              {table_rows}
            </tbody>
          </table>
        </main>
      </body>
    </html>
    """


@admin_router.get("/admin", response_class=HTMLResponse)
async def admin_home(request: Request) -> HTMLResponse:
    settings = _load_settings()
    if not settings.has_admin_tokens():
        return HTMLResponse(_render_disabled_page(settings))
    admin = _current_admin(request, settings)
    if not admin:
        error = request.query_params.get("error") == "invalid"
        return HTMLResponse(_render_login_page(error))
    return HTMLResponse(_render_dashboard(settings, admin_name=admin.name))


@admin_router.post("/admin/login")
async def admin_login(
    request: Request,
    token: str = Form(...),
):
    settings = _load_settings()
    if not settings.has_admin_tokens():
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    token_hash = hash_token(token)
    admin = settings.admin_for_hash(token_hash)
    if not admin:
        response = RedirectResponse(url="/admin?error=invalid", status_code=status.HTTP_303_SEE_OTHER)
        response.delete_cookie(ADMIN_COOKIE_NAME)
        return response
    response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    secure_cookie = request.url.scheme == "https"
    response.set_cookie(
        ADMIN_COOKIE_NAME,
        token_hash,
        max_age=ADMIN_SESSION_MAX_AGE,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
    )
    return response


@admin_router.post("/admin/logout")
async def admin_logout() -> RedirectResponse:
    response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(ADMIN_COOKIE_NAME)
    return response


__all__ = ["admin_router"]

#!/usr/bin/env bash
#
# One-shot installer for the CheckPause API server.
#
# Run as root on the Ubuntu box:
#
#     bash /srv/checkpause/server/deploy/install.sh
#
# Safe to run again after a `git pull`: it refreshes the virtual environment,
# reinstalls the unit files, and restarts the service.

set -euo pipefail

REPO_URL="https://github.com/Comet-zzz/CheckPause.git"
APP_DIR="/srv/checkpause"
SERVICE_USER="checkpause"
SERVICE_NAME="checkpause"

log() {
    printf '\n==> %s\n' "$1"
}

if [ "$(id -u)" -ne 0 ]; then
    echo "Run this script as root." >&2
    exit 1
fi

log "Service account"
if id "$SERVICE_USER" >/dev/null 2>&1; then
    echo "    $SERVICE_USER already exists"
else
    useradd --system --create-home --shell /usr/sbin/nologin "$SERVICE_USER"
    echo "    created $SERVICE_USER"
fi

log "Source code in $APP_DIR"
# The tree belongs to the service account while this script runs as root, and
# git refuses to touch a repository owned by somebody else unless it is listed
# as safe. Setting the key (rather than adding to it) keeps this idempotent.
git config --system safe.directory "$APP_DIR"
if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" pull --ff-only
else
    git clone "$REPO_URL" "$APP_DIR"
fi

# The pull above may have replaced this very script, but bash keeps reading the
# copy it started with. Re-exec once so edits to the installer take effect in
# the same invocation instead of silently waiting for the next one.
if [ "${CHECKPAUSE_REEXEC:-0}" != "1" ]; then
    export CHECKPAUSE_REEXEC=1
    exec bash "$0" "$@"
fi

log "Python virtual environment"
if [ ! -x "$APP_DIR/.venv/bin/python" ]; then
    python3 -m venv "$APP_DIR/.venv"
fi
"$APP_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$APP_DIR/.venv/bin/pip" install --quiet -r "$APP_DIR/server/requirements.txt"

# Everything above ran as root; hand the tree to the service account last.
log "Ownership"
chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"

# Secrets and the tuned prompt live here, never in the checkout. The service
# account owns the directory so only it (and root) can read what is inside.
log "Configuration directory /etc/checkpause"
install -d -m 750 -o "$SERVICE_USER" -g "$SERVICE_USER" /etc/checkpause
install -m 640 -o "$SERVICE_USER" -g "$SERVICE_USER" \
    "$APP_DIR/server/deploy/env.example" /etc/checkpause/env.example

if [ -f /etc/checkpause/env ]; then
    echo "    env file present"
else
    echo "    no env file yet - copy env.example and add the API key:"
    echo "      install -m 640 -o $SERVICE_USER -g $SERVICE_USER \\"
    echo "          /etc/checkpause/env.example /etc/checkpause/env"
fi

if [ -f /etc/checkpause/system_prompt.txt ]; then
    echo "    tuned prompt present"
else
    echo "    no tuned prompt yet - the built-in placeholder is in use"
fi

# The SQLite ledger lives here. The unit asks systemd for the same directory,
# but creating it explicitly keeps the mode right and means a manual run does
# not end up with a root-owned database.
log "State directory /var/lib/checkpause"
install -d -m 750 -o "$SERVICE_USER" -g "$SERVICE_USER" /var/lib/checkpause
if [ -f /var/lib/checkpause/checkpause.db ]; then
    echo "    ledger present"
    # The unit sets UMask so new files are private, but a ledger created
    # before that existed keeps its old mode. Pin it on every deploy.
    chmod 600 /var/lib/checkpause/checkpause.db
else
    echo "    no ledger yet - it is created on first start"
fi

log "systemd unit"
install -m 644 "$APP_DIR/server/deploy/checkpause.service" \
    "/etc/systemd/system/$SERVICE_NAME.service"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME" >/dev/null
systemctl restart "$SERVICE_NAME"

log "nginx site"
install -m 644 "$APP_DIR/server/deploy/nginx-checkpause.conf" \
    /etc/nginx/sites-available/checkpause
ln -sf /etc/nginx/sites-available/checkpause /etc/nginx/sites-enabled/checkpause
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

log "Login banner"
install -m 755 "$APP_DIR/server/deploy/checkpause-motd.sh" \
    /etc/update-motd.d/99-checkpause

log "Waiting for the app to answer on 127.0.0.1:8000"
for _ in $(seq 1 20); do
    if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then
        echo "    the app is up"
        break
    fi
    sleep 0.5
done

log "Through nginx"
curl -fsS http://127.0.0.1/health
echo

log "Service status"
systemctl --no-pager --lines=0 status "$SERVICE_NAME" || true

log "Done"

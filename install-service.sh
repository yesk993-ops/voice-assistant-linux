#!/bin/bash
# Install J.A.R.V.I.S. systemd user service manually
# Usage: bash install-service.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_SRC="$SCRIPT_DIR/voice_assistant/jarvis.service"

if [ ! -f "$SERVICE_SRC" ]; then
    echo "ERROR: jarvis.service template not found at $SERVICE_SRC"
    exit 1
fi

# Fill in the real install path
SERVICE_CONTENT=$(cat "$SERVICE_SRC")
SERVICE_CONTENT="${SERVICE_CONTENT//__INSTALL_DIR__/$SCRIPT_DIR}"

# Install to systemd user directory
SYSTEMD_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_DIR"
echo "$SERVICE_CONTENT" > "$SYSTEMD_DIR/jarvis.service"

# Reload systemd (may fail in containers/sandbox, that's OK)
systemctl --user daemon-reload 2>/dev/null || true

echo ""
echo "=== J.A.R.V.I.S. SERVICE INSTALLED ==="
echo ""
echo "  SYSTEMD SERVICE: $SYSTEMD_DIR/jarvis.service"
echo ""
echo "  Start:   systemctl --user start jarvis"
echo "  Stop:    systemctl --user stop jarvis"
echo "  Restart: systemctl --user restart jarvis"
echo "  Enable:  systemctl --user enable jarvis"
echo "  Status:  systemctl --user status jarvis"
echo "  Logs:    journalctl --user -u jarvis -f"
echo ""
echo "  Then open: http://localhost:5000"
echo ""
echo "========================================"

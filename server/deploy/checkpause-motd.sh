#!/bin/sh
#
# Login banner for the CheckPause server.
# Installed to /etc/update-motd.d/99-checkpause by server/deploy/install.sh.

if [ -d /srv/checkpause ]; then
    printf '\n'
    printf '  CheckPause server\n'
    printf '    docs   : /srv/checkpause/server/README.md\n'
    printf '    status : systemctl status checkpause\n'
    printf '    logs   : journalctl -u checkpause -n 50\n'
    printf '\n'
fi

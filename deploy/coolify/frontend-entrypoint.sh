#!/bin/sh
set -eu

API_BASE="${API_BASE:-https://api.aistoryadventure.xyz}"

cat > /usr/share/nginx/html/config.js <<EOF_CONFIG
(function () {
  window.AI_STORY_CONFIG = {
    API_BASE: "${API_BASE}",
  };
})();
EOF_CONFIG

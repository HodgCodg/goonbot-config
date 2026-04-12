#!/bin/bash
# Pre-transpile React JSX to avoid ~8s in-browser Babel overhead
# Usage: ./build.sh then serve /home/botvm/.openclaw/workspace/static/

set -e
echo "Building dashboard..."

SRC="/home/botvm/.openclaw/workspace/static/index.html"
OUT="/home/botvm/.openclaw/workspace/static/index.built.html"
BUNDLE="/home/botvm/.openclaw/workspace/static/bundle.js"

# Backup original
cp "$SRC" "${SRC}.bak"

# Extract HTML head (everything before body)
sed -n '1,/<\/head>/p' "$SRC" > "$OUT"

# Add body with inline loader
cat >> "$OUT" << 'EOF'
</head>
<body style="opacity:0;transition:opacity 0.3s">
  <div id="root"></div>
  <script>
document.body.style.opacity='1';
document.getElementById('root').innerHTML='<div style="display:flex;flex-direction:column;justify-content:center;align-items:center;height:100vh;color:#94a3b8;font-family:sans-serif;font-size:14px;gap:12px"><span>⚡ Loading dashboard...</span><span style="font-size:12px;color:#64748b">First load may take a moment</span></div>';
  </script>
EOF

# Extract React code from babel script and write to bundle.js
grep -oP '(?s)(?<="type=text/babel">)[^<]*(?=</script>)' "$SRC" > "$BUNDLE"

# Append closing tags with CDN scripts
cat >> "$OUT" << 'EOF'
  <script src="https://cdnjs.cloudflare.com/ajax/libs/react/18.2.0/umd/react.production.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.2.0/umd/react-dom.production.min.js"></script>
  <script src="/bundle.js" type="text/babel"></script>
</body>
</html>
EOF

echo "Build complete! Serve index.built.html instead of index.html"
echo "Note: Still uses in-browser Babel. For true speed, use Vite/Webpack pre-bundling."

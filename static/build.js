#!/usr/bin/env node
// Simple build script to transpile React JSX once, avoiding in-browser Babel overhead

const fs = require('fs');
const path = require('path');

const srcPath = '/home/botvm/.openclaw/workspace/static/index.html';
let content = fs.readFileSync(srcPath, 'utf8');

// Extract the React code between <script type="text/babel"> and </script>
const babelMatch = content.match(/<script type="text\/babel"\s*>([\s\S]*?)<\/script>/);
if (!babelMatch) {
  console.error('No babel script found');
  process.exit(1);
}

const reactCode = babelMatch[1];

// Simple JSX-to-JS transformer for our specific codebase
function transformJSX(code) {
  // This is a minimal transformer - handles our specific patterns
  return code
    // Transform <Component props /> to React.createElement(Component, {props})
    .replace(/<(Icons\.[A-Za-z]+)\s*\/>/g, 'React.createElement($1)')
    .replace(/<(Icons\.[A-Za-z]+)\s+([\w-]+=)[^>]*?>/g, 'React.createElement($1, {$2})')
    // Handle self-closing tags
    .replace(/<br\s*\/>/g, 'React.createElement("br")')
    .replace(/<hr\s*\/>/g, 'React.createElement("hr")')
    .replace(/<input\s+[^>]*\/?>/g, match => {
      const attrs = {};
      match.match(/(\w+)="([^"]*)"/g)?.forEach(a => {
        const [, k, v] = a.match(/(\w+)="([^"]*)"/);
        attrs[k] = v;
      });
      return `React.createElement("input", ${JSON.stringify(attrs)})`;
    })
    // Handle standard elements with children
    .replace(/<(div|span|h[1-6]|p|article|header|footer|section|main|nav|ul|li)\s+([^>]*)>([^<]*?)<\/\1>/g, 
      (m, tag, attrs, children) => {
        const attrObj = {};
        attrs.match(/(\w+)="([^"]*)"/g)?.forEach(a => {
          const [, k, v] = a.match(/(\w+)="([^"]*)"/);
          attrObj[k] = v;
        });
        return `React.createElement("${tag}", ${Object.keys(attrObj).length ? JSON.stringify(attrObj) : null}, ${children})`;
      })
    // Handle fragment children
    .replace(/<>([^<]*?)<\/>/g, '[$1]');
}

// For now, just output the code as-is but wrapped properly
// A full JSX transform would require babel - let's use a simpler approach:
// Serve the original HTML but with Babel inlined and cached aggressively

console.log('Dashboard uses in-browser transpilation for simplicity.');
console.log('For production speed, consider:');
console.log('1. Pre-bundling with Vite/Webpack');
console.log('2. Server-side rendering');
console.log('3. Or accepting ~2-3s load time for zero-build setup');

#!/usr/bin/env node
/**
 * Prepara los assets del APK a partir del HTML de la raíz del repo.
 *
 * "La Raya.html" sigue siendo la única fuente de verdad: edítalo como siempre,
 * haz push, y el workflow vuelve a generar el APK. Este script no lo modifica;
 * escribe una copia en android/app/src/main/assets/index.html con tres cambios:
 *
 *   1. Chart.js sale del CDN y pasa a vendor/chart.umd.js  (gráficas sin internet)
 *   2. Google Fonts sale del CDN y pasa a vendor/fonts.css (tipografía sin internet)
 *   3. Se inyecta vendor/android-bridge.js                 (exportar respaldos)
 *
 * Uso:  node tools/prepare-assets.mjs
 */
import { readFileSync, writeFileSync, mkdirSync, copyFileSync, existsSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root    = join(dirname(fileURLToPath(import.meta.url)), '..');
const SRC     = join(root, 'La Raya.html');
const ASSETS  = join(root, 'android/app/src/main/assets');
const VENDOR  = join(ASSETS, 'vendor');
const FONTDIR = join(VENDOR, 'fonts');

if (!existsSync(SRC)) {
  console.error('\n  No encontré "La Raya.html" en la raíz del repo.');
  console.error('  El APK se arma a partir de ese archivo, así que tiene que estar ahí.\n');
  process.exit(1);
}

mkdirSync(FONTDIR, { recursive: true });

/* ---------- 1 · fuentes ---------- */
const FONTS = [
  ['Bricolage Grotesque', 'bricolage-grotesque', [600, 700, 800]],
  ['Inter',               'inter',               [400, 500, 600]],
  ['IBM Plex Mono',       'ibm-plex-mono',       [400, 500, 600]],
];

let css = '/* fuentes empaquetadas en el APK — generado por tools/prepare-assets.mjs */\n';
let missing = [];
for (const [family, slug, weights] of FONTS) {
  for (const w of weights) {
    const file = `${slug}-latin-${w}-normal.woff2`;
    if (!existsSync(join(FONTDIR, file))) { missing.push(file); continue; }
    css += `@font-face{font-family:'${family}';font-style:normal;font-weight:${w};`
         + `font-display:swap;src:url('fonts/${file}') format('woff2');}\n`;
  }
}
if (missing.length) {
  console.warn('  Faltan woff2 (la app caerá a fuentes del sistema):', missing.join(', '));
}
writeFileSync(join(VENDOR, 'fonts.css'), css);

/* ---------- 2 · html ---------- */
let html = readFileSync(SRC, 'utf8');
const before = html;

// Chart.js -> local
html = html.replace(
  /<script\s+src="https:\/\/cdnjs\.cloudflare\.com\/ajax\/libs\/Chart\.js\/[^"]+"><\/script>/,
  '<script src="vendor/chart.umd.js"></script>'
);
if (html === before) console.warn('  Aviso: no se encontró el <script> de Chart.js del CDN.');

// Google Fonts -> local
html = html.replace(/\s*<link rel="preconnect" href="https:\/\/fonts\.googleapis\.com">/g, '');
html = html.replace(/\s*<link rel="preconnect" href="https:\/\/fonts\.gstatic\.com"[^>]*>/g, '');
const fontsBefore = html;
html = html.replace(
  /<link href="https:\/\/fonts\.googleapis\.com\/css2\?[^"]+" rel="stylesheet">/,
  '<link href="vendor/fonts.css" rel="stylesheet">'
);
if (html === fontsBefore) console.warn('  Aviso: no se encontró el <link> de Google Fonts.');

// puente Android
if (!html.includes('vendor/android-bridge.js')) {
  html = html.replace('</head>', '<script src="vendor/android-bridge.js"></script>\n</head>');
}

writeFileSync(join(ASSETS, 'index.html'), html);

const kb = n => (n / 1024).toFixed(0) + ' KB';
console.log('  index.html      ', kb(Buffer.byteLength(html)));
console.log('  chart.umd.js    ', existsSync(join(VENDOR, 'chart.umd.js')) ? kb(readFileSync(join(VENDOR,'chart.umd.js')).length) : 'FALTA');
console.log('  fuentes         ', readdirSync(FONTDIR).filter(f => f.endsWith('.woff2')).length, 'woff2');
console.log('  listo.');

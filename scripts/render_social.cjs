// Development-only rasterizer. The deployed site uses the committed PNG.
const fs = require('node:fs');
const path = require('node:path');
const { Resvg } = require('@resvg/resvg-js');
const root = path.join(__dirname, '..');
const illustrationPath = path.join(root, 'assets/bengaluru-illustration.svg');
let art = fs.readFileSync(illustrationPath, 'utf8');
// SVGs used through <img> cannot reliably load a separate bitmap resource.
// Embed a display-sized copy of the original logo so the artwork is self-contained.
const logo = fs.readFileSync(path.join(root, 'assets/kannada.png')).toString('base64');
const logoSource = `<svg xmlns="http://www.w3.org/2000/svg" width="480" height="96" viewBox="0 0 1563 313"><image width="1563" height="313" href="data:image/png;base64,${logo}"/></svg>`;
const logoPng = new Resvg(logoSource).render().asPng().toString('base64');
const branding = `  <g id="kannada-brand" aria-label="TaskMetro logo in Kannada">
    <rect x="24" y="24" width="336" height="88" rx="14" fill="#183E32" stroke="#D7E1CB" stroke-opacity=".45"/>
    <image x="34" y="36" width="316" height="64" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,${logoPng}"/>
  </g>`;
art = art.replace(/\n\s*<g id="kannada-brand"[^>]*>[\s\S]*?<\/g>/g, '');
const closingTag = art.lastIndexOf('</svg>');
if (closingTag < 0) throw new Error('Missing illustration SVG root.');
art = art.slice(0, closingTag) + branding + '\n' + art.slice(closingTag);
fs.writeFileSync(illustrationPath, art);
// The sharing card already has its English wordmark; keep its city scene uncluttered.
const socialArt = art.replace(/\n\s*<g id="kannada-brand"[^>]*>[\s\S]*?<\/g>/g, '');
const body = socialArt.slice(socialArt.indexOf('>') + 1, socialArt.lastIndexOf('</svg>'));
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
<rect width="1200" height="630" fill="#faf8f2"/>
<rect x="56" y="48" width="178" height="42" rx="8" fill="#183e32"/>
<text x="76" y="77" fill="#f2d065" font-family="sans-serif" font-size="24" font-weight="700">TaskMetro.</text>
<text x="58" y="158" fill="#526849" font-family="sans-serif" font-size="13" font-weight="600" letter-spacing="2">BENGALURU ERRAND &amp; CONCIERGE SERVICES</text>
<text x="54" y="255" fill="#183e32" font-family="Georgia,serif" font-size="78">Your person</text>
<text x="54" y="340" fill="#183e32" font-family="Georgia,serif" font-size="78">in Bengaluru.</text>
<text x="58" y="416" fill="#56715a" font-family="Georgia,serif" font-size="52" font-style="italic">Wherever you are.</text>
<text x="59" y="482" fill="#56665e" font-family="sans-serif" font-size="20">Local hands. Clear quotes. Peace of mind.</text>
<svg x="686" y="70" width="461" height="423" viewBox="0 0 720 660" fill="none">${body}</svg>
<path d="M58 552h1084" stroke="#d1dacb"/>
<text x="59" y="592" fill="#183e32" font-family="sans-serif" font-size="17">Document pickups · Property errands · Local assistance</text>
</svg>`;
fs.writeFileSync(path.join(root, 'assets/social-card.svg'), svg + '\n');
fs.writeFileSync(path.join(root, 'assets/social-card.png'), new Resvg(svg, {
  font: { loadSystemFonts: true, defaultFontFamily: 'Arial' }
}).render().asPng());
console.log('Rendered 1200×630 sharing image.');

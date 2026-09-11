import {build} from 'esbuild';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {readFileSync,writeFileSync} from 'node:fs';
const here=path.dirname(fileURLToPath(import.meta.url));
await build({entryPoints:[path.join(here,'app.js')],bundle:true,format:'iife',minify:true,
  outfile:path.resolve(here,'../../reve/reve.bundle.js'),legalComments:'external',target:['es2020']});
const output=path.resolve(here,'../../reve/reve.bundle.js');
// Quelques chunks GLSL tiers ont des espaces de fin de ligne, sans signification.
writeFileSync(output,readFileSync(output,'utf8').replace(/[ \t]+$/gm,''));
console.log('Bundle du rêve reconstruit.');

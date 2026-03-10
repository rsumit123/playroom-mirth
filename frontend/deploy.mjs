#!/usr/bin/env node
/**
 * Deploy frontend to Vercel using the v13 Deployments API with inline files.
 * Avoids the Vercel CLI project-mismatch issue.
 */
import { readFileSync, readdirSync, statSync } from 'fs';
import { join, relative } from 'path';

const PROJECT_ID = 'prj_TzR8Kl9n6ptmU1yLRhkS5Ntz0hXs';
const DIST_DIR = new URL('./dist', import.meta.url).pathname;

// Get Vercel token
let token;
try {
  const authPath = join(process.env.HOME, 'Library/Application Support/com.vercel.cli/auth.json');
  const auth = JSON.parse(readFileSync(authPath, 'utf-8'));
  token = auth.token;
} catch {
  try {
    token = readFileSync(join(process.env.HOME, '.vercel-token'), 'utf-8').trim();
  } catch {
    console.error('No Vercel token found');
    process.exit(1);
  }
}

function collectFiles(dir, base = dir) {
  const files = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const stat = statSync(full);
    if (stat.isDirectory()) {
      files.push(...collectFiles(full, base));
    } else {
      const rel = relative(base, full);
      const data = readFileSync(full).toString('base64');
      files.push({ file: rel, data, encoding: 'base64' });
    }
  }
  return files;
}

// Read vercel.json for SPA routing
let routes = [];
try {
  const vj = JSON.parse(readFileSync(new URL('./vercel.json', import.meta.url), 'utf-8'));
  if (vj.rewrites) {
    routes = [{ handle: 'filesystem' }, ...vj.rewrites.map(r => ({ src: r.source, dest: r.destination }))];
  }
} catch {}

const files = collectFiles(DIST_DIR);
console.log(`Deploying ${files.length} files from dist/...`);

const body = {
  name: 'charade-chat',
  project: PROJECT_ID,
  target: 'production',
  files,
  projectSettings: { framework: null, buildCommand: '', installCommand: '', outputDirectory: '.' },
  ...(routes.length ? { routes } : {}),
};

const res = await fetch('https://api.vercel.com/v13/deployments?teamId=team_2ErjNuuM6a2FLAjvJEnkxgkY', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(body),
});

const data = await res.json();
if (!res.ok) {
  console.error('Deploy failed:', data);
  process.exit(1);
}
console.log(`Deployed: https://${data.url}`);
console.log(`Status: ${data.readyState || data.status}`);
if (data.alias?.length) {
  console.log('Aliases:', data.alias.join(', '));
}

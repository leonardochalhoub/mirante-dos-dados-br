#!/usr/bin/env node
// Gera app/public/articles/_meta.json com timestamps de "última geração" de cada
// artigo (Working Paper). Roda em `prebuild` (npm) — tanto local quanto em CI.
//
// Estratégia de timestamp:
//  - "tex_last_edited"  = git log -1 --format=%cI -- articles/<slug>.tex
//                         (timestamp do último commit que tocou o .tex)
//  - "manifest_built_at" = ISO timestamp do momento em que esse script roda
//                         (= momento real de compilação no CI)
//
// O front-end (DocCardWP4/WP6/etc) exibe o que for mais relevante: em geral
// "tex_last_edited" é o "data da última versão do artigo".

import { execSync } from 'node:child_process';
import { existsSync, mkdirSync, readdirSync, writeFileSync } from 'node:fs';
import { join, basename, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname  = dirname(__filename);
const REPO_ROOT  = resolve(__dirname, '..');

const ARTICLES_SRC_DIR = join(REPO_ROOT, 'articles');
const ARTICLES_OUT_DIR = join(REPO_ROOT, 'app', 'public', 'articles');

function gitTimestamp(filePath) {
  try {
    const out = execSync(`git log -1 --format=%cI -- "${filePath}"`, {
      cwd: REPO_ROOT, encoding: 'utf8',
    }).trim();
    return out || null;
  } catch {
    return null;
  }
}

function gitShortSha(filePath) {
  try {
    const out = execSync(`git log -1 --format=%h -- "${filePath}"`, {
      cwd: REPO_ROOT, encoding: 'utf8',
    }).trim();
    return out || null;
  } catch {
    return null;
  }
}

function buildMeta() {
  if (!existsSync(ARTICLES_SRC_DIR)) {
    console.warn(`[articles-meta] articles/ source dir not found, skipping`);
    return;
  }
  if (!existsSync(ARTICLES_OUT_DIR)) {
    mkdirSync(ARTICLES_OUT_DIR, { recursive: true });
  }

  const texFiles = readdirSync(ARTICLES_SRC_DIR).filter((f) => f.endsWith('.tex'));
  const articles = {};

  for (const file of texFiles) {
    const slug    = basename(file, '.tex');
    const fullTex = join(ARTICLES_SRC_DIR, file);
    articles[slug] = {
      tex_last_edited: gitTimestamp(fullTex),
      tex_last_sha:    gitShortSha(fullTex),
    };
  }

  const manifest = {
    manifest_built_at: new Date().toISOString(),
    articles,
  };

  const outPath = join(ARTICLES_OUT_DIR, '_meta.json');
  writeFileSync(outPath, JSON.stringify(manifest, null, 2));
  const count = Object.keys(articles).length;
  console.log(`[articles-meta] ${count} artigos · escrito em ${outPath}`);
}

buildMeta();

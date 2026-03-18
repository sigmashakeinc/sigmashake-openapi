---
name: deploy
description: Build and deploy sigmashake.com to Cloudflare Pages.
disable-model-invocation: true
argument-hint: "[--skip-build] [--skip-tests]"
allowed-tools: Bash(trunk *), Bash(npx wrangler *), Bash(cargo *), Bash(test *), Bash(find *), Bash(grep *), Bash(sigmashake-governance *), Read
---

# Deploy to Cloudflare Pages

Build the site and deploy to Cloudflare Pages. Runs the full quality pipeline unless `--skip-tests` is passed.

## Steps

1. **Pre-flight checks** (unless `$ARGUMENTS` contains `--skip-tests`):
   ```bash
   cargo fmt --check --quiet
   cargo clippy --workspace --quiet -- -D warnings 2>&1 | head -20
   cargo test --workspace --lib --quiet 2>&1 | tail -5
   ```
   If any fail, stop and report the error. Do NOT deploy broken code.

2. **Build** (unless `$ARGUMENTS` contains `--skip-build`):
   ```bash
   trunk build --release 2>&1 | tail -5
   ```

3. **Smoke tests** (always run):
   ```bash
   test -d dist && test -f dist/index.html && test -f dist/_redirects
   find dist -name '*.wasm' -print -quit | grep -q .
   grep -q 'Content-Security-Policy' dist/index.html
   ```
   If any fail, stop. Do NOT deploy.

4. **Deploy**:
   ```bash
   npx wrangler pages deploy dist/ --project-name=sigmashake --commit-dirty=true 2>&1
   ```

5. **Report**: Print the deployment URL and confirm success.

## Rules

- Never deploy if tests, build, or smoke tests fail.
- Always use `--commit-dirty=true` (builds happen outside git's clean state).
- The site is at `sigmashake.pages.dev` and custom domain `sigmashake.com`.
- Auth: `wrangler login` or `CLOUDFLARE_API_TOKEN` env var must be configured.

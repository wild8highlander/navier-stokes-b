# 📱 Guide: Publishing navier-stokes-b to GitHub from Android (Termux)

A step-by-step guide for the **wild8highlander** account. Time: ~10 minutes once;
every later publish is a single command `./push_wild8highlander.sh`.

---

## Step 0. One-time preparation on GitHub (from any device)

1. Sign in at https://github.com as `wild8highlander`.
2. Create an **empty** repository: **New repository** →
   name `navier-stokes-b` → do **not** add a README, .gitignore or a license
   (the folder already ships all of them) → **Create repository**.
3. Create an access token: **Settings → Developer settings →
   Personal access tokens → Tokens (classic) → Generate new token (classic)**:
   - Note: `termux-push`;
   - Expiration: as you prefer (90 days);
   - Scope: ☑ **repo** (full);
   - **Generate token** and **copy it immediately**
     (`ghp_…`) — the page will not show it again.

## Step 1. Install Termux

Install **from F-Droid only** (the Play Market build is outdated):
https://f-droid.org/packages/com.termux/

After installing, open Termux and update packages:

```bash
pkg update && pkg upgrade -y
pkg install git unzip -y
```

## Step 2. Move the archive to the phone

Option A — the archive is already on the phone:

```bash
termux-setup-storage          # grant storage access (creates ~/storage)
cd ~/storage/downloads        # or ~/storage/shared — wherever you saved it
unzip navier-stokes-b.zip -d ~
cd ~/navier-stokes-b
```

Option B — download straight from Termux (if the archive is behind a direct link):

```bash
pkg install wget -y
wget <DIRECT_LINK_TO_navier-stokes-b.zip> -O ~/nsb.zip
unzip ~/nsb.zip -d ~
cd ~/navier-stokes-b
```

## Step 3. Initialize git (only if the folder is not a git repository yet)

```bash
git init -b main
```

## Step 4. Push the repository

```bash
chmod +x push_wild8highlander.sh
./push_wild8highlander.sh
```

The script sets `origin` to `https://github.com/wild8highlander/navier-stokes-b.git`
by itself, commits and pushes. On the first run you will be asked for:

```
Username for 'https://github.com': wild8highlander
Password for 'https://wild8highlander@github.com': <paste the PAT from Step 0.3>
```

⚠️ Paste the **token** (`ghp_…`), not your GitHub password. To paste in Termux:
long press → *Paste*. The characters are not displayed — that is normal, press Enter.

The credentials are remembered (`credential.helper store`) — later pushes ask nothing.

## Step 5. Verify the result

Open https://github.com/wild8highlander/navier-stokes-b — the files are there.

---

## Subsequent publishes

```bash
cd ~/navier-stokes-b
./push_wild8highlander.sh "one-sentence description of what changed"
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Authentication failed` | The token expired or was copied incompletely — create a new one (Step 0.3) |
| `Repository not found` | The repository was not created or the name has a typo — recheck Step 0.2 |
| `remote origin already exists` | Not an error: the script refreshes the origin URL itself |
| `error: src refspec main…` | Run `git init -b main` first (Step 3), then retry |
| Push "hangs" on a slow network | Retry the command; the repository is ~100 MB, mobile uploads may take minutes |
| Termux dies in the background | Take **Acquire wakelock** in the notification bar before pushing |

## Git cheat sheet (if you need it manually)

```bash
git status                        # what changed
git add -A                        # stage everything
git commit -m "message"           # commit
git push origin main              # publish
git pull --rebase                 # fetch upstream changes
```

*IPL-RP-1.0: the content is the property of Isaev Iskhak Khamzatovich (wild8highlander). All rights reserved.*

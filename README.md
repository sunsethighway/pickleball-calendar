# Pickleball England Calendar

Auto-updating Google Calendar subscription for all Pickleball England tournaments.

A GitHub Action scrapes [pickleballengland.org/tournaments](https://www.pickleballengland.org/tournaments/) every morning at 07:00 UTC, generates `calendar.ics`, and commits it back to the repo. GitHub Pages serves the file as a public URL that Google Calendar subscribes to — so your calendar stays up to date automatically. Totally free.

---

## One-time setup (~10 minutes)

### 1. Create the GitHub repo

1. Go to [github.com/new](https://github.com/new)
2. Name it **`pickleball-calendar`**
3. Set it to **Public** (required for GitHub Pages)
4. Click **Create repository**

### 2. Upload these files

Upload all files from this folder to the repo root:
- `scrape.py`
- `requirements.txt`
- `.github/workflows/update-calendar.yml`
- `README.md`

*(Drag-and-drop in the GitHub web UI works fine, or use `git push` if you prefer.)*

### 3. Enable GitHub Pages

1. In the repo, go to **Settings → Pages**
2. Under **Source**, select **Deploy from a branch**
3. Branch: **main**, folder: **/ (root)**
4. Click **Save**

After a minute or so, GitHub will show you your Pages URL — it'll look like:
```
https://YOUR-USERNAME.github.io/pickleball-calendar/
```

### 4. Run the action for the first time

1. Go to **Actions → Update Pickleball Calendar**
2. Click **Run workflow → Run workflow**
3. Wait ~30 seconds — it should go green and commit `calendar.ics`

### 5. Subscribe in Google Calendar

Your calendar.ics URL will be:
```
https://YOUR-USERNAME.github.io/pickleball-calendar/calendar.ics
```

In Google Calendar:
1. Click **+** next to **Other calendars → From URL**
2. Paste the URL above
3. Click **Add calendar**

That's it — Google Calendar will check for updates periodically (usually every 24 hours).

---

## How it works

```
GitHub Actions (daily cron)
  └── runs scrape.py
        └── fetches pickleballengland.org/tournaments/
        └── parses 3 tables (PbE, PickleB, All Others)
        └── writes calendar.ics
  └── commits calendar.ics if changed
  └── GitHub Pages serves calendar.ics as a public URL
        └── Google Calendar subscribes to the URL
```

## Running locally

```bash
pip install -r requirements.txt
python scrape.py
# → writes calendar.ics
```

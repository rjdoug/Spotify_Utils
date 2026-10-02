# Spotify Discography Discovery Harvester

I built this tool because I keep a rolling playlist of bands I listen to, and whenever I want to deep-dive into their back catalogs, doing it manually is a massive slog. 

If you've ever tried to dump an entire artist's discography into a playlist on Spotify, you know how messy it gets:
- You end up with 3 or 4 copies of the same track because of pre-release singles, deluxe editions, and anniversary remasters.
- Half the queue gets clogged with live bootlegs, crowd noise, and festival cuts.
- Track-by-track commentaries, interviews, and spoken-word interludes interrupt the music.
- 30-second intro tracks and soundbites clutter the tracklist.

This script takes a source playlist, extracts every unique artist from it, crawls their full catalog of albums and singles, filters out the junk, deduplicates repeated songs, and builds clean discovery playlists directly in your library.

---

## What It Handles

- **Scrapes any source playlist:** Pulls all unique artists whether your starter playlist has 20 songs or 800+.
- **Deduplication that actually works:** Normalizes track titles across standalone singles, EPs, and deluxe albums without accidentally butchering real songs that have hyphens or brackets in the title.
- **Filters the noise:** Drops live recordings (`- Live`, `Live at...`), radio sessions (Audiotree, KEXP), commentary tracks, demos, and short skits (< 60s), while keeping legitimate studio acoustic versions intact.
- **Built for Spotify Dev Mode limits:** Spotify strictly enforces a hard cap of 10 items per page on catalog endpoints in development mode. The crawler pages through releases properly and handles rate limits automatically so it doesn't crash halfway through.
- **Auto-splits large queues:** Spotify caps playlists at 10,000 tracks. If the scraped discographies exceed that limit, the script automatically splits them into private sequentially numbered playlists (`Part 1`, `Part 2`, etc.).

---

## Setup

### 1. Clone & install dependencies

```bash
git clone <REPO_URL>
cd Spotify_All_Artists_Playlist
pip install spotipy python-dotenv requests urllib3
```

### 2. Configure `.env`

Create a `.env` file in the project root:

```env
# Spotify Developer Credentials
SPOTIPY_CLIENT_ID="your_client_id_here"
SPOTIPY_CLIENT_SECRET="your_client_secret_here"
SPOTIPY_REDIRECT_URI="http://localhost:9090"

# Target Settings
SOURCE_PLAYLIST_ID="your_spotify_playlist_id_or_link"
SPOTIFY_MARKET="NZ"
```

#### How to get these values:

**Spotify API Credentials:**
1. Head over to the Spotify Developer Dashboard in your browser and log in.
2. Click **Create App**.
3. Name it whatever you want (e.g. `Discography Harvester`).
4. Set the **Redirect URI** to: `http://localhost:9090` (or `http://127.0.0.1:9090`).
5. Under "Which API/SDKs are you planning to use?", check **Web API**.
6. Save the app, open **Settings**, and grab your **Client ID** and **Client Secret**.

**Source Playlist ID:**
1. In Spotify (desktop, mobile, or web), navigate to the playlist you want to pull artists from.
2. Click the three dots (`...`) -> **Share** -> **Copy link to playlist**.
3. Paste it into `SOURCE_PLAYLIST_ID`. You can paste the raw 22-character ID or the full URL—the script strips out any trailing query tracking junk (`?si=...`) automatically.

---

## How to Run It

Run the main script using Python:

```bash
python all_artists_songs_playlist.py
```

Note: On your first run, a browser tab will pop up asking you to grant permissions. Click **Agree**—it will redirect back to localhost, save your token to a local `.cache` file, and start running in the terminal.

### CLI Flags

| Flag | What it does |
| :--- | :--- |
| `--dry-run` | Runs the full scrape, filtering, and deduplication logic without actually creating playlists on your Spotify account. |
| `--debug` | Dumps the raw API response for your source playlist to `.debug_playlist.json` and streams every single rejected track in real time to `duplicates_debug.log`. |
| `-n`, `--name` | Sets a custom title for the generated playlist(s). Defaults to `"Full Discography Discovery"`. |

### Examples

**Simulate a run first to see track counts:**
```bash
python all_artists_songs_playlist.py --dry-run
```

**Run a dry run and inspect track rejections in real time:**
```bash
python all_artists_songs_playlist.py --dry-run --debug
```

**Build the playlists with a custom name:**
```bash
python all_artists_songs_playlist.py --name "Favorite Artists - Complete Catalog"
```

---

## Generated Files

When running in `--debug` mode or authenticating, a few files get written locally:

- **`duplicates_debug.log`:** Created when running with `--debug`. Writes out every dropped track, the release it came from, and why it was skipped (matched keyword, short interlude cutoff, or duplicate of an earlier album track). It flushes to disk line-by-line, so if you hit `Ctrl+C` after 3 artists, everything logged up to that second is still there.
- **`.debug_playlist.json`:** Created when running with `--debug`. Contains the raw JSON Spotify returned for your playlist container and first page of tracks.
- **`.cache`:** Generated automatically by Spotipy so you don't have to log into your browser every single time you run the script. Do not commit this file.


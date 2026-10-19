# Running and hosting Amoxcalli

[Español](DESPLIEGUE.md)

Amoxcalli is a single Python process that uses only the standard library: there is no external database and nothing to install to use it.

## 1. On your computer

Requirements: Python 3.11 or newer, and git.

```bash
git clone https://github.com/pescamill/amoxcalli.git
cd amoxcalli
make demo
```

Open <http://127.0.0.1:8766>. The first time, `make demo` builds the derived analysis caches (about a minute); after that it starts in seconds.

Without `make` (for example on Windows):

```bash
python -c "from nahuatl_local.stems import WordStudy; WordStudy()._build()"
python -m nahuatl_local.platform serve
```

Useful `serve` options: `--port 8766`, `--demo` (read-only, see below) and `--explain-model claude` (Claude-written explanations; sends the question and passages to the Anthropic API, see [EVIDENCIA.md](EVIDENCIA.md), in Spanish).

Tests: `make test` (Python and a simulated browser; the browser part needs Node.js and `npm ci --ignore-scripts`).

## 2. With Docker

```bash
docker build -t amoxcalli .
docker run -p 7860:7860 amoxcalli
```

Open <http://127.0.0.1:7860>. The image is about 230 MB, builds the analysis caches when it is created and starts in a few seconds. It runs in **demo mode** (`--demo`).

## 3. Demo mode

On free hosting the disk is usually wiped on restart, and a public instance should not store other people's contributions or voices without a privacy and custody agreement. With `--demo` everything can be browsed, but the server rejects every write (profiles, proposals, recordings) with a clear message. To receive real contributions, use an instance with persistent storage, backups and a published privacy policy.

## 4. Where to host it for free

Measured on 17 October 2026: with every index built the server uses about **760 MB of RAM**, so you need a plan with **at least 1 GB**. Providers change their terms; check them when you sign up.

| Option | Fits | Notes |
|---|---|---|
| Oracle Cloud "Always Free" (virtual machine) | Yes | Always on, plenty of memory; more steps (install Docker or Python, open the port, set up HTTPS). |
| **Google Cloud Run (free tier)** | Yes, recommended | Scales to zero: no visits, no usage; a low-traffic demo fits the monthly free tier. Needs an account with billing enabled. Tutorial below. |
| Hugging Face Spaces (Docker) | Paid only | Since October 2026, Docker Spaces, even on CPU basic, require the PRO subscription (about USD 9 a month). With PRO it is the simplest option: tutorial below. |
| 512 MB free plans (Render, Koyeb and similar) | No | The server runs out of memory while building its indexes. |
| GitHub Pages or other static hosting | No | Amoxcalli needs its Python server for analysis and search. |

## 5. Tutorial: Google Cloud Run (free with low traffic)

1. Create an account at <https://cloud.google.com>, a project, and enable billing (the free tier covers a low-traffic demo; you can set a budget alert at USD 1).
2. Install the `gcloud` tool (<https://cloud.google.com/sdk/docs/install>) and log in:

   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT
   ```

3. From the project folder, build and publish the container:

   ```bash
   gcloud run deploy amoxcalli --source . --region us-central1 --allow-unauthenticated --memory 1Gi
   ```

4. Copy the URL it prints (`https://amoxcalli-….run.app`) and give it to the server:

   ```bash
   gcloud run services update amoxcalli --region us-central1 --set-env-vars AMOXCALLI_PUBLIC_ORIGIN=https://amoxcalli-XXXX.run.app
   ```

5. Open the URL. The first visit after a quiet period takes a few seconds to wake up.

To update it, repeat step 3.

## 6. Tutorial: Hugging Face Spaces (requires PRO)

1. Create an account at <https://huggingface.co> and a new **Space**: SDK **Docker**, blank template, **CPU basic** hardware (with the PRO subscription). Decide whether it is public or private: a public Space publishes the project's code and data.
2. Install the tool and log in (it asks for a write token from your account):

   ```bash
   pip install -U huggingface_hub
   hf auth login
   ```

   In older versions the tool is called `huggingface-cli` (`huggingface-cli login`, `huggingface-cli upload`).
3. From the project folder, upload the files (replace `USER`). The second command replaces the Space's README with its card, which tells Hugging Face to use Docker and port 7860:

   ```bash
   hf upload USER/amoxcalli . . --repo-type=space \
     --exclude ".git/*" ".venv/*" "node_modules/*" "models/*" "outputs/*" "data/*" "experiments/*" "reports/iterations/*" "reports/*-backups/*" "reports/*-experiments/*" "*.sqlite3*"
   hf upload USER/amoxcalli deploy/huggingface/README.md README.md --repo-type=space
   ```

   The tool uploads large files (such as `corpus/lexicon-catalog.json`, 13 MB) without setting up Git LFS.
4. In the Space, under **Settings → Variables**, add `AMOXCALLI_PUBLIC_ORIGIN` with the Space's public URL, which looks like `https://USER-amoxcalli.hf.space`. Without it the server only accepts its own internal name and turns visitors away.
5. Wait for the build to finish (a few minutes; see **Logs**) and open the URL.

To update it, repeat step 3.

## 7. Tutorial: any server with Docker

On a virtual machine (Oracle Cloud, a VPS or your own computer) with Docker:

```bash
git clone https://github.com/pescamill/amoxcalli.git && cd amoxcalli
docker build -t amoxcalli .
docker run -d --restart unless-stopped -p 7860:7860 \
  -e AMOXCALLI_PUBLIC_ORIGIN=https://your-domain.org amoxcalli
```

Put an HTTPS proxy in front (for example Caddy: `reverse_proxy 127.0.0.1:7860`) and open port 443. `AMOXCALLI_PUBLIC_ORIGIN` must be exactly the HTTPS address people will use.

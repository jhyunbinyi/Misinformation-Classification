# Deploying the overview on GitHub Pages

This folder is the **overview site** for the Factuality Evaluator. It’s meant to be served as **GitHub Pages**, with the live **evaluation demo** hosted separately on **Streamlit Cloud** and linked from this page.

## 1. Set your URLs

Edit **`docs/script.js`** and update the config at the top:

```javascript
var config = {
  streamlitAppUrl: 'https://YOUR-APP-NAME.streamlit.app',  // your Streamlit Cloud app URL
  reportUrl: '',   // optional: full report URL, or '' to hide the link
  githubUrl: 'https://github.com/YOUR-USERNAME/Misinformation-Classification'
};
```

Also replace `YOUR-APP-NAME` in **`docs/index.html`** in the three places where the Streamlit URL appears (header CTA, “Try it and learn more” link, footer). If you keep `script.js` in sync, the script will override those links at runtime; updating the HTML avoids a brief wrong link before JS runs.

## 2. Enable GitHub Pages from `/docs`

1. Push this repo to GitHub (e.g. `origin`).
2. On GitHub: **Settings → Pages** (in the repo menu).
3. Under **Build and deployment**:
   - **Source**: Deploy from a branch.
   - **Branch**: `main` (or your default branch).
   - **Folder**: choose **/docs** (not "/(root)").
4. Click **Save**. After a minute or two, the site will be at:
   - `https://<username>.github.io/<repo-name>/`

GitHub will serve `docs/index.html` as the site home. The overview is the only page; "Try the Evaluator" sends users to your Streamlit app.

**If you see the README instead of the overview:** the Folder is set to root. Change it to **/docs** and save. Leave root and README for the repo; the static site lives only in `docs/`.

## 3. Deploy the evaluator on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. **New app** → choose this repo, branch `main`, and **Main file path**: `app.py`.
3. Add a secret: **GOOGLE_API_KEY** or **GEMINI_API_KEY** (same as your local `.env`).
4. Deploy. You’ll get a URL like `https://<your-app-name>.streamlit.app`.
5. Put that URL into `docs/script.js` as `streamlitAppUrl` (and in `index.html` if you want the initial HTML to match).

Your GitHub Pages overview will then link to this Streamlit app for the “Try the Evaluator” / evaluation demo.

## Summary

| What              | Where                         |
|-------------------|-------------------------------|
| Overview (this)   | GitHub Pages from `/docs`     |
| Evaluation demo   | Streamlit Cloud (`app.py`)    |

Users land on the overview and use the “Try the Evaluator” button/link to open the Streamlit app.

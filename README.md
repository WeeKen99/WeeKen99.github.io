# weeken99.github.io

Live at https://weeken99.github.io/

My portfolio site. The project cards are built automatically from my GitHub repos.

## How a project gets onto the site

1. Make the repo **public**.
2. Add the topic **`portfolio`** (repo page → ⚙️ next to *About* → *Topics*).
3. Add a **`portfolio.json`** file at the root of the repo:

```json
{
  "title": "EV Purchase Prediction (Kaggle Playground)",
  "category": "Machine Learning",
  "summary": "One or two sentences on what the project does.",
  "result": "CV ROC AUC 0.9411 → 0.9460",
  "tags": ["LightGBM", "CatBoost", "Python"]
}
```

The site picks it up within a day. To update it straight away, go to **Actions → Build portfolio → Run workflow**.

| Field | Required | What it does |
|---|---|---|
| `title` | yes | Card heading |
| `category` | yes | Which tab the card appears under; a new category creates a new tab |
| `summary` | yes | Card description |
| `result` | no | The blue highlight line, e.g. an accuracy score |
| `tags` | no | Tool chips at the bottom of the card |
| `badge` | no | Small label after the category, e.g. `"Kaggle"` or `"Team project"` |
| `order` | no | Position in the list (current projects use 10, 20, 30…). Projects without it appear first, newest first |
| `path` | no | Subfolder the card links to, for a repo that holds several projects |
| `featured` | no | Shows the project in the top 3 with a screenshot: `{"image": "images/screenshot.png", "imageAlt": "...", "summary": "...", "result": "..."}`. Only the first 3 featured projects (by `order`) are shown |

A repo with several projects can use a list of these objects, each with its own `path` (see `data-analytics-portfolio`).

Without `portfolio.json`, a tagged repo still gets a card from its GitHub description, language and topics.

Projects that have no public repo are listed in [`data/manual-projects.json`](data/manual-projects.json). Entries there need a `link`, or `"private": true` to show a "Private repo · request details" email link instead. Team projects in other people's repos go there too, with `"badge": "Team project"`.

## Editing the rest of the page

About, skills, credentials and contact live in [`src/index.template.html`](src/index.template.html). Pushing a change to this repo rebuilds the site.

To preview locally:

```bash
python scripts/build.py   # writes _site/index.html
```

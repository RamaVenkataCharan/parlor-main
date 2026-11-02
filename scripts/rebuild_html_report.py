"""Rebuild docs/FINAL_PROJECT_REPORT.html directly from docs/FINAL_PROJECT_REPORT.md using markdown-it-py."""
from pathlib import Path
from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parent.parent
MD_PATH = ROOT / "docs" / "FINAL_PROJECT_REPORT.md"
HTML_PATH = ROOT / "docs" / "FINAL_PROJECT_REPORT.html"

md_content = MD_PATH.read_text(encoding="utf-8")

# Initialize markdown-it with tables and html enabled
md = MarkdownIt("commonmark", {"html": True, "breaks": True}).enable("table")
rendered_body = md.render(md_content)

html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Major Project Report — EMO Assistant ("Parlor") — Batch 14</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"
        onload="renderMathInElement(document.body, {{
            delimiters: [
                {{left: '$$', right: '$$', display: true}},
                {{left: '$', right: '$', display: false}}
            ]
        }});"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Charter:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  :root {{
    --text-color: #1a1a1a;
    --bg-color: #f8fafc;
    --accent-color: #0f4c81;
    --border-color: #e2e8f0;
    --code-bg: #f1f5f9;
  }}

  body {{
    font-family: 'Charter', Georgia, serif;
    font-size: 11pt;
    line-height: 1.65;
    color: var(--text-color);
    background-color: var(--bg-color);
    margin: 0;
    padding: 2rem 1rem;
  }}

  .document-container {{
    max-width: 900px;
    margin: 0 auto;
    background: #ffffff;
    padding: 3.5rem 4.5rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    border: 1px solid var(--border-color);
    border-radius: 4px;
  }}

  h1, h2, h3, h4, h5, h6 {{
    font-family: 'Inter', -apple-system, sans-serif;
    color: #0f172a;
    font-weight: 700;
    line-height: 1.3;
    margin-top: 2.2rem;
    margin-bottom: 0.8rem;
  }}

  h1 {{ font-size: 19pt; border-bottom: 2px solid var(--accent-color); padding-bottom: 0.5rem; }}
  h2 {{ font-size: 14pt; border-bottom: 1px solid var(--border-color); padding-bottom: 0.3rem; margin-top: 2.4rem; }}
  h3 {{ font-size: 12pt; color: #1e293b; }}
  h4 {{ font-size: 11pt; color: #334155; }}

  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 1.5rem 0;
    font-size: 9.5pt;
    font-family: 'Inter', sans-serif;
  }}

  th, td {{
    border: 1px solid var(--border-color);
    padding: 8px 12px;
    text-align: left;
  }}

  th {{
    background-color: #f1f5f9;
    font-weight: 600;
    color: #0f172a;
  }}

  tr:nth-child(even) {{
    background-color: #f8fafc;
  }}

  code {{
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 9pt;
    background: var(--code-bg);
    padding: 2px 5px;
    border-radius: 3px;
    border: 1px solid #e2e8f0;
  }}

  pre {{
    background: var(--code-bg);
    border: 1px solid var(--border-color);
    padding: 1rem;
    border-radius: 4px;
    overflow-x: auto;
  }}

  pre code {{
    background: transparent;
    border: none;
    padding: 0;
  }}

  blockquote {{
    border-left: 4px solid var(--accent-color);
    margin: 1.2rem 0;
    padding: 0.6rem 1.2rem;
    background: #f8fafc;
    color: #334155;
    font-style: italic;
  }}

  hr {{
    border: none;
    border-top: 1px solid var(--border-color);
    margin: 2.5rem 0;
  }}

  @media print {{
    body {{
      background: #ffffff;
      padding: 0;
    }}
    .document-container {{
      border: none;
      box-shadow: none;
      padding: 0;
      max-width: 100%;
    }}
  }}
</style>
</head>
<body>
<div class="document-container">
{rendered_body}
</div>
</body>
</html>
"""

HTML_PATH.write_text(html_template, encoding="utf-8")
print(f"Successfully rebuilt {HTML_PATH} from {MD_PATH} ({len(html_template)} bytes)")

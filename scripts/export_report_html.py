"""Export Final Project Report from Markdown to Self-Contained Styled HTML.

Uses `markdown-it-py` to generate a publication-grade, printable HTML report
with academic formatting, page breaks, typography, tables, and print stylesheets.
"""

import os
import sys
from markdown_it import MarkdownIt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_MD = os.path.join(BASE_DIR, "docs", "FINAL_PROJECT_REPORT.md")
OUTPUT_HTML = os.path.join(BASE_DIR, "docs", "FINAL_PROJECT_REPORT.html")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Major Project Report — EMO Assistant ("Parlor") — Batch 14</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Charter:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  :root {
    --text-color: #1a1a1a;
    --bg-color: #ffffff;
    --accent-color: #0f4c81;
    --border-color: #e2e8f0;
    --code-bg: #f8fafc;
    --callout-bg: #f1f5f9;
  }

  body {
    font-family: 'Charter', Georgia, serif;
    font-size: 11pt;
    line-height: 1.6;
    color: var(--text-color);
    background-color: var(--bg-color);
    margin: 0;
    padding: 2rem;
  }

  .document-container {
    max-width: 850px;
    margin: 0 auto;
    background: #ffffff;
    padding: 3rem 4rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    border: 1px solid var(--border-color);
  }

  h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', -apple-system, sans-serif;
    color: #0f172a;
    font-weight: 700;
    line-height: 1.25;
    margin-top: 2rem;
    margin-bottom: 0.75rem;
  }

  h1 { font-size: 20pt; border-bottom: 2px solid var(--accent-color); padding-bottom: 0.5rem; }
  h2 { font-size: 15pt; border-bottom: 1px solid var(--border-color); padding-bottom: 0.3rem; margin-top: 2.2rem; }
  h3 { font-size: 12.5pt; color: #1e293b; }
  h4 { font-size: 11pt; color: #334155; }

  p, li {
    font-size: 11pt;
    text-align: justify;
  }

  blockquote {
    border-left: 4px solid var(--accent-color);
    background-color: var(--callout-bg);
    margin: 1.5rem 0;
    padding: 0.8rem 1.2rem;
    color: #334155;
    font-style: normal;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.5rem 0;
    font-family: 'Inter', sans-serif;
    font-size: 9.5pt;
  }

  th, td {
    border: 1px solid var(--border-color);
    padding: 8px 12px;
    text-align: left;
  }

  th {
    background-color: #f8fafc;
    color: #0f172a;
    font-weight: 600;
  }

  tr:nth-child(even) td {
    background-color: #fbfcfe;
  }

  code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9.5pt;
    background-color: var(--code-bg);
    padding: 2px 5px;
    border-radius: 3px;
    border: 1px solid #e2e8f0;
  }

  pre {
    background-color: var(--code-bg);
    border: 1px solid var(--border-color);
    padding: 1rem;
    border-radius: 6px;
    overflow-x: auto;
  }

  pre code {
    background: none;
    padding: 0;
    border: none;
    font-size: 9pt;
    line-height: 1.45;
  }

  hr {
    border: 0;
    border-top: 1px solid var(--border-color);
    margin: 2.5rem 0;
  }

  @media print {
    body {
      padding: 0;
      background: white;
    }
    .document-container {
      box-shadow: none;
      border: none;
      padding: 0;
      max-width: 100%;
    }
    h1, h2 {
      page-break-after: avoid;
    }
    table, pre, blockquote {
      page-break-inside: avoid;
    }
    .page-break {
      page-break-after: always;
    }
  }
</style>
</head>
<body>
<div class="document-container">
{{CONTENT}}
</div>
</body>
</html>
"""


def main():
    if not os.path.exists(INPUT_MD):
        # Check alternative path
        alt_path = os.path.join(os.path.dirname(BASE_DIR), "docs", "FINAL_PROJECT_REPORT.md")
        if os.path.exists(alt_path):
            md_path = alt_path
        else:
            print(f"[ERROR] Markdown file not found at: {INPUT_MD}", file=sys.stderr)
            sys.exit(1)
    else:
        md_path = INPUT_MD

    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    md = MarkdownIt("commonmark", {"breaks": True, "html": True})
    rendered_body = md.render(md_content)

    final_html = HTML_TEMPLATE.replace("{{CONTENT}}", rendered_body)

    out_dir = os.path.dirname(OUTPUT_HTML)
    os.makedirs(out_dir, exist_ok=True)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"[SUCCESS] Exported report to HTML: {OUTPUT_HTML}")
    print(f" Size: {len(final_html):,} bytes")
    print(" You can open this file in Chrome/Edge and press Ctrl+P to save as PDF.")


if __name__ == "__main__":
    main()

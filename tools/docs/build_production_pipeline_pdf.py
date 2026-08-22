from pathlib import Path
import markdown
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/production/OMEGA_HOUSE_CORE_PRODUCTION_ASSET_PIPELINE_V1.0.md"
OUTPUT = ROOT / "docs/production/OMEGA_HOUSE_CORE_PRODUCTION_ASSET_PIPELINE_V1.0_Technical_Edition.pdf"

md = SOURCE.read_text(encoding="utf-8")
body = markdown.markdown(md, extensions=["tables", "fenced_code", "toc"])

html = f'''<!doctype html>
<html><head><meta charset="utf-8"><style>
@page {{ size: A4 landscape; margin: 16mm 15mm 15mm 15mm;
  @bottom-left {{ content: "OMEGA HOUSE STUDIO / CORE PRODUCTION ASSET PIPELINE / V1.0"; color:#777; font-size:8px; }}
  @bottom-right {{ content: counter(page); color:#777; font-size:8px; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:#0b0b0b; color:#f4f0e8; font-family:Arial,Helvetica,sans-serif; font-size:10pt; line-height:1.42; }}
h1,h2,h3 {{ color:#ff6a00; break-after:avoid; }}
h1 {{ font-size:26pt; line-height:1.05; margin:0 0 8pt; }}
h2 {{ font-size:18pt; margin:18pt 0 8pt; border-left:4px solid #ff6a00; padding-left:9pt; }}
h3 {{ font-size:12pt; margin:12pt 0 5pt; }}
p {{ margin:5pt 0 7pt; }}
blockquote {{ border-left:4px solid #ff6a00; margin:10pt 0; padding:7pt 12pt; font-weight:700; font-size:14pt; }}
pre {{ background:#171717; border:1px solid #333; padding:10pt; overflow-wrap:anywhere; white-space:pre-wrap; color:#f4f0e8; font-size:8pt; }}
code {{ color:#ffb27a; }}
table {{ width:100%; border-collapse:collapse; margin:9pt 0 12pt; break-inside:avoid; }}
th {{ background:#ff6a00; color:#0b0b0b; text-align:left; padding:7pt; }}
td {{ background:#1a1a1a; border:1px solid #303030; padding:7pt; vertical-align:top; }}
ul,ol {{ margin-top:4pt; }}
strong {{ color:#fff; }}
hr {{ border:0; border-top:2px solid #ff6a00; margin:16pt 0; }}
</style></head><body>{body}</body></html>'''

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
HTML(string=html, base_url=str(ROOT)).write_pdf(str(OUTPUT))
print(OUTPUT)

#!/usr/bin/env python3
"""
Enhanced HTML Report Generator with Jinja2 Template Integration
- Uses the existing Jinja2 template for better styling
- Improved data integration and error handling
- Better visualization of agent decisions and confidence levels
"""

import json
import argparse
import datetime
import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
import html


def _norm_id(s):
    return re.sub(r"[^0-9a-zA-Z]+", "", str(s).strip().lower()) if s else ""


def _as_list(m):
    return m if isinstance(m, list) else (list(m.values()) if isinstance(m, dict) else [])


def _build_news_index(news_blob):
    """Build enhanced news index with better error handling"""
    idx, idx_norm = {}, {}
    for it in _as_list(news_blob):
        nid = (it.get("id") or it.get("news_id") or "").strip()
        if not nid:
            continue

        # Enhanced news record with fallbacks
        rec = {
            "id": nid,
            "headline": it.get("headline", ""),
            "summary": it.get("summary", ""),
            "datetime": it.get("datetime", it.get("date", "")),
            "source": it.get("source", ""),
            "region": it.get("region", ""),
            "sector": it.get("sector", ""),
            "url": it.get("source_url", ""),
            "tickers": it.get("tickers", []),
            "news_type": it.get("news_type", "")
        }
        idx[nid] = rec
        idx_norm[_norm_id(nid)] = rec
    return idx, idx_norm


def _lookup(nid, idx, idxn):
    return idx.get(nid) or idx.get(str(nid).strip()) or idxn.get(_norm_id(nid))


def _format_confidence(conf):
    """Format confidence as percentage with color coding"""
    try:
        pct = round(float(conf) * 100, 1)
        if pct >= 70:
            color = "#059669"  # green
        elif pct >= 50:
            color = "#D97706"  # orange
        else:
            color = "#DC2626"  # red
        return f'<span style="color: {color}; font-weight: 600;">{pct}%</span>'
    except:
        return "—"


def _format_sector_label(label):
    """Format sector decision label with styling"""
    label_colors = {
        "UP": ("#10B981", "#ECFDF5"),
        "DOWN": ("#EF4444", "#FEF2F2"),
        "NO_IMPACT": ("#6B7280", "#F9FAFB")
    }
    color, bg = label_colors.get(label, ("#6B7280", "#F9FAFB"))
    return f'<span style="background: {bg}; color: {color}; padding: 4px 12px; border-radius: 6px; font-weight: 600; font-size: 12px;">{label}</span>'


def _format_rationale(rationale):
    """Format rationale with better typography"""
    if not rationale or rationale == "—":
        return "No detailed rationale provided."

    # Convert bullet points if present
    if "•" in rationale:
        points = [p.strip() for p in rationale.split("•") if p.strip()]
        if points:
            return "<ul>" + "".join(f"<li>{html.escape(p)}</li>" for p in points) + "</ul>"

    return html.escape(str(rationale))


def _format_news_item(news_item, idx, idxn):
    """Enhanced news item formatting"""
    if not news_item:
        return '<div class="news-item"><div class="news-head">News item not found</div><div class="muted-row">Unable to retrieve news details.</div></div>'

    nid = news_item.get("id", "")
    rec = _lookup(nid, idx, idxn)

    if rec:
        head = html.escape(rec.get("headline", ""))
        summ = html.escape(rec.get("summary", ""))
        dt = html.escape((rec.get("datetime") or "")[:10])
        src = html.escape(rec.get("source", ""))
        url = html.escape(rec.get("url", ""))

        # Enhanced news display
        source_link = f'<a href="{url}" target="_blank" style="color: #3B82F6;">{src}</a>' if url else src

        return f'''
        <div class="news-item">
            <div class="news-head">{head}</div>
            <div class="muted-row">{dt} • {source_link} • ID: {html.escape(rec.get("id",""))}</div>
            <div class="news-summary">{summ or "No summary available."}</div>
            {f'<div class="news-meta">Type: {html.escape(rec.get("news_type",""))} • Tickers: {", ".join(rec.get("tickers",[]))}</div>' if rec.get("news_type") or rec.get("tickers") else ''}
        </div>
        '''
    else:
        return f'<div class="news-item"><div class="news-head">ID: {html.escape(str(nid))}</div><div class="muted-row">No matching news found in index.</div></div>'


def generate_enhanced_report(input_path, output_path, news_path=None, title="Agent-2 Sector Decisions"):
    """Generate enhanced HTML report using Jinja2 template"""

    # Load summary data
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            summary = json.load(f)
    except Exception as e:
        print(f"Error loading summary data: {e}")
        return False

    # Load news data if provided
    idx, idxn = {}, {}
    if news_path and Path(news_path).exists():
        try:
            with open(news_path, 'r', encoding='utf-8') as f:
                news_blob = json.load(f)
            idx, idxn = _build_news_index(news_blob)
        except Exception as e:
            print(f"Warning: Could not load news data: {e}")

    # Prepare template data
    generated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    # Process sectors with enhanced formatting
    processed_sectors = []
    for sector, data in (summary or {}).items():
        # Enhanced data processing
        label = data.get("label", "NO_IMPACT")
        confidence = _format_confidence(data.get("confidence"))
        consensus = f'{round(float(data.get("consensus", 0)) * 100, 1)}%' if data.get("consensus") else "—"
        weighted_mean = round(float(data.get("weighted_mean", 0)), 3) if data.get("weighted_mean") else "—"
        n_signals = data.get("n_signals", "—")

        # Format rationale
        rationale = _format_rationale(data.get("rationale"))

        # Process top signals with enhanced news lookup
        top_ids = data.get("top_signals", [])
        news_items = []
        for nid in top_ids:
            if nid:  # Only process non-null IDs
                news_item_html = _format_news_item({"id": nid}, idx, idxn)
                news_items.append(news_item_html)

        # Format sector label
        sector_label = _format_sector_label(label)

        processed_sectors.append({
            'sector': html.escape(sector),
            'label': label,
            'sector_label_html': sector_label,
            'weighted_mean': weighted_mean,
            'consensus': consensus,
            'confidence': confidence,
            'n_signals': n_signals,
            'rationale': rationale,
            'top_signals': top_ids,
            'news_items': news_items,
            'thresholds_used': data.get("thresholds_used", {})
        })

    # Load and render Jinja2 template
    template_path = Path(__file__).parent / "templates"
    if not template_path.exists():
        template_path = Path("scripts/templates")

    try:
        env = Environment(loader=FileSystemLoader(template_path))
        template = env.get_template("enhanced_sector_report.html.j2")

        html_output = template.render(
            title=title,
            summary=summary,
            processed_sectors=processed_sectors,
            generated_at=generated_at,
            news_index=idx,
            news_index_norm=idxn
        )

        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_output)

        print(f"Enhanced HTML report generated: {output_path}")
        return True

    except Exception as e:
        print(f"Error generating enhanced report: {e}")
        print("Falling back to basic HTML generation...")
        return generate_basic_html(input_path, output_path, news_path, title)


def generate_basic_html(input_path, output_path, news_path=None, title="Agent-2 Sector Decisions"):
    """Fallback basic HTML generation (original method)"""

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            summary = json.load(f)
    except Exception as e:
        print(f"Error loading summary data: {e}")
        return False

    # Load news data if provided
    idx, idxn = {}, {}
    if news_path and Path(news_path).exists():
        try:
            with open(news_path, 'r', encoding='utf-8') as f:
                news_blob = json.load(f)
            idx, idxn = _build_news_index(news_blob)
        except Exception as e:
            print(f"Warning: Could not load news data: {e}")

    # Generate basic HTML (similar to original)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    cards = []
    for sector, data in (summary or {}).items():
        label = html.escape(str(data.get("label", "NO_IMPACT")))
        wm = round(float(data.get("weighted_mean", 0)), 3) if data.get("weighted_mean") else "—"
        cons = f'{round(float(data.get("consensus", 0)) * 100, 1)}%' if data.get("consensus") else "—"
        conf = _format_confidence(data.get("confidence"))
        rat = _format_rationale(data.get("rationale", "—"))
        ns = html.escape(str(data.get("n_signals", "—")))

        top = data.get("top_signals") or []
        chips = "".join(f'<span class="chip">{html.escape(str(x))}</span>' for x in top) or "—"

        news_html = []
        for nid in top:
            if nid:
                rec = _lookup(nid, idx, idxn)
                if rec:
                    head = html.escape(rec.get("headline", ""))
                    summ = html.escape(rec.get("summary", ""))
                    dt = html.escape((rec.get("datetime") or "")[:10])
                    src = html.escape(rec.get("source", ""))
                    news_html.append(f'<div class="news-item"><div class="news-head">{head}</div><div class="muted-row">{dt} • {src} • ID: {html.escape(rec.get("id",""))}</div><div class="news-body">{summ or "—"}</div></div>')
                else:
                    news_html.append(f'<div class="news-item"><div class="news-head">ID: {html.escape(str(nid))}</div><div class="muted-row">No matching news found in index.</div></div>')

        news_block = f'<details><summary>News details ({len(news_html)})</summary><div class="news">{"".join(news_html)}</div></details>' if news_html else ""

        cards.append(f'''
        <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <h2 style="margin:0;font-size:18px;">{html.escape(sector)}</h2>
                <span class="label {label}">{label}</span>
            </div>
            <div style="display:flex;gap:12px;margin-top:6px;">
                <div><strong>Weighted Mean</strong><br>{wm}</div>
                <div><strong>Consensus</strong><br>{cons}</div>
                <div><strong>Confidence</strong><br>{conf}</div>
                <div><strong>Signals</strong><br>{ns}</div>
            </div>
            <table>
                <tr><th style="width:120px;">Rationale</th><td>{rat}</td></tr>
                <tr><th>Top Signals</th><td><div class="chips">{chips}</div></td></tr>
            </table>
            {news_block}
        </div>
        ''')

    css = """
    body{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:24px;color:#111827}
    .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:16px;margin-top:16px}
    .card{border:1px solid #E5E7EB;border-radius:12px;padding:16px;background:#fff}
    .label{font-weight:600;padding:2px 8px;border-radius:999px;display:inline-block}
    .UP{background:#DCFCE7;color:#065F46}.DOWN{background:#FEE2E2;color:#7F1D1D}.NO_IMPACT{background:#E5E7EB;color:#111827}
    table{width:100%;border-collapse:collapse;margin-top:8px}th,td{text-align:left;padding:8px;border-bottom:1px solid #F3F4F6;vertical-align:top}
    .chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
    .chip{background:#F3F4F6;padding:2px 8px;border-radius:999px;font-size:12px;color:#374151}
    details{background:#F9FAFB;border:1px solid #E5E7EB;border-radius:10px;padding:8px 10px;margin-top:10px}
    .news-item{padding:8px 0;border-top:1px dashed #E5E7EB}.news-item:first-child{border-top:none}
    .news-head{font-weight:600}.muted-row{color:#6B7280;font-size:12px}
    .news-summary{margin-top:4px;color:#374151;font-size:14px}
    .news-meta{margin-top:4px;font-size:11px;color:#6B7280}
    """

    html_out = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{html.escape(title)}</title><style>{css}</style></head>
<body><h1>{html.escape(title)}</h1><div class="muted">Generated {now}</div>
<div class="grid">{"".join(cards)}</div></body></html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_out)

    print(f"Basic HTML report generated: {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate enhanced HTML report for Agent-2 sector decisions")
    parser.add_argument("--input", required=True, help="Input JSON file with sector summary")
    parser.add_argument("--output", required=True, help="Output HTML file")
    parser.add_argument("--news", default=None, help="Optional news JSON file for enhanced news details")
    parser.add_argument("--title", default="Agent-2 Sector Decisions", help="Report title")
    parser.add_argument("--fallback", action="store_true", help="Force basic HTML generation")

    args = parser.parse_args()

    if args.fallback:
        success = generate_basic_html(args.input, args.output, args.news, args.title)
    else:
        success = generate_enhanced_report(args.input, args.output, args.news, args.title)

    if not success:
        print("Failed to generate report")
        exit(1)


if __name__ == "__main__":
    main()

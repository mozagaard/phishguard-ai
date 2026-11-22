"""PhishGuard AI - Security Operations (Streamlit UI mengikuti mockup Figma)."""
import html as _html
import os
import time

import streamlit as st

from phishguard_core import Engine, default_artifact_path

st.set_page_config(page_title="PhishGuard AI - Security Operations", page_icon="🛡️", layout="wide")

BG, CARD, BORDER, TEXT, MUTE = "#0B0F15", "#131B26", "#223042", "#E6EDF5", "#8B9AAE"
GREEN, RED, AMBER, BLUE, CYAN, SKY = "#00CC96", "#FF4B4B", "#F5A524", "#4DA3FF", "#22D3EE", "#7CC4FF"
LEVEL = {
    "High": ("High Risk / Phishing", RED),
    "Medium": ("Medium Risk / Unverified", AMBER),
    "Low": ("Low Risk / Likely Benign", GREEN),
}


STEP_DELAY = float(os.environ.get("PG_STEP_DELAY", "0.35"))   # jeda kecil agar tiap langkah terlihat
FOOTNOTE = "Educational tool, not a replacement for a security filter. The model only reads the domain text."


def rgba(hex_color, a):
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


def esc(x):
    return _html.escape(str(x), quote=True)


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, .stApp, p, label, input, textarea, div[data-testid="stMarkdownContainer"] {{ font-family: 'Inter', system-ui, sans-serif; }}
button:not(:has([data-testid="stIconMaterial"])) {{ font-family: 'Inter', system-ui, sans-serif; }}
[data-testid="stIconMaterial"], .material-symbols-rounded {{ font-family: 'Material Symbols Rounded' !important; }}
.stApp {{ background: {BG}; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 1.4rem; max-width: 1400px; }}
section[data-testid="stSidebar"] {{ background: #0E141C; border-right: 1px solid {BORDER}; }}
div[class*="st-key-card"] {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px; padding: 20px 22px; }}
div[data-baseweb="input"] > div {{ background: {BG}; border: 1px solid #2F415A; border-radius: 10px; }}
div[data-baseweb="input"] input {{ color: {TEXT}; }}
button[kind="primary"]:hover {{ background: #00e0a8; color: {BG}; }}

button[kind="primary"], button[data-testid="stBaseButton-primary"] {{ background: {GREEN}; color: {BG}; font-weight: 600; border: 0; border-radius: 10px; }}
.st-key-btn_analyze button {{ height: 46px; min-height: 46px; padding: 0 14px; border-radius: 10px; }}
.st-key-btn_analyze button p {{ white-space: nowrap; font-size: 14px; font-weight: 600; margin: 0; }}
.st-key-btn_analyze button span[data-testid="stIconMaterial"] {{ font-size: 18px; margin-right: 2px; }}
.st-key-url_in div[data-baseweb="input"] > div {{ min-height: 46px; }}
.st-key-url_in input {{ font-size: 14px; }}
.st-key-btn_analyze button:disabled {{ background: #1E2A3B !important; color: {MUTE} !important; border: 1px solid #2F415A !important; box-shadow: none !important; opacity: 1 !important; }}
.st-key-btn_analyze button:disabled span[data-testid="stIconMaterial"] {{ animation: pgspin 1s linear infinite; display: inline-block; }}
@keyframes pgspin {{ to {{ transform: rotate(360deg); }} }}
.spinner {{ width: 14px; height: 14px; border-radius: 50%; border: 2px solid {rgba(BLUE, .25)}; border-top-color: {BLUE}; animation: pgspin .9s linear infinite; display: inline-block; flex: none; }}
.step {{ display: flex; align-items: center; gap: 10px; font-size: 13px; margin-top: 12px; }}
.chk {{ color: {GREEN}; font-weight: 700; width: 14px; text-align: center; flex: none; }}
.pend {{ width: 14px; height: 14px; border-radius: 50%; border: 2px solid #2F415A; display: inline-block; flex: none; box-sizing: border-box; }}
.skel {{ height: 10px; border-radius: 5px; background: rgba(42,58,80,.8); }}
.banner {{ display: flex; align-items: center; gap: 12px; border-radius: 12px; padding: 14px 16px; margin-top: 14px; }}
.banner b {{ font-size: 15px; }}
.banner .bs {{ font-size: 12px; color: {TEXT}; margin-top: 3px; }}
.why {{ display: flex; gap: 12px; margin-top: 14px; }}
.why .d {{ width: 8px; height: 8px; border-radius: 50%; margin-top: 6px; flex: none; }}
.why .t {{ font-size: 13px; font-weight: 600; color: {TEXT}; }}
.why .x {{ font-size: 12px; color: {MUTE}; margin-top: 3px; line-height: 1.45; }}
.pg-title {{ font-size: 20px; font-weight: 600; color: {TEXT}; padding-top: 6px; }}
.pg-title span {{ color: {MUTE}; font-weight: 400; }}
.pg-avatar {{ width: 40px; height: 40px; border-radius: 50%; background: #1B2A3D; border: 1.5px solid {rgba(GREEN, .5)};
  color: {GREEN}; font-weight: 600; font-size: 13px; display: flex; align-items: center; justify-content: center; margin-left: auto; }}
.kpi-label {{ color: {MUTE}; font-size: 13px; font-weight: 500; display: flex; align-items: center; gap: 8px; }}
.kpi-dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; }}
.kpi-value {{ font-size: 36px; font-weight: 700; line-height: 1.25; margin: 8px 0 4px; }}
.kpi-cap {{ color: {MUTE}; font-size: 12px; }}
.card-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }}
.card-title {{ font-size: 16px; font-weight: 600; color: {TEXT}; }}
.card-sub {{ font-size: 12px; color: {MUTE}; margin-top: 3px; }}
.tag {{ font-size: 11px; font-weight: 500; padding: 4px 10px; border-radius: 20px; display: inline-flex; align-items: center; gap: 6px; }}
.panel {{ border-radius: 12px; padding: 18px 20px; margin-top: 14px; }}
.panel-label {{ font-size: 11px; font-weight: 600; color: {MUTE}; letter-spacing: .06em; }}
.badge-row {{ display: flex; justify-content: space-between; align-items: center; margin: 12px 0; gap: 12px; flex-wrap: wrap; }}
.badge {{ font-size: 15px; font-weight: 600; padding: 9px 15px; border-radius: 10px; display: inline-flex; align-items: center; gap: 10px; }}
.big {{ font-size: 32px; font-weight: 700; }}
.row2 {{ display: flex; justify-content: space-between; font-size: 13px; color: {TEXT}; margin-bottom: 8px; font-weight: 500; }}
.mute {{ color: {MUTE}; }}
.small {{ font-size: 12px; color: {MUTE}; margin-top: 10px; line-height: 1.5; }}
.bar {{ height: 8px; border-radius: 4px; background: #1E2A3B; }}
.bar.thin {{ height: 6px; }}
.fill {{ height: 100%; border-radius: 4px; }}
.feat {{ margin-bottom: 16px; }}
.feat-top {{ display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 7px; }}
.mgrid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; margin-bottom: 18px; }}
.metric {{ background: {BG}; border: 1px solid {BORDER}; border-radius: 12px; padding: 14px 16px; }}
.metric .l {{ font-size: 12px; color: {MUTE}; font-weight: 500; }}
.metric .v {{ font-size: 24px; font-weight: 700; margin-top: 6px; }}
.cm {{ display: grid; grid-template-columns: 96px 1fr 1fr; gap: 8px; align-items: center; font-size: 12px; color: {MUTE}; }}
.cm .cell {{ border-radius: 10px; padding: 12px 6px; text-align: center; }}
.cm .cell b {{ display: block; font-size: 20px; }}
.cm .cell span {{ font-size: 10.5px; color: {MUTE}; }}
.imp {{ display: grid; grid-template-columns: 150px 1fr 48px; gap: 14px; align-items: center; margin-bottom: 18px; font-size: 13px; }}
.imp .val {{ text-align: right; font-weight: 600; }}
</style>
"""


# ---------- state & engine ----------
@st.cache_resource(show_spinner="Loading model...")
def load_engine():
    return Engine(default_artifact_path())


def init_state():
    st.session_state.setdefault("counts", {"total": 0, "high": 0, "medium": 0, "low": 0})
    st.session_state.setdefault("last", None)
    st.session_state.setdefault("error", None)
    st.session_state.setdefault("job", None)


def start_job(url):
    st.session_state["error"] = None
    st.session_state["job"] = {"url": str(url), "phase": 0}


def scan_from_header():
    start_job(st.session_state.get("q_header", ""))


def scan_from_card():
    start_job(st.session_state.get("url_in", ""))


def run_job():
    """Jalankan satu langkah analisis per rerun supaya state 'Analyzing' benar-benar terlihat."""
    job = st.session_state.get("job")
    if not job:
        return
    eng = load_engine()
    if STEP_DELAY:
        time.sleep(STEP_DELAY)
    ph = job["phase"]
    if ph == 0:
        parsed = eng.parse(job["url"])
        if parsed is None:
            st.session_state["error"] = "Please enter a valid URL or domain, for example paypal.com.secure-update.xyz/login"
            st.session_state["job"] = None
            st.rerun()
        job["host"], job["reg"] = parsed
    elif ph == 1:
        job["fz"] = eng.featurize(job["host"], job["reg"])
    else:
        res = eng.decide(job["url"], job["host"], job["reg"], job["fz"])
        st.session_state["last"] = res
        c = st.session_state["counts"]
        c["total"] += 1
        c[res["level"].lower()] += 1
        st.session_state["job"] = None
        st.rerun()
    job["phase"] = ph + 1
    st.rerun()


def state_css():
    """Warna tombol Analyze mengikuti hasil terakhir (merah untuk High, kuning untuk Medium)."""
    if st.session_state.get("job"):
        return ""
    last = st.session_state.get("last")
    lvl = last["level"] if last else None
    if lvl == "High":
        bg, fg = RED, "#FFFFFF"
    elif lvl == "Medium":
        bg, fg = AMBER, BG
    else:
        return ""
    return (f"<style>.st-key-btn_analyze button {{ background: {bg} !important; color: {fg} !important; "
            f"box-shadow: 0 0 16px {rgba(bg, .45)} !important; border: 0 !important; }}</style>")


# ---------- komponen UI ----------
def header():
    c1, c2, c3 = st.columns([5, 4, 1], vertical_alignment="center")
    c1.markdown('<div class="pg-title">PhishGuard AI <span>- Security Operations</span></div>', unsafe_allow_html=True)
    c2.text_input("Search", key="q_header", placeholder="Search URL, domain or IP address, then press Enter",
                  label_visibility="collapsed", on_change=scan_from_header)
    c3.markdown('<div class="pg-avatar">MN</div>', unsafe_allow_html=True)
    st.write("")


def card_head(title, sub, tag=None, tag_color=GREEN):
    t = ""
    if tag:
        t = (f'<span class="tag" style="background:{rgba(tag_color, .12)};border:1px solid {rgba(tag_color, .4)};color:{tag_color}">'
             f'<span class="kpi-dot" style="width:6px;height:6px;background:{tag_color}"></span>{esc(tag)}</span>')
    return (f'<div class="card-head"><div><div class="card-title">{esc(title)}</div>'
            f'<div class="card-sub">{esc(sub)}</div></div>{t}</div>')


def kpi_row(eng):
    c = st.session_state["counts"]
    auc = eng.metrics.get("roc_auc_test")
    items = [
        ("Total Scanned URLs", f"{c['total']:,}", "This session", SKY),
        ("High Risk Detected", f"{c['high']:,}", "This session", RED),
        ("Medium Risk Detected", f"{c['medium']:,}", "This session", AMBER),
        ("Low Risk URLs", f"{c['low']:,}", "This session", GREEN),
        ("Model ROC-AUC", f"{auc:.2f}" if auc is not None else "n/a", "Held-out domains (test)", CYAN),
    ]
    for i, (col, (lab, val, cap, color)) in enumerate(zip(st.columns(5, gap="small"), items)):
        with col.container(key=f"card_kpi_{i}"):
            st.markdown(
                f'<div class="kpi-label"><span class="kpi-dot" style="background:{color};box-shadow:0 0 8px {color}"></span>{esc(lab)}</div>'
                f'<div class="kpi-value" style="color:{color};text-shadow:0 0 18px {rgba(color, .45)}">{esc(val)}</div>'
                f'<div class="kpi-cap">{esc(cap)}</div>', unsafe_allow_html=True)


def result_panel(res):
    if res is None:
        return (f'<div class="panel" style="background:{rgba(BLUE, .05)};border:1px solid {rgba(BLUE, .25)}">'
                f'<div class="panel-label">PREDICTION RESULT</div>'
                f'<div class="small" style="margin-top:12px">Enter a URL above and press <b>Analyze URL</b>. '
                f'Nothing has been analyzed yet.</div></div>')
    label, color = LEVEL[res["level"]]
    popular = res["allowlisted"] and not res["spoof"]
    pct = f'{res["score"] * 100:.0f}%'
    note = "Not used (popular domain)" if popular else f'{res["score"]:.2f} / 1.00'
    width = 0 if popular else res["score"] * 100
    big = "&mdash;" if popular else pct
    strong = res["level"] == "High"
    border = f'{1.5 if strong else 1}px solid {rgba(color, .75 if strong else .35)}'
    shadow = f'box-shadow:0 0 20px {rgba(color, .25)};' if strong else ''
    return (
        f'<div class="panel" style="background:{rgba(color, .12 if strong else .06)};border:{border};{shadow}">'
        f'<div class="panel-label">PREDICTION RESULT</div>'
        f'<div class="badge-row"><span class="badge" style="background:{rgba(color, .16)};border:1px solid {rgba(color, .6)};color:{color};box-shadow:0 0 16px {rgba(color, .3)}">'
        f'<span class="kpi-dot" style="width:10px;height:10px;background:{color};box-shadow:0 0 8px {color}"></span>{label}</span>'
        f'<span class="big" style="color:{color};text-shadow:0 0 16px {rgba(color, .5)}">{big}</span></div>'
        f'<div class="row2"><span>Model suspicion score</span><span class="mute">{note}</span></div>'
        f'<div class="bar"><div class="fill" style="width:{width:.0f}%;background:{color};box-shadow:0 0 10px {rgba(color, .55)}"></div></div>'
        f'<div class="small">{esc(res["reason"])}</div>'
        f'<div class="small" style="margin-top:4px">Analyzed domain: <b style="color:{TEXT}">{esc(res["domain"])}</b>'
        f' &middot; Host: {esc(res["host"])}</div></div>')


def analyzing_panel(phase):
    steps = ["URL parsed", "Features extracted", "Running Random Forest model…"]
    rows = []
    for i, t in enumerate(steps):
        if i < phase:
            mark, w, c = '<span class="chk">✓</span>', 500, MUTE
        elif i == phase:
            mark, w, c = '<span class="spinner"></span>', 600, TEXT
        else:
            mark, w, c = '<span class="pend"></span>', 400, MUTE
        rows.append(f'<div class="step">{mark}<span style="font-weight:{w};color:{c}">{t}</span></div>')
    width = [25, 55, 85][min(phase, 2)]
    return (f'<div class="panel" style="background:{rgba(BLUE, .05)};border:1px solid {rgba(BLUE, .3)}">'
            f'<div class="panel-label">ANALYZING</div>{"".join(rows)}'
            f'<div class="bar" style="margin-top:16px"><div class="fill" style="width:{width}%;background:{BLUE};box-shadow:0 0 10px {rgba(BLUE, .55)}"></div></div></div>')


def banner_html(res):
    if res is None:
        return ""
    if res["level"] == "High":
        color, title, sub = RED, "Do Not Open — Be Careful", "Do not enter passwords or personal data on this site."
    elif res["level"] == "Medium":
        color, title, sub = AMBER, "Proceed With Caution", "Do not enter passwords or personal data unless you are sure this site is legitimate."
    else:
        return ""
    return (f'<div class="banner" style="background:{rgba(color, .16)};border:1px solid {rgba(color, .6)}">'
            f'<span style="font-size:22px;color:{color}">⚠</span>'
            f'<div><b style="color:{color}">{title}</b><div class="bs">{sub}</div></div></div>')


def analyzer_card():
    job = st.session_state.get("job")
    res = st.session_state.get("last")
    with st.container(key="card_analyzer"):
        st.markdown(card_head("URL Analyzer", "Classify a URL in real time", "Live"), unsafe_allow_html=True)
        c1, c2 = st.columns([3.4, 1.3], vertical_alignment="center")
        c1.text_input("URL", key="url_in", placeholder="http://paypal.com.secure-update.xyz/login?id=123",
                      label_visibility="collapsed", disabled=bool(job))
        if job:
            c2.button("Analyzing…", type="primary", key="btn_analyze", icon=":material/progress_activity:",
                      disabled=True, use_container_width=True)
        else:
            c2.button("Analyze URL", type="primary", key="btn_analyze", icon=":material/radar:",
                      on_click=scan_from_card, use_container_width=True)
        if st.session_state.get("error"):
            st.warning(st.session_state["error"])
        if job:
            st.markdown(analyzing_panel(job["phase"]), unsafe_allow_html=True)
        else:
            st.markdown(result_panel(res) + banner_html(res), unsafe_allow_html=True)
        st.markdown(f'<div class="small" style="margin-top:14px">{FOOTNOTE}</div>', unsafe_allow_html=True)


def why_card():
    res = st.session_state.get("last")
    if st.session_state.get("job") or not res or res["level"] == "Low":
        return
    color = RED if res["level"] == "High" else AMBER
    reasons = res.get("reasons") or [(
        "Pattern-based score",
        "No single red flag stands out. The score comes from the overall pattern of the domain name (length, character mix).")]
    with st.container(key="card_why"):
        st.markdown(card_head("Why is this risky?", "Signals behind this verdict"), unsafe_allow_html=True)
        st.markdown("".join(
            f'<div class="why"><span class="d" style="background:{color};box-shadow:0 0 8px {rgba(color, .8)}"></span>'
            f'<div><div class="t">{esc(t)}</div><div class="x">{esc(d)}</div></div></div>' for t, d in reasons)
            + '<div class="small" style="margin-top:14px">These are common red flags read from the domain text. '
              'The model score is computed separately and may weigh signals differently.</div>', unsafe_allow_html=True)


TELE = [  # key, label, max untuk panjang bar, (batas kuning, batas merah) -- hanya panduan visual
    ("num_subdomains", "num_subdomains", 4, (2, 3)),
    ("entropy", "entropy", 4.5, (3.2, 3.6)),
    ("sensitive_keyword_count", "sensitive_keyword_count", 3, (1, 2)),
    ("brand_hits", "brand_hits", 2, (99, 1)),
    ("count_hyphen", "count_hyphen", 4, (1, 3)),
    ("has_ip", "has_ip", 1, (99, 1)),
]


def tele_color(v, amber_at, red_at):
    return RED if v >= red_at else AMBER if v >= amber_at else GREEN


def telemetry_card():
    res = st.session_state.get("last")
    job = st.session_state.get("job")
    with st.container(key="card_telemetry"):
        st.markdown(card_head("URL Telemetry", "Extracting features…" if job else "Features extracted from this URL",
                              "Visual guide only", MUTE), unsafe_allow_html=True)
        if job:
            st.markdown("".join(
                f'<div class="feat"><div class="feat-top"><span style="font-weight:500;color:{MUTE}">{label}</span>'
                f'<div class="skel" style="width:28px"></div></div><div class="bar thin"></div></div>'
                for _, label, _, _ in TELE), unsafe_allow_html=True)
            return
        if res is None:
            st.markdown('<div class="small">Analyze a URL to see its extracted features.</div>', unsafe_allow_html=True)
            return
        rows = []
        for key, label, mx, (am, rd) in TELE:
            v = res["telemetry"][key]
            ratio = min(v / mx, 1.0)
            color = tele_color(v, am, rd)
            vtxt = ("Yes" if v else "0  ·  No") if key == "has_ip" else f"{v}"
            rows.append(
                f'<div class="feat"><div class="feat-top"><span style="font-weight:500">{label}</span>'
                f'<span style="font-weight:600;color:{color}">{vtxt}</span></div>'
                f'<div class="bar thin"><div class="fill" style="width:{ratio * 100:.0f}%;background:{color}"></div></div></div>')
        st.markdown("".join(rows), unsafe_allow_html=True)
        st.markdown('<div class="small">Bar colors are a visual guide. <b>num_subdomains</b> is shown for information; '
                    'the model itself reads only the registered domain, and subdomain spoofing is handled by a separate rule.</div>',
                    unsafe_allow_html=True)


def pct(x):
    return "n/a" if x is None else f"{x * 100:.1f}%"


def performance_card(eng):
    m = eng.metrics
    with st.container(key="card_perf"):
        st.markdown(card_head("Model Performance", "Random Forest on registered-domain features, split by domain"), unsafe_allow_html=True)
        cards = [
            ("ROC-AUC (test)", f'{m.get("roc_auc_test", float("nan")):.3f}', GREEN),
            (f'ROC-AUC (external, n={m.get("n_external", "?")})', f'{m.get("roc_auc_external", float("nan")):.3f}', BLUE),
            ("Recall @ High (FP ≤ 5%)", pct(m.get("recall_high_test")), BLUE),
            ("Recall @ Medium+ (FP ≤ 20%)", pct(m.get("recall_med_test")), BLUE),
        ]
        st.markdown('<div class="mgrid">' + "".join(
            f'<div class="metric"><div class="l">{esc(l)}</div><div class="v" style="color:{c};text-shadow:0 0 12px {rgba(c, .35)}">{esc(v)}</div></div>'
            for l, v, c in cards) + '</div>', unsafe_allow_html=True)
        cm = m.get("confusion_med_test")
        if cm:
            (tn, fp), (fn, tp) = cm
            def cell(n, lab, col):
                return (f'<div class="cell" style="background:{rgba(col, .12)};border:1px solid {rgba(col, .35)}">'
                        f'<b style="color:{col}">{n:,}</b><span>{lab}</span></div>')
            st.markdown(
                '<div class="card-title" style="font-size:13px;margin-bottom:10px">Confusion matrix (test, Medium+ threshold)</div>'
                '<div class="cm"><div></div><div style="text-align:center">Predicted benign</div><div style="text-align:center">Predicted phishing</div>'
                f'<div>Actual benign</div>{cell(tn, "True negative", GREEN)}{cell(fp, "False positive", RED)}'
                f'<div>Actual phishing</div>{cell(fn, "False negative", RED)}{cell(tp, "True positive", GREEN)}</div>',
                unsafe_allow_html=True)


def importance_card(eng):
    imp = sorted(eng.importance.items(), key=lambda kv: kv[1], reverse=True)[:5]
    with st.container(key="card_imp"):
        st.markdown(card_head("Top 5 Feature Importance", "Which domain features drive the model score"), unsafe_allow_html=True)
        if not imp:
            st.markdown('<div class="small">No importance data in the model file.</div>', unsafe_allow_html=True)
            return
        mx = imp[0][1] or 1
        st.markdown("".join(
            f'<div class="imp"><span style="font-weight:500">{esc(k)}</span>'
            f'<div class="bar" style="height:10px"><div class="fill" style="width:{v / mx * 100:.0f}%;background:{BLUE}"></div></div>'
            f'<span class="val">{v:.3f}</span></div>' for k, v in imp), unsafe_allow_html=True)
        st.markdown('<div class="small">Importance = mean decrease in impurity across all trees. '
                    'It shows what the model uses, not what is causally malicious.</div>', unsafe_allow_html=True)


def settings_card(eng):
    meta = eng.meta
    with st.container(key="card_settings"):
        st.markdown(card_head("Settings & About", "Read-only configuration of the deployed model"), unsafe_allow_html=True)
        st.markdown(
            f'- **High risk threshold** (false positive ≤ 5% on validation): `{eng.thr_high:.3f}`\n'
            f'- **Medium risk threshold** (false positive ≤ 20% on validation): `{eng.thr_med:.3f}`\n'
            f'- **Allowlist:** registered domains in Tranco top {meta.get("top_n", 100000):,} ({len(eng.allow):,} domains), list ID `{meta.get("tranco_list_id", "n/a")}`\n'
            f'- **Model built:** {meta.get("created", "n/a")}')
        st.markdown("**How a verdict is made**")
        st.markdown("1. **Spoof rule:** a brand name in the subdomain, but the registered domain is not the brand's → *High*.\n"
                    "2. **Allowlist:** popular registered domain → *Low*.\n"
                    "3. **Model:** score of the registered-domain name pattern → *High / Medium / Low* using the two thresholds.")
        st.markdown("**Known limitations**")
        st.markdown("- The model reads only the domain text, not the page content, so it cannot see scams that live inside a page.\n"
                    "- Phishing hosted on legitimate, popular platforms can be missed (allowlist).\n"
                    "- Some phishing labels may be compromised legitimate sites (label noise).\n"
                    "- Training data was balanced 1:1, so real-world precision will be lower than test numbers.\n"
                    "- The external test set is small (about 100 domains), so those numbers are rough.\n"
                    "- A *Medium* or *High* result means **be careful**, not **certainly phishing**.")


# ---------- halaman ----------
def page_home():
    header()
    eng = load_engine()
    kpi_row(eng)
    st.write("")
    a, b = st.columns(2, gap="medium")
    with a:
        analyzer_card()
        why_card()
    with b:
        telemetry_card()
    st.write("")
    c, d = st.columns(2, gap="medium")
    with c:
        performance_card(eng)
    with d:
        importance_card(eng)
    run_job()


def page_scanner():
    header()
    a, b = st.columns(2, gap="medium")
    with a:
        analyzer_card()
        why_card()
    with b:
        telemetry_card()
    run_job()


def page_analytics():
    header()
    eng = load_engine()
    c, d = st.columns(2, gap="medium")
    with c:
        performance_card(eng)
    with d:
        importance_card(eng)
    run_job()


def page_settings():
    header()
    settings_card(load_engine())
    run_job()


st.markdown(CSS, unsafe_allow_html=True)
init_state()
st.markdown(state_css(), unsafe_allow_html=True)
if not default_artifact_path().exists():
    st.error("Model file not found: `artifacts/phishguard_v4.joblib`. Export it from the Colab notebook and place it in the artifacts folder.")
    st.stop()

nav = st.navigation([
    st.Page(page_home, title="Home", icon=":material/home:", default=True, url_path="home"),
    st.Page(page_scanner, title="Scanner", icon=":material/radar:", url_path="scanner"),
    st.Page(page_analytics, title="Analytics", icon=":material/analytics:", url_path="analytics"),
    st.Page(page_settings, title="Settings", icon=":material/settings:", url_path="settings"),
])
nav.run()

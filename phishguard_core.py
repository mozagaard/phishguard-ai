"""
PhishGuard AI - logika inferensi (tanpa UI).

Alur putusan berlapis:
  1) Aturan spoof : nama merek di SUBDOMAIN, domain terdaftar bukan milik merek -> High
  2) Allowlist    : domain terdaftar ada di Tranco top N                         -> Low
  3) Model ML     : skor pola nama domain -> High / Medium / Low via 2 threshold

Aplikasi TIDAK membuka atau mengunduh URL yang dianalisis. Hanya membaca teksnya.
"""
import math
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import joblib
import pandas as pd
import tldextract

_ext = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)   # offline, pakai snapshot bawaan

SUSPICIOUS_WORDS = ["login", "verify", "secure", "account", "update", "signin", "confirm",
                    "password", "wallet", "billing", "support", "helpdesk",
                    "verifikasi", "aktivasi", "klaim", "hadiah"]
BRANDS = {  # token merek -> domain resmi (harus SAMA dengan yang dipakai saat training)
    "paypal": {"paypal.com", "paypal.me"},
    "google": {"google.com", "google.co.id", "googleapis.com", "googleusercontent.com", "gstatic.com", "googlevideo.com"},
    "microsoft": {"microsoft.com", "live.com", "office.com", "microsoftonline.com"},
    "apple": {"apple.com", "icloud.com"},
    "amazon": {"amazon.com", "amazonaws.com", "amazon.co.id"},
    "facebook": {"facebook.com", "fbcdn.net"}, "instagram": {"instagram.com"},
    "netflix": {"netflix.com"}, "whatsapp": {"whatsapp.com", "whatsapp.net"},
    "tokopedia": {"tokopedia.com"}, "shopee": {"shopee.co.id", "shopee.com"},
    "bca": {"bca.co.id"}, "bni": {"bni.co.id"}, "mandiri": {"bankmandiri.co.id"}, "gojek": {"gojek.com"},
}
SHORT_BRANDS = {"bca", "bni"}   # merek pendek: cocokkan sebagai token utuh saja
IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


# ---------- pembersihan ----------
def to_hostname(url):
    """URL/domain apa pun -> hostname bersih (huruf kecil, tanpa skema, port, user@, www.)."""
    s = str(url).strip().lower()
    if not s:
        return None
    if "://" not in s:
        s = "http://" + s
    try:
        host = urlparse(s).hostname
    except ValueError:
        return None
    if not host:
        return None
    host = re.sub(r"^www\d*\.", "", host.strip("."))
    return host or None


def reg_domain(host):
    e = _ext(host)
    return f"{e.domain}.{e.suffix}" if e.suffix else e.domain


# ---------- fitur (identik dengan notebook training) ----------
def shannon_entropy(s):
    if not s:
        return 0.0
    c = Counter(s)
    t = len(s)
    return -sum((v / t) * math.log2(v / t) for v in c.values()) + 0.0


def host_features(host):
    e = _ext(host)
    dom = e.domain
    reg = f"{e.domain}.{e.suffix}" if e.suffix else e.domain
    sub_labels = e.subdomain.split(".") if e.subdomain else []
    labels = host.split(".")
    tokens = set(re.split(r"[.\-]", host))
    nd = sum(ch.isdigit() for ch in host)
    return {
        "host_length": len(host),
        "num_dots": host.count("."),
        "num_subdomains": len(sub_labels),
        "tld_length": len(e.suffix),
        "domain_length": len(dom),
        "longest_label": max(len(l) for l in labels),
        "count_hyphen": host.count("-"),
        "hyphen_in_domain": dom.count("-"),
        "num_digits": nd,
        "digit_ratio": nd / len(host),
        "entropy": shannon_entropy(host),
        "domain_entropy": shannon_entropy(dom),
        "has_ip": int(bool(IP_RE.match(host))),
        "suspicious_word_count": sum(w in host for w in SUSPICIOUS_WORDS),
        "brand_in_wrong_place": sum(1 for t in tokens if t in BRANDS and reg not in BRANDS[t]),
    }


def brand_hits(host):
    e = _ext(host)
    reg = f"{e.domain}.{e.suffix}" if e.suffix else e.domain
    low = host.lower()
    toks = set(re.split(r"[.\-]", low))
    n = 0
    for b, official in BRANDS.items():
        if reg in official:
            continue
        if (b in SHORT_BRANDS and b in toks) or (b not in SHORT_BRANDS and b in low):
            n += 1
    return n


def spoof_brands(host):
    """Daftar merek yang muncul di SUBDOMAIN padahal domain terdaftarnya bukan milik merek itu."""
    e = _ext(host)
    reg = f"{e.domain}.{e.suffix}" if e.suffix else e.domain
    toks = set(re.split(r"[.\-]", e.subdomain.lower()))
    return sorted(b for b, official in BRANDS.items() if b in toks and reg not in official)


def spoof_rule(host):
    """Aturan terpisah (bukan ML): nama merek di SUBDOMAIN tapi domain terdaftarnya bukan milik merek itu."""
    return bool(spoof_brands(host))


def brand_hit_list(reg):
    """Merek yang muncul di dalam domain terdaftar padahal bukan domain resminya."""
    low = reg.lower()
    toks = set(re.split(r"[.\-]", low))
    out = []
    for b, official in BRANDS.items():
        if reg in official:
            continue
        if (b in SHORT_BRANDS and b in toks) or (b not in SHORT_BRANDS and b in low):
            out.append(b)
    return out


BRAND_NAMES = {"paypal": "PayPal", "google": "Google", "microsoft": "Microsoft", "apple": "Apple", "amazon": "Amazon",
               "facebook": "Facebook", "instagram": "Instagram", "netflix": "Netflix", "whatsapp": "WhatsApp",
               "tokopedia": "Tokopedia", "shopee": "Shopee", "bca": "BCA", "bni": "BNI", "mandiri": "Mandiri", "gojek": "Gojek"}


def _quoted(words):
    q = [f"'{w}'" for w in words]
    return q[0] if len(q) == 1 else ", ".join(q[:-1]) + " and " + q[-1]


def explain(host, reg, spoof_b):
    """Alasan yang bisa dibaca manusia, dihasilkan dari sinyal nyata di teks domain.
    Ini adalah tanda bahaya umum (panduan), bukan rincian bobot internal model."""
    items = []
    for b in spoof_b:
        name = BRAND_NAMES.get(b, b.title())
        items.append(("Imitates a known brand", f"'{b}' appears in the subdomain of {reg}, which is not {name}'s official domain."))
    for b in [x for x in brand_hit_list(reg) if x not in spoof_b][:1]:
        name = BRAND_NAMES.get(b, b.title())
        items.append(("Brand name inside the domain", f"'{b}' is part of {reg}, which is not an official {name} domain."))
    words = [w for w in SUSPICIOUS_WORDS if w in host]
    if words:
        items.append(("Sensitive keywords in the domain", f"{_quoted(words[:3])} are common in credential-phishing domains."))
    f = apex_features(reg)
    e = _ext(host)
    n_sub = len(e.subdomain.split(".")) if e.subdomain else 0
    if f["has_ip"]:
        items.append(("IP address instead of a domain name", "Legitimate services rarely ask you to sign in on a bare IP address."))
    if n_sub >= 3:
        items.append(("Many subdomain levels", f"{n_sub} subdomain levels in front of {reg} can hide the real domain."))
    if f["hyphen_in_domain"] >= 2:
        items.append(("Several hyphens in the domain", "Chained hyphenated words are a common way to look official."))
    elif f["hyphen_in_domain"] == 1 and words:
        items.append(("Hyphenated domain name", "Hyphens are often used to chain keywords together so the domain looks official."))
    if f["digit_ratio"] >= 0.3 and f["domain_length"] >= 8:
        items.append(("Many digits in the domain", f"{f['digit_ratio'] * 100:.0f}% of the characters are digits."))
    if f["domain_entropy"] >= 3.6:
        items.append(("Random-looking domain name", f"High character entropy ({f['domain_entropy']:.2f})."))
    if f["domain_length"] >= 25:
        items.append(("Very long domain name", f"The domain name is {f['domain_length']} characters long."))
    return items[:4]


def apex_features(reg):
    f = host_features(reg)
    for k in ("num_subdomains", "num_dots", "brand_in_wrong_place"):
        f.pop(k)
    f["brand_hits"] = brand_hits(reg)
    return f


# ---------- mesin ----------
class Engine:
    def __init__(self, path):
        art = joblib.load(path)
        self.model = art["model"]
        self.features = art["features"]
        self.thr_high = art["thr_high"]
        self.thr_med = art["thr_med"]
        self.allow = set(art["allow"])
        self.importance = art.get("importance", {})
        self.metrics = art.get("metrics", {})
        self.meta = art.get("meta", {})

    # --- langkah 1: parsing ---
    def parse(self, url):
        """Return (host, reg) atau None kalau input bukan URL/domain yang valid."""
        host = to_hostname(url)
        if not host or "." not in host:
            return None
        return host, reg_domain(host)

    # --- langkah 2: ekstraksi fitur ---
    def featurize(self, host, reg):
        return {"feats": apex_features(reg), "spoof_brands": spoof_brands(host), "telemetry": self.telemetry(host, reg)}

    # --- langkah 3: model + putusan ---
    def decide(self, url, host, reg, fz):
        p = float(self.model.predict_proba(pd.DataFrame([fz["feats"]])[self.features])[0, 1])
        spoof_b = fz["spoof_brands"]
        spoof = bool(spoof_b)
        in_allow = reg in self.allow
        if spoof:
            level, why = "High", "A brand name appears in the subdomain, but the registered domain does not belong to that brand."
        elif in_allow:
            level, why = "Low", f"Popular domain (Tranco top {self.meta.get('top_n', 100000):,}). Model score is not used."
        elif p >= self.thr_high:
            level, why = "High", "The domain name pattern strongly resembles known phishing domains."
        elif p >= self.thr_med:
            level, why = "Medium", "The domain name pattern looks somewhat suspicious. Treat with caution."
        else:
            level, why = "Low", "The domain name pattern does not look suspicious."
        reasons = explain(host, reg, spoof_b) if level in ("High", "Medium") else []
        return {"input": str(url).strip(), "host": host, "domain": reg, "score": p, "level": level,
                "reason": why, "spoof": spoof, "allowlisted": in_allow, "telemetry": fz["telemetry"], "reasons": reasons}

    def scan(self, url):
        """Semua langkah sekaligus. Return dict hasil, atau None kalau input tidak valid."""
        parsed = self.parse(url)
        if parsed is None:
            return None
        host, reg = parsed
        return self.decide(url, host, reg, self.featurize(host, reg))

    @staticmethod
    def telemetry(host, reg):
        e = _ext(host)
        f = apex_features(reg)
        return {
            "num_subdomains": len(e.subdomain.split(".")) if e.subdomain else 0,
            "entropy": round(f["domain_entropy"], 2),
            "sensitive_keyword_count": sum(w in host for w in SUSPICIOUS_WORDS),
            "brand_hits": f["brand_hits"],
            "count_hyphen": host.count("-"),
            "has_ip": f["has_ip"],
        }


def default_artifact_path():
    return Path(__file__).parent / "artifacts" / "phishguard_v4.joblib"

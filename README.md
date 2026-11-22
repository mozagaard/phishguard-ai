# PhishGuard AI - Security Operations

An educational **domain-based phishing risk scorer** built with Streamlit. Paste a URL, get a risk level
(Low / Medium / High), the reason, extracted features, and the model's honest evaluation numbers.

> This tool never opens or downloads the URL you enter. It only reads the text of the domain.

## How a verdict is made

1. **Spoof rule** - a brand name appears in the *subdomain* but the registered domain is not the brand's
   (e.g. `paypal.com.secure-update.xyz`) -> **High**.
2. **Allowlist** - the registered domain is in the Tranco top 100k -> **Low**.
3. **Model** - a Random Forest scores the registered-domain name pattern; two thresholds (chosen on a
   validation set by false-positive rate: 5% and 20%) map the score to **High / Medium / Low**.

## Honest results

| Evaluation | ROC-AUC |
|---|---|
| Held-out domains (test, grouped by registered domain) | ~0.70 |
| Small external set (OpenPhish vs unseen Tranco long-tail, ~100 domains) | ~0.6 |

The model alone is a **weak signal**. A *Medium* or *High* result means "be careful", not "certainly phishing".
Earlier iterations looked much better (94% accuracy) but that came from dataset artifacts (scheme, `https`,
`www.`, path, subdomain) and random train/test splits. See the project write-up for the full story.

## Known limitations

- Reads only domain text, not page content (cannot see scams inside a page).
- Phishing hosted on legitimate popular platforms can be missed (allowlist).
- Some phishing labels may be compromised legitimate sites (label noise).
- Training data is balanced 1:1, so real-world precision is lower than test numbers.
- The external test set is small, so those numbers are rough.
- Allowlist depends on a Tranco snapshot and needs periodic refresh.

## Data sources

- Benign: [Tranco](https://tranco-list.eu) top sites ranking.
- Phishing: [Phishing.Database](https://github.com/Phishing-Database/Phishing.Database) (MIT) and the
  [OpenPhish](https://openphish.com) community feed (non-commercial use).

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Place the exported model at `artifacts/phishguard_v4.joblib` (created by the Colab export cell).

## Deploy (Streamlit Community Cloud)

Push this folder to GitHub, create a new app pointing to `app.py`, and in *Advanced settings* choose the
same Python minor version you used to train the model (pickled scikit-learn models are version-sensitive).

## Files

- `app.py` - Streamlit UI (Home, Scanner, Analytics, Settings)
- `phishguard_core.py` - cleaning, features, spoof rule, verdict logic (must match the training notebook)
- `artifacts/phishguard_v4.joblib` - model, thresholds, allowlist, metrics
- `.streamlit/config.toml` - dark theme

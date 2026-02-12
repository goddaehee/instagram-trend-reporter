# Instagram Trend Reporter - Troubleshooting Guide

This guide documents common issues, root causes, and solutions based on actual bug reports and production incidents.

---

## Table of Contents

- [Authentication Issues](#authentication-issues)
- [Scraping Issues](#scraping-issues)
- [Category Classification Issues](#category-classification-issues)
- [v2.0 Release Improvements](#v20-release-improvements)

---

## Authentication Issues

### Google OAuth Configuration Missing

**Issue Reference:** #2591

#### Problem
Instagram scraping succeeds, but Google Sheets report generation fails with error:

```
ValueError: Google OAuth 설정을 찾을 수 없습니다.
```

#### Root Cause
`src/sheets.py:_get_credentials()` cannot locate Google OAuth credentials in the environment.

#### Solution

**Local Environment:**
```yaml
# config/settings.yaml
google:
  client_id: "your-client-id.apps.googleusercontent.com"
  client_secret: "your-client-secret"
```

Or set environment variables:
```bash
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"
```

**Streamlit Cloud:**
Add to `.streamlit/secrets.toml`:
```toml
GOOGLE_CLIENT_ID = "your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "your-client-secret"
SHEETS_TOKEN = '{"token":"...","refresh_token":"..."}'
GMAIL_TOKEN = '{"token":"...","refresh_token":"..."}'
```

---

### Missing Python Dependencies

**Issue Reference:** #2590

#### Problem
```
ModuleNotFoundError: No module named 'apify_client'
ModuleNotFoundError: No module named 'google_auth_oauthlib'
```

#### Root Cause
Required Python packages not installed.

#### Solution
Install all dependencies:
```bash
pip install -r requirements.txt
```

**Required packages:**
| Package | Version | Purpose |
|---------|---------|---------|
| `apify-client` | 1.12.2 | Instagram data scraping |
| `google-auth-oauthlib` | 1.2.4 | Google OAuth authentication |
| `matplotlib` | Latest | Chart generation (wordcloud) |
| `wordcloud` | Latest | Hashtag wordcloud |
| `plotly` | Latest | Interactive charts |
| `kaleido` | Latest | Static chart export |
| `keyring` | 25.7.0 | Credential storage (local) |

---

### OAuth Token Expired

#### Problem
```
Error: Token has been expired or revoked.
```

#### Solution

**Local (keyring):**
```bash
# Delete stored token
python -c "import keyring; keyring.delete_password('instagram-trend-reporter', 'sheets')"

# Re-run to trigger OAuth flow
python main.py test
```

**Streamlit Cloud:**
Generate new OAuth tokens and update Secrets:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials
3. Run local auth flow once to get refresh token
4. Copy token JSON to Secrets

---

## Scraping Issues

### Instagram GraphQL Parse Error

**Issue Reference:** #2598

#### Problem
```
Parse Error: Expected HTTP/, RTSP/ or ICE/
Error: malformed HTTP response
```

- Occurs with ~50% failure rate
- Instagram API returns malformed responses

#### Root Cause
- Instagram bot detection mechanisms
- Rate limiting on Instagram GraphQL API
- Proxy IP blocks

#### Mitigation Strategies

| Strategy | Implementation |
|----------|----------------|
| **Retry Logic** | Apify CheerioCrawler session rotation |
| **Timeout Extension** | `timeout_secs: 300` (5 min) + per-account buffer |
| **Chunk Splitting** | Auto-split >30 day periods into chunks |
| **Cost Cap** | `max_cost_usd: 2.0` per run |

#### Config Recommendations
```yaml
scraper:
  max_request_retries: 3
  max_concurrency: 5
  timeout_secs: 300
  timeout_per_account_secs: 30
  max_cost_usd: 2.0
```

---

### High Retry Rate / Proxy Errors

**Issue Reference:** #2703

#### Symptoms
```
proxy 590 UPSTREAM503
request blocked
session errors
```

#### Explanation
These are **normal retry behaviors** from Apify's CheerioCrawler:
- Session rotation triggers on detected blocks
- Proxy pool rotation is working as designed
- Retries are built into the scraper

#### When to Be Concerned
| Metric | Threshold | Action |
|--------|-----------|--------|
| Failure rate | >80% | Check Apify dashboard |
| Zero results | 0 posts | Verify account names |
| Consistent timeouts | Every run | Increase `timeout_secs` |

---

### Data Quality Validation Failed

#### Problem
```
데이터 품질이 너무 낮아 분석을 진행할 수 없습니다.
```

#### Root Cause
Insufficient data collected due to:
- Private/inactive accounts
- Instagram rate limits
- Very short time periods

#### Solution
Check quality metrics in `src/fetcher.py:validate_fetch_quality()`:

| Metric | Minimum | Warning Message |
|--------|----------|-----------------|
| Posts per account | 2 | `포스트 부족` |
| Caption rate | 30% | `캡션 비율 낮음` |
| Engagement rate | 50% | `인게이지먼트 데이터 부족` |

**Fixes:**
1. Verify target accounts are public and active
2. Increase `days` parameter (default: 7)
3. Reduce number of target accounts
4. Check if Apify quota is exhausted

---

## Category Classification Issues

### Missing Celebrity/Brand Mappings

**Issue Reference:** #2829

#### Problem
10 celebrity tags and 4 brand tags incorrectly classified as "general".

#### Missing Tags (Fixed)
| Type | Missing Tags |
|------|--------------|
| **Celebrity** | 저스틴비버 (Justin Bieber), 랄리사 (Lalisa), bts완전체, 몽클레르 |
| **Brand** | Moncler (misspelled as 몽클레르) |

#### Solution
Keywords added to `src/categories.py`:
```python
_CELEB_SUBSTRING = frozenset({
    ...
    "저스틴비버", "justinbieber", "비버부부",
    "bts완전체",
    ...
})

_BRAND_SUBSTRING = frozenset({
    ...
    "몽클레르", "몽클레어", "moncler",  # Added both spellings
    ...
})
```

---

### Categorization Accuracy Improvement

**Issue Reference:** #2774

#### Before/After
| Metric | Before | After | Improvement |
|--------|---------|--------|-------------|
| Celebrity accuracy | 13 | 20 | +54% |
| Item accuracy | 8 | 10 | +25% |
| General (noise) | 40% | 22% | -45% |

#### Changes Made
1. **Korean spelling variations** added for common fashion terms:
   - `김제니` → `제니`, `jennie`, `jenniekim`, `kimjennie`
   - `재킷` → `자켓`, `jacket`
   - `드레스` → `원피스`, `dress`

2. **2-stage matching** implemented:
   ```python
   # Stage 1: Exact match for ambiguous short words
   if tag_clean in exact_set:
       return cat

   # Stage 2: Substring match for unique keywords
   for kw in substring_set:
       if kw in tag_clean:
           return cat
   ```

---

### Celebrity Name Noise in Trend Analysis

**Issue References:** #2705, #2767

#### Problem
Fan content creates noise in trend analysis - celebrity hashtags dominate trends even when not fashion-relevant.

#### Solution
Celebrity exclusion filter in `app.py`:

**100+ Korean celebrities** excluded by default across categories:
- **Girl Groups / Female Idols**: IVE, BLACKPINK, NewJeans, aespa, LE SSERAFIM, etc.
- **Male Idols**: BTS, EXO, NCT, Stray Kids, SEVENTEEN, etc.
- **Actors**: Son Ye-jin, Kim Tae-ri, Han So-hee, etc.
- **Hip-hop / R&B**: Zico, Crush, pH-1, etc.
- **Entertainment / MC**: Yoo Jae-suk, Kang Ho-dong, etc.

**Usage in UI:**
```python
use_celeb_filter = st.checkbox(
    f"셀럽/인물 이름 자동 제외 ({len(_DEFAULT_EXCLUDE_CELEB)}개)",
    value=False,
    help="활성화하면 아이돌, 배우 등 인물 이름 해시태그를 자동 제외합니다. "
         "패션 매거진처럼 셀럽 태그가 트렌드 신호인 경우 OFF 권장.",
)
```

**Note:** For fashion magazines where celebrity tags ARE trend signals, keep this filter **OFF**.

---

## v2.0 Release Improvements

**Issue Reference:** #2720

### Features Added

| Feature | Description |
|---------|-------------|
| **Visualization Dashboard** | Streamlit UI with interactive charts |
| **Enhanced Defense Logic** | Data quality validation, chunk splitting, cost caps |
| **Extended Celebrity Filter** | 100+ Korean celebrities exclusion list |
| **Korean Wordcloud** | Native Korean font support for visualization |

### Quality Improvements

#### Before v2.0
- Basic error handling
- No data validation
- Manual configuration only

#### After v2.0
- Comprehensive quality validation
- Automatic 30-day chunk splitting
- Web UI for non-developers
- Real-time progress feedback

---

## Quick Reference

### Common Error Messages

| Error | Cause | Quick Fix |
|-------|--------|-----------|
| `APIFY_TOKEN이 설정되지 않았습니다` | Missing Apify token | Set `APIFY_TOKEN` environment variable |
| `Google OAuth 설정을 찾을 수 없습니다` | Missing Google credentials | Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` |
| `수집 완전 실패` | Zero data collected | Check account names, verify they're public |
| `SHEETS_TOKEN이 설정되지 않았습니다` | Cloud missing token | Add OAuth token to Streamlit Secrets |
| `Maximum total charge exceeded` | Cost cap reached | Increase `max_cost_usd` or reduce accounts |
| `ModuleNotFoundError` | Missing dependencies | Run `pip install -r requirements.txt` |

### Environment Variables Reference

| Variable | Purpose | Required |
|----------|---------|----------|
| `APIFY_TOKEN` | Apify API authentication | Yes |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Local only |
| `GOOGLE_CLIENT_SECRET` | Google OAuth secret | Local only |
| `SHEETS_TOKEN` | Sheets OAuth token (JSON) | Cloud only |
| `GMAIL_TOKEN` | Gmail OAuth token (JSON) | Cloud only |

### Configuration Best Practices

```yaml
# config/settings.yaml
scraper:
  max_request_retries: 3      # Retry failed requests
  max_concurrency: 5          # Parallel requests
  timeout_secs: 300           # 5 minute base timeout
  timeout_per_account_secs: 30  # Additional time per account
  max_cost_usd: 2.0          # Cost safety limit
  min_results_threshold: 3     # Minimum posts to continue

analysis:
  days: 7                     # Analysis period (days)
  content_type: reels          # posts, reels, or stories
  limit_per_account: 50        # Max posts per account
```

---

## Still Having Issues?

1. Check the [README.md](../README.md) for full setup instructions
2. Review [USER_GUIDE.md](USER_GUIDE.md) for usage details
3. Open an issue on GitHub with:
   - Error message
   - Configuration used
   - Environment (local / Streamlit Cloud)
   - Steps to reproduce

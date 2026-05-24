# ============================================================
# UNIFIED OPTIONS TRADING DASHBOARD
# ============================================================
# One app — full workflow:
#   1. Macro regime (always visible — read this first)
#   2. Trade Ideas — income and growth candidates with
#      specific strategy suggestions and IBKR sizing
#   3. ETF Sector Screener — what sectors are moving
#   4. Holdings Drill-Down — leading stocks inside sectors
#   5. Options Filter — IV, earnings, signal per stock
#
# Run:  streamlit run dashboard.py
# ============================================================

import time
import requests
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Options Trading Dashboard",
    page_icon="🎯",
    layout="wide",
)

# ============================================================
# CONFIG — EDIT THESE LISTS TO CUSTOMISE YOUR UNIVERSE
# ============================================================

# -- ETF sectors (for sector screener tab) -------------------
ETF_SECTORS = {
    "Broad Market":         [("SPY","SPDR S&P 500"),("QQQ","Invesco QQQ"),("IVV","iShares S&P 500"),("VTI","Vanguard Total Market"),("IWM","iShares Russell 2000")],
    "Nasdaq / Growth":      [("QQQ","Invesco QQQ"),("AMOM","QRAFT AI Momentum")],
    "Technology":           [("XLK","Tech Select Sector"),("SKYY","First Trust Cloud"),("CIBR","First Trust Cybersecurity"),("IGV","iShares Software"),("SOCL","Global X Social Media")],
    "Semiconductors":       [("SMH","VanEck Semiconductors"),("SOXX","iShares Semiconductors")],
    "Robotics / AI":        [("BOTZ","Global X Robotics & AI")],
    "Data Centers":         [("SRVR","Pacer Data & Infrastructure")],
    "Fintech / Blockchain": [("FINX","Global X FinTech"),("BLOK","Amplify Blockchain"),("MILN","Global X Millennials")],
    "Clean Energy / EV":    [("TAN","Invesco Solar"),("DRIV","Global X EV"),("ICLN","iShares Clean Energy"),("LIT","Global X Lithium"),("URA","Global X Uranium")],
    "Energy":               [("XLE","Energy Select Sector"),("XOP","SPDR Oil & Gas Exploration"),("OIH","VanEck Oil Services")],
    "Space":                [("UFO","Procure Space ETF")],
    "Industrials":          [("XLI","Industrials Select"),("IYT","iShares Transportation"),("ITA","iShares Aerospace & Defense"),("PAVE","Global X Infrastructure")],
    "Materials":            [("XLB","Materials Select"),("GDX","VanEck Gold Miners"),("SIL","Global X Silver Miners"),("REMX","VanEck Rare Earth")],
    "Consumer Discr":       [("XLY","Consumer Discr Select"),("XRT","SPDR Retail"),("PEJ","Invesco Leisure"),("ITB","iShares Homebuilders")],
    "Consumer Staples":     [("XLP","Consumer Staples Select"),("DBA","Invesco Agriculture"),("PBJ","Invesco Food & Bev"),("PPH","VanEck Pharma")],
    "Healthcare":           [("XLV","Healthcare Select"),("IBB","iShares Biotech"),("XBI","SPDR Biotech"),("IHI","iShares Med Devices"),("ARKG","ARK Genomics")],
    "Financials":           [("XLF","Financials Select"),("KBE","SPDR Bank"),("KRE","SPDR Regional Banking"),("KIE","SPDR Insurance")],
    "Utilities":            [("XLU","Utilities Select"),("VPU","Vanguard Utilities"),("PHO","Invesco Water")],
    "Real Estate":          [("VNQ","Vanguard Real Estate"),("IFGL","iShares Intl Real Estate")],
    "Communication":        [("VOX","Vanguard Communication"),("XLC","Communication Select"),("METV","Roundhill Metaverse")],
    "Macro / Rates":        [("TLT","iShares 20Y Treasury"),("HYG","iShares High Yield"),("GLD","SPDR Gold"),("SLV","iShares Silver")],
    "International":        [("KWEB","KraneShares China Internet"),("FXI","iShares China Large Cap"),("EEM","iShares Emerging Markets")],
    "High Vol / Spec":      [("ARKK","ARK Innovation"),("JETS","US Global Airlines"),("XHB","SPDR Homebuilders")],
}

# -- Stock universe for trade ideas --------------------------
# US stocks: most liquid options, tight spreads on IBKR
# UK stocks: listed as US ADRs — trade these on IBKR for
#            better options liquidity than UK-listed options
STOCK_UNIVERSE = {
    # ── US Technology ─────────────────────────────────────
    "NVDA":  ("NVIDIA",             "Technology", "US"),
    "AAPL":  ("Apple",              "Technology", "US"),
    "MSFT":  ("Microsoft",          "Technology", "US"),
    "META":  ("Meta",               "Technology", "US"),
    "GOOGL": ("Alphabet",           "Technology", "US"),
    "AMZN":  ("Amazon",             "Technology", "US"),
    "AMD":   ("AMD",                "Technology", "US"),
    "AVGO":  ("Broadcom",           "Technology", "US"),
    "CRM":   ("Salesforce",         "Technology", "US"),
    "NOW":   ("ServiceNow",         "Technology", "US"),
    "CRWD":  ("CrowdStrike",        "Technology", "US"),
    "PANW":  ("Palo Alto Networks", "Technology", "US"),
    "SNOW":  ("Snowflake",          "Technology", "US"),
    # ── US Semiconductors ─────────────────────────────────
    "MU":    ("Micron",             "Semiconductors", "US"),
    "QCOM":  ("Qualcomm",           "Semiconductors", "US"),
    "TSM":   ("Taiwan Semi",        "Semiconductors", "US"),
    "AMAT":  ("Applied Materials",  "Semiconductors", "US"),
    "INTC":  ("Intel",              "Semiconductors", "US"),
    # ── US Financials ─────────────────────────────────────
    "JPM":   ("JPMorgan",           "Financials", "US"),
    "GS":    ("Goldman Sachs",      "Financials", "US"),
    "BAC":   ("Bank of America",    "Financials", "US"),
    "MS":    ("Morgan Stanley",     "Financials", "US"),
    "V":     ("Visa",               "Financials", "US"),
    "MA":    ("Mastercard",         "Financials", "US"),
    # ── US Healthcare ─────────────────────────────────────
    "LLY":   ("Eli Lilly",          "Healthcare", "US"),
    "UNH":   ("UnitedHealth",       "Healthcare", "US"),
    "ABBV":  ("AbbVie",             "Healthcare", "US"),
    "MRK":   ("Merck",              "Healthcare", "US"),
    "AMGN":  ("Amgen",              "Healthcare", "US"),
    "VRTX":  ("Vertex Pharma",      "Healthcare", "US"),
    # ── US Energy ─────────────────────────────────────────
    "XOM":   ("ExxonMobil",         "Energy", "US"),
    "CVX":   ("Chevron",            "Energy", "US"),
    "COP":   ("ConocoPhillips",     "Energy", "US"),
    "SLB":   ("SLB",                "Energy", "US"),
    # ── US Consumer / Other ───────────────────────────────
    "TSLA":  ("Tesla",              "Consumer Discr", "US"),
    "HD":    ("Home Depot",         "Consumer Discr", "US"),
    "COST":  ("Costco",             "Consumer Staples", "US"),
    "NFLX":  ("Netflix",            "Communication", "US"),
    "DIS":   ("Disney",             "Communication", "US"),
    # ── ETFs (liquid options, good for income plays) ──────
    "SPY":   ("SPDR S&P 500",       "Broad Market", "ETF"),
    "QQQ":   ("Invesco QQQ",        "Broad Market", "ETF"),
    "IWM":   ("Russell 2000",       "Broad Market", "ETF"),
    "GLD":   ("SPDR Gold",          "Commodities",  "ETF"),
    "TLT":   ("iShares 20Y Bonds",  "Rates",        "ETF"),
    # ── UK stocks (US-listed ADRs — better options liquidity
    #    than trading UK-listed options on IBKR) ───────────
    "AZN":   ("AstraZeneca",        "Healthcare",   "UK-ADR"),
    "GSK":   ("GSK plc",            "Healthcare",   "UK-ADR"),
    "BP":    ("BP plc",             "Energy",       "UK-ADR"),
    "SHEL":  ("Shell plc",          "Energy",       "UK-ADR"),
    "HSBC":  ("HSBC Holdings",      "Financials",   "UK-ADR"),
    "RIO":   ("Rio Tinto",          "Materials",    "UK-ADR"),
    "VOD":   ("Vodafone",           "Communication","UK-ADR"),
    "BCS":   ("Barclays",           "Financials",   "UK-ADR"),
    "LYG":   ("Lloyds Banking",     "Financials",   "UK-ADR"),
    "LSXMA": ("Liberty Media",      "Communication","UK-ADR"),
}


# ============================================================
# SMALL CAP UNIVERSE
# ============================================================
# Covers small/mid caps ($500M-$15B market cap) across sectors.
# Split into two uses:
#   OPTIONS: those with liquid options (vol > 300/day on IBKR)
#   INVESTMENT: strong fundamentals worth buying as shares
#
# All US-listed. UK investors trade these on IBKR in USD.
# Options are far more liquid on US-listed names than UK-listed.
# ============================================================
SMALL_CAP_UNIVERSE = {
    # ── Technology / Software ──────────────────────────────
    "APP":   ("AppLovin",          "Technology",      "options+invest"),
    "PLTR":  ("Palantir",          "Technology",      "options+invest"),
    "AXON":  ("Axon Enterprise",   "Technology",      "options+invest"),
    "DUOL":  ("Duolingo",          "Technology",      "invest"),
    "PINS":  ("Pinterest",         "Technology",      "options+invest"),
    "SNAP":  ("Snap",              "Technology",      "options"),
    "RBLX":  ("Roblox",            "Technology",      "options"),
    "U":     ("Unity Software",    "Technology",      "options"),
    "DDOG":  ("Datadog",           "Technology",      "options+invest"),
    "MDB":   ("MongoDB",           "Technology",      "options+invest"),
    "GTLB":  ("GitLab",            "Technology",      "invest"),
    "ZI":    ("ZoomInfo",          "Technology",      "options"),
    # ── Fintech / Crypto ───────────────────────────────────
    "COIN":  ("Coinbase",          "Fintech",         "options+invest"),
    "AFRM":  ("Affirm",            "Fintech",         "options"),
    "SOFI":  ("SoFi Tech",         "Fintech",         "options+invest"),
    "HOOD":  ("Robinhood",         "Fintech",         "options"),
    "NU":    ("Nu Holdings",       "Fintech",         "invest"),
    "MSTR":  ("MicroStrategy",     "Fintech",         "options"),
    # ── Semiconductors / Hardware ──────────────────────────
    "SMCI":  ("Super Micro Comp",  "Semiconductors",  "options+invest"),
    "WOLF":  ("Wolfspeed",         "Semiconductors",  "options"),
    "ACMR":  ("ACM Research",      "Semiconductors",  "invest"),
    "ONTO":  ("Onto Innovation",   "Semiconductors",  "invest"),
    "FORM":  ("FormFactor",        "Semiconductors",  "invest"),
    # ── Healthcare / Biotech ───────────────────────────────
    "ALNY":  ("Alnylam Pharma",    "Biotech",         "options+invest"),
    "INSP":  ("Inspire Medical",   "Healthcare",      "invest"),
    "TMDX":  ("TransMedics",       "Healthcare",      "options+invest"),
    "IRTC":  ("iRhythm Tech",      "Healthcare",      "invest"),
    "RXRX":  ("Recursion Pharma",  "Biotech",         "options"),
    "KRYS":  ("Krystal Biotech",   "Biotech",         "invest"),
    "NRIX":  ("Nurix Therapeutics","Biotech",         "invest"),
    # ── Consumer ───────────────────────────────────────────
    "WING":  ("Wingstop",          "Consumer",        "options+invest"),
    "CAVA":  ("Cava Group",        "Consumer",        "options+invest"),
    "DKNG":  ("DraftKings",        "Consumer",        "options+invest"),
    "CELH":  ("Celsius Holdings",  "Consumer",        "options+invest"),
    "ELF":   ("e.l.f. Beauty",     "Consumer",        "options+invest"),
    "TXRH":  ("Texas Roadhouse",   "Consumer",        "invest"),
    # ── Industrials / Energy ───────────────────────────────
    "GTLS":  ("Chart Industries",  "Industrials",     "invest"),
    "NVT":   ("nVent Electric",    "Industrials",     "invest"),
    "SAIA":  ("Saia Inc",          "Industrials",     "options+invest"),
    "TREX":  ("Trex Company",      "Industrials",     "invest"),
    "BLDR":  ("Builders FirstSrc", "Industrials",     "options+invest"),
    "CCJ":   ("Cameco",            "Energy",          "options+invest"),
    "RRC":   ("Range Resources",   "Energy",          "options"),
    # ── Materials ──────────────────────────────────────────
    "MP":    ("MP Materials",      "Materials",       "options+invest"),
    "ALTM":  ("Arcadium Lithium",  "Materials",       "invest"),
    "HCC":   ("Warrior Met Coal",  "Materials",       "invest"),
    # ── International small caps (US-listed) ───────────────
    "MELI":  ("MercadoLibre",      "International",   "options+invest"),
    "SE":    ("Sea Limited",       "International",   "options+invest"),
    "GRAB":  ("Grab Holdings",     "International",   "invest"),
}

# Macro tickers
MACRO_TICKERS = {
    "VIX":             "^VIX",
    "Gold":            "GC=F",
    "Crude Oil":       "CL=F",
    "US Dollar (DXY)": "DX-Y.NYB",
    "10Y Treasury":    "^TNX",
    "2Y Treasury":     "^IRX",
    "HYG":             "HYG",
    "TLT":             "TLT",
    "SPY":             "^GSPC",
    "RSP":             "RSP",
    "IWM":             "IWM",
}

# GBP/USD rate for sizing (approximation)
GBPUSD = 1.27


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def gbp(usd_amount):
    """Convert USD to GBP string."""
    return f"£{usd_amount / GBPUSD:,.0f}"


def safe_float(val, default=None):
    try:
        return float(val)
    except Exception:
        return default


def pct(val):
    if val is None:
        return "N/A"
    return f"{val:+.1f}%"


def color_val(val, good_positive=True):
    """Return green/red based on value sign."""
    if val is None:
        return "gray"
    if good_positive:
        return "#16a34a" if val >= 0 else "#dc2626"
    return "#dc2626" if val >= 0 else "#16a34a"


# ============================================================
# DATA FETCHING
# ============================================================

@st.cache_data(ttl=300)
def fetch_macro_snapshot():
    """
    Fetch all macro indicators in one pass.
    Returns dict of current values and % changes.
    """
    result = {}
    for name, ticker in MACRO_TICKERS.items():
        try:
            t    = yf.Ticker(ticker)
            info = t.info
            price = (info.get("regularMarketPrice")
                     or info.get("currentPrice")
                     or info.get("previousClose"))
            hist  = t.history(period="1mo")
            if not hist.empty and price:
                prev_close = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else float(hist["Close"].iloc[-1])
                chg_1d = round((float(price) - prev_close) / prev_close * 100, 2)
                start  = float(hist["Close"].iloc[0])
                chg_1m = round((float(price) - start) / start * 100, 2)
                result[name] = {
                    "price": round(float(price), 2),
                    "chg_1d": chg_1d,
                    "chg_1m": chg_1m,
                }
        except Exception:
            pass
    return result


@st.cache_data(ttl=300)
def detect_regime_quick(macro):
    """
    Fast regime classification from macro snapshot.
    Returns (regime_label, colour, short_description, bias)
    """
    risk_off = 0
    risk_on  = 0

    vix = macro.get("VIX", {}).get("price")
    vix_chg = macro.get("VIX", {}).get("chg_1d")
    gold_chg = macro.get("Gold", {}).get("chg_1d")
    hyg_chg  = macro.get("HYG", {}).get("chg_1d")
    spy_chg  = macro.get("SPY", {}).get("chg_1d")
    oil_chg  = macro.get("Crude Oil", {}).get("chg_1d")
    dxy_chg  = macro.get("US Dollar (DXY)", {}).get("chg_1d")

    if vix:
        if vix >= 35:   risk_off += 3
        elif vix >= 25: risk_off += 2
        elif vix <= 15: risk_on  += 2
        else:           risk_on  += 1

    if vix_chg:
        if vix_chg >= 10:  risk_off += 2
        elif vix_chg >= 5: risk_off += 1
        elif vix_chg <= -10: risk_on += 2
        elif vix_chg <= -5:  risk_on += 1

    if gold_chg:
        if gold_chg >= 2:  risk_off += 2
        elif gold_chg <= -1: risk_on += 1

    if hyg_chg:
        if hyg_chg <= -1:  risk_off += 3
        elif hyg_chg >= 1: risk_on  += 2

    if spy_chg:
        if spy_chg >= 2:   risk_on  += 2
        elif spy_chg >= 1: risk_on  += 1
        elif spy_chg <= -2: risk_off += 2
        elif spy_chg <= -1: risk_off += 1

    # Stagflation check
    stag = (oil_chg or 0) >= 3 and (dxy_chg or 0) >= 1

    if stag and risk_off >= 2:
        return ("⚠️ Stagflation Risk", "#b45309",
                "Oil + dollar surging. Growth stocks squeezed. Favour energy/commodities.",
                "puts")

    if risk_off >= 5:
        return ("🔴 Risk-Off", "#dc2626",
                f"VIX {vix:.0f} — fear dominant. HYG falling. Focus on puts and selling premium.",
                "puts")

    if risk_off >= 3:
        return ("🟠 Cautious", "#ea580c",
                "Mixed but leaning risk-off. Reduce size. Use spreads, not naked options.",
                "reduce")

    if risk_on >= 4:
        return ("🟢 Risk-On", "#16a34a",
                f"VIX {vix:.0f} — low fear, credit healthy. Favour calls on leading sectors.",
                "calls")

    if risk_on >= 2:
        return ("🟡 Mildly Risk-On", "#ca8a04",
                "Positive but not euphoric. Selective calls. Monitor for changes.",
                "calls")

    return ("🟡 Neutral", "#6b7280",
            "No dominant signal. Use defined-risk spreads. Wait for clarity.",
            "neutral")


@st.cache_data(ttl=300)
def fetch_stock_data(ticker):
    """
    Fetch everything needed to evaluate a trade idea for one stock:
    price, IV, HV30, earnings, momentum, 52W range.
    """
    try:
        t    = yf.Ticker(ticker)
        info = t.info
        price = safe_float(
            info.get("regularMarketPrice") or info.get("currentPrice")
        )
        if not price:
            return None

        low52  = safe_float(info.get("fiftyTwoWeekLow",  0))
        high52 = safe_float(info.get("fiftyTwoWeekHigh", 0))
        range_pct = (
            round((price - low52) / (high52 - low52) * 100, 1)
            if high52 and high52 != low52 else None
        )

        # Historical volatility (30-day annualised)
        hist = t.history(period="3mo", auto_adjust=True)
        hv30 = None
        if len(hist) >= 30:
            lr   = np.log(hist["Close"] / hist["Close"].shift(1)).dropna()
            hv30 = round(float(lr.tail(30).std() * np.sqrt(252) * 100), 1)

        # 1-month momentum
        mom_1m = None
        if len(hist) >= 21:
            mom_1m = round(
                (float(hist["Close"].iloc[-1]) - float(hist["Close"].iloc[-21]))
                / float(hist["Close"].iloc[-21]) * 100, 1
            )

        # IV from nearest ATM option
        iv = None
        options_vol = None
        pc_ratio    = None
        try:
            dates = t.options
            if dates:
                chain = t.option_chain(dates[0])
                calls = chain.calls
                puts  = chain.puts
                atm   = calls.iloc[(calls["strike"] - price).abs().argsort()[:1]]
                if not atm.empty:
                    iv = round(float(atm["impliedVolatility"].values[0]) * 100, 1)
                cv = calls["volume"].fillna(0).sum()
                pv = puts["volume"].fillna(0).sum()
                options_vol = int(cv + pv)
                if cv > 0:
                    pc_ratio = round(pv / cv, 2)
        except Exception:
            pass

        # ── True IV Rank (52-week percentile) ───────────────────
        # IV rank answers: "Is IV expensive or cheap RIGHT NOW
        # compared to how expensive it has been over the past year?"
        #
        # Method: sample weekly ATM IV over the past 52 weeks by
        # downloading weekly options chains and recording ATM IV.
        # Then calculate where today's IV sits in that distribution.
        #
        # Because fetching 52 weekly chains is slow, we approximate
        # using the stock's weekly close-to-close volatility over 52W
        # to build a realised vol distribution, then compare current IV.
        # This gives a much better rank than IV/HV alone.
        iv_rank = None
        iv_pct_label = "N/A"
        try:
            hist_1y = t.history(period="1y", auto_adjust=True)
            if len(hist_1y) >= 50 and iv:
                # Weekly realised vol samples (proxy for weekly IV history)
                weekly = hist_1y["Close"].resample("W").last().dropna()
                log_rets = np.log(weekly / weekly.shift(1)).dropna()

                # Annualised vol for each rolling 4-week window
                vol_samples = []
                for i in range(4, len(log_rets) + 1):
                    window_vol = float(log_rets.iloc[max(0,i-4):i].std() * np.sqrt(52) * 100)
                    vol_samples.append(window_vol)

                if vol_samples:
                    vol_min = min(vol_samples)
                    vol_max = max(vol_samples)
                    if vol_max > vol_min:
                        # Where does current IV sit in the 52W vol range?
                        iv_rank = round((iv - vol_min) / (vol_max - vol_min) * 100, 0)
                        iv_rank = min(100, max(0, iv_rank))

                        if iv_rank >= 80:
                            iv_pct_label = f"~{iv_rank:.0f}% 🔴 Very High"
                        elif iv_rank >= 60:
                            iv_pct_label = f"~{iv_rank:.0f}% 🟠 High"
                        elif iv_rank >= 40:
                            iv_pct_label = f"~{iv_rank:.0f}% 🟡 Moderate"
                        elif iv_rank >= 20:
                            iv_pct_label = f"~{iv_rank:.0f}% 🟢 Low"
                        else:
                            iv_pct_label = f"~{iv_rank:.0f}% 🟢 Very Low"
        except Exception:
            pass

        # Keep proxy as fallback if true rank fails
        iv_rank_proxy = iv_rank
        if iv_rank_proxy is None and iv and hv30:
            iv_rank_proxy = round(iv / hv30 * 50, 0)
            iv_rank_proxy = min(100, max(0, iv_rank_proxy))
            iv_pct_label  = f"~{iv_rank_proxy:.0f}% (proxy)"

        # Earnings date (3 methods)
        earnings = None
        try:
            ts = info.get("earningsTimestampNext") or info.get("earningsTimestamp")
            if ts:
                dt = pd.Timestamp(ts, unit="s")
                if dt > pd.Timestamp.now():
                    earnings = dt.date()
        except Exception:
            pass

        if not earnings:
            try:
                cal = t.calendar
                if cal and "Earnings Date" in cal:
                    for d in cal["Earnings Date"]:
                        ts = pd.Timestamp(d)
                        if ts.tzinfo:
                            ts = ts.tz_localize(None)
                        if ts > pd.Timestamp.now():
                            earnings = ts.date()
                            break
            except Exception:
                pass

        earnings_days = None
        if earnings:
            earnings_days = (pd.Timestamp(str(earnings)) - pd.Timestamp.now()).days

        # Average daily volume
        avg_vol = safe_float(info.get("averageVolume"))

        # RSI (14-day) — is price momentum stretched?
        rsi = None
        try:
            if len(hist) >= 15:
                delta = hist["Close"].diff()
                gain  = delta.clip(lower=0).rolling(14).mean()
                loss  = (-delta.clip(upper=0)).rolling(14).mean()
                rs    = gain / loss
                rsi   = round(float(100 - (100 / (1 + rs)).iloc[-1]), 1)
        except Exception:
            pass

        # % above 50-day MA — is price stretched from average?
        pct_above_ma50 = None
        try:
            ma50 = hist["Close"].rolling(50).mean().iloc[-1]
            pct_above_ma50 = round((price - float(ma50)) / float(ma50) * 100, 1)
        except Exception:
            pass

        # ATR (14-day) — average daily range, used for range-bound detection
        atr = None
        try:
            if len(hist) >= 15:
                high = hist["High"]
                low  = hist["Low"]
                close_prev = hist["Close"].shift(1)
                tr = pd.concat([
                    high - low,
                    (high - close_prev).abs(),
                    (low  - close_prev).abs()
                ], axis=1).max(axis=1)
                atr = round(float(tr.rolling(14).mean().iloc[-1]), 2)
        except Exception:
            pass

        # Range-bound check: is ATR contracting vs recent average?
        is_range_bound = False
        try:
            if atr and len(hist) >= 30:
                atr_30 = float(tr.rolling(30).mean().iloc[-1])
                is_range_bound = atr < atr_30 * 0.85  # ATR 15% below 30-day avg
        except Exception:
            pass

        return {
            "ticker":          ticker,
            "name":            STOCK_UNIVERSE.get(ticker, (ticker, "", ""))[0],
            "sector":          STOCK_UNIVERSE.get(ticker, ("", "", ""))[1],
            "market":          STOCK_UNIVERSE.get(ticker, ("", "", ""))[2],
            "price":           price,
            "range_pct":       range_pct,
            "hv30":            hv30,
            "iv":              iv,
            "iv_rank_proxy":   iv_rank_proxy,
            "iv_pct_label":    iv_pct_label,
            "mom_1m":          mom_1m,
            "pc_ratio":        pc_ratio,
            "options_vol":     options_vol,
            "earnings":        str(earnings) if earnings else None,
            "earnings_days":   earnings_days,
            "avg_vol":         avg_vol,
            "rsi":             rsi,
            "pct_above_ma50":  pct_above_ma50,
            "atr":             atr,
            "is_range_bound":  is_range_bound,
        }
    except Exception:
        return None


def generate_income_idea(d, regime_bias):
    """
    Given stock data dict, generate an income (sell premium) trade idea.
    Returns dict with trade details or None if stock not suitable.

    Income plays work best when:
    - IV is high (you collect more premium)
    - Stock is range-bound or mildly trending
    - No earnings within 30 days (earnings cause IV spikes
      which would hurt short premium positions)
    - Options are liquid (tight spreads on IBKR)
    """
    if not d or not d["iv"] or not d["hv30"] or not d["price"]:
        return None

    iv_rank = d["iv_rank_proxy"] or 0
    iv      = d["iv"]
    price   = d["price"]
    hv30    = d["hv30"]

    # Income criteria:
    # IV rank > 50 means options are expensive relative to
    # actual moves — good time to sell premium
    if iv_rank < 45:
        return None

    # Avoid earnings within 30 days:
    # When earnings approach, IV spikes dramatically.
    # If you're short premium, this spike works against you.
    if d["earnings_days"] and d["earnings_days"] < 30:
        return None

    # Need liquid options
    if d["options_vol"] and d["options_vol"] < 500:
        return None

    # ── Dynamic spread width based on stock price ──────────────
    # A $5 spread on a $50 stock (10% wide) is very different from
    # a $5 spread on NVDA at $900 (0.5% wide — almost meaningless).
    # Scale the spread width so it represents a consistent ~3-4% of price.
    if price < 50:
        spread_width = 2.50
        sell_pct     = 0.94    # 6% OTM on cheap stocks
    elif price < 150:
        spread_width = 5.0
        sell_pct     = 0.93    # 7% OTM
    elif price < 500:
        spread_width = 10.0
        sell_pct     = 0.92    # 8% OTM — more room needed on mid-price stocks
    else:
        spread_width = 25.0
        sell_pct     = 0.91    # 9% OTM on high-price stocks like NVDA

    # ── Anchor sell strike to 50MA or recent low if available ───
    # Selling puts BELOW a known support level is safer than mechanical OTM %.
    # The stock has to break that support level before you lose money.
    ma50_level = None
    recent_low = None
    try:
        _hist_s = yf.Ticker(ticker).history(period="3mo", auto_adjust=True)
        if len(_hist_s) >= 50:
            ma50_level = float(_hist_s["Close"].rolling(50).mean().iloc[-1])
        if len(_hist_s) >= 20:
            recent_low = float(_hist_s["Low"].tail(20).min())
    except Exception:
        pass

    # Choose the best anchor for the sell strike:
    # Prefer the level that is below price but above the mechanical OTM strike
    mech_sell = round(price * sell_pct, 0)
    sell_put  = mech_sell

    if ma50_level and ma50_level < price * 0.98 and ma50_level > price * 0.85:
        # 50MA is a natural support — sell just below it
        sell_put = round(ma50_level * 0.99, 0)
    elif recent_low and recent_low < price * 0.97 and recent_low > price * 0.84:
        sell_put = round(recent_low * 0.985, 0)

    buy_put = sell_put - spread_width

    # Estimated premium scaled to spread width and IV rank
    est_premium_per_share = round(spread_width * 0.30 * (iv_rank / 100), 2)
    est_premium_per_share = max(est_premium_per_share, spread_width * 0.15)
    est_premium_contract  = round(est_premium_per_share * 100, 0)
    max_risk_contract     = (spread_width - est_premium_per_share) * 100
    max_risk_contract     = max(max_risk_contract, spread_width * 70)

    # How many contracts for £700 max risk
    max_risk_gbp = 700
    max_risk_usd = max_risk_gbp * GBPUSD
    contracts    = max(1, int(max_risk_usd / max_risk_contract))

    # ── Income scoring — higher = better candidate ──────────────
    # Weights explained:
    #   IV rank (40pts): the higher options are priced vs history,
    #     the more premium you collect. This is the primary signal.
    #   Earnings (20pts): short premium = short vega. Earnings cause
    #     IV to spike, which hurts your position. Avoid within 30 days.
    #   Liquidity (20pts): wide bid/ask spreads eat your collected premium.
    #     Need >1000 daily options volume for reasonable fills on IBKR.
    #   Range-bound (15pts): selling puts into a strong downtrend is
    #     dangerous. Stocks near mid-range or contracting ATR are safer.
    #   RSI moderate (10pts): avoid selling puts on overbought stocks
    #     (RSI>75) — pullback risk is high.
    score = 0
    score += min(40, iv_rank * 0.4)
    if d["earnings_days"] and d["earnings_days"] > 45:
        score += 20
    elif d.get("earnings_days") and d["earnings_days"] > 30:
        score += 10
    if d["options_vol"] and d["options_vol"] > 5000:
        score += 20
    elif d["options_vol"] and d["options_vol"] > 1000:
        score += 10
    if d.get("is_range_bound"):
        score += 15                              # ATR contracting = consolidating
    elif d.get("range_pct") and 30 < d["range_pct"] < 70:
        score += 8                               # mid 52W range also a good sign
    rsi = d.get("rsi")
    if rsi and 40 < rsi < 65:
        score += 10                              # RSI not stretched
    elif rsi and (rsi > 75 or rsi < 30):
        score -= 10                              # overbought/oversold = risky

    # ── Dynamic expiry recommendation based on VIX ─────────────
    # VIX spike → shorter expiry collects same premium with less risk
    # Low VIX → longer expiry needed to collect meaningful premium
    if vix_val and vix_val >= 30:
        rec_expiry = "14-21 DTE"
        expiry_note = f"VIX {vix_val:.0f} — elevated. Shorter expiry (14-21 DTE) collects same premium with less time exposure."
    elif vix_val and vix_val <= 15:
        rec_expiry = "45 DTE"
        expiry_note = f"VIX {vix_val:.0f} — low. Use longer expiry (45 DTE) to collect meaningful premium."
    else:
        rec_expiry = "21-30 DTE"
        expiry_note = f"VIX {vix_val:.0f} — normal. Standard 21-30 DTE expiry."

    return {
        "type":                "income",
        "ticker":              d["ticker"],
        "name":                d["name"],
        "sector":              d["sector"],
        "market":              d["market"],
        "price":               price,
        "iv":                  iv,
        "iv_rank_proxy":       iv_rank,
        "iv_pct_label":        d.get("iv_pct_label", f"~{iv_rank:.0f}%"),
        "hv30":                hv30,
        "rsi":                 d.get("rsi"),
        "pct_above_ma50":      d.get("pct_above_ma50"),
        "is_range_bound":      d.get("is_range_bound"),
        "range_pct":           d["range_pct"],
        "mom_1m":              d["mom_1m"],
        "earnings":            d["earnings"],
        "earnings_days":       d["earnings_days"],
        "options_vol":         d["options_vol"],
        "sell_put":            sell_put,
        "buy_put":             buy_put,
        "est_premium":         est_premium_contract,
        "max_risk_contract":   max_risk_contract,
        "contracts":           contracts,
        "score":               round(score, 0),
        "strategy":            f"Sell ${sell_put:.0f}/${buy_put:.0f} Put Spread",
        "spread_width":        spread_width,
        "rec_expiry":          rec_expiry,
        "expiry_note":         expiry_note,
        "anchor_used":         "50MA" if (ma50_level and sell_put != mech_sell and ma50_level < price) else ("Recent Low" if (recent_low and sell_put != mech_sell) else "Mechanical OTM"),
    }


def generate_growth_idea(d, regime_bias, sector_strong=True):
    """
    Given stock data dict, generate a growth (buy options) trade idea.
    Returns dict with trade details or None if stock not suitable.

    Growth plays work best when:
    - Stock has clear directional momentum
    - IV is low (options are cheap — you're buying)
    - Sector is in a strong trend (tailwind behind the trade)
    - No earnings within 14 days (unless intentionally trading earnings)
    """
    if not d or not d["iv"] or not d["hv30"] or not d["price"]:
        return None

    iv_rank = d["iv_rank_proxy"] or 0
    iv      = d["iv"]
    price   = d["price"]
    mom_1m  = d["mom_1m"] or 0
    rng     = d["range_pct"] or 50

    # For calls: need positive momentum + near annual high
    # For puts: need negative momentum + near annual low
    is_call = mom_1m >= 3 and rng >= 55
    is_put  = mom_1m <= -3 and rng <= 45

    if not is_call and not is_put:
        return None

    # IV rank < 55: options not too expensive to buy
    if iv_rank > 60:
        return None

    # Avoid earnings within 14 days
    # (unless you specifically want an earnings play —
    # that's a different strategy not covered here)
    if d["earnings_days"] and d["earnings_days"] < 14:
        return None

    # Need some options liquidity
    if d["options_vol"] and d["options_vol"] < 200:
        return None

    direction = "Call" if is_call else "Put"

    # Suggest slightly OTM strike (best risk/reward for directional plays)
    if direction == "Call":
        strike = round(price * 1.03, 0)   # 3% OTM call
    else:
        strike = round(price * 0.97, 0)   # 3% OTM put

    # Rough premium estimate (OTM option, ~14-21 DTE)
    # Using Black-Scholes approximation: premium ≈ 0.4 × IV × price × √(T/252)
    T = 21 / 252
    est_premium_per_share = round(0.4 * (iv / 100) * price * np.sqrt(T), 2)
    est_premium_per_share = max(est_premium_per_share, 0.50)
    est_cost_contract     = round(est_premium_per_share * 100, 0)

    # How many contracts for £700 budget
    budget_gbp   = 700
    budget_usd   = budget_gbp * GBPUSD
    contracts    = max(1, int(budget_usd / est_cost_contract))
    # Cap at 5 — diversification
    contracts    = min(contracts, 5)

    # ── Growth scoring — higher = better candidate ──────────────
    # Weights explained:
    #   Momentum (30pts): is there already a move in the right direction?
    #     Buying calls on a stock already moving up = momentum confirmation.
    #   52W position (25pts): calls need the stock near its high (strong trend).
    #     Puts need the stock near its low (established downtrend).
    #   IV cheapness (20pts): the less you pay for options relative to
    #     historical volatility, the better your risk/reward.
    #   RSI (15pts): for calls, RSI 50-70 is ideal — not overbought yet.
    #     For puts, RSI 30-50 is ideal — not oversold yet.
    #   Liquidity + sector (15pts): ensures the trade is executable.
    score = 0
    score += min(30, abs(mom_1m) * 2)
    score += min(25, (rng - 50) * 1.2) if is_call else min(25, (50 - rng) * 1.2)
    score += max(0, (55 - iv_rank) * 0.4)
    rsi = d.get("rsi")
    if rsi:
        if is_call and 50 <= rsi <= 70:
            score += 15                          # ideal call RSI — trending not overbought
        elif is_call and rsi > 75:
            score -= 15                          # overbought — pullback risk for calls
        elif not is_call and 30 <= rsi <= 50:
            score += 15                          # ideal put RSI — trending down not oversold
        elif not is_call and rsi < 25:
            score -= 15                          # oversold — bounce risk for puts
    pct_ma = d.get("pct_above_ma50")
    if pct_ma:
        if is_call and 0 < pct_ma < 15:
            score += 10                          # above MA but not too stretched
        elif is_call and pct_ma >= 15:
            score -= 5                           # too far above MA — stretched
        elif not is_call and -15 < pct_ma < 0:
            score += 10                          # below MA but not too oversold
    if d["options_vol"] and d["options_vol"] > 2000:
        score += 10
    if sector_strong:
        score += 10

    return {
        "type":            "growth",
        "direction":       direction,
        "ticker":          d["ticker"],
        "name":            d["name"],
        "sector":          d["sector"],
        "market":          d["market"],
        "price":           price,
        "iv":              iv,
        "iv_rank_proxy":   iv_rank,
        "iv_pct_label":    d.get("iv_pct_label", f"~{iv_rank:.0f}%"),
        "hv30":            d["hv30"],
        "rsi":             d.get("rsi"),
        "pct_above_ma50":  d.get("pct_above_ma50"),
        "range_pct":       rng,
        "mom_1m":          mom_1m,
        "earnings":        d["earnings"],
        "earnings_days":   d["earnings_days"],
        "options_vol":     d["options_vol"],
        "strike":          strike,
        "direction":       direction,
        "est_cost":        est_cost_contract,
        "contracts":       contracts,
        "score":           round(score, 0),
        "strategy":        f"Buy ${strike:.0f} {direction} (21 DTE)",
    }



@st.cache_data(ttl=3600)   # 1-hour cache — fundamentals don't change hourly
def fetch_fundamentals(ticker):
    """
    Fetches financial quality metrics for investment screening.
    Returns dict of fundamental data or None if unavailable.

    Why each metric matters for small cap investment:
      Revenue growth  — is the business actually expanding?
      Free cashflow   — does it generate real cash, not just accounting profit?
      FCF yield       — how much cash do you get per £ invested?
      Debt/Equity     — can it survive a downturn without going bust?
      ROE             — how efficiently does management use shareholder money?
      Gross margin    — does the business have pricing power?
      P/E or P/S      — are you paying a reasonable price for the growth?
    """
    try:
        t    = yf.Ticker(ticker)
        info = t.info

        # Price and market cap
        price   = safe_float(info.get("regularMarketPrice") or info.get("currentPrice"))
        mkt_cap = safe_float(info.get("marketCap"))

        if not price or not mkt_cap:
            return None

        mkt_cap_b = round(mkt_cap / 1e9, 2)   # in billions

        # Revenue metrics
        rev         = safe_float(info.get("totalRevenue"))
        rev_growth  = safe_float(info.get("revenueGrowth"))      # YoY as decimal
        rev_growth_pct = round(rev_growth * 100, 1) if rev_growth else None

        # Profitability
        gross_margin  = safe_float(info.get("grossMargins"))
        profit_margin = safe_float(info.get("profitMargins"))
        roe           = safe_float(info.get("returnOnEquity"))
        gross_pct     = round((gross_margin or 0) * 100, 1)
        roe_pct       = round((roe or 0) * 100, 1)

        # Cashflow — the most important metric for small caps
        # Free cashflow = operating cashflow minus capex
        # Positive FCF means the business generates real cash
        fcf           = safe_float(info.get("freeCashflow"))
        op_cf         = safe_float(info.get("operatingCashflow"))
        fcf_yield     = round(fcf / mkt_cap * 100, 1) if fcf and mkt_cap else None

        # Debt
        de_ratio      = safe_float(info.get("debtToEquity"))      # as ratio (100 = 1x)
        de_ratio_norm = round(de_ratio / 100, 2) if de_ratio else None  # normalise to 1x

        # Valuation
        pe            = safe_float(info.get("trailingPE") or info.get("forwardPE"))
        ps            = safe_float(info.get("priceToSalesTrailingTwelveMonths"))

        # 52W range and momentum
        low52  = safe_float(info.get("fiftyTwoWeekLow"))
        high52 = safe_float(info.get("fiftyTwoWeekHigh"))
        range_pct = (
            round((price - low52) / (high52 - low52) * 100, 1)
            if high52 and high52 != low52 else None
        )

        # 1-month and 6-month momentum
        try:
            hist   = t.history(period="1y", auto_adjust=True)
            mom_1m = round((float(hist["Close"].iloc[-1]) / float(hist["Close"].iloc[-21]) - 1) * 100, 1) if len(hist) >= 21 else None
            mom_6m = round((float(hist["Close"].iloc[-1]) / float(hist["Close"].iloc[-126]) - 1) * 100, 1) if len(hist) >= 126 else None
        except Exception:
            mom_1m = mom_6m = None

        # IWM relative strength (1 month)
        rs_vs_iwm = None
        try:
            iwm_hist = yf.download("IWM", period="1mo", auto_adjust=True, progress=False)
            iwm_ret  = round((float(iwm_hist["Close"].iloc[-1]) / float(iwm_hist["Close"].iloc[0]) - 1) * 100, 1)
            if mom_1m is not None:
                rs_vs_iwm = round(mom_1m - iwm_ret, 1)
        except Exception:
            pass

        # Quality score (0-100)
        # Designed to surface genuinely strong small cap businesses
        q_score = 0
        # Revenue growth — but also check for deceleration
        # A company growing at 20% last year but now at 5% is NOT a 20% grower.
        # yfinance revenueGrowth is the most recent quarter YoY.
        # We penalise if growth is decelerating vs what the market expects.
        if rev_growth_pct and rev_growth_pct >= 20:
            q_score += 25
        elif rev_growth_pct and rev_growth_pct >= 10:
            q_score += 15
        elif rev_growth_pct and rev_growth_pct >= 0:
            q_score += 5
        elif rev_growth_pct and rev_growth_pct < 0:
            q_score -= 10   # declining revenue = serious red flag for small caps

        if fcf and fcf > 0:                           q_score += 25   # cash generative
        elif op_cf and op_cf > 0:                     q_score += 10   # at least positive ops CF

        if gross_pct >= 60:                            q_score += 15   # high margin business
        elif gross_pct >= 40:                          q_score += 8

        if de_ratio_norm is not None:
            if de_ratio_norm < 0.5:                   q_score += 15   # low debt
            elif de_ratio_norm < 1.0:                 q_score += 8
            elif de_ratio_norm > 2.0:                 q_score -= 10   # overleveraged

        if rs_vs_iwm and rs_vs_iwm >= 5:              q_score += 15   # beating small cap index
        elif rs_vs_iwm and rs_vs_iwm >= 0:            q_score += 8
        elif rs_vs_iwm and rs_vs_iwm < -10:           q_score -= 10   # lagging badly

        if roe_pct >= 15:                              q_score += 5
        q_score = max(0, min(100, q_score))

        # Verdict
        if q_score >= 75 and fcf and fcf > 0 and rev_growth_pct and rev_growth_pct >= 15:
            verdict = "🟢 Strong Buy Candidate"
            verdict_note = "High quality business: growing revenue, generating cash, manageable debt, beating IWM."
        elif q_score >= 55 and (fcf and fcf > 0 or op_cf and op_cf > 0):
            verdict = "🟡 Watch List"
            verdict_note = "Good fundamentals but one or more metrics need monitoring."
        elif q_score >= 40:
            verdict = "⚪ Neutral"
            verdict_note = "Mixed signals. Not strong enough to act on yet."
        else:
            verdict = "🔴 Avoid"
            verdict_note = "Weak fundamentals or deteriorating trend."

        return {
            "ticker":       ticker,
            "name":         SMALL_CAP_UNIVERSE.get(ticker, (ticker,"",""))[0],
            "sector":       SMALL_CAP_UNIVERSE.get(ticker, ("","",""))[1],
            "use":          SMALL_CAP_UNIVERSE.get(ticker, ("","","invest"))[2],
            "price":        price,
            "mkt_cap_b":    mkt_cap_b,
            "rev_growth":   rev_growth_pct,
            "gross_pct":    gross_pct,
            "fcf":          fcf,
            "fcf_yield":    fcf_yield,
            "op_cf":        op_cf,
            "de_ratio":     de_ratio_norm,
            "roe_pct":      roe_pct,
            "pe":           round(pe, 1) if pe else None,
            "ps":           round(ps, 1) if ps else None,
            "range_pct":    range_pct,
            "mom_1m":       mom_1m,
            "mom_6m":       mom_6m,
            "rs_vs_iwm":    rs_vs_iwm,
            "q_score":      q_score,
            "verdict":      verdict,
            "verdict_note": verdict_note,
        }
    except Exception:
        return None


@st.cache_data(ttl=300)
def scan_small_cap_options():
    """
    Scans small cap universe for options trade candidates.
    Reuses fetch_stock_data for options metrics.
    Filters to only those with sufficient options liquidity.
    """
    income = []
    growth = []
    for ticker, (name, sector, use) in SMALL_CAP_UNIVERSE.items():
        if "options" not in use:
            continue
        d = fetch_stock_data(ticker)
        if not d:
            continue
        # Small caps need at least 300 options volume — less than large caps
        # but enough for reasonable fills on IBKR
        if d.get("options_vol") and d["options_vol"] < 300:
            continue
        # Must have positive cashflow signal (avoid pure momentum plays)
        fund = fetch_fundamentals(ticker)
        if fund:
            if fund.get("fcf") and fund["fcf"] < 0 and (fund.get("op_cf") or 0) < 0:
                continue   # burning cash = too risky for selling premium

        inc = generate_income_idea(d, "neutral")
        if inc:
            inc["is_small_cap"] = True
            income.append(inc)

        gr = generate_growth_idea(d, "neutral",
                                  sector_strong=(fund and (fund.get("rs_vs_iwm") or 0) >= 0))
        if gr:
            gr["is_small_cap"] = True
            growth.append(gr)

        time.sleep(0.15)

    income.sort(key=lambda x: x["score"], reverse=True)
    growth.sort(key=lambda x: x["score"], reverse=True)
    return income[:6], growth[:6]


@st.cache_data(ttl=3600)
def scan_investment_watchlist():
    """
    Scans full small cap universe for investment candidates.
    Returns sorted list of fundamentally strong small caps.
    """
    results = []
    for ticker in SMALL_CAP_UNIVERSE:
        fund = fetch_fundamentals(ticker)
        if fund:
            results.append(fund)
        time.sleep(0.2)
    results.sort(key=lambda x: x["q_score"], reverse=True)
    return results

@st.cache_data(ttl=300)
def fetch_all_candidates():
    """
    Scan all stocks in STOCK_UNIVERSE and return
    income and growth candidates sorted by score.
    """
    income_candidates  = []
    growth_candidates  = []

    for ticker in STOCK_UNIVERSE:
        d = fetch_stock_data(ticker)
        if not d:
            continue

        income = generate_income_idea(d, "neutral")
        if income:
            income_candidates.append(income)

        growth = generate_growth_idea(d, "neutral")
        if growth:
            growth_candidates.append(growth)

        time.sleep(0.2)

    income_candidates.sort(key=lambda x: x["score"], reverse=True)
    growth_candidates.sort(key=lambda x: x["score"], reverse=True)
    return income_candidates[:8], growth_candidates[:8]


@st.cache_data(ttl=600)
def fetch_all_etf_returns(tickers):
    """Batch fetch returns for all ETFs."""
    all_t = list(set(tickers + ["SPY"]))
    try:
        # Daily for 3D/1W/1M/3M
        raw = yf.download(all_t, period="6mo", interval="1d",
                          auto_adjust=True, progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            closes = raw["Close"]
        else:
            closes = raw
        if hasattr(closes.index, "tz") and closes.index.tz:
            closes.index = closes.index.tz_localize(None)

        # Intraday for 1D (today vs yesterday's close)
        intra = yf.download(all_t, period="5d", interval="5m",
                            auto_adjust=True, progress=False)
        if isinstance(intra.columns, pd.MultiIndex):
            intra_c = intra["Close"]
        else:
            intra_c = intra
        if hasattr(intra_c.index, "tz") and intra_c.index.tz:
            intra_c.index = intra_c.index.tz_localize(None)

        today     = pd.Timestamp.now().normalize()
        yesterday = today - pd.tseries.offsets.BDay(1)

        def safe_ret(series, n):
            s = series.dropna()
            return round((float(s.iloc[-1]) / float(s.iloc[-n]) - 1) * 100, 2) if len(s) >= n else None

        def live_1d(ticker):
            if intra_c.empty or ticker not in intra_c.columns:
                return None
            s = intra_c[ticker].dropna()
            if s.empty:
                return None
            latest  = float(s.iloc[-1])
            prev    = s[s.index.normalize() <= yesterday]
            if prev.empty:
                return None
            return round((latest / float(prev.iloc[-1]) - 1) * 100, 2)

        spy_1m = safe_ret(closes["SPY"], 21) if "SPY" in closes.columns else None

        results = {}
        for t in tickers:
            if t not in closes.columns:
                continue
            r1m = safe_ret(closes[t], 21)
            results[t] = {
                "ret_1d":    live_1d(t),
                "ret_3d":    safe_ret(closes[t], 3),
                "ret_1w":    safe_ret(closes[t], 5),
                "ret_1m":    r1m,
                "ret_3m":    safe_ret(closes[t], 63),
                "rs_vs_spy": round(r1m - spy_1m, 2) if r1m and spy_1m else None,
            }
        return results
    except Exception:
        return {}


@st.cache_data(ttl=86400)
def fetch_holdings(etf_ticker, fmp_key=""):
    """Fetch ETF holdings from stockanalysis.com or FMP."""
    try:
        url  = f"https://stockanalysis.com/etf/{etf_ticker.lower()}/holdings/"
        hdrs = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r    = requests.get(url, headers=hdrs, timeout=12)
        if r.status_code == 200:
            tables = pd.read_html(r.text)
            if tables:
                df = tables[0].head(15).copy()
                col_map = {}
                for c in df.columns:
                    cl = str(c).lower()
                    if "symbol" in cl or "ticker" in cl: col_map[c] = "Ticker"
                    elif "name" in cl or "company" in cl: col_map[c] = "Name"
                    elif "weight" in cl or cl == "%": col_map[c] = "Weight %"
                df = df.rename(columns=col_map)
                keep = [c for c in ["Ticker","Name","Weight %"] if c in df.columns]
                if "Ticker" in keep:
                    df = df[keep]
                    if "Weight %" in df.columns:
                        df["Weight %"] = (pd.to_numeric(
                            df["Weight %"].astype(str).str.replace("%","",regex=False).str.strip(),
                            errors="coerce"
                        ).round(2))
                        df = df.sort_values("Weight %", ascending=False)
                    df["Source"] = "🟢 Live"
                    return df.reset_index(drop=True)
    except Exception:
        pass

    if fmp_key:
        try:
            url  = f"https://financialmodelingprep.com/api/v3/etf-holder/{etf_ticker}?apikey={fmp_key}"
            r    = requests.get(url, timeout=10).json()
            if isinstance(r, list) and r:
                df = pd.DataFrame(r[:15]).rename(columns={
                    "asset":"Ticker","weightPercentage":"Weight %","name":"Name"})
                df["Weight %"] = pd.to_numeric(df.get("Weight %",0), errors="coerce").round(2)
                cols = [c for c in ["Ticker","Name","Weight %"] if c in df.columns]
                df = df[cols].sort_values("Weight %", ascending=False).reset_index(drop=True)
                df["Source"] = "🟡 Live (FMP)"
                return df
        except Exception:
            pass

    return pd.DataFrame(columns=["Ticker","Name","Weight %"])


@st.cache_data(ttl=3600)
def calc_relative_strength(stock_tickers, etf_ticker, period="1mo"):
    """Calculate each stock's return vs the ETF."""
    all_t = list(set(stock_tickers + [etf_ticker]))
    try:
        raw    = yf.download(all_t, period=period, auto_adjust=True, progress=False)
        closes = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
        rets   = ((closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0] * 100).round(2)
        etf_r  = float(rets.get(etf_ticker, 0))
        rows   = []
        for t in stock_tickers:
            sr = rets.get(t)
            if sr is not None:
                vs = round(float(sr) - etf_r, 2)
                rows.append({
                    "Ticker":   t,
                    f"Ret ({period}) %": round(float(sr), 2),
                    "ETF Ret %": round(etf_r, 2),
                    "vs ETF %": vs,
                    "Status":   "✅ Leading" if vs > 0 else "⚠️ Lagging",
                })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()



@st.cache_data(ttl=300)   # 5-min cache — VWAP is intraday, needs to be fresh
def fetch_vwap(tickers):
    """
    Fetches today's VWAP for each ticker using 5-minute intraday data.

    VWAP = Volume Weighted Average Price.
    Resets every trading day at market open.
    Institutional traders use it as a key reference:
      • Price above VWAP = buyers in control = call bias
      • Price below VWAP = sellers in control = put bias
      • Price crossing VWAP upward = potential entry for calls
      • Price crossing VWAP downward = potential entry for puts

    For options specifically:
      ENTRY: buy calls when price is above VWAP and pulling back to it
             buy puts when price is below VWAP and bouncing up to it
      EXIT:  take profit on calls when price hits VWAP resistance
             take profit on puts when price hits VWAP support

    Only meaningful during market hours — outside hours shows yesterday's
    closing VWAP which is less useful.
    """
    result = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, period="1d", interval="5m",
                             auto_adjust=True, progress=False)
            if df.empty:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            # VWAP = sum(typical_price × volume) / sum(volume)
            # Typical price = (High + Low + Close) / 3
            typical = (df["High"] + df["Low"] + df["Close"]) / 3
            cum_tpv  = (typical * df["Volume"]).cumsum()
            cum_vol  = df["Volume"].cumsum()
            vwap_series = cum_tpv / cum_vol
            vwap_val = float(vwap_series.iloc[-1])
            last_price = float(df["Close"].iloc[-1])

            pct_vs_vwap = round((last_price - vwap_val) / vwap_val * 100, 2)

            if pct_vs_vwap >= 1.5:
                vwap_sig = f"📈 {pct_vs_vwap:+.1f}% above — Call bias"
            elif pct_vs_vwap >= 0.3:
                vwap_sig = f"🟡 {pct_vs_vwap:+.1f}% above — Near VWAP"
            elif pct_vs_vwap <= -1.5:
                vwap_sig = f"📉 {pct_vs_vwap:+.1f}% below — Put bias"
            elif pct_vs_vwap <= -0.3:
                vwap_sig = f"🟡 {pct_vs_vwap:+.1f}% below — Near VWAP"
            else:
                vwap_sig = f"⚖️ AT VWAP — Wait for direction"

            result[ticker] = {
                "vwap":         round(vwap_val, 2),
                "price":        round(last_price, 2),
                "pct_vs_vwap":  pct_vs_vwap,
                "vwap_sig":     vwap_sig,
            }
        except Exception:
            pass
    return result

# ============================================================
# UI HELPERS
# ============================================================

def color_range_cell(val):
    if val is None: return ""
    if val >= 60:  return "background-color:#bbf7d0"
    if val >= 35:  return "background-color:#fef08a"
    return "background-color:#fecaca"


def render_trade_card(idea, regime_bias):
    """Render one trade idea as a styled expander card."""
    if not idea:
        return

    ticker    = idea["ticker"]
    name      = idea["name"]
    sector    = idea["sector"]
    market    = idea["market"]
    price     = idea["price"]
    iv        = idea["iv"]
    iv_rank   = idea.get("iv_rank_proxy", 0) or 0
    hv30      = idea["hv30"]
    mom_1m    = idea["mom_1m"]
    rng       = idea["range_pct"]
    earnings  = idea["earnings"]
    earn_days = idea["earnings_days"]
    opt_vol   = idea["options_vol"]
    strategy  = idea["strategy"]
    score     = idea["score"]
    iv_rank   = idea.get("iv_rank_proxy", 0) or 0
    iv_label  = idea.get("iv_pct_label") or f"~{iv_rank:.0f}%"
    mkt_flag  = "🇬🇧" if market == "UK-ADR" else ("📊" if market == "ETF" else "🇺🇸")

    if idea["type"] == "income":
        sell_put  = idea["sell_put"]
        buy_put   = idea["buy_put"]
        premium   = idea["est_premium"]
        max_risk  = idea["max_risk_contract"]
        contracts = idea["contracts"]

        header = (
            f"💰 {mkt_flag} {ticker}  —  {name}  —  ${price:.2f}  "
            f"|  IV Rank {iv_label}  |  Score {score:.0f}  "
            f"▼ expand"
        )

        with st.expander(header, expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Strategy:** {strategy}")
                rsi_val    = idea.get("rsi")
                ma50_val   = idea.get("pct_above_ma50")
                range_b    = idea.get("is_range_bound")

                rsi_note = ""
                if rsi_val:
                    if 40 < rsi_val < 65:
                        rsi_note = f"RSI {rsi_val:.0f} — not stretched, good for selling puts."
                    elif rsi_val >= 75:
                        rsi_note = f"⚠️ RSI {rsi_val:.0f} — elevated. Put spread below support preferred."
                    else:
                        rsi_note = f"RSI {rsi_val:.0f}."

                ma_note = ""
                if ma50_val is not None:
                    if abs(ma50_val) < 8:
                        ma_note = f"Price within {abs(ma50_val):.1f}% of 50MA — range-bound."
                    elif ma50_val >= 8:
                        ma_note = f"Price {ma50_val:.1f}% above 50MA — stretched, use wider OTM strikes."

                range_note = "✅ ATR contracting — stock consolidating (good for income)." if range_b else ""

                st.markdown(
                    f"**Why this is an income play:**  \n"
                    f"IV at **{iv:.1f}%** vs HV30 **{hv30:.1f}%** — "
                    f"options pricing in bigger moves than the stock is actually making. "
                    f"IV rank **{iv_label}** — options are expensive vs the past year.  \n"
                    + (f"{rsi_note}  \n" if rsi_note else "")
                    + (f"{ma_note}  \n" if ma_note else "")
                    + (f"{range_note}" if range_note else "")
                )
                st.markdown(
                    f"**Sell the ${sell_put:.0f} put, buy the ${buy_put:.0f} put.**  \n"
                    f"You collect premium upfront. As long as {ticker} stays above "
                    f"${sell_put:.0f} at expiry, you keep it all.  \n"
                    f"If it falls below ${sell_put:.0f}, your loss is capped at the "
                    f"spread width ($5) minus the premium collected."
                )

            with c2:
                st.markdown("**Trade details:**")
                st.markdown(
                    f"- Collect: ~**${premium:.0f}/contract** ({gbp(premium)})"
                )
                st.markdown(
                    f"- Max risk: ~**${max_risk:.0f}/contract** ({gbp(max_risk)})"
                )
                st.markdown(
                    f"- For £700 max risk: **{contracts} contract(s)**"
                )
                st.markdown(
                    f"- Sector: {sector} | {mkt_flag} {market}"
                )
                if earn_days:
                    colour = "🔴" if earn_days < 30 else "🟢"
                    st.markdown(
                        f"- {colour} Earnings: {earnings} ({earn_days} days away)"
                    )
                else:
                    st.markdown("- ⚪ Earnings date unknown — verify on IBKR")

                st.markdown(f"- Options volume: {opt_vol:,}" if opt_vol else "- Options volume: unknown")

            st.divider()
            # Show dynamic expiry recommendation and anchor info
            rec_exp  = idea.get("rec_expiry", "21-30 DTE")
            exp_note = idea.get("expiry_note", "")
            anchor   = idea.get("anchor_used", "Mechanical OTM")
            sw       = idea.get("spread_width", 5)
            st.markdown(f"**⏱ Recommended expiry:** {rec_exp}")
            if exp_note:
                st.caption(exp_note)
            st.caption(
                f"Strike anchor: **{anchor}** — "
                f"spread width: **${sw:.2f}** "
                f"(scaled to stock price for meaningful risk/reward)"
            )
            st.markdown(
                f"**On IBKR:** Options chain → select expiry **{rec_exp}** → "
                f"Sell {ticker} ${sell_put:.0f} Put / Buy {ticker} ${buy_put:.0f} Put "
                f"(bull put spread, ${sw:.0f} wide). "
                "Check the mid-price — collect at least 25-30% of spread width to make it worthwhile."
            )

    else:  # growth
        direction = idea["direction"]
        strike    = idea["strike"]
        cost      = idea["est_cost"]
        contracts = idea["contracts"]
        emoji     = "📈" if direction == "Call" else "📉"

        header = (
            f"{emoji} {mkt_flag} {ticker}  —  {name}  —  ${price:.2f}  "
            f"|  Mom {pct(mom_1m)}  |  IV Rank ~{iv_rank:.0f}%  |  Score {score:.0f}  "
            f"▼ expand for trade details"
        )

        with st.expander(header, expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Strategy:** {strategy}")
                st.markdown(
                    f"**Why this is a growth play:**  \n"
                    f"{ticker} has moved **{pct(mom_1m)}** over the last month and sits at "
                    f"**{rng:.0f}%** of its 52-week range — "
                    f"{'near the top, momentum is strong' if rng >= 65 else 'near the bottom, bearish momentum'}.  \n"
                    f"IV rank proxy ~**{iv_rank:.0f}%** — options are "
                    f"{'reasonably priced for buying' if iv_rank < 50 else 'slightly elevated but momentum justifies it'}."
                )
                if direction == "Call":
                    st.markdown(
                        f"**Buy the ${strike:.0f} call, 21 DTE.**  \n"
                        f"You profit if {ticker} moves above ${strike:.0f} + premium paid before expiry. "
                        f"Target: 2× the premium paid. "
                        f"Stop: exit if you lose 50% of premium paid."
                    )
                else:
                    st.markdown(
                        f"**Buy the ${strike:.0f} put, 21 DTE.**  \n"
                        f"You profit if {ticker} falls below ${strike:.0f} before expiry. "
                        f"Target: 2× the premium paid. "
                        f"Stop: exit if you lose 50% of premium paid."
                    )

            with c2:
                st.markdown("**Trade details:**")
                st.markdown(
                    f"- Est. cost: ~**${cost:.0f}/contract** ({gbp(cost)})"
                )
                st.markdown(
                    f"- For £700 budget: **{contracts} contract(s)**"
                )
                st.markdown(
                    f"- Total spend: ~{gbp(cost * contracts)}"
                )
                st.markdown(
                    f"- Target exit: ~{gbp(cost * contracts * 2)} (+100%)"
                )
                st.markdown(
                    f"- Stop loss: ~{gbp(cost * contracts * 0.5)} (-50%)"
                )
                st.markdown(f"- Sector: {sector} | {mkt_flag} {market}")

                if earn_days:
                    colour = "🔴" if earn_days < 14 else "🟢"
                    st.markdown(
                        f"- {colour} Earnings: {earnings} ({earn_days} days)"
                    )
                else:
                    st.markdown("- ⚪ Earnings date unknown — verify on IBKR")

            st.divider()
            st.markdown(
                f"**On IBKR:** Options chain → select expiry ~21 days out → "
                f"Buy {ticker} ${strike:.0f} {direction}. "
                "Always check the bid/ask spread — if it's wider than $0.10, "
                "use a limit order at the mid-price."
            )




# ============================================================
# TAB 6 — SMALL CAP OPTIONS
# ============================================================

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("⚙️ Settings")
    fmp_key = st.text_input("FMP API Key (optional)",
                            type="password",
                            help="Free at financialmodelingprep.com — unlocks ETF holdings.")
    st.divider()
    st.markdown("**Income plays** (sell premium)")
    st.markdown("Best when: VIX elevated, stock range-bound, IV expensive")
    st.markdown("**Growth plays** (buy options)")
    st.markdown("Best when: VIX low, clear trend, IV cheap")
    st.divider()
    st.markdown("**Position sizing rule**")
    st.markdown("Max risk per trade: **£700** (2% of £35K)")
    st.markdown("Max concurrent trades: **5-7**")
    st.markdown("Never risk more than **£3,500** total in open options")
    st.divider()
    st.markdown("**IBKR tips**")
    st.markdown("• Always use limit orders at the mid-price")
    st.markdown("• Check bid/ask spread — wider than $0.15 = illiquid")
    st.markdown("• Set GTC (Good Till Cancelled) orders")
    st.markdown("• Verify earnings dates in IBKR before entering")


# ============================================================
# LOAD MACRO DATA (used everywhere)
# ============================================================

macro = fetch_macro_snapshot()
regime_label, regime_colour, regime_desc, regime_bias = detect_regime_quick(macro)

vix_data  = macro.get("VIX", {})
vix_val   = vix_data.get("price")
vix_chg   = vix_data.get("chg_1d")


# ============================================================
# ALWAYS-VISIBLE REGIME BANNER
# ============================================================

st.markdown(
    f"<div style='background:{regime_colour}22;border-left:6px solid {regime_colour};"
    f"padding:10px 16px;border-radius:6px;margin-bottom:12px'>"
    f"<b style='color:{regime_colour};font-size:1.1rem'>{regime_label}</b>"
    f" &nbsp;|&nbsp; {regime_desc}"
    f"</div>",
    unsafe_allow_html=True
)

st.title("🎯 Options Trading Dashboard")
st.caption(
    "**Workflow:** Read the regime banner → check Trade Ideas → "
    "confirm sector in ETF Screener → verify on IBKR → execute manually."
)


# ============================================================
# MAIN TABS
# ============================================================

tab_ideas, tab_macro, tab_sectors, tab_holdings, tab_options, tab_smallcap, tab_invest, tab_journal = st.tabs([
    "🎯 Trade Ideas",
    "🌍 Macro",
    "📈 ETF Sectors",
    "🔍 Holdings",
    "⚡ Options Filter",
    "🔬 Small Cap Options",
    "📊 Investment Watchlist",
    "📒 Trade Journal",
])


# ============================================================
# TAB 1 — TRADE IDEAS
# ============================================================

with tab_ideas:
    st.subheader("🎯 Trade Ideas")
    st.caption(
        "Scans all stocks in your universe every 5 minutes. "
        "Income plays (sell premium) and growth plays (buy options) are ranked separately. "
        "**These are starting points — always verify on IBKR before trading.**"
    )

    # Regime adjustment note
    if regime_bias == "puts":
        st.error(
            "⚠️ **Regime is Risk-Off** — favour put growth plays and income plays "
            "(selling elevated premium). Be cautious on call growth plays."
        )
    elif regime_bias == "calls":
        st.success(
            "✅ **Regime is Risk-On** — call growth plays are favoured. "
            "Income plays also work well in calmer conditions."
        )
    elif regime_bias == "reduce":
        st.warning(
            "🟡 **Mixed regime** — reduce size on all trades. "
            "Prefer income plays (selling defined-risk spreads) over directional bets."
        )

    # VIX premium note
    if vix_val:
        if vix_val >= 30:
            st.info(
                f"📌 **VIX {vix_val:.0f} — options are EXPENSIVE.** "
                "This is a good environment for income plays (selling premium). "
                "For growth plays, use debit spreads rather than buying naked options "
                "to reduce the cost."
            )
        elif vix_val <= 15:
            st.info(
                f"📌 **VIX {vix_val:.0f} — options are CHEAP.** "
                "Good time to buy options (growth plays). "
                "Income plays collect less premium at low VIX — be selective."
            )

    if st.button("🔄 Scan for Trade Ideas", type="primary", key="scan_btn"):
        with st.spinner("Scanning all stocks... this takes ~60 seconds..."):
            income_list, growth_list = fetch_all_candidates()
        st.session_state["income_list"] = income_list
        st.session_state["growth_list"] = growth_list

    income_list = st.session_state.get("income_list", [])
    growth_list = st.session_state.get("growth_list", [])

    if not income_list and not growth_list:
        st.info("Click **Scan for Trade Ideas** above to find today's candidates.")
    else:
        # ── Regime-weighted display ───────────────────────────
        # The regime determines which strategy to show first
        # and how prominently to display it.
        if regime_bias == "puts":
            # Risk-off: income plays first (elevated IV = more premium),
            # then put growth plays. Call growth plays pushed to bottom.
            primary_label   = "### 💰 Income Plays — PRIMARY (Risk-Off regime)"
            secondary_label = "### 📉 Growth Plays — Puts Only"
            primary_list    = income_list
            secondary_list  = [i for i in growth_list if i.get("direction") == "Put"]
            call_list       = [i for i in growth_list if i.get("direction") == "Call"]
            primary_cap     = (
                "Risk-off regime — options are expensive. "
                "**Sell premium now.** Collect elevated IV as income. "
                "Put credit spreads below support = limited risk, collect upfront."
            )
            secondary_cap   = (
                "Put growth plays — stocks in clear downtrends. "
                "Buy puts only if momentum is very strong and IV is still reasonable. "
                "Avoid call growth plays in risk-off."
            )
        elif regime_bias == "calls":
            # Risk-on: growth call plays first, income second
            primary_label   = "### 🚀 Growth Plays — PRIMARY (Risk-On regime)"
            secondary_label = "### 💰 Income Plays — Secondary"
            primary_list    = [i for i in growth_list if i.get("direction") == "Call"]
            secondary_list  = income_list
            call_list       = []
            primary_cap     = (
                "Risk-on regime — buy calls on strong momentum stocks. "
                "IV is lower in calm markets = cheaper to buy options. "
                "Target stocks leading their sector with RSI not yet overbought."
            )
            secondary_cap   = (
                "Income plays — collect premium on range-bound stocks. "
                "Less premium available in low VIX but still viable for "
                "high IV-rank individual stocks."
            )
        else:
            # Neutral/mixed: equal split, income slightly preferred
            primary_label   = "### 💰 Income Plays"
            secondary_label = "### 🚀 Growth Plays"
            primary_list    = income_list
            secondary_list  = growth_list
            call_list       = []
            primary_cap     = (
                "Sell premium — collect money upfront. "
                "**Strategy: put credit spreads (defined risk).** "
                "Best when IV is high and stock is range-bound."
            )
            secondary_cap   = (
                "Buy options — need a directional move. "
                "**Strategy: buy slightly OTM calls or puts, 21 DTE.** "
                "Target 2× premium. Stop at -50%."
            )

        col_inc, col_gr = st.columns(2)

        with col_inc:
            st.markdown(primary_label)
            st.caption(primary_cap)
            if primary_list:
                for idea in primary_list[:5]:
                    render_trade_card(idea, regime_bias)
            else:
                st.info("No strong candidates found for the primary strategy.")

        with col_gr:
            st.markdown(secondary_label)
            st.caption(secondary_cap)
            if secondary_list:
                for idea in secondary_list[:5]:
                    render_trade_card(idea, regime_bias)
            else:
                st.info("No strong candidates found right now.")

        # Show call growth plays below in risk-off regime with clear warning
        if call_list:
            st.markdown("---")
            st.warning(
                "⚠️ **Call growth plays — PROCEED WITH CAUTION in risk-off regime.** "
                "Only consider these if you have a very strong sector-specific thesis "
                "and are using defined-risk debit spreads, not naked calls."
            )
            for idea in call_list[:3]:
                render_trade_card(idea, regime_bias)

        st.divider()
        st.markdown("### 📋 How to Use These on IBKR")
        with st.expander("Step-by-step guide for executing on IBKR", expanded=False):
            st.markdown("""
**For Income Plays (put credit spreads):**
1. Search the ticker in IBKR TWS or mobile app
2. Right-click → Trade → Options → Options Chain
3. Select expiry ~21-30 days out
4. Find the suggested sell strike — check the bid price
5. Find the buy strike (5 points lower) — check the ask price
6. The net credit = sell bid minus buy ask
7. If net credit < $0.30, skip — not worth the risk
8. Place as a combo order (spread) not two separate legs
9. Use a limit order at the mid-price of the spread

**For Growth Plays (buying calls or puts):**
1. Search the ticker → Options Chain
2. Select expiry ~21 days out
3. Find the suggested strike — check the ask price
4. Check bid/ask spread — if wider than $0.15, it's illiquid
5. Place a limit order at the mid-price
6. Set a target sell order at 2× what you paid
7. Set a mental stop at 50% loss — exit manually

**General rules:**
- Always verify the earnings date in IBKR before entering
- Never spend more than £700 on a single trade
- Check the option has at least 100 open interest
- If in doubt, paper trade first using IBKR's paper account
            """)


# ============================================================
# TAB 2 — MACRO
# ============================================================

with tab_macro:
    st.subheader("🌍 Macro Dashboard")
    st.caption("The macro regime drives everything else. Read this to calibrate your Trade Ideas.")

    # Key metric tiles
    tile_cols = st.columns(6)
    metrics = [
        ("VIX",             "VIX",             "Fear index. >25 = elevated. >35 = extreme."),
        ("10Y Treasury",    "10Y Yield %",      "Rising = headwind for growth stocks."),
        ("2Y Treasury",     "2Y Yield %",       "Fed expectations proxy."),
        ("US Dollar (DXY)", "Dollar (DXY)",     "Rising = headwind for commodities."),
        ("Gold",            "Gold ($)",         "Rising = safe-haven demand."),
        ("Crude Oil",       "Crude Oil ($)",    "Rising = inflation/stagflation risk."),
    ]
    for col, (key, label, tip) in zip(tile_cols, metrics):
        d = macro.get(key, {})
        with col:
            if d:
                st.metric(label,
                          f"{d['price']:.2f}",
                          delta=f"{d['chg_1d']:+.2f}%",
                          help=tip)
            else:
                st.metric(label, "N/A")

    # Yield curve spread
    y10 = macro.get("10Y Treasury", {}).get("price")
    y2  = macro.get("2Y Treasury",  {}).get("price")
    if y10 and y2:
        spread = y10 - y2
        sc1, sc2 = st.columns([1, 3])
        with sc1:
            colour = "red" if spread < 0 else ("orange" if spread < 0.3 else "green")
            st.markdown(
                f"**10Y–2Y Spread: "
                f"<span style='color:{colour}'>{spread:+.2f}%</span>**",
                unsafe_allow_html=True
            )
        with sc2:
            if spread < 0:
                st.error("⚠️ Inverted yield curve — recession signal. Avoid cyclicals. Favour quality and defensive.")
            elif spread < 0.3:
                st.warning("🟡 Flat curve — financials neutral. Prefer shorter expiries.")
            else:
                st.success("🟢 Normal curve — financials have tailwind. LEAPS viable on strong trends.")

    st.divider()

    # How to read each macro signal in context of your trading
    st.markdown("### 📖 What each signal means for your trades")
    with st.expander("VIX — Fear Index", expanded=False):
        vix_display = f"{vix_val:.1f}" if vix_val else "N/A"
        st.markdown(f"""
**Current VIX: {vix_display}** (change today: {pct(vix_chg)})

VIX measures how much the options market expects the S&P 500 to move over the next 30 days.

| VIX Level | What it means | Your strategy |
|-----------|--------------|---------------|
| Below 15 | Very calm, low fear | Options are cheap → favour buying (growth plays) |
| 15–20 | Normal | Both strategies work → let IV rank decide |
| 20–25 | Mild concern | Slightly favour income plays, reduce growth play size |
| 25–35 | Elevated fear | Income plays preferred — premium is elevated |
| Above 35 | Extreme fear | Sell premium aggressively. Do NOT buy naked options. |

**VIX direction matters as much as the level:**
- VIX rising fast = fear accelerating → reduce all positions
- VIX falling steadily = fear draining → add growth plays
        """)

    with st.expander("HYG — High Yield Credit (the canary)", expanded=False):
        hyg = macro.get("HYG", {})
        st.markdown(f"""
**HYG today: {pct(hyg.get('chg_1d'))}**

HYG holds high-yield (junk) bonds. When companies start to struggle, their bonds fall first — before their stock prices do.

**Why it matters:**
- HYG falling while stocks hold up = warning. Stocks usually follow HYG down within days.
- HYG rising = credit markets healthy = genuine risk-on signal
- This is the single most reliable early warning signal available without a Bloomberg terminal.

**Rule of thumb:**
If HYG drops more than 1% on a day when SPY is flat or up, reduce your call positions.
        """)

    with st.expander("Yield Curve — 10Y vs 2Y", expanded=False):
        st.markdown(f"""
**Current spread: {f'{spread:+.2f}%' if y10 and y2 else 'N/A'}**

The yield curve shows the difference between what you earn lending money for 10 years vs 2 years.

**Normal curve (positive):** Longer lending = more reward = healthy economy.
→ Banks profitable → financials have tailwind → cyclicals work.

**Inverted curve (negative — 2Y yields higher than 10Y):**
This is unusual. It means the market expects rates to fall in future (i.e., expects a slowdown).
→ Historically precedes every US recession since 1970.
→ Avoid long-dated LEAPS on cyclicals. Favour quality, defence, healthcare.
→ Bank earnings squeezed (they borrow short, lend long — inverted curve = their margin shrinks).
        """)

    with st.expander("Dollar (DXY) — Who it helps and hurts", expanded=False):
        dxy = macro.get("US Dollar (DXY)", {})
        st.markdown(f"""
**DXY today: {pct(dxy.get('chg_1d'))}**

The dollar index measures USD strength vs a basket of currencies (EUR, JPY, GBP, CAD, SEK, CHF).

**Dollar RISING hurts:**
- Commodities (oil, gold, copper — priced in USD, more expensive for foreign buyers)
- Emerging markets (they have USD-denominated debt)
- US multinationals (overseas earnings worth less when converted back to USD)
- Sectors: XLE, GDX, SIL, EEM, KWEB

**Dollar RISING helps:**
- Domestic US companies (mostly domestic revenue)
- UK companies reporting in GBP (their USD earnings buy more pounds)
- Sectors: XLP, XLV, XLF (domestic focus)

**Dollar FALLING — reverse of the above.**
GLD, XLE, KWEB, EEM all get a tailwind from a weaker dollar.
        """)


# ============================================================
# TAB 3 — ETF SECTORS
# ============================================================

with tab_sectors:
    st.subheader("📈 ETF Sector Screener")
    st.caption(
        "Identifies which subsectors are moving. "
        "Use this to confirm the sector behind a Trade Idea, "
        "or to find new sectors to drill into."
    )

    all_tickers = list(dict.fromkeys(
        t for etfs in ETF_SECTORS.values() for t, _ in etfs
    ))

    sel_sectors = st.multiselect(
        "Sectors to show",
        list(ETF_SECTORS.keys()),
        default=list(ETF_SECTORS.keys()),
    )
    custom_input = st.text_input(
        "Add custom tickers (comma separated)",
        placeholder="e.g. ARKK, MSOS",
        key="custom_tickers",
    )
    custom_tickers = [t.strip().upper() for t in custom_input.split(",") if t.strip()] if custom_input else []

    if st.button("🔄 Load Sector Data", key="load_sectors"):
        with st.spinner("Fetching all ETF data..."):
            returns_data = fetch_all_etf_returns(all_tickers + custom_tickers)
        st.session_state["returns_data"] = returns_data
        st.session_state["sectors_loaded"] = True

    if not st.session_state.get("sectors_loaded"):
        st.info("Click **Load Sector Data** to populate the heatmap and tables.")
    else:
        returns_data = st.session_state.get("returns_data", {})

        # ── Heatmap ───────────────────────────────────────────
        st.markdown("### Sector Rotation Heatmap")
        st.caption(
            "Read left to right: green across all columns = accelerating. "
            "Green on right but red on left = recovering. "
            "Red on right but green on left = may be topping. "
            "The most actionable plays have green across ALL columns."
        )
        hm_rows = []
        for sector, etfs in ETF_SECTORS.items():
            if sector not in sel_sectors:
                continue
            for ticker, _ in etfs:
                if ticker in returns_data:
                    d = returns_data[ticker]
                    hm_rows.append({
                        "Sector": sector, "Ticker": ticker,
                        "1D %":  d.get("ret_1d"),  "3D %":  d.get("ret_3d"),
                        "1W %":  d.get("ret_1w"),  "1M %":  d.get("ret_1m"),
                        "3M %":  d.get("ret_3m"),  "RS vs SPY": d.get("rs_vs_spy"),
                    })

        if hm_rows:
            hm_df    = pd.DataFrame(hm_rows)
            num_cols = ["1D %","3D %","1W %","1M %","3M %","RS vs SPY"]
            def _hm(val):
                if pd.isna(val): return ""
                if val >= 5:   return "background-color:#166534;color:white"
                if val >= 2:   return "background-color:#bbf7d0"
                if val >= -2:  return "background-color:#fef08a"
                if val >= -5:  return "background-color:#fecaca"
                return "background-color:#991b1b;color:white"
            st.dataframe(
                hm_df.style.map(_hm, subset=num_cols)
                .format({c: "{:+.1f}%" for c in num_cols}, na_rep="N/A"),
                use_container_width=True, hide_index=True, height=400,
            )

        st.divider()

        # ── Build all_rows (used by both conflict panel and calls/puts) ──
        # Fetches 52W range and P/C ratio for every ETF in selected sectors.
        # P/C ratio is needed for conflict detection (bullish range but bearish options).
        all_rows = []
        for sector in sel_sectors:
            for ticker, name in ETF_SECTORS.get(sector, []):
                d    = returns_data.get(ticker, {})
                rng  = None
                pc_r = None
                try:
                    t    = yf.Ticker(ticker)
                    info = t.info
                    p    = safe_float(info.get("regularMarketPrice") or info.get("currentPrice"))
                    lo   = safe_float(info.get("fiftyTwoWeekLow"))
                    hi   = safe_float(info.get("fiftyTwoWeekHigh"))
                    if p and lo and hi and hi != lo:
                        rng = round((p - lo) / (hi - lo) * 100, 1)
                    # P/C ratio — needed for conflict detection
                    try:
                        dates = t.options
                        if dates:
                            chain = t.option_chain(dates[0])
                            cv    = chain.calls["volume"].fillna(0).sum()
                            pv    = chain.puts["volume"].fillna(0).sum()
                            if cv > 0:
                                pc_r = round(pv / cv, 2)
                    except Exception:
                        pass
                except Exception:
                    pass
                all_rows.append({
                    "Sector":    sector,
                    "Ticker":    ticker,
                    "1M %":      d.get("ret_1m"),
                    "RS vs SPY": d.get("rs_vs_spy"),
                    "52W %":     rng,
                    "P/C":       pc_r,
                })

        # ── Conflict Detection Panel ──────────────────────────
        # Restores the conflict analysis from the previous dashboard.
        # Fires when an ETF is near its 52W high (looks bullish)
        # but has a bearish P/C ratio (options market disagrees).
        # This divergence needs explanation before trading it.
        st.markdown("### ⚡ Conflict Detection")
        st.caption(
            "Fires when an ETF looks bullish (near 52W high) but options "
            "market is loading puts (P/C > 1.0). "
            "Could be routine hedging OR genuine distribution — "
            "the indicators below help you tell which."
        )

        conflict_found = False
        for row in all_rows:
            rng_v  = row.get("52W %",   0) or 0
            pc_v   = row.get("P/C",     0) or 0
            ticker = row.get("Ticker","")
            if rng_v >= 65 and pc_v > 1.0:
                conflict_found = True
                with st.expander(
                    f"⚡ {ticker} — 52W Range {rng_v:.1f}% (Bullish) × P/C {pc_v:.2f} (Bearish) ▼",
                    expanded=False,
                ):
                    st.markdown(
                        f"**{ticker}** is at {rng_v:.1f}% of its 52-week range — "
                        f"that looks bullish. But P/C ratio is {pc_v:.2f} — "
                        f"meaning {pc_v:.1f}x more puts than calls are being bought. "
                        "This is the conflict. The indicators below explain why:"
                    )
                    st.divider()

                    # Fetch conflict data
                    try:
                        _t    = yf.Ticker(ticker)
                        _hist = _t.history(period="6mo")
                        _info = _t.info
                        _price = safe_float(_info.get("regularMarketPrice") or _info.get("currentPrice"))

                        if _hist.empty or not _price:
                            st.warning("Could not fetch conflict data.")
                        else:
                            _closes = _hist["Close"]
                            _vols   = _hist["Volume"]

                            # RSI
                            delta = _closes.diff()
                            gain  = delta.clip(lower=0).rolling(14).mean()
                            loss  = (-delta.clip(upper=0)).rolling(14).mean()
                            rs    = gain / loss
                            _rsi  = round(float(100 - (100/(1+rs)).iloc[-1]), 1)

                            # MA50 distance
                            _ma50     = float(_closes.rolling(50).mean().iloc[-1])
                            _pct_ma   = round((_price - _ma50) / _ma50 * 100, 1)

                            # OBV trend
                            _obv = (_vols * _closes.diff().apply(
                                lambda x: 1 if x > 0 else (-1 if x < 0 else 0)
                            )).cumsum()
                            _obv_trend = "rising" if float(_obv.iloc[-1]) > float(_obv.iloc[-20]) else "falling"

                            # Volume 5/10/20 day averages
                            _v5  = round(float(_vols.tail(5).mean())  / float(_vols.tail(20).mean()), 2)
                            _v10 = round(float(_vols.tail(10).mean()) / float(_vols.tail(20).mean()), 2)

                            # Put skew
                            _skew = None
                            try:
                                _dates = _t.options
                                if _dates:
                                    _chain  = _t.option_chain(_dates[0])
                                    _atm_c  = _chain.calls.iloc[(_chain.calls["strike"] - _price).abs().argsort()[:1]]
                                    _atm_p  = _chain.puts.iloc[(_chain.puts["strike"]  - _price).abs().argsort()[:1]]
                                    _civ    = float(_atm_c["impliedVolatility"].values[0])
                                    _piv    = float(_atm_p["impliedVolatility"].values[0])
                                    if _civ > 0:
                                        _skew = round(_piv / _civ, 2)
                            except Exception:
                                pass

                            warnings = 0
                            ci1, ci2, ci3 = st.columns(3)

                            # RSI card
                            with ci1:
                                if _rsi >= 75:
                                    st.error(f"**RSI {_rsi:.0f} — Overbought**")
                                    st.markdown("Price moved too far too fast. Put buying at these levels is a genuine warning — pullback likely.")
                                    warnings += 1
                                elif _rsi >= 60:
                                    st.warning(f"**RSI {_rsi:.0f} — Elevated**")
                                    st.markdown("Momentum firm but not extreme. Put buying could still be routine hedging.")
                                else:
                                    st.success(f"**RSI {_rsi:.0f} — Not Overbought**")
                                    st.markdown("No momentum excess. High P/C is likely routine protection buying.")

                            # MA50 distance card
                            with ci2:
                                if _pct_ma >= 15:
                                    st.error(f"**{_pct_ma:+.1f}% above 50MA — Stretched**")
                                    st.markdown(
                                        f"Price is {_pct_ma:.1f}% above its 50-day average — like a rubber band pulled tight. "
                                        "When large investors buy heavy puts here, it often signals **distribution**: "
                                        "they are quietly selling into retail buyers who are still pushing price up."
                                    )
                                    warnings += 1
                                elif _pct_ma >= 7:
                                    st.warning(f"**{_pct_ma:+.1f}% above 50MA — Moderate**")
                                    st.markdown("Some stretch but not extreme. Not a distribution signal on its own.")
                                else:
                                    st.success(f"**{_pct_ma:+.1f}% above 50MA — Near Average**")
                                    st.markdown("Price close to average. Overextension is not the cause of the conflict.")

                            # OBV / Volume card
                            with ci3:
                                if _obv_trend == "falling" and _v5 < 0.8:
                                    st.error(f"**OBV falling + Volume {_v5:.2f}x avg**")
                                    st.markdown(
                                        "Price rising but volume and OBV falling — "
                                        "fewer buyers are showing up. Classic distribution signal."
                                    )
                                    warnings += 1
                                elif _obv_trend == "rising":
                                    st.success(f"**OBV rising — Volume {_v5:.2f}x avg**")
                                    st.markdown("Volume supporting the price move. Put buying is likely routine hedging.")
                                else:
                                    st.warning(f"**OBV {_obv_trend} — Volume {_v5:.2f}x avg**")
                                    st.markdown("Mixed volume signal. Monitor over next few days.")

                            # Skew card
                            ci4, ci5, ci6 = st.columns(3)
                            with ci4:
                                if _skew:
                                    if _skew >= 1.3:
                                        st.error(f"**Put Skew {_skew:.2f} — Significant**")
                                        st.markdown(f"Puts are {_skew:.2f}x more expensive than calls. Real institutional fear — not routine hedging.")
                                        warnings += 1
                                    elif _skew >= 1.1:
                                        st.warning(f"**Put Skew {_skew:.2f} — Mild**")
                                        st.markdown("Slight put premium. Some caution but not alarming.")
                                    else:
                                        st.success(f"**Put Skew {_skew:.2f} — Neutral**")
                                        st.markdown("Puts and calls priced similarly. No real fear premium.")
                                else:
                                    st.info("Put skew unavailable")

                            with ci5:
                                v5c  = "🔴" if _v5  < 0.8 else ("🟡" if _v5  < 0.95 else "🟢")
                                v10c = "🔴" if _v10 < 0.8 else ("🟡" if _v10 < 0.95 else "🟢")
                                st.markdown(f"**Volume Trend**")
                                st.markdown(f"{v5c} 5-day vol: {_v5:.2f}x 20-day avg")
                                st.markdown(f"{v10c} 10-day vol: {_v10:.2f}x 20-day avg")
                                if _v5 < _v10 < 1.0:
                                    st.markdown("Volume fading — buyers stepping back.")
                                elif _v5 > _v10:
                                    st.markdown("Volume picking up recently — buyers returning.")

                            st.divider()
                            st.markdown("### Overall Interpretation")
                            if warnings >= 3:
                                st.error(
                                    "🚨 **Strong Distribution Warning** — Multiple signals align with the bearish put buying. "
                                    "Large investors appear to be selling into strength. "
                                    "Avoid new long entries. If already in, consider protective puts or reducing size."
                                )
                            elif warnings == 2:
                                st.warning(
                                    "⚠️ **Genuine Caution** — Two signals back up the bearish put signal. "
                                    "Wait for a pullback before entering, or use defined-risk spreads rather than naked calls."
                                )
                            elif warnings == 1:
                                st.info(
                                    "🟡 **Mixed Signal** — One indicator flashing. The put buying may be "
                                    "precautionary rather than directional. Monitor over the next few days."
                                )
                            else:
                                st.success(
                                    "✅ **Likely Routine Hedging** — Indicators don't support distribution. "
                                    "Large holders near the 52W high are protecting gains. Bullish trend intact."
                                )
                    except Exception as e:
                        st.warning(f"Could not fetch conflict data: {e}")

        if not conflict_found:
            st.info("No conflicts detected — all ETFs with bullish 52W range have neutral or bullish P/C ratios.")

        st.divider()

        # ── Calls / Puts panels ───────────────────────────────
        st.markdown("### Best Sectors for Calls vs Puts")

        if all_rows:
            all_df = pd.DataFrame(all_rows)
            calls_df = all_df[
                (all_df["52W %"].fillna(0) >= 60) &
                (all_df["RS vs SPY"].fillna(-99) >= 0)
            ].sort_values("RS vs SPY", ascending=False).head(5)

            puts_df = all_df[
                (all_df["52W %"].fillna(100) <= 40) &
                (all_df["RS vs SPY"].fillna(0) <= 0)
            ].sort_values("RS vs SPY", ascending=True).head(5)

            cc, cp = st.columns(2)
            with cc:
                st.markdown("**📈 Strongest — drill into these for call ideas**")
                if not calls_df.empty:
                    for _, r in calls_df.iterrows():
                        with st.expander(
                            f"{r['Ticker']}  —  {r['Sector']}  "
                            f"|  52W {r['52W %']:.0f}%  |  RS {pct(r['RS vs SPY'])}  ▼",
                            expanded=False,
                        ):
                            st.markdown(f"**Drill into holdings** → Holdings tab")
                            h = fetch_holdings(r["Ticker"], fmp_key)
                            if not h.empty:
                                rs = calc_relative_strength(
                                    h["Ticker"].tolist(), r["Ticker"], "1mo"
                                )
                                if not rs.empty:
                                    h = h.merge(rs[["Ticker","vs ETF %","Status"]], on="Ticker", how="left")
                                def _hl(row):
                                    s = [""] * len(row)
                                    if "Status" in row.index:
                                        i = list(row.index).index("Status")
                                        s[i] = "background-color:#bbf7d0" if row["Status"] == "✅ Leading" else ("background-color:#fecaca" if row["Status"] == "⚠️ Lagging" else "")
                                    return s
                                st.dataframe(h.style.apply(_hl, axis=1), use_container_width=True, hide_index=True)
                                leading = h[h.get("Status","") == "✅ Leading"]["Ticker"].tolist() if "Status" in h.columns else []
                                if leading:
                                    st.success(f"Leading: {', '.join(leading)}")
                                    st.text_input("Copy to Options Filter:", ", ".join(leading), key=f"copy_c_{r['Ticker']}")
                            else:
                                st.link_button(f"Look up {r['Ticker']} holdings",
                                               f"https://stockanalysis.com/etf/{r['Ticker'].lower()}/holdings/")
                else:
                    st.info("No strong call sectors right now.")

            with cp:
                st.markdown("**📉 Weakest — drill into these for put ideas**")
                if not puts_df.empty:
                    for _, r in puts_df.iterrows():
                        with st.expander(
                            f"{r['Ticker']}  —  {r['Sector']}  "
                            f"|  52W {r['52W %']:.0f}%  |  RS {pct(r['RS vs SPY'])}  ▼",
                            expanded=False,
                        ):
                            h = fetch_holdings(r["Ticker"], fmp_key)
                            if not h.empty:
                                rs = calc_relative_strength(
                                    h["Ticker"].tolist(), r["Ticker"], "1mo"
                                )
                                if not rs.empty:
                                    h = h.merge(rs[["Ticker","vs ETF %","Status"]], on="Ticker", how="left")
                                def _hl2(row):
                                    s = [""] * len(row)
                                    if "Status" in row.index:
                                        i = list(row.index).index("Status")
                                        s[i] = "background-color:#bbf7d0" if row["Status"] == "✅ Leading" else ("background-color:#fecaca" if row["Status"] == "⚠️ Lagging" else "")
                                    return s
                                st.dataframe(h.style.apply(_hl2, axis=1), use_container_width=True, hide_index=True)
                                lagging = h[h.get("Status","") == "⚠️ Lagging"]["Ticker"].tolist() if "Status" in h.columns else []
                                if lagging:
                                    st.error(f"Put candidates: {', '.join(lagging)}")
                                    st.text_input("Copy to Options Filter:", ", ".join(lagging), key=f"copy_p_{r['Ticker']}")
                            else:
                                st.link_button(f"Look up {r['Ticker']} holdings",
                                               f"https://stockanalysis.com/etf/{r['Ticker'].lower()}/holdings/")
                else:
                    st.info("No weak put sectors right now.")


# ============================================================
# TAB 4 — HOLDINGS DRILL DOWN
# ============================================================

with tab_holdings:
    st.subheader("🔍 Holdings Drill-Down")
    st.caption(
        "Pick any ETF to see its top holdings, "
        "and which stocks are leading vs lagging the ETF. "
        "Leading stocks = call candidates. Lagging stocks = put candidates."
    )

    hcol1, hcol2 = st.columns(2)
    with hcol1:
        sector_choice = st.selectbox("Sector", list(ETF_SECTORS.keys()), key="h_sector")
    with hcol2:
        etf_labels = [f"{t}  —  {n}" for t, n in ETF_SECTORS[sector_choice]]
        etf_choice = st.selectbox("ETF", etf_labels, key="h_etf")
        etf_ticker = etf_choice.split("  —  ")[0].strip()

    period = st.radio("Comparison period", ["1wk","1mo","3mo"], index=1, horizontal=True)

    if st.button("🔍 Drill Down", key="drill_btn"):
        with st.spinner(f"Fetching {etf_ticker} holdings..."):
            holdings = fetch_holdings(etf_ticker, fmp_key)

        if holdings.empty:
            st.error(f"Could not fetch holdings for {etf_ticker}")
            c1, c2 = st.columns(2)
            with c1:
                st.link_button(f"stockanalysis.com — {etf_ticker}",
                               f"https://stockanalysis.com/etf/{etf_ticker.lower()}/holdings/")
            with c2:
                st.link_button(f"ETF Database — {etf_ticker}",
                               f"https://etfdb.com/etf/{etf_ticker}/#holdings")
        else:
            tickers_list = holdings["Ticker"].tolist()
            with st.spinner("Calculating relative strength..."):
                rs_df = calc_relative_strength(tickers_list, etf_ticker, period=period)

            if not rs_df.empty:
                merged = holdings.merge(
                    rs_df[["Ticker", f"Ret ({period}) %", "vs ETF %", "Status"]],
                    on="Ticker", how="left"
                )
            else:
                merged = holdings.copy()

            def _hl_h(row):
                styles = [""] * len(row)
                if "Status" in row.index:
                    i = list(row.index).index("Status")
                    if row["Status"] == "✅ Leading":
                        styles[i] = "background-color:#bbf7d0"
                    elif row["Status"] == "⚠️ Lagging":
                        styles[i] = "background-color:#fecaca"
                return styles

            st.dataframe(merged.style.apply(_hl_h, axis=1),
                         use_container_width=True, hide_index=True)

            if not rs_df.empty:
                fig = px.bar(
                    rs_df.sort_values("vs ETF %"),
                    x="vs ETF %", y="Ticker", orientation="h",
                    color="vs ETF %",
                    color_continuous_scale=["#dc2626","#fef08a","#16a34a"],
                    text="vs ETF %", height=max(300, len(rs_df) * 35),
                )
                fig.update_traces(texttemplate="%{text:+.2f}%", textposition="outside")
                fig.add_vline(x=0, line_dash="dash", line_color="gray")
                fig.update_layout(showlegend=False, coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

            leading = merged[merged.get("Status","") == "✅ Leading"]["Ticker"].tolist() if "Status" in merged.columns else tickers_list
            lagging = merged[merged.get("Status","") == "⚠️ Lagging"]["Ticker"].tolist() if "Status" in merged.columns else []

            col_l, col_r = st.columns(2)
            with col_l:
                if leading:
                    st.success(f"**Call candidates (leading):** {', '.join(leading)}")
                    st.text_input("Copy to Options Filter:", ", ".join(leading), key="copy_leading")
            with col_r:
                if lagging:
                    st.error(f"**Put candidates (lagging):** {', '.join(lagging)}")
                    st.text_input("Copy to Options Filter:", ", ".join(lagging), key="copy_lagging")


# ============================================================
# TAB 5 — OPTIONS FILTER
# ============================================================

with tab_options:
    st.subheader("⚡ Options Filter")
    st.caption(
        "Paste tickers from the Holdings tab or Trade Ideas. "
        "Checks IV, HV30, earnings date, and gives a signal for each stock."
    )

    ticker_input = st.text_input(
        "Tickers (comma separated)",
        placeholder="e.g. NVDA, AMD, AVGO, TSM",
        key="opt_tickers",
    )

    if st.button("⚡ Analyse", key="opt_btn") and ticker_input:
        raw_tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

        with st.spinner(f"Fetching options data for {', '.join(raw_tickers)}..."):
            # Fetch VWAP first (intraday entry/exit signal)
            vwap_data = fetch_vwap(raw_tickers)
            results = []
            for ticker in raw_tickers:
                d = fetch_stock_data(ticker)
                if d:
                    # Signal
                    iv, hv30 = d["iv"], d["hv30"]
                    if iv and hv30:
                        ratio = iv / hv30
                        if ratio > 1.2:   sig = "🔴 Sell Premium (expensive)"
                        elif ratio < 0.8: sig = "🟢 Buy Options (cheap)"
                        else:             sig = "🟡 Fair Value"
                    else:
                        sig = "⚪ N/A"

                    # RSI signal
                    rsi_v = d.get("rsi")
                    if rsi_v:
                        if rsi_v >= 75:   rsi_sig = f"🔴 {rsi_v:.0f} Overbought"
                        elif rsi_v >= 60: rsi_sig = f"🟡 {rsi_v:.0f} Elevated"
                        elif rsi_v <= 30: rsi_sig = f"🟢 {rsi_v:.0f} Oversold"
                        elif rsi_v <= 45: rsi_sig = f"🟡 {rsi_v:.0f} Low"
                        else:             rsi_sig = f"🟢 {rsi_v:.0f} Neutral"
                    else:
                        rsi_sig = "N/A"

                    # Direction signal combining momentum + RSI
                    mom = d.get("mom_1m", 0) or 0
                    rng = d.get("range_pct", 50) or 50
                    if mom >= 5 and rng >= 65 and (not rsi_v or rsi_v < 75):
                        dir_sig = "📈 Call bias"
                    elif mom <= -5 and rng <= 40 and (not rsi_v or rsi_v > 25):
                        dir_sig = "📉 Put bias"
                    elif rsi_v and rsi_v >= 75:
                        dir_sig = "⚠️ Overbought — caution on calls"
                    elif rsi_v and rsi_v <= 30:
                        dir_sig = "⚠️ Oversold — caution on puts"
                    else:
                        dir_sig = "🟡 Neutral"

                    results.append({
                        "Ticker":        ticker,
                        "Price":         f"${d['price']:.2f}" if d["price"] else "N/A",
                        "Direction":     dir_sig,
                        "RSI":           rsi_sig,
                        "Mom 1M":        f"{mom:+.1f}%",
                        "52W Range":     f"{rng:.0f}%",
                        "VWAP Signal":   vwap_data.get(ticker, {}).get("vwap_sig", "⚪ Fetching..."),
                        "vs VWAP":       f"{vwap_data.get(ticker, {}).get('pct_vs_vwap', 0):+.2f}%" if ticker in vwap_data else "N/A",
                        "IV %":          d["iv"],
                        "HV30 %":        d["hv30"],
                        "IV/HV":         round(d["iv"]/d["hv30"],2) if d["iv"] and d["hv30"] else None,
                        "IV Signal":     sig,
                        "IV Rank ~":     f"~{d['iv_rank_proxy']:.0f}%" if d["iv_rank_proxy"] else "N/A",
                        "Options Vol":   d["options_vol"],
                        "Next Earnings": d["earnings"] or "⚠️ Check manually",
                        "Days to Earn":  d["earnings_days"],
                    })
                time.sleep(0.2)

        if results:
            df = pd.DataFrame(results)

            def _style_opts(row):
                styles = [""] * len(row)
                if "Signal" in row.index:
                    i = list(row.index).index("Signal")
                    sig = str(row["Signal"])
                    if "Sell"  in sig: styles[i] = "background-color:#fecaca"
                    elif "Buy" in sig: styles[i] = "background-color:#bbf7d0"
                    elif "Fair" in sig: styles[i] = "background-color:#fef08a"
                return styles

            st.dataframe(df.style.apply(_style_opts, axis=1),
                         use_container_width=True, hide_index=True)

            # VWAP section
            st.markdown("#### 📍 VWAP Entry & Exit Signals")
            st.caption(
                "VWAP resets daily. Most useful for 1-5 day options plays. "
                "Use it to time your entry — don't just buy the signal, wait for price to confirm with VWAP."
            )
            with st.expander("How to use VWAP for entries and exits on IBKR", expanded=False):
                st.markdown("""
**For CALLS:**
- **Ideal entry:** Price pulls back to VWAP from above, then bounces up → buy the call at the bounce
- **Avoid:** Buying calls when price is already far above VWAP — you're chasing
- **Take profit:** When price stalls at a resistance level or VWAP is rising fast and price extends too far above
- **Stop:** Exit the call if price closes below VWAP on a 30-minute candle

**For PUTS:**
- **Ideal entry:** Price bounces up to VWAP from below, then rolls over → buy the put at the roll
- **Avoid:** Buying puts when price is already far below VWAP — risk of a VWAP snap-back bounce
- **Take profit:** When price reaches the next support level or bounces off the day's low
- **Stop:** Exit the put if price closes back above VWAP

**AT VWAP signal:**
- Price is at equilibrium — wait for the next directional move before entering
- This is not a signal to trade — it's a signal to watch

**On IBKR:**
- Open the chart for the stock → add VWAP indicator (Indicators → VWAP)
- Switch to 5-minute or 15-minute candles for intraday view
- Watch for price to test VWAP and react — that reaction is your entry signal
                """)

            if vwap_data:
                vwap_rows = []
                for ticker in raw_tickers:
                    if ticker in vwap_data:
                        v = vwap_data[ticker]
                        vwap_rows.append({
                            "Ticker":      ticker,
                            "Price":       f"${v['price']:.2f}",
                            "VWAP":        f"${v['vwap']:.2f}",
                            "vs VWAP":     f"{v['pct_vs_vwap']:+.2f}%",
                            "Signal":      v["vwap_sig"],
                            "Entry?":      (
                                "✅ Wait for pullback to VWAP, buy call on bounce"
                                if v["pct_vs_vwap"] >= 1
                                else "✅ Wait for bounce to VWAP, buy put on roll"
                                if v["pct_vs_vwap"] <= -1
                                else "⏳ AT VWAP — wait for direction"
                            )
                        })
                if vwap_rows:
                    def _style_vwap(row):
                        styles = [""] * len(row)
                        if "Signal" in row.index:
                            i = list(row.index).index("Signal")
                            s = str(row["Signal"])
                            if "Call" in s:  styles[i] = "background-color:#bbf7d0"
                            elif "Put" in s: styles[i] = "background-color:#fecaca"
                            else:            styles[i] = "background-color:#fef08a"
                        return styles
                    st.dataframe(
                        pd.DataFrame(vwap_rows).style.apply(_style_vwap, axis=1),
                        use_container_width=True, hide_index=True
                    )

            # Earnings warnings
            st.markdown("#### ⚠️ Earnings Risk")
            warned = False
            for r in results:
                days = r["Days to Earn"]
                earn = r["Next Earnings"]
                if "Check" in str(earn):
                    st.error(f"**{r['Ticker']}** — earnings date unknown. Check on IBKR before trading.")
                    warned = True
                elif days is not None:
                    if 0 <= days <= 14:
                        st.error(f"**{r['Ticker']}** — earnings in {days} days ({earn}). Very high risk. Avoid unless trading earnings specifically.")
                        warned = True
                    elif days <= 21:
                        st.warning(f"**{r['Ticker']}** — earnings in {days} days ({earn}). IV will spike into date.")
                        warned = True
                    else:
                        st.success(f"**{r['Ticker']}** — earnings {days} days away ({earn}). Safe to trade. ✅")
                        warned = True
            if not warned:
                st.success("No earnings concerns for the tickers checked.")

            # Summary
            st.markdown("#### 🎯 Summary")
            sell_list = [r["Ticker"] for r in results if "Sell" in r["Signal"]]
            buy_list  = [r["Ticker"] for r in results if "Buy"  in r["Signal"]]
            sc1, sc2  = st.columns(2)
            with sc1:
                if buy_list:
                    st.success(f"**Buy options (cheap IV):** {', '.join(buy_list)}")
            with sc2:
                if sell_list:
                    st.info(f"**Sell premium (expensive IV):** {', '.join(sell_list)}")

            st.divider()
            st.markdown(
                "**Next step:** Take your chosen ticker to IBKR. "
                "Check the live options chain — use these signals as a guide, "
                "not an instruction. Always verify the IV rank in IBKR's "
                "options analytics before placing the trade."
            )


with tab_smallcap:
    st.subheader("🔬 Small Cap Options")
    st.caption(
        "Scans 50 small/mid cap stocks ($500M–$15B market cap) for options plays. "
        "Filtered to only those with sufficient options liquidity for IBKR. "
        "Small caps offer higher IV (more income premium) and bigger moves (better growth plays) "
        "than large caps — but only if the options are liquid enough to trade."
    )

    # IWM context — is small cap environment favourable?
    iwm_data  = macro.get("IWM", {})
    iwm_chg   = iwm_data.get("chg_1m") or iwm_data.get("chg_1d")
    spy_chg_m = macro.get("SPY", {}).get("chg_1m")

    if iwm_chg and spy_chg_m:
        rs_iwm_spy = round(iwm_chg - spy_chg_m, 1)
        if rs_iwm_spy >= 2:
            st.success(
                f"✅ **Small caps leading large caps by {rs_iwm_spy:+.1f}%** — "
                "IWM outperforming SPY. Small cap environment is strong. "
                "Growth plays in small caps have a tailwind."
            )
        elif rs_iwm_spy <= -2:
            st.warning(
                f"⚠️ **Small caps lagging large caps by {rs_iwm_spy:.1f}%** — "
                "IWM underperforming SPY. Large caps leading. "
                "Be more selective on small cap growth plays. "
                "Income plays (selling premium) still valid — elevated IV."
            )
        else:
            st.info(
                f"🟡 Small caps roughly in line with large caps (RS: {rs_iwm_spy:+.1f}%). "
                "No strong directional advantage for small caps right now."
            )

    st.markdown(
        "**Why small caps have higher IV:**  \n"
        "Less analyst coverage + thinner trading volume = wider price swings. "
        "This means options are priced to reflect bigger moves — "
        "which means MORE premium to collect (income) "
        "or CHEAPER calls/puts relative to the actual move when a trend starts (growth).  \n"
        "**The catch:** options bid/ask spreads are wider. Always use limit orders at mid-price on IBKR."
    )

    if st.button("🔬 Scan Small Cap Options", type="primary", key="sc_scan"):
        with st.spinner("Scanning small cap universe (~90 seconds)..."):
            sc_income, sc_growth = scan_small_cap_options()
        st.session_state["sc_income"] = sc_income
        st.session_state["sc_growth"] = sc_growth

    sc_income = st.session_state.get("sc_income", [])
    sc_growth = st.session_state.get("sc_growth", [])

    if not sc_income and not sc_growth:
        st.info("Click **Scan Small Cap Options** to find candidates.")
    else:
        # Regime-weighted just like Tab 1
        if regime_bias == "puts":
            col1_label = "### 💰 Small Cap Income Plays"
            col2_label = "### 📉 Small Cap Growth — Puts"
            col1_list  = sc_income
            col2_list  = [i for i in sc_growth if i.get("direction") == "Put"]
        elif regime_bias == "calls":
            col1_label = "### 🚀 Small Cap Growth — Calls"
            col2_label = "### 💰 Small Cap Income Plays"
            col1_list  = [i for i in sc_growth if i.get("direction") == "Call"]
            col2_list  = sc_income
        else:
            col1_label = "### 💰 Small Cap Income Plays"
            col2_label = "### 🚀 Small Cap Growth Plays"
            col1_list  = sc_income
            col2_list  = sc_growth

        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown(col1_label)
            st.caption(
                "Small caps typically have IV rank 20-30% higher than large caps. "
                "More premium to collect — but always check the bid/ask on IBKR first."
            )
            for idea in col1_list[:5]:
                render_trade_card(idea, regime_bias)

        with sc2:
            st.markdown(col2_label)
            st.caption(
                "Small caps make bigger moves when momentum kicks in. "
                "A stock at 90% of its 52W range with strong IWM outperformance "
                "is a high-conviction growth play."
            )
            for idea in col2_list[:5]:
                render_trade_card(idea, regime_bias)

        st.divider()
        st.markdown("### ⚠️ Small Cap Options — Key Rules for IBKR")
        st.markdown(
            "1. **Always check open interest** before trading — need >200 OI on the specific strike  \n"
            "2. **Use limit orders at mid-price** — never use market orders on small cap options  \n"
            "3. **Maximum 1 contract** on illiquid names until you've verified the spread  \n"
            "4. **Position size smaller** — £400-500 max risk per trade (vs £700 for large caps)  \n"
            "5. **Exit before expiry week** — liquidity disappears in the final week for small caps"
        )


# ============================================================
# TAB 7 — INVESTMENT WATCHLIST
# ============================================================

with tab_invest:
    st.subheader("📊 Investment Watchlist")
    st.caption(
        "Screens small/mid cap stocks for investment quality — buying shares, not options. "
        "Filters by revenue growth, free cashflow, debt levels, and relative strength vs IWM. "
        "These are 3-12 month investment ideas, not weekly options plays."
    )

    # When is small cap investment most attractive?
    st.markdown("### When to invest in small caps vs large caps")
    with st.expander("Understanding the small cap investment cycle", expanded=False):
        st.markdown("""
**Small caps outperform large caps during:**
- Early bull markets (after a correction or bear market bottom)
- Periods of falling interest rates (small caps carry more debt, lower rates = relief)
- When IWM starts outperforming SPY consistently (the signal is already in your Macro tab)
- When the yield curve is steepening (normalising from flat/inverted)

**Large caps outperform small caps during:**
- Late bull markets (flight to quality, liquidity)
- Rising rate environments (large caps can refinance cheaply)
- Risk-off periods (small caps sell off faster)
- When IWM is lagging SPY (the signal to stay in large caps)

**The practical rule:**
Watch the IWM/SPY ratio in your Macro tab.
- Ratio rising for 4+ weeks → start building small cap positions
- Ratio falling → stay in large caps or reduce small cap exposure

**Why strong cashflow matters for small caps specifically:**
Large caps can borrow cheaply and weather a downturn.
Small caps cannot. A small cap burning cash in a risk-off market
may not be able to raise money — it can go to zero.
Positive free cashflow = the business funds itself. Much safer.
        """)

    # IWM investment environment signal
    if regime_bias in ("puts", "reduce"):
        st.warning(
            "⚠️ **Risk-off or cautious regime** — this is not ideal timing for new small cap investments. "
            "Use this screen to build a watchlist now, then invest when regime turns Risk-On."
        )
    else:
        st.success(
            "✅ **Risk-On or neutral regime** — conditions are reasonable for building small cap positions. "
            "Focus on high-score stocks with positive FCF and strong IWM relative strength."
        )

    if st.button("📊 Run Investment Screen", type="primary", key="invest_scan"):
        with st.spinner("Scanning fundamentals... (~2 minutes)..."):
            watchlist = scan_investment_watchlist()
        st.session_state["watchlist"] = watchlist

    watchlist = st.session_state.get("watchlist", [])

    if not watchlist:
        st.info("Click **Run Investment Screen** to scan for quality small cap investments.")
    else:
        # ── Summary table ─────────────────────────────────────
        st.markdown(f"### Results — {len(watchlist)} stocks screened")

        table_rows = []
        for w in watchlist:
            table_rows.append({
                "Verdict":      w["verdict"],
                "Ticker":       w["ticker"],
                "Name":         w["name"],
                "Sector":       w["sector"],
                "Score":        w["q_score"],
                "Mkt Cap £B":   round((w["mkt_cap_b"] or 0) / GBPUSD, 1),
                "Rev Growth":   f"{w['rev_growth']:+.0f}%" if w["rev_growth"] else "N/A",
                "FCF Yield":    f"{w['fcf_yield']:+.1f}%" if w["fcf_yield"] else "N/A",
                "Gross Margin": f"{w['gross_pct']:.0f}%" if w["gross_pct"] else "N/A",
                "Debt/Equity":  f"{w['de_ratio']:.1f}x" if w["de_ratio"] else "N/A",
                "ROE":          f"{w['roe_pct']:.0f}%" if w["roe_pct"] else "N/A",
                "52W Range":    f"{w['range_pct']:.0f}%" if w["range_pct"] else "N/A",
                "RS vs IWM":    f"{w['rs_vs_iwm']:+.1f}%" if w["rs_vs_iwm"] else "N/A",
                "Mom 1M":       f"{w['mom_1m']:+.1f}%" if w["mom_1m"] else "N/A",
            })

        tbl_df = pd.DataFrame(table_rows)

        def _style_invest(row):
            styles = [""] * len(row)
            if "Verdict" in row.index:
                i = list(row.index).index("Verdict")
                v = str(row["Verdict"])
                if "Strong" in v:   styles[i] = "background-color:#bbf7d0"
                elif "Watch" in v:  styles[i] = "background-color:#fef08a"
                elif "Avoid" in v:  styles[i] = "background-color:#fecaca"
            if "Score" in row.index:
                i = list(row.index).index("Score")
                s = row["Score"]
                if s >= 75:  styles[i] = "background-color:#bbf7d0"
                elif s >= 55: styles[i] = "background-color:#fef08a"
                else:         styles[i] = "background-color:#fecaca"
            return styles

        st.dataframe(
            tbl_df.style.apply(_style_invest, axis=1),
            use_container_width=True, hide_index=True,
        )

        # ── Detailed cards for top picks ──────────────────────
        st.divider()
        st.markdown("### 🟢 Top Investment Candidates — Full Detail")
        top_picks = [w for w in watchlist if w["q_score"] >= 65 and
                     w.get("fcf") and w["fcf"] > 0]

        if not top_picks:
            st.info("No stocks currently meet the high-quality threshold (score ≥ 65 + positive FCF).")
        else:
            for w in top_picks[:8]:
                ticker  = w["ticker"]
                name    = w["name"]
                sector  = w["sector"]
                score   = w["q_score"]
                verdict = w["verdict"]
                note    = w["verdict_note"]
                fcf_y   = w["fcf_yield"]
                rev_g   = w["rev_growth"]
                gross   = w["gross_pct"]
                de      = w["de_ratio"]
                roe     = w["roe_pct"]
                rs_iwm  = w["rs_vs_iwm"]
                mom_6m  = w["mom_6m"]
                rng     = w["range_pct"]
                pe      = w["pe"]
                ps      = w["ps"]
                price   = w["price"]
                cap     = w["mkt_cap_b"]

                filled  = int(round(score / 10))
                bar     = "█" * filled + "░" * (10 - filled)

                with st.expander(
                    f"{verdict[:2]} {ticker}  —  {name}  —  ${price:.2f}  "
                    f"|  Score {score}/100  |  {sector}  ▼ expand for full analysis",
                    expanded=False,
                ):
                    st.markdown(f"`{bar}` **{score}/100** — {verdict}")
                    st.markdown(f"*{note}*")
                    st.divider()

                    d1, d2, d3 = st.columns(3)

                    with d1:
                        st.markdown("**📈 Growth**")
                        if rev_g:
                            c = "🟢" if rev_g >= 15 else ("🟡" if rev_g >= 5 else "🔴")
                            st.markdown(f"{c} Revenue growth: **{rev_g:+.0f}% YoY**")
                            if rev_g >= 20:
                                st.caption("Rapid expansion — business is scaling.")
                            elif rev_g >= 10:
                                st.caption("Solid growth. Comfortably above inflation.")
                            else:
                                st.caption("Slow growth. Watch for deceleration.")
                        else:
                            st.markdown("Revenue growth: N/A")

                        if gross:
                            c = "🟢" if gross >= 60 else ("🟡" if gross >= 40 else "🔴")
                            st.markdown(f"{c} Gross margin: **{gross:.0f}%**")
                            if gross >= 60:
                                st.caption("High margin = pricing power. Software/pharma quality.")
                            elif gross >= 40:
                                st.caption("Decent margin. Room to invest in growth.")
                            else:
                                st.caption("Low margin. Vulnerable to cost increases.")

                        if mom_6m:
                            c = "🟢" if mom_6m >= 15 else ("🟡" if mom_6m >= 0 else "🔴")
                            st.markdown(f"{c} 6M momentum: **{mom_6m:+.1f}%**")

                    with d2:
                        st.markdown("**💰 Cashflow & Debt**")
                        if fcf_y is not None:
                            c = "🟢" if fcf_y >= 3 else ("🟡" if fcf_y >= 0 else "🔴")
                            st.markdown(f"{c} FCF yield: **{fcf_y:.1f}%**")
                            if fcf_y >= 5:
                                st.caption(
                                    f"For every £100 invested, this company generates "
                                    f"£{fcf_y:.1f} of free cash annually. Very attractive."
                                )
                            elif fcf_y >= 2:
                                st.caption("Positive cashflow — self-funding business.")
                            elif fcf_y < 0:
                                st.caption(
                                    "⚠️ Burning cash. Needs external funding. "
                                    "Higher risk — ensure it has runway."
                                )

                        if de is not None:
                            c = "🟢" if de < 0.5 else ("🟡" if de < 1.0 else "🔴")
                            st.markdown(f"{c} Debt/Equity: **{de:.1f}x**")
                            if de < 0.3:
                                st.caption("Very low debt. Can survive a downturn.")
                            elif de < 1.0:
                                st.caption("Manageable debt. Watch cashflow coverage.")
                            else:
                                st.caption("⚠️ High debt. Vulnerable if rates rise or earnings disappoint.")

                        if roe:
                            c = "🟢" if roe >= 15 else ("🟡" if roe >= 8 else "🔴")
                            st.markdown(f"{c} ROE: **{roe:.0f}%**")
                            st.caption(
                                "Return on equity — how well management uses your money. "
                                "Above 15% = efficient capital allocation."
                            )

                    with d3:
                        st.markdown("**📍 Technicals & Valuation**")
                        if rng:
                            c = "🟢" if rng >= 70 else ("🟡" if rng >= 40 else "🔴")
                            st.markdown(f"{c} 52W Range: **{rng:.0f}%**")
                            if rng >= 70:
                                st.caption("Near annual high. Momentum is with the buyer.")
                            elif rng <= 30:
                                st.caption(
                                    "Near annual low. Could be a value entry "
                                    "IF fundamentals are intact — or a falling knife. "
                                    "Check revenue trend carefully."
                                )

                        if rs_iwm is not None:
                            c = "🟢" if rs_iwm >= 5 else ("🟡" if rs_iwm >= 0 else "🔴")
                            st.markdown(f"{c} RS vs IWM: **{rs_iwm:+.1f}%**")
                            if rs_iwm >= 5:
                                st.caption(
                                    "Beating the small cap index. Institutional money "
                                    "is choosing this stock over its peers."
                                )
                            elif rs_iwm < 0:
                                st.caption("Lagging its benchmark. Investigate why.")

                        val_str = f"P/E {pe:.0f}x" if pe else ""
                        val_str += f"  P/S {ps:.1f}x" if ps else ""
                        if val_str:
                            st.markdown(f"**Valuation:** {val_str}")
                            if pe and pe > 50:
                                st.caption(
                                    "High P/E — market is pricing in significant growth. "
                                    "Only justified if revenue growth is >20%."
                                )
                            elif ps and ps < 3 and rev_g and rev_g >= 15:
                                st.caption(
                                    "Low P/S for a growing business — potentially undervalued."
                                )

                    st.divider()
                    st.markdown("**💡 Investment approach for IBKR:**")
                    if mom_6m and mom_6m >= 10 and rng and rng >= 60:
                        st.markdown(
                            f"**Momentum entry:** {ticker} is in an uptrend with strong fundamentals. "
                            "Buy in 2-3 tranches — 1/3 now, 1/3 on a 5% pullback, 1/3 on confirmation. "
                            f"Position size: £2,000-£4,000 for a full position at £35K capital. "
                            "Stop loss: 15-20% below entry (small caps are volatile — give it room)."
                        )
                    elif rng and rng <= 35 and fcf_y and fcf_y >= 3:
                        st.markdown(
                            f"**Value/Recovery entry:** {ticker} is near its annual low but generating cash. "
                            "This is a contrarian bet. Buy in 2 tranches. "
                            "The thesis: the business is stronger than the price implies. "
                            "Stop loss: 20% below entry. "
                            "Wait for IWM to start outperforming SPY before sizing up."
                        )
                    else:
                        st.markdown(
                            f"**Patient entry:** Add {ticker} to your watchlist. "
                            "Wait for either: (a) IWM outperforming SPY for 2+ consecutive weeks, "
                            "or (b) the stock pulling back 10-15% to a better entry. "
                            "Don't chase — the fundamentals will still be here."
                        )

        st.divider()
        st.markdown("### 📖 Understanding the Quality Score")
        with st.expander("How the 0-100 score is calculated", expanded=False):
            st.markdown("""
The quality score combines five factors, weighted by importance:

| Factor | Max Points | What it measures |
|--------|-----------|-----------------|
| **Revenue growth** | 25 | Is the business expanding? ≥20% = 25pts, ≥10% = 15pts |
| **Free cashflow** | 25 | Does it generate real cash? Positive FCF = 25pts |
| **Gross margin** | 15 | Does it have pricing power? ≥60% = 15pts |
| **Debt level** | 15 | Can it survive a downturn? Debt/Equity <0.5 = 15pts |
| **IWM relative strength** | 15 | Is institutional money choosing this stock? +5% vs IWM = 15pts |
| **ROE** | 5 | Management efficiency bonus |

**Score interpretation:**
- 75+ with positive FCF = Strong Buy Candidate → act when regime is Risk-On
- 55-74 = Watch List → monitor for improving signals
- Below 55 = Neutral/Avoid → pass or investigate further

**Important:** The score tells you about business quality, not timing.
A score of 80 in a Risk-Off regime is still a great business — but wait for
the regime to turn before committing capital.
            """)




# ============================================================
# TAB 8 — TRADE JOURNAL
# ============================================================

with tab_journal:
    st.subheader("📒 Trade Journal")
    st.caption(
        "Log every trade you take from this dashboard. "
        "Tracks whether the signals actually worked over time. "
        "Stored in your browser session — export to CSV to save permanently."
    )

    # Initialise journal in session state
    if "journal" not in st.session_state:
        st.session_state["journal"] = []

    # ── Log a new trade ───────────────────────────────────────
    st.markdown("### ➕ Log a Trade")
    with st.form("journal_form", clear_on_submit=True):
        jc1, jc2, jc3 = st.columns(3)
        with jc1:
            j_ticker    = st.text_input("Ticker", placeholder="NVDA").upper()
            j_type      = st.selectbox("Trade Type", [
                "Income — Put Credit Spread",
                "Growth — Buy Call",
                "Growth — Buy Put",
                "Income — Call Credit Spread",
                "Other",
            ])
        with jc2:
            j_entry     = st.number_input("Premium paid / collected ($)", min_value=0.0, step=0.05)
            j_contracts = st.number_input("Contracts", min_value=1, step=1)
            j_expiry    = st.date_input("Expiry date")
        with jc3:
            j_regime    = st.selectbox("Regime at entry", [
                regime_label,
                "🟢 Risk-On",
                "🟡 Mildly Risk-On",
                "🟡 Neutral",
                "🟠 Cautious",
                "🔴 Risk-Off",
                "⚠️ Stagflation Risk",
            ])
            j_iv_rank   = st.number_input("IV Rank at entry (~%)", min_value=0, max_value=100, step=1)
            j_thesis    = st.text_area("Thesis / why this trade", height=80,
                                       placeholder="e.g. SMH breaking out, NVDA leading semis, IV rank 75%")

        j_submitted = st.form_submit_button("📝 Log Trade", type="primary")
        if j_submitted and j_ticker:
            entry_cost_gbp = round(j_entry * j_contracts * 100 / GBPUSD, 0)
            st.session_state["journal"].append({
                "Date":          pd.Timestamp.now().strftime("%Y-%m-%d"),
                "Ticker":        j_ticker,
                "Type":          j_type,
                "Premium $":     j_entry,
                "Contracts":     int(j_contracts),
                "Total Cost £":  entry_cost_gbp,
                "Expiry":        str(j_expiry),
                "Regime":        j_regime,
                "IV Rank ~":     j_iv_rank,
                "Thesis":        j_thesis,
                "Exit Price $":  None,
                "P&L £":         None,
                "Result":        "Open",
            })
            st.success(f"✅ {j_ticker} {j_type} logged.")

    # ── Update existing trades ────────────────────────────────
    journal = st.session_state["journal"]

    if journal:
        st.divider()
        st.markdown("### 📋 Open & Closed Trades")

        open_trades = [(i, t) for i, t in enumerate(journal) if t["Result"] == "Open"]
        if open_trades:
            st.markdown("**Update open trades:**")
            for idx, trade in open_trades:
                with st.expander(
                    f"📌 {trade['Date']} — {trade['Ticker']} {trade['Type']} | "
                    f"Entry: ${trade['Premium $']:.2f} × {trade['Contracts']} contracts | "
                    f"Expiry: {trade['Expiry']}",
                    expanded=False
                ):
                    st.markdown(f"**Regime at entry:** {trade['Regime']}")
                    st.markdown(f"**Thesis:** {trade['Thesis']}")
                    uc1, uc2 = st.columns(2)
                    with uc1:
                        exit_price = st.number_input(
                            "Exit price $ (0 = expired worthless)",
                            min_value=0.0, step=0.05,
                            key=f"exit_{idx}"
                        )
                    with uc2:
                        result = st.selectbox(
                            "Result",
                            ["Open", "Win", "Loss", "Break-even", "Expired worthless"],
                            key=f"result_{idx}"
                        )
                    if st.button("💾 Update", key=f"update_{idx}"):
                        # P&L calculation
                        entry = trade["Premium $"]
                        contracts = trade["Contracts"]
                        if "Income" in trade["Type"]:
                            # Sold premium: profit = entry - exit
                            pnl_per_share = entry - exit_price
                        else:
                            # Bought options: profit = exit - entry
                            pnl_per_share = exit_price - entry
                        pnl_usd = round(pnl_per_share * contracts * 100, 2)
                        pnl_gbp = round(pnl_usd / GBPUSD, 0)

                        st.session_state["journal"][idx]["Exit Price $"] = exit_price
                        st.session_state["journal"][idx]["P&L £"]        = pnl_gbp
                        st.session_state["journal"][idx]["Result"]        = result
                        st.rerun()

        # ── Full journal table ────────────────────────────────
        st.divider()
        st.markdown("### 📊 Full Journal")
        jdf = pd.DataFrame(journal)

        def _style_journal(row):
            styles = [""] * len(row)
            if "Result" in row.index:
                i = list(row.index).index("Result")
                r = str(row["Result"])
                if r in ("Win","Expired worthless"):   styles[i] = "background-color:#bbf7d0"
                elif r == "Loss":                       styles[i] = "background-color:#fecaca"
                elif r == "Break-even":                 styles[i] = "background-color:#fef08a"
                else:                                   styles[i] = "background-color:#e0f2fe"
            if "P&L £" in row.index:
                i = list(row.index).index("P&L £")
                try:
                    v = float(row["P&L £"])
                    styles[i] = "background-color:#bbf7d0" if v >= 0 else "background-color:#fecaca"
                except Exception:
                    pass
            return styles

        st.dataframe(
            jdf.style.apply(_style_journal, axis=1),
            use_container_width=True, hide_index=True
        )

        # ── Stats ─────────────────────────────────────────────
        closed = [t for t in journal if t["Result"] != "Open"]
        if closed:
            st.divider()
            st.markdown("### 📈 Performance Summary")
            wins   = len([t for t in closed if t["Result"] in ("Win","Expired worthless")])
            losses = len([t for t in closed if t["Result"] == "Loss"])
            total  = len(closed)
            win_rate = round(wins / total * 100, 0) if total else 0
            total_pnl = sum(t["P&L £"] or 0 for t in closed)

            ps1, ps2, ps3, ps4 = st.columns(4)
            ps1.metric("Win Rate",     f"{win_rate:.0f}%",
                       delta=f"{wins}W / {losses}L")
            ps2.metric("Total P&L",   f"£{total_pnl:,.0f}",
                       delta="profit" if total_pnl >= 0 else "loss")
            ps3.metric("Trades taken", total)
            ps4.metric("Avg per trade",
                       f"£{total_pnl/total:,.0f}" if total else "N/A")

            # Win rate by strategy
            by_type = {}
            for t in closed:
                tp = t["Type"]
                by_type.setdefault(tp, {"wins": 0, "total": 0, "pnl": 0})
                by_type[tp]["total"] += 1
                if t["Result"] in ("Win", "Expired worthless"):
                    by_type[tp]["wins"] += 1
                by_type[tp]["pnl"] += t["P&L £"] or 0

            st.markdown("**By strategy:**")
            for tp, stats in by_type.items():
                wr = round(stats["wins"] / stats["total"] * 100, 0)
                pl = stats["pnl"]
                colour = "🟢" if pl >= 0 else "🔴"
                st.markdown(
                    f"{colour} **{tp}**: "
                    f"{stats['total']} trades, {wr:.0f}% win rate, "
                    f"P&L: £{pl:,.0f}"
                )

        # ── Export ────────────────────────────────────────────
        st.divider()
        csv = jdf.to_csv(index=False)
        st.download_button(
            "📥 Export Journal to CSV",
            data=csv,
            file_name=f"trade_journal_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
        st.caption(
            "⚠️ The journal is stored in your browser session — "
            "it will be lost when you close the tab. "
            "Export to CSV regularly to keep a permanent record. "
            "In a future version this can be connected to Google Sheets for persistence."
        )

        if st.button("🗑️ Clear All Trades", key="clear_journal"):
            st.session_state["journal"] = []
            st.rerun()

    else:
        st.info(
            "No trades logged yet. "
            "Use the form above to log your first trade. "
            "Tracking your trades is the only way to know if the signals are working for you."
        )
        st.markdown("""
**Why track every trade:**
- You'll quickly see which signal combinations actually work for your style
- Win rate by strategy tells you whether income or growth plays suit you better
- Regime at entry lets you see if you're trading with or against the macro trend
- It creates accountability — you can't fool yourself about performance
        """)

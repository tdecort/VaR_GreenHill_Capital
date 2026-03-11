import yfinance as yf
import numpy as np
import pandas as pd
import datetime

# 1. Portfolio Definition: Absolute values in Euros (Vi)
# Extracted from your screenshots
portfolio_values = {
    "AAPL": 6956.71, "ABBN.SW": 8409.50, "ABBV": 3050.88, "ABI.BR": 6030.64,
    "ACKB.BR": 14728.80, "ACLN.SW": 395.40, "AD.AS": 9693.75, "ADBE": 658.05,
    "AED.BR": 6164.00, "ALSN": 8871.28, "ALV.DE": 2651.60, "ASM.AS": 2845.60,
    "ASML.AS": 2498.40, "BEI.DE": 5390.00, "BEPC": 5086.20, "BLK": 6493.20,
    "BREB.BR": 5439.20, "BSN.DE": 5106.32, "BYDDY": 5054.40, "COFB.BR": 3277.80,
    "CPR.MI": 1695.75, "CVC.AS": 2543.45, "DEME.BR": 6336.00, "ENEL.MI": 2764.50,
    "EOAN.DE": 6098.40, "EVO.ST": 719.70, "EXO.AS": 4304.05, "GOOGL": 3740.24,
    "GRMN": 8866.62, "HNR1.DE": 1744.40, "IBE.MC": 6550.50, "IBKR": 3533.60,
    "INVE-B.ST": 8731.20, "JNJ": 7198.80, "JPM": 3426.93, "LOGN.SW": 5144.88,
    "MA": 2678.94, "MC.PA": 4464.00, "MDT": 1725.15, "MSFT": 7749.16,
    "NOVO-B.CO": 2353.40, "PHM": 3206.52, "SHEL": 2030.10, "SOF.BR": 2440.00,
    "TCOM": 1759.02, "TSM": 10685.52, "TTWO": 1016.40, "UNH": 2213.73,
    "VGP.BR": 2910.60, "WDP.BR": 3697.92, "X.TO": 1941.40, "CEMU.AS": 9267.20,
    "CNDX.AS": 7209.60, "EMIM.AS": 4938.10, "ESPO.L": 4088.25, "IH2O.MI": 3131.68,
    "IQQH.DE": 4970.14, "ISPY.MI": 8402.40, "IUSA.AS": 30239.86, "IWQU.L": 7727.50,
    "OSX4.DE": 5058.35, "SMLK.DE": 9525.00, "WTEL.AS": 4089.60, "ZPRG.DE": 7241.20,
    "COMF.MI": 10028.60, "PPFB.DE": 15431.40,
    "CASH": 45089.47 # Liquid position
}

# 2. Weights calculation (wi = Vi / Vtot)
v_tot = sum(portfolio_values.values())
weights_dict = {ticker: value / v_tot for ticker, value in portfolio_values.items()}

print(f"Total Portfolio Value (Vtot): {v_tot:,.2f} €")
print(f"Weights check: Sum = {sum(weights_dict.values()):.4f}\n")

# 3. Separating CASH for the Yahoo Finance API
# We do not download "CASH" from Yahoo
tickers_to_download = [t for t in portfolio_values.keys() if t != "CASH"]

# 4. Downloading historical data (e.g., last 2 years)
end_date = datetime.datetime.today()
start_date = end_date - datetime.timedelta(days=2*365)

print(f"Downloading Yahoo Finance data...")
try:
    # The threads=False argument prevents the "database is locked" error
    data = yf.download(tickers_to_download, start=start_date, end=end_date, threads=False)['Close']
except Exception as e:
    print(f"Error during download: {e}")
    exit()

# --- NEW CLEANING BLOCK ---
# Drops only the columns (stocks) that completely failed
data = data.dropna(axis=1, how='all')

# Forward-fills non-trading days (local holidays) with the previous day's price
data = data.ffill()
# ---------------------------------

# 5. Daily returns calculation
returns = data.pct_change().dropna()

# Adding the CASH column with a 0% return
returns["CASH"] = 0.0

# 6. Column alignment and safe weight recalculation
# Listing tickers that ACTUALLY survived the download + CASH
tickers_valides = list(data.columns) + ["CASH"]

# Isolating the returns dataframe in the correct order
returns = returns[tickers_valides]

# Calculating the "new" Vtot, ignoring stocks that failed
v_tot_valide = sum(portfolio_values[t] for t in tickers_valides)

# Recalculating exact weights on this healthy base
weights_array = np.array([portfolio_values[t] / v_tot_valide for t in tickers_valides])

# Historical portfolio returns
portfolio_returns = returns.dot(weights_array)

# 7. VaR and CVaR Calculation (Historical Approach)
confidence_level = 99
alpha = 100 - confidence_level

# VaR in % and in value (Euros) - Based on the valid total value
var_pct = np.percentile(portfolio_returns, alpha)
var_value = var_pct * v_tot_valide

# CVaR in % and in value (Euros)
cvar_pct = portfolio_returns[portfolio_returns <= var_pct].mean()
cvar_value = cvar_pct * v_tot_valide

# 8. Displaying results
print("\n" + "="*50)
print(" RISK ANALYSIS RESULTS (1 DAY)")
print("="*50)
print(f"Analyzed assets     : {len(tickers_valides)} / {len(portfolio_values)}")
print(f"Analyzed value      : {v_tot_valide:,.2f} €")
print(f"Confidence level    : {confidence_level}%")
print("-" * 50)
print(f"VaR ({confidence_level}%)  : {var_pct * 100:>7.2f}%  or  {var_value:>10,.2f} €")
print(f"CVaR ({confidence_level}%) : {cvar_pct * 100:>7.2f}%  or  {cvar_value:>10,.2f} €")

print("="*50)

# =============================================================================
# 9. VÉRIFICATION DES CONDITIONS DE VALIDITÉ DE LA VaR
# =============================================================================

print("\n" + "="*50)
print(" VÉRIFICATION DES CONDITIONS DE LA VaR")
print("="*50)

# --- Condition 1 : Vérification de la Sous-additivité (Cohérence) ---
# Formule du cours : Q(V1) + Q(V2) >= Q(V1+V2)
# On calcule la VaR de chaque actif individuellement pour les sommer.

indiv_var_values = []
for ticker in tickers_valides:
    if ticker == "CASH":
        continue
    # On calcule la VaR de l'actif i
    tick_var_pct = np.percentile(returns[ticker].dropna(), alpha)
    tick_var_value = tick_var_pct * portfolio_values[ticker]
    indiv_var_values.append(tick_var_value)

# Somme des VaR individuelles (en valeur absolue pour représenter la perte)
sum_indiv_vars_loss = sum(abs(v) for v in indiv_var_values)
port_var_loss = abs(var_value)

print("1. Propriété de Sous-additivité (Cohérence) :")
print(f"   VaR globale du portefeuille    : {port_var_loss:>10,.2f} €")
print(f"   Somme des VaR individuelles    : {sum_indiv_vars_loss:>10,.2f} €")

if port_var_loss <= sum_indiv_vars_loss:
    print("   -> CONDITION VALIDÉE : La VaR de ce portefeuille est sous-additive (bénéfice de diversification).")
else:
    print("   -> CONDITION NON VALIDÉE : La VaR n'est pas sous-additive ici (violation de la cohérence).")

# --- Condition 2 : Backtesting de base (Taux d'échec / Failure rate) ---
# Formule du cours : m / n doit converger vers (1 - c)
# Note : Pour un vrai backtest, il faudrait idéalement le faire sur des données hors-échantillon (out-of-sample).
# Ici, on le fait in-sample pour vérifier la consistance de la distribution historique.

n_obs = len(portfolio_returns)
# Un dépassement (breach) correspond à une perte pire que la VaR
breaches = portfolio_returns[portfolio_returns < var_pct]
m_breaches = len(breaches)
failure_rate = m_breaches / n_obs
expected_failure_rate = alpha / 100

print("\n2. Backtesting (Taux d'échec - m/n) :")
print(f"   Nombre d'observations (n)      : {n_obs}")
print(f"   Nombre de dépassements (m)     : {m_breaches}")
print(f"   Dépassements attendus          : {n_obs * expected_failure_rate:.1f}")
print(f"   Taux d'échec observé (m/n)     : {failure_rate * 100:.2f}%")
print(f"   Taux d'échec cible (1 - c)     : {alpha:.2f}%")

# Tolérance arbitraire de 20% autour de la cible pour l'affichage (peut être ajustée)
if abs(failure_rate - expected_failure_rate) < (expected_failure_rate * 0.2):
    print("   -> CONDITION VALIDÉE : Le taux d'échec est très proche de la probabilité cible.")
else:
    print("   -> À SURVEILLER : Le taux d'échec s'éloigne de la cible (typique en simulation historique in-sample).")

print("="*50)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Credit Risk & Loan Default Assessment",
    page_icon="🏦",
    layout="wide",
)

st.title("🏦 Credit Risk Analytics & Loan Assessment System")
st.markdown(
    "Evaluate loan applicant default risk, score profiles, and get automated"
    " underwriting decisions."
)
st.markdown("---")

# ==========================================
# 2. INPUT FORM (SIDEBAR & MAIN COLUMNS)
# ==========================================
col1, col2 = st.columns(2)

with col1:
  st.subheader("👤 Applicant Demographics & Financials")
  age = st.number_input("Age", min_value=18, max_value=80, value=31)
  income = st.number_input(
      "Annual Income (₹)", min_value=10000, max_value=10000000, value=650000
  )
  employment_years = st.number_input(
      "Years of Employment", min_value=0, max_value=50, value=5
  )
  credit_score = st.slider(
      "Credit Score",
      min_value=300,
      max_value=850,
      value=742,
      help="Bureau Credit Score (300-850)",
  )
  dti_ratio = st.slider(
      "Debt-to-Income (DTI) Ratio %",
      min_value=0,
      max_value=100,
      value=34,
      help="Percentage of monthly income going toward existing debt",
  )

with col2:
  st.subheader("💳 Loan Details & Credit History")
  loan_amount = st.number_input(
      "Requested Loan Amount (₹)",
      min_value=10000,
      max_value=50000000,
      value=800000,
  )
  loan_term = st.selectbox(
      "Loan Term (Months)", [12, 24, 36, 48, 60], index=2
  )
  interest_rate = st.number_input(
      "Interest Rate (%)", min_value=1.0, max_value=35.0, value=10.5
  )
  late_payments = st.number_input("Late Payments (Past 2 yrs)", 0, 20, 0)
  missed_payments = st.number_input("Missed Payments Count", 0, 10, 0)

st.markdown("---")


# ==========================================
# 3. PREDICTION & RISK LOGIC
# ==========================================
def calculate_risk(
    credit_score, dti, late_pay, missed_pay, inc, loan_amt, term, rate
):
  """Calculates risk probability score based on credit attributes"""
  # Score penalty weights
  score_factor = (850 - credit_score) / 550 * 0.40
  dti_factor = (dti / 100) * 0.25
  delinquency_factor = (late_pay * 0.05) + (missed_pay * 0.10)

  # Calculate monthly EMI vs income
  monthly_income = inc / 12
  r = (rate / 100) / 12
  emi = loan_amt * r * ((1 + r) ** term) / (((1 + r) ** term) - 1)
  emi_ratio = emi / monthly_income if monthly_income > 0 else 1.0

  emi_factor = emi_ratio * 0.25

  # Base probability
  raw_prob = score_factor + dti_factor + delinquency_factor + emi_factor
  calibrated_prob = max(0.01, min(0.99, raw_prob))

  return round(calibrated_prob, 4), round(emi, 2)


# Action button
if st.button("🚀 Evaluate Loan Risk & Generate Decision", type="primary"):

  default_prob, emi_value = calculate_risk(
      credit_score,
      dti_ratio,
      late_payments,
      missed_payments,
      income,
      loan_amount,
      loan_term,
      interest_rate,
  )

  st.subheader("📊 Underwriting Decision & Assessment")

  res_col1, res_col2, res_col3 = st.columns(3)

  with res_col1:
    st.metric(
        label="Predicted Default Probability", value=f"{default_prob * 100:.2f}%"
    )

  with res_col2:
    st.metric(label="Calculated Monthly EMI", value=f"₹{emi_value:,.2f}")

  with res_col3:
    if default_prob < 0.15:
      risk_tier = "Very Low Risk"
      color = "green"
    elif default_prob < 0.30:
      risk_tier = "Low Risk"
      color = "blue"
    elif default_prob < 0.45:
      risk_tier = "Moderate Risk"
      color = "orange"
    elif default_prob < 0.65:
      risk_tier = "High Risk"
      color = "red"
    else:
      risk_tier = "Very High Risk"
      color = "darkred"

    st.metric(label="Risk Tier", value=risk_tier)

  # Automated Lending Decision Callout
  if default_prob < 0.15:
    st.success("✅ **APPROVED** — Full terms (Lowest Interest Rate Tier)")
  elif default_prob < 0.30:
    st.info("✅ **APPROVED** — Standard interest rate terms")
  elif default_prob < 0.45:
    st.warning("⚠️ **CONDITIONAL APPROVAL** — Requires higher interest rate")
  elif default_prob < 0.65:
    st.warning(
        "⚠️ **MANUAL REVIEW** — Requires collateral or co-signer/guarantor"
    )
  else:
    st.error(
        "❌ **REJECTED** — High default risk exposure exceeding risk appetite"
    )

  # Visual Gauge Chart
  fig, ax = plt.subplots(figsize=(6, 1))
  ax.barh(["Risk"], [default_prob], color=color, height=0.3)
  ax.set_xlim(0, 1)
  ax.set_xlabel("Default Risk Scale (0.0 = Safe, 1.0 = Default)")
  ax.axvline(0.15, color="green", linestyle="--", alpha=0.7)
  ax.axvline(0.45, color="orange", linestyle="--", alpha=0.7)
  ax.axvline(0.65, color="red", linestyle="--", alpha=0.7)
  st.pyplot(fig)

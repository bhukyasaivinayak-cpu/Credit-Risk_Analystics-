import io
import sqlite3
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Credit Risk Analytics",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f2f6, #ffffff);
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-header">🏦 Credit Risk Analytics & Assessment'
    " Dashboard</div>",
    unsafe_allow_html=True,
)

# ==========================================
# 2. HELPER FUNCTIONS & LOGIC
# ==========================================


def calculate_risk(
    credit_score,
    dti,
    late_pay,
    missed_pay=0,
    inc=650000,
    loan_amt=800000,
    term=36,
    rate=10.5,
):
  score_factor = (850 - credit_score) / 550 * 0.40
  dti_factor = (dti / 100) * 0.25
  delinquency_factor = (late_pay * 0.05) + (missed_pay * 0.10)

  monthly_income = inc / 12
  r = (rate / 100) / 12
  emi = (
      loan_amt * r * ((1 + r) ** term) / (((1 + r) ** term) - 1)
      if r > 0
      else loan_amt / term
  )
  emi_ratio = emi / monthly_income if monthly_income > 0 else 1.0

  emi_factor = emi_ratio * 0.25
  raw_prob = score_factor + dti_factor + delinquency_factor + emi_factor
  calibrated_prob = max(0.01, min(0.99, raw_prob))

  return round(calibrated_prob, 4), round(emi, 2)


def generate_pdf_report(summary_data):
  buffer = io.BytesIO()
  doc = SimpleDocTemplate(buffer, pagesize=letter)
  styles = getSampleStyleSheet()
  elements = []

  elements.append(
      Paragraph("Credit Risk Assessment Report", styles["Title"])
  )
  elements.append(Spacer(1, 12))

  table_data = [["Metric", "Value"]]
  for k, v in summary_data.items():
    table_data.append([str(k), str(v)])

  table = Table(table_data)
  table.setStyle(
      TableStyle([
          ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
          ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
          ("ALIGN", (0, 0), (-1, -1), "CENTER"),
          ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
          ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
          ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
          ("GRID", (0, 0), (-1, -1), 1, colors.black),
      ])
  )
  elements.append(table)

  doc.build(elements)
  buffer.seek(0)
  return buffer


# ==========================================
# 3. SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("📊 Navigation")
page = st.sidebar.radio(
    "Select Module:",
    [
        "🏠 Single Evaluation",
        "🔮 What-If Analysis",
        "📊 Batch Predictions",
        "👥 Customer Segmentation",
        "📈 Real-time Monitoring",
    ],
)

# ==========================================
# 4. MODULE CONTROLLERS
# ==========================================

# ---------------- MODULE 1: SINGLE EVALUATION ----------------
if page == "🏠 Single Evaluation":
  st.subheader("👤 Individual Applicant Risk Calculator")

  col1, col2 = st.columns(2)
  with col1:
    age = st.number_input("Age", 18, 80, 31)
    income = st.number_input("Annual Income (₹)", 10000, 10000000, 650000)
    employment_years = st.number_input("Years of Employment", 0, 50, 5)
    credit_score = st.slider("Credit Score", 300, 850, 742)
    dti_ratio = st.slider("Debt-to-Income (DTI) %", 0, 100, 34)

  with col2:
    loan_amount = st.number_input("Requested Loan (₹)", 10000, 50000000, 800000)
    loan_term = st.selectbox("Loan Term (Months)", [12, 24, 36, 48, 60], index=2)
    interest_rate = st.number_input("Interest Rate (%)", 1.0, 35.0, 10.5)
    late_payments = st.number_input("Late Payments", 0, 20, 0)
    missed_payments = st.number_input("Missed Payments", 0, 10, 0)

  if st.button("🚀 Evaluate Loan Risk", type="primary"):
    prob, emi = calculate_risk(
        credit_score,
        dti_ratio,
        late_payments,
        missed_payments,
        income,
        loan_amount,
        loan_term,
        interest_rate,
    )

    r1, r2, r3 = st.columns(3)
    r1.metric("Predicted Default Prob", f"{prob * 100:.2f}%")
    r2.metric("Monthly EMI", f"₹{emi:,.2f}")
    r3.metric(
        "Risk Category",
        "Low Risk"
        if prob < 0.25
        else ("Moderate" if prob < 0.45 else "High Risk"),
    )

    pdf_buffer = generate_pdf_report({
        "Credit Score": credit_score,
        "Income": f"₹{income:,}",
        "Loan Amount": f"₹{loan_amount:,}",
        "Default Probability": f"{prob * 100:.2f}%",
        "Monthly EMI": f"₹{emi:,}",
    })

    st.download_button(
        label="📥 Download Executive PDF Report",
        data=pdf_buffer,
        file_name="credit_risk_report.pdf",
        mime="application/pdf",
    )

# ---------------- MODULE 2: WHAT-IF ANALYSIS ----------------
elif page == "🔮 What-If Analysis":
  st.subheader("🔮 What-If Scenario Analysis")

  col1, col2 = st.columns(2)
  with col1:
    st.markdown("### Current Profile")
    cs1 = st.slider("Current Credit Score", 300, 850, 650, key="cs1")
    dti1 = st.slider("Current DTI Ratio %", 0, 100, 45, key="dti1")
    late1 = st.slider("Current Late Payments", 0, 10, 2, key="late1")

  with col2:
    st.markdown("### Modified Profile")
    cs2 = st.slider("Target Credit Score", 300, 850, 750, key="cs2")
    dti2 = st.slider("Target DTI Ratio %", 0, 100, 25, key="dti2")
    late2 = st.slider("Target Late Payments", 0, 10, 0, key="late2")

  curr_prob, _ = calculate_risk(cs1, dti1, late1)
  new_prob, _ = calculate_risk(cs2, dti2, late2)

  m1, m2 = st.columns(2)
  m1.metric("Base Default Risk", f"{curr_prob * 100:.1f}%")
  m2.metric(
      "Simulated Default Risk",
      f"{new_prob * 100:.1f}%",
      delta=f"{(new_prob - curr_prob) * 100:.1f}%",
      delta_color="inverse",
  )

# ---------------- MODULE 3: BATCH PREDICTIONS ----------------
elif page == "📊 Batch Predictions":
  st.subheader("📊 Batch CSV Prediction Processing")
  uploaded_file = st.file_uploader(
      "Upload CSV File (Requires credit_score, dti, late_payments)", type=["csv"]
  )

  if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Preview of Uploaded Data:")
    st.dataframe(df.head())

    if st.button("Run Batch Predictions"):
      probs = []
      for _, row in df.iterrows():
        cs = row.get("credit_score", 700)
        dti = row.get("dti", 30)
        late = row.get("late_payments", 0)
        p, _ = calculate_risk(cs, dti, late)
        probs.append(p)

      df["Predicted_Default_Prob"] = probs
      df["Risk_Level"] = [
          "High" if p > 0.4 else ("Medium" if p > 0.2 else "Low") for p in probs
      ]
      st.success("✅ Predictions Complete!")
      st.dataframe(df)

# ---------------- MODULE 4: CUSTOMER SEGMENTATION ----------------
elif page == "👥 Customer Segmentation":
  st.subheader("👥 Customer Portfolio Segmentation (K-Means)")

  # Generate Mock Portfolio
  np.random.seed(42)
  sample_df = pd.DataFrame({
      "income": np.random.randint(200000, 2000000, 200),
      "credit_score": np.random.randint(500, 850, 200),
      "dti_ratio": np.random.randint(10, 60, 200),
      "loan_amount": np.random.randint(50000, 1000000, 200),
  })

  X = sample_df[["income", "credit_score", "dti_ratio", "loan_amount"]]
  scaler = StandardScaler()
  X_scaled = scaler.fit_transform(X)

  kmeans = KMeans(n_clusters=4, random_state=42)
  sample_df["segment"] = kmeans.fit_predict(X_scaled)

  fig = px.scatter_3d(
      sample_df,
      x="income",
      y="credit_score",
      z="dti_ratio",
      color="segment",
      title="3D Portfolio Clustering",
  )
  st.plotly_chart(fig, use_container_width=True)

# ---------------- MODULE 5: REAL-TIME MONITORING ----------------
elif page == "📈 Real-time Monitoring":
  st.subheader("📈 Real-time Portfolio Risk Metrics")

  c1, c2, c3, c4 = st.columns(4)
  c1.metric("Total Applications", "12,847", "+23%")
  c2.metric("Portfolio Default Rate", "18.4%", "-2.3%")
  c3.metric("High Risk Accounts", "847", "+12%")
  c4.metric("Approval Rate", "72.3%", "+5.1%")

  dates = pd.date_range(start="2026-01-01", periods=30, freq="D")
  df_time = pd.DataFrame({
      "date": dates,
      "applications": np.random.randint(100, 500, 30),
      "defaults": np.random.randint(10, 50, 30),
  })

  fig = go.Figure()
  fig.add_trace(
      go.Scatter(
          x=df_time["date"],
          y=df_time["applications"],
          name="Applications",
          line=dict(color="blue"),
      )
  )
  fig.add_trace(
      go.Scatter(
          x=df_time["date"],
          y=df_time["defaults"],
          name="Defaults",
          line=dict(color="red"),
      )
  )
  fig.update_layout(title="Daily Application Traffic vs Defaults")
  st.plotly_chart(fig, use_container_width=True)

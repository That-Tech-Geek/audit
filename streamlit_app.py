import streamlit as st
import sqlite3
import pandas as pd
import json
from fpdf import FPDF
import random
import time
import os
import plotly.express as px
from datetime import datetime

# --------------------------
# Database Setup and Schema Update
# --------------------------
DB_NAME = 'startups.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def initialize_db(conn):
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS startups (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT, 
          sector TEXT, 
          website TEXT, 
          email TEXT, 
          created_at TIMESTAMP,
          overall_score INTEGER,
          category_scores TEXT,
          recommendations TEXT
        )
    ''')
    conn.commit()

# Optionally upgrade schema if new columns are missing.
def update_db_schema(conn):
    c = conn.cursor()
    # Get existing columns
    c.execute("PRAGMA table_info(startups)")
    columns = [info[1] for info in c.fetchall()]
    # Check for new columns if not in table, then add them
    schema_updates = {
        "overall_score": "ALTER TABLE startups ADD COLUMN overall_score INTEGER",
        "category_scores": "ALTER TABLE startups ADD COLUMN category_scores TEXT",
        "recommendations": "ALTER TABLE startups ADD COLUMN recommendations TEXT"
    }
    for col, alter in schema_updates.items():
        if col not in columns:
            try:
                c.execute(alter)
                conn.commit()
            except Exception as e:
                st.error(f"Error updating DB schema for {col}: {e}")

# --------------------------
# Utility: PDF Report Generation with Header/Footer
# --------------------------
class PDFReport(FPDF):
    def header(self):
        # Title
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'QuantumShift Labs Deep-Tech Readiness Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        # Page number at the bottom
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(startup_name, analysis):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Report Title and Timestamp
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.cell(200, 10, txt=f"Startup: {startup_name}", ln=1, align='L')
    pdf.cell(200, 10, txt=f"Report Generated: {now_str}", ln=1, align='L')
    pdf.ln(5)
    
    # Scores Table
    pdf.cell(200, 10, txt="Category Scores:", ln=1)
    for category, score in analysis['category_scores'].items():
        pdf.cell(200, 10, txt=f"{category.replace('_', ' ').title()}: {score}/10", ln=1)
    pdf.ln(5)

    # Overall Score
    pdf.cell(200, 10, txt=f"Overall Score: {analysis['overall_score']}/10", ln=1)
    pdf.ln(5)
    
    # Recommendations
    pdf.cell(200, 10, txt="Strategic Recommendations:", ln=1)
    if analysis['recommendations']:
        for rec in analysis['recommendations']:
            pdf.cell(200, 10, txt=f"- {rec}", ln=1)
    else:
        pdf.cell(200, 10, txt="No recommendations provided.", ln=1)
    
    # Save PDF Report
    safe_name = startup_name.replace(' ', '_')
    reports_dir = 'reports'
    os.makedirs(reports_dir, exist_ok=True)
    filename = os.path.join(reports_dir, f"{safe_name}_report.pdf")
    pdf.output(filename)
    return filename

# --------------------------
# Mock AI Grading System
# --------------------------
def grade_readiness(startup_data):
    # Simulated scores for demonstration purposes
    scores = {
        'tech_maturity': random.randint(3, 8),
        'talent': random.randint(4, 9),
        'funding': random.randint(2, 7),
        'ip_strength': random.randint(5, 10)
    }
    
    recommendations = []
    if scores['tech_maturity'] < 5:
        recommendations.append("🔬 Partner with a quantum computing research lab.")
    if scores['funding'] < 6:
        recommendations.append("💸 Explore climate tech VC funds.")
    if scores['talent'] < 7:
        recommendations.append("👩💻 Recruit deep-tech PhDs through our network.")
        
    overall = sum(scores.values()) // len(scores)
    return {
        'overall_score': overall,
        'category_scores': scores,
        'recommendations': recommendations
    }

# --------------------------
# Pages
# --------------------------
def deeptech_audit_page(conn):
    st.title("🚀 QuantumShift Labs Deep-Tech Readiness Audit")
    st.markdown("*Get your AI-powered deep-tech readiness assessment in 24 hours!*")
    
    with st.form("audit_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Startup Name", placeholder="Enter your startup's name")
            sector = st.selectbox("Primary Sector", 
                            ["Quantum Computing", "Neurotech", "Climate AI", "Other"])
        with col2:
            website = st.text_input("Website", placeholder="https://")
            email = st.text_input("Contact Email", placeholder="example@domain.com")
        
        submitted = st.form_submit_button("Generate Free Report")
    
    if submitted:
        if not name or not email:
            st.error("Please fill out all required fields.")
        else:
            with st.spinner('Analyzing your deep-tech readiness...'):
                analysis = grade_readiness({
                    'name': name,
                    'sector': sector,
                    'website': website
                })
                report_path = generate_pdf_report(name, analysis)
                time.sleep(2)  # Simulate processing time
                st.success("Analysis complete!")
                st.balloons()
                
                # Convert current timestamp to a string for SQLite
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Store submission along with analysis
                c = conn.cursor()
                c.execute('''INSERT INTO startups 
                           (name, sector, website, email, created_at, overall_score, category_scores, recommendations)
                           VALUES (?,?,?,?,?,?,?,?)''',
                          (name, sector, website, email, created_at,
                           analysis['overall_score'],
                           json.dumps(analysis['category_scores']),
                           json.dumps(analysis['recommendations'])))
                conn.commit()
                
                # Display metrics
                st.subheader(f"Overall Readiness Score: {analysis['overall_score']}/10")
                for category, score in analysis['category_scores'].items():
                    st.progress(score/10, text=f"{category.replace('_', ' ').title()} ({score}/10)")
                
                st.subheader("Strategic Recommendations")
                for rec in analysis['recommendations']:
                    st.markdown(f"- {rec}")
                
                with open(report_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Full Report",
                        data=f,
                        file_name=os.path.basename(report_path),
                        mime="application/pdf"
                    )
                st.markdown("---")
                st.markdown("""
                    ### Next Steps
                    Upgrade to our **Premium Implementation Roadmap** for:
                    - Investor matching with quantum/climate VCs
                    - Custom technology adoption timeline
                    - Regulatory risk assessment
                    """)
                if st.button("🚀 Upgrade to Premium (₹20k/month)"):
                    st.session_state.show_payment = True
                    premium_upgrade_page()

def audit_history_page(conn):
    st.title("📊 Audit History")
    c = conn.cursor()
    c.execute("SELECT id, name, sector, website, email, created_at, overall_score FROM startups ORDER BY created_at DESC")
    rows = c.fetchall()
    if rows:
        df = pd.DataFrame(rows, columns=["ID", "Name", "Sector", "Website", "Email", "Submitted On", "Overall Score"])
        st.dataframe(df)
        
        # Chart: Average Overall Score by Sector
        avg_scores = df.groupby("Sector")["Overall Score"].mean().reset_index()
        fig = px.bar(avg_scores, x="Sector", y="Overall Score", 
                     title="Average Overall Score by Sector", 
                     text_auto=".2f")
        st.plotly_chart(fig)
    else:
        st.info("No audit records found.")

def premium_upgrade_page():
    st.title("🚀 Premium Upgrade")
    st.markdown("""
        **Premium Implementation Roadmap includes:**
        - Investor matching with quantum/climate VCs
        - Custom technology adoption timeline
        - Regulatory risk assessment
        - Dedicated expert consultation 
        """)
    # Simulate a payment process
    if st.button("Proceed with Payment (Simulated)"):
        with st.spinner("Processing payment..."):
            time.sleep(2)
        st.success("Payment successful! Our team will contact you shortly to schedule a consultation.")
    
# --------------------------
# Main Application with Navigation
# --------------------------
def main():
    st.set_page_config(page_title="QuantumShift Labs - Deep-Tech Audit", page_icon="🚀")
    
    # Establish database connection and update schema if needed.
    conn = get_db_connection()
    initialize_db(conn)
    update_db_schema(conn)
    
    # Sidebar navigation
    page = st.sidebar.radio("Navigation", ["Deep-Tech Audit", "Audit History", "Premium Upgrade"])
    
    if page == "Deep-Tech Audit":
        deeptech_audit_page(conn)
    elif page == "Audit History":
        audit_history_page(conn)
    elif page == "Premium Upgrade":
        premium_upgrade_page()
    
    # Close the connection on shutdown
    # (If your app grows, consider using context managers or session state to manage DB connections.)

if __name__ == '__main__':
    main()

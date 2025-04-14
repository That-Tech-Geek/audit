# audit_app.py
import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF
import random
import time
import os

# Setup database
conn = sqlite3.connect('startups.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS startups
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT, sector TEXT, website TEXT, 
              email TEXT, created_at TIMESTAMP)''')
conn.commit()

# Create reports directory
os.makedirs('reports', exist_ok=True)

# Mock AI Grading System
def grade_readiness(startup_data):
    """Simulated AI grading system"""
    scores = {
        'tech_maturity': random.randint(3, 8),
        'talent': random.randint(4, 9),
        'funding': random.randint(2, 7),
        'ip_strength': random.randint(5, 10)
    }
    
    recommendations = []
    if scores['tech_maturity'] < 5:
        recommendations.append("🔬 Partner with a quantum computing research lab")
    if scores['funding'] < 6:
        recommendations.append("💸 Explore climate tech VC funds")
    if scores['talent'] < 7:
        recommendations.append("👩💻 Recruit deep-tech PhDs through our network")
        
    return {
        'overall_score': sum(scores.values())//4,
        'category_scores': scores,
        'recommendations': recommendations
    }

# PDF Report Generation
def generate_pdf_report(startup_name, analysis):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Header
    pdf.cell(200, 10, txt=f"QuantumShift Labs Deep-Tech Readiness Report: {startup_name}",
             ln=1, align='C')
    
    # Scores Table
    pdf.cell(200, 10, txt="Category Scores:", ln=1)
    for category, score in analysis['category_scores'].items():
        pdf.cell(200, 10, txt=f"{category.replace('_', ' ').title()}: {score}/10", ln=1)
    
    # Recommendations
    pdf.cell(200, 10, txt="Strategic Recommendations:", ln=1)
    for rec in analysis['recommendations']:
        pdf.cell(200, 10, txt=f"- {rec}", ln=1)
    
    filename = f"reports/{startup_name.replace(' ', '_')}_report.pdf"
    pdf.output(filename)
    return filename

# Streamlit UI
st.set_page_config(page_title="QuantumShift Labs - Deep-Tech Audit", page_icon="🚀")

st.title("🚀 QuantumShift Labs Deep-Tech Readiness Audit")
st.markdown("""
    *Get your AI-powered deep-tech readiness assessment in 24 hours!*
    """)

with st.form("audit_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Startup Name")
        sector = st.selectbox("Primary Sector", 
                            ["Quantum Computing", "Neurotech", "Climate AI", "Other"])
    with col2:
        website = st.text_input("Website")
        email = st.text_input("Contact Email")
    
    submitted = st.form_submit_button("Generate Free Report")
    
    if submitted:
        with st.spinner('Analyzing your deep-tech readiness...'):
            # Store submission
            c.execute('''INSERT INTO startups 
                      (name, sector, website, email, created_at)
                      VALUES (?,?,?,?,?)''',
                   (name, sector, website, email, pd.Timestamp.now()))
            conn.commit()
            
            # Generate analysis
            analysis = grade_readiness({
                'name': name,
                'sector': sector,
                'website': website
            })
            
            # Generate PDF
            report_path = generate_pdf_report(name, analysis)
            time.sleep(2)  # Simulate processing time

            # Show results
            st.success("Analysis complete!")
            st.balloons()
            
            # Display metrics
            st.subheader(f"Overall Readiness Score: {analysis['overall_score']}/10")
            
            # Score visualization
            for category, score in analysis['category_scores'].items():
                st.progress(score/10, text=f"{category.replace('_', ' ').title()} ({score}/10)")
            
            # Recommendations
            st.subheader("Strategic Recommendations")
            for rec in analysis['recommendations']:
                st.markdown(f"- {rec}")
            
            # PDF Download
            with open(report_path, "rb") as f:
                st.download_button(
                    label="📥 Download Full Report",
                    data=f,
                    file_name=os.path.basename(report_path),
                    mime="application/pdf"
                )
            
            # Upsell
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

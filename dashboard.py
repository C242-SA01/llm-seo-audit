import streamlit as st
import pandas as pd
from helper_function import (
    get_pagespeed_scores,
    scrape_metatags_and_structure,
    predict_seo_structure,
    grade_category,
    mobile_friendly,
    siteliner_run_example,
    generate_notes,
    generate_recommendation,
    main_audit_process
)

st.title("SEO Audit Dashboard")
st.write("Masukkan URL untuk melihat hasil audit PageSpeed.")

# Input URL
url = st.text_input("URL:", "https://example.com")

if st.button("Ambil Data"):
    try:
        # Memanggil fungsi utama untuk audit
        result = main_audit_process(url, maxpages=10)
        
        # Memeriksa apakah ada error
        if 'error' in result:
            st.error(result['error'])
        else:
            # Tampilkan hasil audit
            st.subheader("PageSpeed Data")
            st.success("Data berhasil diambil!")
            st.metric("Performance", f"{result['Audit Data'].get('Performance', 'Not available')}%")
            st.metric("Accessibility", f"{result['Audit Data'].get('Accessibility', 'Not available')}%")
            st.metric("Best Practices", f"{result['Audit Data'].get('Best Practices', 'Not available')}%")
            st.metric("SEO", f"{result['Audit Data'].get('SEO', 'Not available')}%")

            # Meta Tags Data
            st.subheader("Meta Tags Data")
            st.table(pd.DataFrame(list(result['Audit Data'].items()), columns=["Attribute", "Value"]))

            # Structure Prediction
            st.subheader("SEO Structure Prediction")
            st.write(f"Structure value: {result['Audit Data']['Structure']}")

            # Grade Category
            st.subheader("SEO Grade Category")
            st.write(f"Grade: {result['Audit Data']['Grade']}")

            # Mobile Friendly Status
            st.subheader("Mobile Friendly")
            st.write(f"Is it mobile-friendly? {result['Audit Data']['Mobile Friendly']}")

            # Additional Notes
            st.subheader("Additional Notes")
            st.write(result['Notes Analysis'])

            # Actionable Recommendations
            st.subheader("Recommendations")
            st.write(result['Actionable Recommendations'])
    
    except Exception as e:
        st.error(f"Terjadi kesalahan saat menjalankan audit: {e}")

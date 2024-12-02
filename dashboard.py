import streamlit as st
import pandas as pd
from helper_function import(
    get_pagespeed_scores,
    scrape_metatags_and_structure,
    predict_seo_structure,
    grade_category,
    mobile_friendly,
    siteliner_run_example,
    generate_notes,
    generate_recommendation
) 

st.title("SEO Audit Dashboard")
st.write("Masukkan URL untuk melihat hasil audit PageSpeed.")

url = st.text_input("URL:", "https://example.com")

if st.button("Ambil Data"):
    try:
        #if __name__ == "__main__":
        scores = get_pagespeed_scores(url)
        
        if scores:
            # Tampilkan skor di dashboard Streamlit
            st.subheader("PageSpeed Data")
            st.success("Data berhasil diambil!")
            st.metric("Performance", f"{scores.get('performance', 'Not available')}%")
            st.metric("Accessibility", f"{scores.get('accessibility', 'Not available')}%")
            st.metric("Best Practices", f"{scores.get('best-practices', 'Not available')}%")
            st.metric("SEO", f"{scores.get('seo', 'Not available')}%")
        else:
            print("Tidak dapat mengambil data PageSpeed.")

    except Exception as e:
        st.error(f"Terjadi kesalahan pada saat mengambil data pagespeed: {e}")
    #menampilkan metatag
    try:
        metatag_data = scrape_metatags_and_structure(url)
        st.subheader("Meta Tag Data")
        st.success("Data berhasil diambil")
        st.subheader("Meta Tags Data")
        st.table(pd.DataFrame(list(metatag_data.items()), columns=["Attribute", "Value"]))
    except Exception as e:
        st.error(f"Terjadi kesalahan pada saat mengambil data meta tag: {e}")
    #menampilkan structure value
    try:
        structure_value = predict_seo_structure(url)
        st.subheader("structure prediction")
        st.success("prediksi berhasil")
        st.write(f"Your structure prediction value:*{structure_value}*")
    except Exception as e:
        st.error(f"Terjadi kesalahan pada saat memprediksi: {e}")
    #Menampilkan kategori grade 
    try:
        grade = grade_category(url)
        st.subheader("Category Audit")
        st.success("prediksi berhasil")
        st.write(f"Your grade category:*{grade}*")
    except Exception as e:
        st.error(f"Terjadi kesalahan pada saat memprediksi: {e}")
    #Menampilkan mobile friendly
    try:
        friendly = mobile_friendly(url)
        st.subheader("Mobile Frindly")
        st.success("prediksi berhasil")
        st.write(f"Is it mobile friendly? :*{friendly}*")
    except Exception as e:
        st.error(f"Terjadi kesalahan pada saat memprediksi: {e}")

    # Siteliner Data
    try:
        data_scan = siteliner_run_example(url, 10)
        st.subheader("Siteliner Insights")
        st.json(data_scan)
    except Exception as e:
        st.error(f"Terjadi kesalahan saat mendapatkan data Siteliner: {e}")
    
    #Generate Note
    try:
        notes = generate_notes(url, 10)
        st.subheader("Additional Notes")
        st.write(notes)
    except Exception as e:
        st.error(f"Terjadi kesalahan saat generate notes: {e}")
    
    #Generate Note
    try:
        recom = generate_recommendation(url, 10)
        st.subheader("Your Reccomendation")
        st.write(recom)
    except Exception as e:
        st.error(f"Terjadi kesalahan saat generate recommendation: {e}")
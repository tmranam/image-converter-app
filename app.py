import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image

# Import layout-aware open source table tools
from img2table.document import Image as TableImage
from img2table.ocr import EasyOCR

# Initialize and cache the OCR model to keep your app fast
@st.cache_resource
def load_ocr_engine():
    return EasyOCR(lang=["en"])

ocr_engine = load_ocr_engine()

# Layout Configuration
st.set_page_config(page_title="Grid Table OCR", layout="centered")
st.title("📊 Structural Table Data Extractor")
st.write("Extracts image data while strictly preserving rows and columns.")

# File Uploader
uploaded_file = st.file_uploader("Upload table or spreadsheet image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save file into local memory buffer so img2table can process it
    image_bytes = uploaded_file.getvalue()
    
    # Render preview
    image_preview = Image.open(uploaded_file)
    st.image(image_preview, caption="Uploaded Data Sheet", use_container_width=True)
    
    # Tick Boxes
    want_excel = st.checkbox("Convert into Clean Excel Spreadsheet")
    
        if st.button("Extract Grid Structure"):
        if not want_excel:
            st.warning("Please check the Excel conversion checkbox first.")
        else:
            with st.spinner("Analyzing column layout... This can take up to a minute on free tier servers."):
                try:
                    # 1. Load image using img2table object wrapper
                    src_image = TableImage(BytesIO(image_bytes))
                    
                    # 2. Extract structural table mapping
                    extracted_tables = src_image.extract_tables(
                        ocr=ocr_engine, 
                        implicit_rows=True, 
                        borderless_tables=True
                    )
                    
                    # 3. FIX: Check if any table objects were returned in the list
                    if not extracted_tables:
                        st.error("Could not trace table borders. Trying fallback extraction...")
                        # Fallback simple dataframe if geometry fails completely
                        fallback_text = ocr_engine.readtext(image_bytes)
                        df = pd.DataFrame([line.split() for line in fallback_text])
                    else:
                        # Grab the first actual Table object from the list index [0]
                        primary_table = extracted_tables[0]
                        
                        # Now .to_dataframe() will work perfectly on the single table object
                        df = primary_table.to_dataframe()
                    
                    # Clean up empty data fields or formatting hiccups
                    df = df.fillna("")
                    
                    # Render interactive preview grid directly inside your Streamlit UI
                    st.subheader("📝 Extracted Data Preview")
                    st.dataframe(df, use_container_width=True)
                    
                    # 4. Generate structured in-memory Excel file
                    excel_buffer = BytesIO()
                    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, header=False, sheet_name="OCR Grid Output")
                    excel_buffer.seek(0)
                    
                    # Download Trigger
                    st.download_button(
                        label="📥 Download Grid-Aligned Excel",
                        data=excel_buffer,
                        file_name="aligned_table_output.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                except Exception as error_msg:
                    st.error(f"Execution Error: {str(error_msg)}")


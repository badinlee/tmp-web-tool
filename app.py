import streamlit as st
import fitz  # PyMuPDF
import io
from datetime import datetime, time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Rapid TMP Generator", page_icon="🚧", layout="wide")

# --- RISK LOGIC (Your Logic) ---
RISK_LIBRARY = {
    "lvr": {"label": "Low Volume Rural (LVR)", "score": "25", "controls": "Extended tapers. TSL mandatory. 100km/h warning distance.", "res": "6"},
    "live_lane": {"label": "Work in Live Lane", "score": "25", "controls": "Safety spotter required. High-vis PPE. Cone delineation.", "res": "9"},
    "height": {"label": "Overhead Services / Height", "score": "15", "controls": "Maintain 4m MAD. Dedicated spotter. Permit-to-dig.", "res": "4"},
    "pedestrian": {"label": "Pedestrian Interface", "score": "16", "controls": "Cone bars/fencing. Safe alternative route. Accessible for prams.", "res": "4"},
    "machinery": {"label": "Plant & Machinery", "score": "16", "controls": "360 checks. Spotter for reversing. Competent operators.", "res": "4"},
    "stopgo": {"label": "Stop/Go Operation", "score": "16", "controls": "Maintain safety zones. Clear sight lines. Radio comms.", "res": "6"},
}

# --- HEADER ---
st.title("🚧 Rapid Traffic Management Plan (TMP) Generator")
st.markdown("Generate **NZGTTM Compliant** PDFs instantly. Fill the form below.")

# --- SIDEBAR: PRESETS ---
with st.sidebar:
    st.header("⚡ Quick Load Presets")
    preset = st.selectbox("Select Activity Type:", ["Custom", "Pole Maintenance", "Transformer Replacement", "Geotech Drilling"])
    
    # Preset Logic
    if preset == "Pole Maintenance":
        def_desc = "Undertaking pole maintenance along road corridor. Replacing HV/LV pins."
        def_plant = "Bucket Trucks, Utes"
        def_method = "Mobile Operation for install/removal. Stop/Go for works."
    elif preset == "Geotech Drilling":
        def_desc = "Drilling Borehole in loading bay/berm."
        def_plant = "Drill Rig, Ute"
        def_method = "Shoulder Closure. Work limited to berm."
    else:
        def_desc = ""
        def_plant = ""
        def_method = ""

# --- FORM TABS ---
tab1, tab2, tab3 = st.tabs(["📝 General Details", "⚠️ Risk Assessment", "🗺️ Diagram"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Reference Info")
        tmp_ref = st.text_input("TMP Reference No.", placeholder="e.g. 150126001")
        contract_ref = st.text_input("RCA / Contract Reference", placeholder="e.g. CAR 12345")
        
        st.subheader("Road Characteristics")
        road_name = st.text_input("Road Name(s)", placeholder="e.g. Meremere Road")
        suburb = st.text_input("Suburb", placeholder="e.g. Ohangai")
        road_level = st.selectbox("Road Level", ["Low Volume", "Level 1", "Level 2", "Level 3"])
        speed = st.number_input("Permanent Speed (km/h)", value=100, step=10)
        aadt = st.number_input("AADT (Daily Traffic)", value=250, step=50)

    with col2:
        st.subheader("Programme (Dates/Times)")
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            start_date = st.date_input("Start Date")
            start_time = st.time_input("Start Time", value=time(7,0))
        with d_col2:
            end_date = st.date_input("End Date")
            end_time = st.time_input("End Time", value=time(19,0))
            
        st.subheader("Activity Details")
        activity_desc = st.text_area("Description of Activity", value=def_desc, height=100)
        plant_req = st.text_input("Plant Required", value=def_plant)
        methodology = st.text_area("Work Methodology / Phasing", value=def_method, height=100)

with tab2:
    st.subheader("Select Applicable Hazards")
    st.info("The app will automatically populate the Risk Register page based on your selection.")
    
    selected_risks = []
    r_col1, r_col2 = st.columns(2)
    
    # Create checkboxes for risks
    keys = list(RISK_LIBRARY.keys())
    half = len(keys)//2
    
    with r_col1:
        for k in keys[:half]:
            if st.checkbox(RISK_LIBRARY[k]["label"], value=(preset!="Custom")):
                selected_risks.append(k)
    with r_col2:
        for k in keys[half:]:
            if st.checkbox(RISK_LIBRARY[k]["label"]):
                selected_risks.append(k)

    # Manual Override
    extra_risk = st.text_area("Add Custom Site Specific Risk (Optional)")

with tab3:
    st.subheader("Traffic Management Diagram (TMD)")
    uploaded_tmd = st.file_uploader("Upload TMD Image (PNG/JPG)", type=["png", "jpg", "jpeg"])
    if uploaded_tmd:
        st.image(uploaded_tmd, caption="Preview of Diagram", width=500)

# --- PDF GENERATION ENGINE ---
def generate_pdf():
    try:
        # Load Template from the repo
        doc = fitz.open("template.pdf")
        page1 = doc[0]  # Page 1: General Form
        
        # Helper to draw text
        def draw(page, text, x, y, size=10, color=(0,0,0)):
            if text:
                page.insert_text((x, y), str(text), fontsize=size, fontname="helv", color=color)

        # --- MAPPING: GENERAL FORM (You must tune these X,Y coords) ---
        draw(page1, tmp_ref, 450, 100, size=12)  # Top Ref
        draw(page1, contract_ref, 450, 130)      # RCA Ref
        draw(page1, road_name, 50, 280)          # Road Name Table
        draw(page1, suburb, 150, 280)
        draw(page1, f"{road_level}", 300, 280)
        draw(page1, f"{speed} km/h", 400, 280)
        draw(page1, f"{aadt}", 480, 280)

        # Dates Table (Approx coords)
        draw(page1, f"{start_date}", 150, 380)
        draw(page1, f"{end_date}", 400, 380)
        draw(page1, f"{start_time}", 150, 410)
        draw(page1, f"{end_time}", 400, 410)

        # Page 2: Activity
        page2 = doc[1]
        draw(page2, activity_desc, 50, 150)
        draw(page2, plant_req, 50, 200)
        draw(page2, methodology, 50, 300)

        # Page 6/7: Risk Register (Assuming it's later in your doc)
        # Find the page that has "Risk Assessment" in text if possible, or hardcode index
        # For now, let's assume Page 7 (Index 6)
        if len(doc) > 6:
            risk_page = doc[6]
            y = 200
            # Always add Site Establishment
            draw(risk_page, "Site Establishment", 50, y)
            draw(risk_page, "16", 200, y)
            draw(risk_page, "Standard setup controls...", 250, y, size=8)
            y += 40
            
            for r_key in selected_risks:
                risk = RISK_LIBRARY[r_key]
                draw(risk_page, risk['label'], 50, y)
                draw(risk_page, risk['score'], 200, y)
                draw(risk_page, risk['controls'], 250, y, size=8)
                draw(risk_page, risk['res'], 500, y)
                y += 40
            
            if extra_risk:
                draw(risk_page, "Site Specific", 50, y)
                draw(risk_page, extra_risk, 250, y, size=8)

        # Diagram Page (Last Page)
        if uploaded_tmd:
            page_last = doc[-1]
            # Overlay image. Rect(x0, y0, x1, y1)
            page_last.insert_image(fitz.Rect(50, 100, 550, 700), stream=uploaded_tmd.read())

        # Save to memory buffer
        return doc.write()

    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return None

# --- ACTION BUTTON ---
st.divider()
if st.button("🚀 GENERATE TMP PDF", type="primary"):
    pdf_bytes = generate_pdf()
    
    if pdf_bytes:
        st.success("TMP Generated Successfully!")
        filename = f"TMP_{tmp_ref if tmp_ref else 'Draft'}_{datetime.now().strftime('%H%M')}.pdf"
        
        st.download_button(
            label="⬇️ Download PDF",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf"
        )

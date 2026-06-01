import streamlit as st
import pandas as pd

st.set_page_config(page_title="Booking Engine", layout="wide")

st.title("📊 Booking Reconciliation Engine")

# Month mapping
month_map = {
    "January": "-01-",
    "February": "-02-",
    "March": "-03-",
    "April": "-04-",
    "May": "-05-",
    "June": "-06-",
    "July": "-07-",
    "August": "-08-",
    "September": "-09-",
    "October": "-10-",
    "November": "-11-",
    "December": "-12-"
}

# UI
month = st.selectbox("Select Month", list(month_map.keys()))
file = st.file_uploader("Upload Excel File", type=["xlsx"])

# Normalize account name
def normalize(name):
    return " ".join(str(name).strip().upper().split())

if file:
    df = pd.read_excel(file, engine="openpyxl")

    # Clean column names (critical fix)
    df.columns = [col.strip() for col in df.columns]

    # ✅ Robust AVC detection
    avc_col = None
    for col in df.columns:
        if col.upper() == "CPQ AVC (RETRO NET)":
            avc_col = col
        elif col.upper() == "CRQ AVC (RETRO NET)":
            avc_col = col

    if avc_col is None:
        st.error(f"❌ Missing AVC column. Found columns: {list(df.columns)}")
        st.stop()

    # Filter month
    df["Close Date"] = df["Close Date"].astype(str)
    df = df[df["Close Date"].str.contains(month_map[month], na=False)]

    # Remove True-up
    df = df[df["Type"].astype(str).str.strip() != "True-up"]

    # Filter valid RGO values
    df["RGO Product"] = df["RGO Product"].astype(str).str.strip()
    valid_rgo = ["Clinical", "CSG", "Pharmacy", "PPO", "Specialty"]
    df = df[df["RGO Product"].isin(valid_rgo)]

    # Normalize
    df["RGO Product"] = df["RGO Product"].str.upper()
    df["Account Name"] = df["Account Name"].apply(normalize)

    # Business units
    business_units = ["CLINICAL", "CSG", "PHARMACY", "PPO", "SPECIALTY"]

    for bu in business_units:
        st.subheader(bu)

        subset = df[df["RGO Product"] == bu]

        if len(subset) == 0:
            st.write("Bookings: 0")
            st.write("Summed total bookings: $0")
            st.write("Top highest bookings: (none)")
            continue

        grouped = subset.groupby("Account Name")[avc_col].sum()

        st.write(f"Bookings: {len(grouped)}")
        st.write(f"Summed total bookings: ${grouped.sum():,.2f}")

        top3 = grouped.sort_values(ascending=False).head(3)
        top_df = top3.reset_index()
        top_df.columns = ["Account Name", "AVC"]

        st.dataframe(top_df)

    st.success("✅ Processing complete")

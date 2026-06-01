import streamlit as st
import pandas as pd

st.title("Booking Reconciliation Engine")

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

# Main processing
if file:
    df = pd.read_excel(file)

    # Find AVC column
    if "CPQ AVC (Retro net)" in df.columns:
        avc_col = "CPQ AVC (Retro net)"
    elif "CRQ AVC (Retro net)" in df.columns:
        avc_col = "CRQ AVC (Retro net)"
    else:
        st.error("Missing AVC column")
        st.stop()

    # Filter by month
    df["Close Date"] = df["Close Date"].astype(str)
    df = df[df["Close Date"].str.contains(month_map[month], na=False)]

    # Remove True-up
    df = df[df["Type"].astype(str).str.strip() != "True-up"]

    # Filter valid RGO
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
        st.dataframe(top3.reset_index())

    st.success("✅ Done")

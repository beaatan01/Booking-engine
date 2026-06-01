import streamlit as st
import pandas as pd

st.set_page_config(page_title="Booking Engine", layout="wide")
st.title("📊 Booking Reconciliation Engine")

month_map = {
    "January": "-01-","February": "-02-","March": "-03-",
    "April": "-04-","May": "-05-","June": "-06-",
    "July": "-07-","August": "-08-","September": "-09-",
    "October": "-10-","November": "-11-","December": "-12-"
}

month = st.selectbox("Select Month", list(month_map.keys()))
file = st.file_uploader("Upload Excel File", type=["xlsx"])

def normalize(name):
    return " ".join(str(name).strip().upper().split())

def detect_header(df_raw):
    for i in range(len(df_raw)):
        row_values = df_raw.iloc[i].astype(str).str.upper().tolist()
        if (
            any("ACCOUNT" in v for v in row_values) and
            any("CLOSE" in v for v in row_values) and
            any(("AVC" in v) or ("ACV" in v) for v in row_values)
        ):
            return i
    return None

def find_col(df_cols, keywords):
    for col in df_cols:
        for k in keywords:
            if k in col:
                return col
    return None

def number_to_words(n):
    words = {
        0:"zero",1:"one",2:"two",3:"three",4:"four",
        5:"five",6:"six",7:"seven",8:"eight",9:"nine",
        10:"ten",11:"eleven",12:"twelve"
    }
    return words.get(n, str(n))

if file:
    try:
        # Load raw
        raw_df = pd.read_excel(file, engine="openpyxl", header=None)

        # Detect header row
        header_row = detect_header(raw_df)
        if header_row is None:
            st.error("❌ Could not find valid header row")
            st.stop()

        # Reload correctly
        df = pd.read_excel(file, engine="openpyxl", skiprows=header_row)
        df.columns = [str(c).strip().upper() for c in df.columns]

        # Detect columns
        account_col = find_col(df.columns, ["ACCOUNT"])
        close_col = find_col(df.columns, ["CLOSE"])
        type_col = find_col(df.columns, ["TYPE"])
        rgo_col = find_col(df.columns, ["RGO"])

        avc_col = None
        for col in df.columns:
            if "AVC" in col or "ACV" in col:
                avc_col = col
                break

        # Ensure required columns exist
        if not all([account_col, close_col, type_col, rgo_col, avc_col]):
            st.error("❌ Required columns not found")
            st.stop()

        # Standardize
        df = df.rename(columns={
            account_col: "Account Name",
            close_col: "Close Date",
            type_col: "Type",
            rgo_col: "RGO Product",
            avc_col: "AVC"
        })

        df["AVC"] = pd.to_numeric(df["AVC"], errors="coerce").fillna(0)

        # STRICT FILTERING
        df["Close Date"] = df["Close Date"].astype(str)
        df = df[df["Close Date"].str.contains(month_map[month], na=False)]

        df = df[df["Type"].astype(str).str.strip() != "True-up"]

        df["RGO Product"] = df["RGO Product"].astype(str).str.strip()

        valid_rgo = ["Clinical","CSG","Pharmacy","PPO","Specialty"]
        df = df[df["RGO Product"].isin(valid_rgo)]

        df["RGO Product"] = df["RGO Product"].str.upper()
        df["Account Name"] = df["Account Name"].apply(normalize)

        business_units = ["CLINICAL","CSG","PHARMACY","PPO","SPECIALTY"]
        results = {}

        # OUTPUT
        for bu in business_units:
            st.subheader(bu)

            subset = df[df["RGO Product"] == bu]

            if subset.empty:
                st.write("Bookings: 0")
                st.write("Summed total bookings: $0")
                st.write("Top highest bookings: (none)")
                results[bu] = {"count":0,"total":0,"top3":[]}
                continue

            grouped = subset.groupby("Account Name")["AVC"].sum()

            count = len(grouped)
            total = grouped.sum()
            top3 = grouped.sort_values(ascending=False).head(3)

            st.write(f"Bookings: {count}")
            st.write(f"Summed total bookings: ${total:,.2f}")
            st.dataframe(top3.reset_index())

            results[bu] = {"count":count,"total":total,"top3":top3}

        # SUMMARY
        st.markdown("## Summary")

        summary_lines = []

        for bu in business_units:
            data = results[bu]

            if data["count"] == 0:
                text = f"{bu.title()}: No bookings in {month}"
                summary_lines.append(text)
                st.markdown(f"**{text}**")
                continue

            names = list(data["top3"].index)

            if len(names) == 1:
                name_str = names[0]
            elif len(names) == 2:
                name_str = f"{names[0]} and {names[1]}"
            else:
                name_str = f"{names[0]}, {names[1]}, and {names[2]}"

            text = f"{number_to_words(data['count']).capitalize()} bookings in {month}, totaling ${data['total']:,.2f}, led by {name_str}"

            summary_lines.append(f"{bu.title()}: {text}")
            st.markdown(f"**{bu.title()}:** {text}")

        st.markdown("### Copy Summary")
        st.code("Summary\n" + "\n".join(summary_lines))

    except Exception as e:
        st.error("❌ Something went wrong")
        st.text(str(e))
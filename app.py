import streamlit as st
import pandas as pd

st.set_page_config(page_title="Booking Engine", layout="wide")

st.title("📊 Booking Reconciliation Engine 2.0")

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

def number_to_words(n):
    words = {
        0:"zero",1:"one",2:"two",3:"three",4:"four",
        5:"five",6:"six",7:"seven",8:"eight",9:"nine",
        10:"ten",11:"eleven",12:"twelve"
    }
    return words.get(n, str(n))

if file:
    try:
        df = pd.read_excel(file, engine="openpyxl")

        # Normalize column names
        df.columns = [str(c).strip().upper() for c in df.columns]

        # SAFE COLUMN DETECTION
        def find_col(keys):
            for col in df.columns:
                for k in keys:
                    if k in col:
                        return col
            return None

        account_col = find_col(["ACCOUNT"])
        close_col = find_col(["CLOSE"])
        type_col = find_col(["TYPE"])
        rgo_col = find_col(["RGO"])

        avc_col = None
        for c in df.columns:
            if "AVC" in c:
                avc_col = c
                break

        # Fallbacks (NO CRASH)
        df["Account Name"] = df[account_col] if account_col else "UNKNOWN"
        df["Close Date"] = df[close_col] if close_col else ""
        df["Type"] = df[type_col] if type_col else ""
        df["RGO Product"] = df[rgo_col] if rgo_col else ""
        df["AVC"] = pd.to_numeric(df[avc_col], errors="coerce").fillna(0) if avc_col else 0

        # FILTERING
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

        # ✅ SUMMARY
        st.markdown("## Summary")

        summary_lines = []

        for bu in business_units:
            data = results[bu]

            if data["count"] == 0:
                text = f"{bu.title()}: No bookings in {month}"
                st.markdown(f"**{text}**")
                summary_lines.append(text)
                continue

            names = list(data["top3"].index)

            if len(names) == 1:
                name_str = names[0]
            elif len(names) == 2:
                name_str = f"{names[0]} and {names[1]}"
            else:
                name_str = f"{names[0]}, {names[1]}, and {names[2]}"

            text = f"{number_to_words(data['count']).capitalize()} bookings in {month}, totaling ${data['total']:,.2f}, led by {name_str}"

            st.markdown(f"**{bu.title()}:** {text}")
            summary_lines.append(f"{bu.title()}: {text}")

        st.markdown("### Copy Summary")
        full_summary = "Summary\n" + "\n".join(summary_lines)
        st.code(full_summary)

    except Exception as e:
        st.error("❌ App failed — but still running safely")
        st.text(str(e))

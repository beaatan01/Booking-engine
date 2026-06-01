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

# Convert number to words
def number_to_words(n):
    words = {
        0: "zero",
        1: "one",
        2: "two",
        3: "three",
        4: "four",
        5: "five",
        6: "six",
        7: "seven",
        8: "eight",
        9: "nine",
        10: "ten",
        11: "eleven",
        12: "twelve"
    }
    return words.get(n, str(n))

if file:
    df = pd.read_excel(file, engine="openpyxl")

    # Clean column names
    df.columns = [col.strip() for col in df.columns]

    # Detect AVC column (robust)
    avc_col = None
    for col in df.columns:
        if col.upper() == "CPQ AVC (RETRO NET)":
            avc_col = col
        elif col.upper() == "CRQ AVC (RETRO NET)":
            avc_col = col

    if avc_col is None:
        st.error(f"❌ Missing AVC column. Found: {list(df.columns)}")
        st.stop()

    # Filter month
    df["Close Date"] = df["Close Date"].astype(str)
    df = df[df["Close Date"].str.contains(month_map[month], na=False)]

    # Remove True-up
    df = df[df["Type"].astype(str).str.strip() != "True-up"]

    # Filter RGO
    df["RGO Product"] = df["RGO Product"].astype(str).str.strip()
    valid_rgo = ["Clinical", "CSG", "Pharmacy", "PPO", "Specialty"]
    df = df[df["RGO Product"].isin(valid_rgo)]

    # Normalize
    df["RGO Product"] = df["RGO Product"].str.upper()
    df["Account Name"] = df["Account Name"].apply(normalize)

    business_units = ["CLINICAL", "CSG", "PHARMACY", "PPO", "SPECIALTY"]

    results = {}

    # ---------------- MAIN OUTPUT ----------------
    for bu in business_units:
        st.subheader(bu)

        subset = df[df["RGO Product"] == bu]

        if len(subset) == 0:
            st.write("Bookings: 0")
            st.write("Summed total bookings: $0")
            st.write("Top highest bookings: (none)")
            results[bu] = {"count": 0, "total": 0, "top3": pd.Series(dtype=float)}
            continue

        grouped = subset.groupby("Account Name")[avc_col].sum()

        count = len(grouped)
        total = grouped.sum()
        top3 = grouped.sort_values(ascending=False).head(3)

        st.write(f"Bookings: {count}")
        st.write(f"Summed total bookings: ${total:,.2f}")

        top_df = top3.reset_index()
        top_df.columns = ["Account Name", "AVC"]
        st.dataframe(top_df)

        results[bu] = {
            "count": count,
            "total": total,
            "top3": top3
        }

    # ---------------- SUMMARY SECTION ----------------

    st.markdown("## Summary")

    summary_lines = []

    for bu in business_units:
        data = results[bu]
        count = data["count"]
        total = data["total"]
        top3 = data["top3"]

        if count == 0:
            line = f"**{bu.title()}:** No bookings in {month}"
            st.markdown(line)
            summary_lines.append(f"{bu.title()}: No bookings in {month}")
        else:
            names = top3.index.tolist()

            if len(names) == 1:
                top_names = names[0]
            elif len(names) == 2:
                top_names = f"{names[0]} and {names[1]}"
            else:
                top_names = f"{names[0]}, {names[1]}, and {names[2]}"

            sentence = (
                f"**{bu.title()}:** {number_to_words(count).capitalize()} bookings in {month}, "
                f"totaling ${total:,.2f}, led by {top_names}"
            )

            clean_sentence = (
                f"{bu.title()}: {number_to_words(count).capitalize()} bookings in {month}, "
                f"totaling ${total:,.2f}, led by {top_names}"
            )

            st.markdown(sentence)
            summary_lines.append(clean_sentence)

    # ---------------- COPY BLOCK ----------------

    full_summary = "Summary\n" + "\n".join(summary_lines)

    st.markdown("### Copy Summary")
    st.code(full_summary, language="text")
    st.caption("👉 Copy the summary above and paste into email, Slack, or reports.")
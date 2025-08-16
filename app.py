import streamlit as st
import pandas as pd
from datetime import date

st.title("Pendency Report from CSV Upload")

# Step 1: Upload CSV
uploaded_file = st.file_uploader("Upload CSV", type="csv")

if uploaded_file is not None and uploaded_file.size > 10 * 1024 * 1024:  # 10MB limit
    st.error("File too large. Please upload a file smaller than 10MB.")
    st.stop()

if uploaded_file:
    try:
        df = pd.read_csv(
            uploaded_file,
            parse_dates=["case_open_date", "case_close_date"],
            dtype=str,  # read all as string initially
            on_bad_lines="skip"  # skip malformed rows
        )
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        st.stop()
    
   #st.subheader("Full Data")
    #st.dataframe(df)

    # Step 2: Date Input
    start_date = st.date_input("Start Date", value=date(2025, 6, 1))
    end_date = st.date_input("End Date", value=date(2025, 7, 31))

    if start_date > end_date:
        st.error("Start Date cannot be after End Date.")
        st.stop()

    # Step 3: Owner Filter
    all_owners = sorted(df["owner"].dropna().unique())
    selected_owners = st.multiselect("Select Owners", all_owners, default=all_owners)
    filtered_df = df[df["owner"].isin(selected_owners)]

    # Step 4: Process Each Owner
    def generate_report(data):
        report = []
        for owner in sorted(data["owner"].unique()):
            owner_df = data[data["owner"] == owner]
            open_till_start = owner_df[
                (owner_df["case_open_date"] < pd.to_datetime(start_date)) &
                ((owner_df["case_close_date"].isna()) | (owner_df["case_close_date"] >= pd.to_datetime(start_date)))
            ].shape[0]

            new_cases = owner_df[
                (owner_df["case_open_date"] >= pd.to_datetime(start_date)) &
                (owner_df["case_open_date"] <= pd.to_datetime(end_date))
            ].shape[0]

            closed_cases = owner_df[
                (owner_df["case_close_date"] >= pd.to_datetime(start_date)) &
                (owner_df["case_close_date"] <= pd.to_datetime(end_date))
            ].shape[0]

            net_open = open_till_start + new_cases - closed_cases

            open_cases = owner_df[owner_df["case_status"] == "Open"]
            aging = (pd.to_datetime(end_date) - open_cases["case_open_date"]).dt.days
            aging_0_30 = ((aging >= 0) & (aging <= 30)).sum()
            aging_31_90 = ((aging > 30) & (aging <= 90)).sum()
            aging_90_plus = (aging > 90).sum()

            report.append({
                "owner": owner,
                "open_till_start": open_till_start,
                "new_cases": new_cases,
                "closed_cases": closed_cases,
                "net_open": net_open,
                "aging_0_30": aging_0_30,
                "aging_31_90": aging_31_90,
                "aging_90_plus": aging_90_plus
            })
        return pd.DataFrame(report)

    summary_df = generate_report(filtered_df)

    def sanitize_csv(df):
        dangerous_prefixes = ("=", "+", "-", "@")
        return df.applymap(lambda x: x if not isinstance(x, str) or not x.startswith(dangerous_prefixes) else "'" + x)
    
    summary_df = sanitize_csv(summary_df)

    st.subheader("Case Summary")
    st.dataframe(summary_df)

    # Step 5: Download Summary as CSV
    csv = summary_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Summary CSV",
        data=csv,
        file_name="case_summary.csv",
        mime="text/csv",
    )

dummy_csv_path = "case_data_indian_names.csv"
with open(dummy_csv_path, "rb") as f:
    dummy_csv_bytes = f.read()
st.download_button(
    label="Download Dummy CSV",
    data=dummy_csv_bytes,
    file_name="dummy_cases.csv",
    mime="text/csv"
)

# Footer
st.markdown("---")
st.caption("Created by Rochak Kr. Jain")

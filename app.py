import streamlit as st
import pandas as pd
from datetime import date

st.title("Dendency Report from CSV Upload")

# Step 1: Upload CSV
uploaded_file = st.file_uploader("Upload CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file, parse_dates=["case_open_date", "case_close_date"])
    
   #st.subheader("Full Data")
    #st.dataframe(df)

    # Step 2: Date Input
    start_date = st.date_input("Start Date", value=date(2025, 6, 1))
    end_date = st.date_input("End Date", value=date(2025, 7, 31))

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

    st.subheader("Case Summary")
    st.dataframe(summary_df)

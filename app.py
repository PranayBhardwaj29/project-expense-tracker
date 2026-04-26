import csv
import os
from datetime import datetime, date
import streamlit as st
import pandas as pd

FILE_NAME = "expenses.csv"

# ── helpers ──────────────────────────────────────────────────────────────────

def initialize_file():
    if not os.path.exists(FILE_NAME):
        with open(FILE_NAME, "w", newline="") as f:
            csv.writer(f).writerow(["Date", "Category", "Description", "Amount"])

def read_expenses() -> pd.DataFrame:
    initialize_file()
    df = pd.read_csv(FILE_NAME, parse_dates=["Date"])
    if df.empty:
        return pd.DataFrame(columns=["Date", "Category", "Description", "Amount"])
    df["Amount"] = df["Amount"].astype(float)
    return df

def write_expenses(df: pd.DataFrame):
    df.to_csv(FILE_NAME, index=False)

# ── page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="💰 Expense Tracker", layout="wide")
st.title("💰 Expense Tracker")

initialize_file()

tab_add, tab_all, tab_cat, tab_del = st.tabs(
    ["➕ Add Expense", "📋 All Expenses", "📊 By Category", "🗑️ Delete"]
)

# ── TAB 1 – Add ───────────────────────────────────────────────────────────────

with tab_add:
    st.subheader("Add a new expense")
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            expense_date = st.date_input("Date", value=date.today())
            category = st.text_input("Category", placeholder="Food, Transport, Bills…")
        with col2:
            description = st.text_input("Description")
            amount = st.number_input("Amount (₹ / $)", min_value=0.0, step=0.01, format="%.2f")

        submitted = st.form_submit_button("Add Expense", use_container_width=True)

    if submitted:
        if not category or not description or amount <= 0:
            st.error("Please fill in all fields and enter a positive amount.")
        else:
            df = read_expenses()
            new_row = pd.DataFrame([{
                "Date": expense_date.strftime("%Y-%m-%d"),
                "Category": category.strip(),
                "Description": description.strip(),
                "Amount": round(amount, 2)
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            write_expenses(df)
            st.success(f"✅ Added **{description}** — {amount:.2f}")

# ── TAB 2 – All Expenses ──────────────────────────────────────────────────────

with tab_all:
    st.subheader("All Expenses")
    df = read_expenses()

    if df.empty:
        st.info("No expenses recorded yet.")
    else:
        st.dataframe(
            df.sort_values("Date", ascending=False).reset_index(drop=True),
            use_container_width=True,
            column_config={
                "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                "Amount": st.column_config.NumberColumn("Amount", format="%.2f"),
            }
        )
        st.metric("Total Spent", f"{df['Amount'].sum():,.2f}")

# ── TAB 3 – By Category ───────────────────────────────────────────────────────

with tab_cat:
    st.subheader("Spending by Category")
    df = read_expenses()

    if df.empty:
        st.info("No expenses recorded yet.")
    else:
        summary = (
            df.groupby("Category")["Amount"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
            .rename(columns={"Amount": "Total"})
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            st.dataframe(
                summary,
                use_container_width=True,
                column_config={"Total": st.column_config.NumberColumn("Total", format="%.2f")}
            )
            st.metric("Grand Total", f"{summary['Total'].sum():,.2f}")
        with col2:
            st.bar_chart(summary.set_index("Category")["Total"])

# ── TAB 4 – Delete ────────────────────────────────────────────────────────────

with tab_del:
    st.subheader("Delete an Expense")
    df = read_expenses()

    if df.empty:
        st.info("No expenses to delete.")
    else:
        df_display = df.copy()
        df_display.index = df_display.index + 1           # 1-based numbering
        df_display["Amount"] = df_display["Amount"].map("{:.2f}".format)

        st.dataframe(df_display, use_container_width=True)

        row_num = st.number_input(
            "Enter row # to delete", min_value=1, max_value=len(df), step=1
        )
        if st.button("Delete", type="primary"):
            deleted = df.iloc[row_num - 1]
            df = df.drop(index=row_num - 1).reset_index(drop=True)
            write_expenses(df)
            st.success(f"🗑️ Deleted **{deleted['Description']}** ({deleted['Amount']:.2f})")
            st.rerun()

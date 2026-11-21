# ============================================================
# FINTRACK PRO
# PERSONAL FINANCE & EXPENSE MANAGEMENT SYSTEM
# VERSION 2 - Smart categories + aesthetic dashboard
# ============================================================
#
# HOW THIS FILE IS ORGANISED
#   1. Settings            -> categories, hidden minimum balance
#   2. Data                -> where transactions are stored
#   3. Calculations        -> income, expenses, balance, savings rate
#   4. Add transaction     -> validation + minimum balance protection
#   5. Dashboard cards     -> the HTML shown at the top of the dashboard
#   6. Charts              -> pie, bar and line charts
#   7. Saving suggestions  -> simple tips based on your spending
#   8. Search & filter     -> find old transactions
#   9. Export              -> CSV and Excel downloads
#  10. Design (CSS)        -> colors, cards, hover effects
#  11. Interface           -> the Gradio tabs, buttons and inputs
# ============================================================

import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt
import tempfile
import os
from datetime import datetime


# ============================================================
# 1. SETTINGS
# ============================================================

# Hidden safety limit. It is used for protection only and is
# never shown to the user anywhere in the app.
MINIMUM_BALANCE = 25000

# Money coming IN can only come from these sources
INCOME_CATEGORIES = [
    "Salary", "Rent", "Investment",
    "Business", "Freelance", "Gift", "Other"
]

# Money going OUT can only go to these places
EXPENSE_CATEGORIES = [
    "Food", "Transport", "Shopping",
    "Education", "Entertainment",
    "Bills", "Health", "Rent", "Other"
]

# Used by the Search tab (all categories, no duplicates)
ALL_CATEGORIES = sorted(set(INCOME_CATEGORIES + EXPENSE_CATEGORIES))

COLUMNS = ["Date", "Type", "Category", "Description", "Amount"]

# Chart colors (same everywhere so the app looks consistent)
GREEN = "#16a34a"
RED = "#ef4444"
PIE_COLORS = [
    "#6366f1", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981",
    "#3b82f6", "#ef4444", "#14b8a6", "#a855f7"
]


def categories_for(transaction_type):
    """Return the correct category list for Income or Expense."""
    if transaction_type == "Income":
        return INCOME_CATEGORIES
    return EXPENSE_CATEGORIES


# Keep existing records when this code is re-run in the same notebook
if "fintrack_records" not in globals():

    fintrack_records = []

    if "finance" in globals():

        for t in finance.transactions:

            fintrack_records.append({
                "Date": str(t.date),
                "Type": t.transaction_type,
                "Category": t.category,
                "Description": t.description,
                "Amount": float(t.amount)
            })


# ============================================================
# 2. DATA
# ============================================================

def get_data():
    """All transactions as a table."""
    return pd.DataFrame(fintrack_records, columns=COLUMNS)


# ============================================================
# 3. CALCULATIONS
# ============================================================

def calculate_summary():
    """Returns income, expenses, balance and savings rate."""

    df = get_data()

    income = df.loc[df["Type"] == "Income", "Amount"].sum()
    expenses = df.loc[df["Type"] == "Expense", "Amount"].sum()

    # No opening balance: balance = income - expenses
    balance = income - expenses

    savings_rate = (
        ((income - expenses) / income) * 100
        if income > 0 else 0
    )

    return income, expenses, balance, savings_rate


# ============================================================
# 4. ADD TRANSACTION
# ============================================================

def add_new_transaction(
    date, transaction_type,
    category, description, amount
):

    try:

        # --- Basic checks ---------------------------------
        datetime.strptime(date, "%Y-%m-%d")

        amount = float(amount)

        if amount <= 0:
            return "ERROR: Amount must be greater than zero."

        if transaction_type not in ["Income", "Expense"]:
            return "ERROR: Invalid transaction type."

        # Category must match the type (no "Shopping" income!)
        if category not in categories_for(transaction_type):
            return (
                f"ERROR: '{category}' is not a valid "
                f"{transaction_type} category."
            )

        if not description or not description.strip():
            return "ERROR: Please enter a description."

        # --- Minimum balance protection -------------------
        income, expenses, balance, savings = calculate_summary()

        if transaction_type == "Expense":

            balance_after = balance - amount

            if balance_after < MINIMUM_BALANCE:

                return (
                    "ERROR: TRANSACTION BLOCKED!\n\n"
                    "This expense would take your account balance "
                    "below the safe limit.\n\n"
                    f"Current Balance: ₹{balance:,.2f}\n"
                    f"Requested Expense: ₹{amount:,.2f}\n"
                    f"Balance After Expense: ₹{balance_after:,.2f}\n\n"
                    "Please reduce the expense or add income first."
                )

        # --- Save the transaction -------------------------
        fintrack_records.append({
            "Date": date,
            "Type": transaction_type,
            "Category": category,
            "Description": description.strip(),
            "Amount": amount
        })

        # --- Low balance warning --------------------------
        _, _, new_balance, _ = calculate_summary()

        if (
            transaction_type == "Expense"
            and new_balance <= MINIMUM_BALANCE + 5000
        ):

            return (
                "WARNING: Transaction added successfully!\n\n"
                f"Remaining Balance: ₹{new_balance:,.2f}\n"
                "Your balance is getting low. "
                "Avoid unnecessary spending."
            )

        return "SUCCESS: Transaction added successfully!"

    except ValueError:

        return (
            "ERROR: Enter a valid date in YYYY-MM-DD format "
            "and a valid amount."
        )


def update_category_choices(transaction_type):
    """
    Runs when the user switches between Income and Expense.
    Replaces the category dropdown with the correct list.
    """
    choices = categories_for(transaction_type)

    return gr.update(choices=choices, value=choices[0])


# ============================================================
# 5. DASHBOARD CARDS
# ============================================================

def get_dashboard_cards():

    income, expenses, balance, savings = calculate_summary()

    # Decide the account status (limit value is never shown)
    if balance <= MINIMUM_BALANCE:
        status, status_class = "Low Balance", "status-low"
    elif balance <= MINIMUM_BALANCE + 5000:
        status, status_class = "Warning", "status-warning"
    else:
        status, status_class = "Safe", "status-safe"

    return f"""
    <div class="hero-card">
        <div class="hero-label">CURRENT BALANCE</div>
        <div class="hero-value">₹{balance:,.2f}</div>
        <div class="hero-badge {status_class}">● {status}</div>
    </div>

    <div class="dashboard-grid">

        <div class="metric income">
            <div class="metric-icon">📈</div>
            <div class="metric-label">TOTAL INCOME</div>
            <div class="metric-value">₹{income:,.2f}</div>
        </div>

        <div class="metric expense">
            <div class="metric-icon">📉</div>
            <div class="metric-label">TOTAL EXPENSES</div>
            <div class="metric-value">₹{expenses:,.2f}</div>
        </div>

        <div class="metric savings">
            <div class="metric-icon">💎</div>
            <div class="metric-label">SAVINGS RATE</div>
            <div class="metric-value">{savings:.2f}%</div>
        </div>

    </div>
    """


# ============================================================
# 6. CHARTS
# ============================================================

def category_chart():
    """Pie chart of where the money was spent."""

    df = get_data()
    expenses = df[df["Type"] == "Expense"]

    fig, ax = plt.subplots(figsize=(7, 5))

    if expenses.empty:

        ax.text(
            0.5, 0.5, "No expense records available",
            ha="center", va="center"
        )
        ax.axis("off")

    else:

        category_data = expenses.groupby("Category")["Amount"].sum()

        ax.pie(
            category_data.values,
            labels=category_data.index,
            autopct="%1.1f%%",
            startangle=90,
            colors=PIE_COLORS,
            wedgeprops={"width": 0.45, "edgecolor": "white"}  # donut style
        )

        ax.set_title("Where Your Money Goes", fontweight="bold")

    fig.tight_layout()
    return fig


def comparison_chart():
    """Bar chart: income vs expenses."""

    income, expenses, balance, savings = calculate_summary()

    fig, ax = plt.subplots(figsize=(7, 5))

    ax.bar(
        ["Income", "Expenses"],
        [income, expenses],
        color=[GREEN, RED],
        width=0.5
    )

    ax.set_title("Income vs Expenses", fontweight="bold")
    ax.set_ylabel("Amount (₹)")
    ax.grid(axis="y", alpha=0.2)

    # Clean look: remove top and right borders
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    return fig


def monthly_chart():
    """Line chart: income and expenses month by month."""

    df = get_data()

    fig, ax = plt.subplots(figsize=(8, 5))

    if df.empty:

        ax.text(
            0.5, 0.5, "No monthly records available",
            ha="center", va="center"
        )
        ax.axis("off")

    else:

        df["Date"] = pd.to_datetime(df["Date"])
        df["Month"] = df["Date"].dt.to_period("M")

        monthly = df.pivot_table(
            index="Month",
            columns="Type",
            values="Amount",
            aggfunc="sum",
            fill_value=0
        )

        # Make sure both columns exist even if one type is missing
        for column in ["Income", "Expense"]:
            if column not in monthly.columns:
                monthly[column] = 0

        monthly = monthly.sort_index()
        months = monthly.index.astype(str)

        ax.plot(months, monthly["Income"], marker="o",
                color=GREEN, linewidth=2.5, label="Income")

        ax.plot(months, monthly["Expense"], marker="o",
                color=RED, linewidth=2.5, label="Expenses")

        ax.fill_between(months, monthly["Income"],
                        color=GREEN, alpha=0.08)
        ax.fill_between(months, monthly["Expense"],
                        color=RED, alpha=0.08)

        ax.set_title("Monthly Financial Trend", fontweight="bold")
        ax.set_xlabel("Month")
        ax.set_ylabel("Amount (₹)")
        ax.legend()
        ax.grid(alpha=0.2)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    fig.tight_layout()
    return fig


# ============================================================
# 7. SMART SAVING SUGGESTIONS
# ============================================================

def get_saving_suggestions():

    df = get_data()
    income, expenses, balance, savings = calculate_summary()

    if df.empty:
        return "Add transactions to receive saving suggestions."

    expense_df = df[df["Type"] == "Expense"]

    if expense_df.empty:
        return """
        - Record your expenses to understand spending patterns.
        - Keep a healthy balance in your account.
        - Set a monthly savings target.
        """

    # Spending per category, highest first
    category_data = expense_df.groupby(
        "Category"
    )["Amount"].sum().sort_values(ascending=False)

    highest_category = category_data.index[0]
    highest_amount = category_data.iloc[0]

    suggestions = []

    # Tip 1: biggest spending category
    suggestions.append(
        f"**Reduce {highest_category} expenses:** "
        f"A 10% reduction could save ₹{highest_amount * 0.10:,.2f}."
    )

    # Tip 2: savings target
    if income > 0:
        suggestions.append(
            f"**Set a savings target:** Consider aiming to save "
            f"20% of recorded income (₹{income * 0.20:,.2f}), "
            "if essential expenses allow."
        )
    else:
        suggestions.append(
            "**Record income:** Add income transactions to calculate "
            "a meaningful savings target."
        )

    # Tip 3: income vs expenses
    if income > 0 and expenses > income:
        suggestions.append(
            "**Control spending:** Your recorded expenses exceed "
            "your recorded income. Review non-essential expenses."
        )
    elif income > 0:
        suggestions.append(
            "**Maintain your savings habit:** Your recorded income "
            "is higher than expenses."
        )

    # Tip 4: balance protection (limit value not shown)
    if balance <= MINIMUM_BALANCE + 5000:
        suggestions.append(
            "**Balance alert:** Your account balance is low. "
            "Avoid unnecessary spending."
        )
    else:
        suggestions.append(
            "**Protect your balance:** Keep a healthy cushion "
            "in your account for emergencies."
        )

    # Tip 5: second biggest category
    if len(category_data) > 1:
        suggestions.append(
            f"**Review {category_data.index[1]}:** Check whether "
            "some expenses in this category can be reduced."
        )

    return (
        "\n\n".join(f"{i+1}. {s}" for i, s in enumerate(suggestions))
        + "\n\n*Suggestions are based on recorded transactions "
          "and are educational, not professional financial advice.*"
    )


# ============================================================
# 8. TRANSACTION HISTORY + SEARCH & FILTER
# ============================================================

def get_transaction_history():
    return get_data()


def search_transactions(
    search_text, transaction_type,
    category, start_date, end_date
):

    df = get_data()

    if df.empty:
        return pd.DataFrame(columns=COLUMNS), "No transactions available."

    # Search inside description
    if search_text and search_text.strip():
        df = df[
            df["Description"].str.contains(
                search_text.strip(), case=False, na=False
            )
        ]

    # Filter by type and category
    if transaction_type != "All":
        df = df[df["Type"] == transaction_type]

    if category != "All":
        df = df[df["Category"] == category]

    # Filter by dates
    try:

        has_start = bool(start_date and start_date.strip())
        has_end = bool(end_date and end_date.strip())

        if has_start:
            start = pd.to_datetime(start_date, format="%Y-%m-%d")
            df = df[pd.to_datetime(df["Date"]) >= start]

        if has_end:
            end = pd.to_datetime(end_date, format="%Y-%m-%d")
            df = df[pd.to_datetime(df["Date"]) <= end]

        if has_start and has_end and start > end:
            return (
                pd.DataFrame(columns=COLUMNS),
                "ERROR: Start date cannot be after end date."
            )

    except (ValueError, TypeError):
        return (
            pd.DataFrame(columns=COLUMNS),
            "ERROR: Enter dates in YYYY-MM-DD format."
        )

    if len(df) == 0:
        return df, "No matching transactions found."

    summary = f"""
SEARCH SUMMARY

Total Amount: ₹{df["Amount"].sum():,.2f}

Transactions Found: {len(df)}

Highest Transaction: ₹{df["Amount"].max():,.2f}

Average Transaction: ₹{df["Amount"].mean():,.2f}
"""

    return df, summary


def clear_search():
    """Reset all search boxes and show every transaction."""
    return (
        "", "All", "All", "", "",
        get_data(),
        "Showing all transactions."
    )


# ============================================================
# 9. EXPORT
# ============================================================

def export_csv():

    path = os.path.join(tempfile.gettempdir(), "FinTrack_Pro_Report.csv")

    get_data().to_csv(path, index=False)

    return path


def export_excel():

    path = os.path.join(tempfile.gettempdir(), "FinTrack_Pro_Report.xlsx")

    income, expenses, balance, savings = calculate_summary()

    summary = pd.DataFrame({
        "Metric": [
            "Total Income", "Total Expenses",
            "Current Balance", "Savings Rate"
        ],
        "Value": [income, expenses, balance, round(savings, 2)]
    })

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        get_data().to_excel(writer, sheet_name="Transactions", index=False)
        summary.to_excel(writer, sheet_name="Financial Summary", index=False)

    return path


# ============================================================
# REFRESH HELPERS
# ============================================================

def refresh_dashboard():
    """Rebuilds everything on the dashboard."""
    return (
        get_dashboard_cards(),
        category_chart(),
        comparison_chart(),
        monthly_chart(),
        get_saving_suggestions(),
        get_transaction_history()
    )


def add_and_refresh(
    date, transaction_type,
    category, description, amount
):
    """Adds a transaction, then refreshes the dashboard."""

    message = add_new_transaction(
        date, transaction_type, category, description, amount
    )

    return (message, *refresh_dashboard())


# ============================================================
# 10. DESIGN (CSS)
# ============================================================

custom_css = """

.gradio-container {
    max-width: 1350px !important;
    margin: auto !important;
    font-family: 'Segoe UI', Arial, sans-serif !important;
}

body, input, button, textarea, select {
    font-family: 'Segoe UI', Arial, sans-serif !important;
}

/* ---------- Title ---------- */
#main-title {
    text-align: center;
    padding: 25px 10px;
}

#main-title h1 {
    font-size: 40px;
    font-weight: 800;
    letter-spacing: 0.5px;
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

#main-title p {
    font-size: 15px;
}

/* ---------- Big balance card ---------- */
.hero-card {
    position: relative;
    overflow: hidden;
    padding: 34px 30px;
    margin: 18px 0 16px 0;
    border-radius: 20px;
    color: white;
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #db2777 100%);
    box-shadow: 0 12px 30px rgba(99, 102, 241, 0.35);
}

/* soft glowing circles for a modern look */
.hero-card::before,
.hero-card::after {
    content: "";
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.12);
}

.hero-card::before {
    width: 220px;
    height: 220px;
    top: -80px;
    right: -50px;
}

.hero-card::after {
    width: 140px;
    height: 140px;
    bottom: -60px;
    right: 150px;
}

.hero-label {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 2px;
    opacity: 0.85;
}

.hero-value {
    font-size: 46px;
    font-weight: 800;
    margin: 10px 0 16px 0;
    overflow-wrap: anywhere;
}

.hero-badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 700;
    background: rgba(255, 255, 255, 0.2);
    backdrop-filter: blur(4px);
}

.status-safe    { color: #bbf7d0; }
.status-warning { color: #fde68a; }
.status-low     { color: #fecaca; }

/* ---------- Small metric cards ---------- */
.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
    margin: 0 0 25px 0;
}

.metric {
    position: relative;
    padding: 24px;
    border-radius: 16px;
    background: var(--block-background-fill);
    border: 1px solid var(--border-color-primary);
    min-width: 0;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

/* colored line on top of each card */
.metric::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    border-radius: 16px 16px 0 0;
    background: var(--accent);
}

/* lift effect when the mouse is on a card */
.metric:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12);
}

.metric-icon {
    font-size: 26px;
    margin-bottom: 8px;
}

.metric-label {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.8px;
    color: var(--body-text-color-subdued);
}

.metric-value {
    font-size: 26px;
    font-weight: 800;
    margin-top: 10px;
    overflow-wrap: anywhere;
}

.income  { --accent: #16a34a; }
.expense { --accent: #ef4444; }
.savings { --accent: #8b5cf6; }

.income  .metric-value { color: #16a34a; }
.expense .metric-value { color: #ef4444; }
.savings .metric-value { color: #8b5cf6; }

/* ---------- Mobile ---------- */
@media(max-width: 750px) {

    .dashboard-grid {
        grid-template-columns: repeat(1, minmax(0, 1fr));
    }

    .hero-value {
        font-size: 34px;
    }
}

"""


# ============================================================
# 11. INTERFACE
# ============================================================

with gr.Blocks(
    theme=gr.themes.Soft(),
    css=custom_css,
    title="FinTrack Pro"
) as app:

    gr.Markdown(
        """
        # FinTrack Pro

        ### Personal Finance & Expense Management System

        Manage your money, protect your balance and improve your savings.
        """,
        elem_id="main-title"
    )

    # --------------------------------------------------------
    # DASHBOARD TAB
    # --------------------------------------------------------

    with gr.Tab("Dashboard"):

        dashboard_cards = gr.HTML(value=get_dashboard_cards())

        refresh_button = gr.Button("Refresh Dashboard", variant="primary")

        gr.Markdown("## Financial Analytics")

        with gr.Row():

            category_plot = gr.Plot(
                value=category_chart(),
                label="Expense Distribution"
            )

            comparison_plot = gr.Plot(
                value=comparison_chart(),
                label="Income vs Expenses"
            )

        monthly_plot = gr.Plot(
            value=monthly_chart(),
            label="Monthly Financial Trend"
        )

        gr.Markdown("## Smart Saving Suggestions")

        suggestions_output = gr.Markdown(value=get_saving_suggestions())

    # --------------------------------------------------------
    # ADD TRANSACTION TAB
    # --------------------------------------------------------

    with gr.Tab("Add Transaction"):

        gr.Markdown("## Add a Financial Transaction")

        date_input = gr.Textbox(
            label="Transaction Date",
            value=datetime.now().strftime("%Y-%m-%d"),
            placeholder="YYYY-MM-DD"
        )

        type_input = gr.Radio(
            choices=["Income", "Expense"],
            value="Expense",
            label="Transaction Type"
        )

        # Starts with expense categories (because Expense is selected)
        category_input = gr.Dropdown(
            choices=EXPENSE_CATEGORIES,
            value=EXPENSE_CATEGORIES[0],
            label="Category"
        )

        description_input = gr.Textbox(
            label="Description",
            placeholder="Enter transaction details"
        )

        amount_input = gr.Number(label="Amount (₹)", minimum=0)

        add_button = gr.Button("Add Transaction", variant="primary")

        status_output = gr.Textbox(
            label="Transaction Status",
            interactive=False,
            lines=7
        )

    # --------------------------------------------------------
    # TRANSACTION HISTORY TAB
    # --------------------------------------------------------

    with gr.Tab("Transaction History"):

        gr.Markdown("## Financial Transaction Records")

        history_table = gr.Dataframe(
            value=get_transaction_history(),
            headers=COLUMNS,
            interactive=False,
            label="All Transactions"
        )

        history_refresh = gr.Button("Refresh Transaction History")

    # --------------------------------------------------------
    # SEARCH AND FILTER TAB
    # --------------------------------------------------------

    with gr.Tab("Search & Filter"):

        gr.Markdown("## Search Your Transactions")

        search_input = gr.Textbox(
            label="Search Description",
            placeholder="Example: Groceries, Shopping, Electricity"
        )

        with gr.Row():

            search_type = gr.Dropdown(
                choices=["All", "Income", "Expense"],
                value="All",
                label="Transaction Type"
            )

            search_category = gr.Dropdown(
                choices=["All"] + ALL_CATEGORIES,
                value="All",
                label="Category"
            )

        with gr.Row():

            start_date = gr.Textbox(label="Start Date", placeholder="YYYY-MM-DD")
            end_date = gr.Textbox(label="End Date", placeholder="YYYY-MM-DD")

        with gr.Row():

            search_button = gr.Button("Search Transactions", variant="primary")
            clear_button = gr.Button("Show All Transactions")

        search_summary = gr.Textbox(
            label="Search Summary",
            interactive=False,
            lines=6
        )

        search_results = gr.Dataframe(
            value=get_data(),
            headers=COLUMNS,
            interactive=False,
            label="Filtered Transactions"
        )

    # --------------------------------------------------------
    # EXPORT REPORTS TAB
    # --------------------------------------------------------

    with gr.Tab("Export Reports"):

        gr.Markdown("## Download Financial Reports")

        gr.Markdown("Download your transactions and financial summary.")

        with gr.Row():

            csv_button = gr.Button("Download CSV")
            excel_button = gr.Button("Download Excel", variant="primary")

        csv_file = gr.File(label="CSV Report")
        excel_file = gr.File(label="Excel Report")

    # ========================================================
    # BUTTON CONNECTIONS
    # ========================================================

    dashboard_outputs = [
        dashboard_cards,
        category_plot,
        comparison_plot,
        monthly_plot,
        suggestions_output,
        history_table
    ]

    # Switching Income/Expense changes the category list
    type_input.change(
        fn=update_category_choices,
        inputs=type_input,
        outputs=category_input
    )

    refresh_button.click(
        fn=refresh_dashboard,
        inputs=None,
        outputs=dashboard_outputs
    )

    add_button.click(
        fn=add_and_refresh,
        inputs=[
            date_input, type_input, category_input,
            description_input, amount_input
        ],
        outputs=[status_output] + dashboard_outputs
    )

    history_refresh.click(
        fn=get_transaction_history,
        inputs=None,
        outputs=history_table
    )

    search_button.click(
        fn=search_transactions,
        inputs=[
            search_input, search_type, search_category,
            start_date, end_date
        ],
        outputs=[search_results, search_summary]
    )

    clear_button.click(
        fn=clear_search,
        inputs=None,
        outputs=[
            search_input, search_type, search_category,
            start_date, end_date,
            search_results, search_summary
        ]
    )

    csv_button.click(fn=export_csv, inputs=None, outputs=csv_file)
    excel_button.click(fn=export_excel, inputs=None, outputs=excel_file)

    # Load the dashboard when the page opens
    app.load(
        fn=refresh_dashboard,
        inputs=None,
        outputs=dashboard_outputs
    )


# ============================================================
# LAUNCH
# ============================================================

print("FinTrack Pro is ready!")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))

    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False
    )

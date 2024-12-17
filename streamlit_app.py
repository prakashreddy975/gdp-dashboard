import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Define the file to store the budget data
DATA_FILE = 'daily_budget_data.csv'
SALARY_FILE = 'salary_data.csv'  # Separate file for salary records

# Fixed budget values for each category
CATEGORY_BUDGET = {
    'House Rent': 430,
    'Shopping': 100,
    'Groceries': 50,
    'Food': 50,
    'Transport': 20,
    'Entertainment': 100
}

# Fixed monthly income (initially)
MONTHLY_INCOME = 800

# Load existing data if available
def load_data(file=DATA_FILE):
    try:
        return pd.read_csv(file)
    except FileNotFoundError:
        return pd.DataFrame(columns=['Date', 'Category', 'Amount Spent', 'Budgeted Amount'])

# Load salary data, ensure 'Pay Date' column exists
def load_salary_data(file=SALARY_FILE):
    try:
        df = pd.read_csv(file)
        # Ensure 'Pay Date' column exists
        if 'Pay Date' not in df.columns:
            df['Pay Date'] = pd.to_datetime(df['End Date'])  # Create a 'Pay Date' if missing
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=['Start Date', 'End Date', 'Salary', 'Pay Date'])

# Save data to CSV file
def save_data(df, file=DATA_FILE):
    df.to_csv(file, index=False)

# Save salary data
def save_salary_data(df, file=SALARY_FILE):
    df.to_csv(file, index=False)

# Add an entry to the data
def add_entry(date, category, spent, budgeted):
    df = load_data()
    entry = pd.DataFrame([[date, category, spent, budgeted]], columns=df.columns)
    df = pd.concat([df, entry], ignore_index=True)
    save_data(df)

# Add salary entry with pay date
def add_salary(start_date, end_date, salary, pay_date):
    df = load_salary_data()
    entry = pd.DataFrame([[start_date, end_date, salary, pay_date]], columns=['Start Date', 'End Date', 'Salary', 'Pay Date'])
    df = pd.concat([df, entry], ignore_index=True)
    save_salary_data(df)

# Delete a selected entry (daily or salary)
def delete_confirmation(index, is_salary=False):
    if is_salary:
        salary_df = load_salary_data()
        salary_df = salary_df.drop(index).reset_index(drop=True)
        save_salary_data(salary_df)
        st.success("Salary entry deleted successfully!")
    else:
        df = load_data()
        df = df.drop(index).reset_index(drop=True)
        save_data(df)
        st.success("Entry deleted successfully!")

# Get the total salary for the month
def get_total_salary_for_month(month):
    salary_data = load_salary_data()
    salary_data['Start Date'] = pd.to_datetime(salary_data['Start Date'])
    salary_data['End Date'] = pd.to_datetime(salary_data['End Date'])
    
    monthly_salary_data = salary_data[salary_data['Start Date'].dt.strftime('%Y-%m') == month]
    return monthly_salary_data['Salary'].sum()

# Convert Pay Date to datetime, handling errors and specifying a format
def convert_to_datetime(df, column_name):
    # Try to convert to datetime with error handling and mixed format
    df[column_name] = pd.to_datetime(df[column_name], errors='coerce', format=None)  # Let pandas auto-format
    return df

# Set the page title
st.title('Daily Budget Tracker')

# Load data
df = load_data()

# Sidebar - Input Form for Daily Expenses
st.sidebar.header('Enter Daily Budget Data')

# Date picker for selecting the date
date = st.sidebar.date_input('Select Date', datetime.today())

# Category, amount spent, and budgeted
categories = list(CATEGORY_BUDGET.keys())
category = st.sidebar.selectbox('Select Category', categories)
spent = st.sidebar.number_input('Amount Spent', min_value=0, step=1)
budgeted = CATEGORY_BUDGET[category]  # Use fixed budget for the category

# Button to add an entry for daily spending
if st.sidebar.button('Add Entry'):
    date_str = date.strftime('%Y-%m-%d')  # Convert date to string in 'YYYY-MM-DD' format
    add_entry(date_str, category, spent, budgeted)
    st.sidebar.success(f'Entry for {category} on {date_str} added successfully!')

# Sidebar - Input Form for Salary Data
st.sidebar.header('Enter Bi-Weekly Salary Information')

# Date input for start and end date of salary period
start_date = st.sidebar.date_input('Salary Start Date')
end_date = st.sidebar.date_input('Salary End Date')

# Salary input
salary = st.sidebar.number_input('Salary Credit for this period', min_value=0, step=1)

# Pay date input (this is the date when the salary is credited)
pay_date = st.sidebar.date_input('Pay Date')

# Button to add a salary entry
if st.sidebar.button('Add Salary'):
    add_salary(start_date, end_date, salary, pay_date)
    st.sidebar.success(f'Salary for {start_date} to {end_date} added successfully with Pay Date {pay_date}!')

# Get all available months from both daily data and salary data
daily_months = sorted(df['Date'].str[:7].unique())  # Get unique months from daily budget
salary_data = load_salary_data()

# Ensure salary 'Pay Date' is converted to datetime
salary_data = convert_to_datetime(salary_data, 'Pay Date')

# Remove rows with invalid 'Pay Date' (NaT) after conversion
salary_data = salary_data[~salary_data['Pay Date'].isna()]

# Get unique months from salary data
salary_months = sorted(salary_data['Pay Date'].dt.strftime('%Y-%m').unique())

# Combine and deduplicate months from both datasets
available_months = sorted(set(daily_months + salary_months))

# Month filter for overview
st.sidebar.subheader("Select Month for Overview")
month_filter = st.sidebar.selectbox("Select Month", available_months, index=len(available_months) - 1)

# Display daily entries
st.header('Daily Expense Tracker')

# Show daily data for the selected month
selected_month_data = df[df['Date'].str.startswith(month_filter)]

if not selected_month_data.empty:
    st.write(selected_month_data)

    # Option to delete an entry
    delete_index = st.selectbox('Select an entry to delete', selected_month_data.index.tolist(), key="delete")
    if st.button('Delete Selected Entry'):
        delete_confirmation(delete_index)
else:
    st.write(f"No data available for {month_filter} yet.")

# Monthly budget overview for selected month
st.subheader(f'Monthly Overview for {month_filter}')
monthly_data = selected_month_data

# Calculate totals for each category in the selected month
if not monthly_data.empty:
    total_spent_by_category = monthly_data.groupby('Category')['Amount Spent'].sum()
    total_spent = total_spent_by_category.sum()
    total_budgeted = monthly_data.groupby('Category')['Budgeted Amount'].sum().sum()
    remaining_budget = MONTHLY_INCOME - total_spent
    remaining_savings = MONTHLY_INCOME - total_spent

    # Display total spent, budget, and remaining savings
    st.write(f"Total Amount Spent: ${total_spent}")
    st.write(f"Total Budgeted Amount: ${total_budgeted}")
    st.write(f"Remaining Budget: ${remaining_budget}")
    st.write(f"Remaining Savings: ${remaining_savings}")

    # Optional: Bar chart for spending distribution in the selected month
    st.bar_chart(total_spent_by_category)

# Get total salary for the selected month and add it to the monthly income
total_salary_for_month = get_total_salary_for_month(month_filter)
total_monthly_income = MONTHLY_INCOME + total_salary_for_month

st.subheader(f'Total Salary for {month_filter}: ${total_salary_for_month}')
st.write(f"Total Monthly Income (Including Salary): ${total_monthly_income}")

# Show salary data for the selected month
st.subheader(f'Salary Data for {month_filter}')
salary_for_month = salary_data[salary_data['Pay Date'].dt.strftime('%Y-%m') == month_filter]

if not salary_for_month.empty:
    st.write(salary_for_month)

    # Option to delete a salary entry
    delete_salary_index = st.selectbox('Select a salary entry to delete', salary_for_month.index.tolist(), key="delete_salary")
    if st.button('Delete Selected Salary Entry'):
        delete_confirmation(delete_salary_index, is_salary=True)
else:
    st.write(f"No salary data available for {month_filter}.")

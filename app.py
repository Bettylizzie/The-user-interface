import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt  
import numpy as np
import hashlib
import os
import mysql.connector
from fpdf import FPDF

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Database connection setup
def create_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Adjust as per your MySQL credentials
        password="root",  # Adjust as per your MySQL credentials
        database="inventory_db"  # Your MySQL database name
    )

# Function for user login
def login_page():
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", key="login_button"):
        connection = create_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and hash_password(password) == user['password_hash']:
            st.success(f"Welcome {username}!")
            st.session_state['logged_in'] = True
            st.session_state['current_user'] = username

            try:
                cursor.execute("SELECT * FROM datasets WHERE username = %s", (username,))
                dataset = cursor.fetchone()

                if dataset:
                    st.session_state['data'] = pd.read_json(dataset['data'])
                    st.success("Loaded your previously uploaded dataset from the database.")
                else:
                    st.warning("No dataset found. Please upload your data.")
                    st.session_state['data'] = None  # Placeholder if no dataset in DB
            except Exception as e:
                st.warning("")
                st.session_state['data'] = None

        else:
            st.error("Incorrect username or password.")
        connection.close()

# Function for user signup
def signup_page():
    st.subheader("Sign Up")
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Sign Up", key="signup_button"):
        if new_password != confirm_password:
            st.error("Passwords do not match.")
        else:
            connection = create_connection()
            cursor = connection.cursor()

            cursor.execute("SELECT * FROM users WHERE username = %s", (new_username,))
            if cursor.fetchone():
                st.error("Username already taken. Please choose another.")
            else:
                hashed_password = hash_password(new_password)
                cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", 
                               (new_username, hashed_password))
                connection.commit()
                st.success("Account created successfully! Please [log in](#).", unsafe_allow_html=True)

            connection.close()

# Function to fetch data from the database
def fetch_data_from_db():
    conn = create_connection()
    query = "SELECT * FROM inventory_data"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Dataset upload and persistence
def upload_dataset_page():
    st.title("Upload Your Dataset")
    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

    if uploaded_file is not None:
        data = pd.read_excel(uploaded_file)
        st.session_state['data'] = data
        st.success("Data loaded successfully from uploaded file!")
        st.dataframe(data)

        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO datasets (username, data) VALUES (%s, %s) ON DUPLICATE KEY UPDATE data=%s", 
            (st.session_state['current_user'], data.to_json(), data.to_json())
        )
        connection.commit()
        connection.close()
    else:
        st.warning("Please upload an Excel file if the database is not available.")

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Main app flow
if st.session_state['logged_in']:
    st.write(f"Welcome, {st.session_state['current_user']}!")

    if st.button("Logout"):
        st.session_state.clear()
        st.experimental_rerun()  # Refresh the app

else:
    page_choice = st.selectbox("Choose a page", ["Login", "Sign Up"])
    if page_choice == "Login":
        login_page()
    else:
        signup_page()

# Check if user is logged in
if st.session_state['logged_in']:
    st.sidebar.title("Navigation")
    options = st.sidebar.radio("Select a page:", (  
        "Upload Dataset",  
        "Dashboard",  
        "Inventory Monitoring",  
        "Sales Trends Analysis",  
        "User Settings",  
        "Reporting"  
    ))  

    if options == "Upload Dataset":
        upload_dataset_page()

    # Fetch data from session state or database
    if 'data' not in st.session_state or st.session_state['data'] is None:
        try:
            st.session_state['data'] = fetch_data_from_db()
            st.success("The data was loaded successfully from the database!")
        except Exception as e:
            st.warning("Unable to fetch data from the database. Please upload your dataset.")

    # Use the unified st.session_state['data'] for all pages
    if 'data' in st.session_state and st.session_state['data'] is not None:
        data = st.session_state['data']

    # Custom Styles for Blue Menubar
    st.markdown("""
        <style>
            .blue-menubar {
                background-color: #007bff;
                padding: 10px;
                font-size: 24px;
                font-weight: bold;
                color: white;
                text-align: center;
            }
            .dashboard-stat {
                background-color: #f9f9f9;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                margin: 10px 0;
                font-size: 18px;
            }
            .notification {
                color: red;
            }
            .button-style {
                background-color: #28a745;
                color: white;
                padding: 10px;
                border: None;
                border-radius: 5px;
                cursor: pointer;
            }
            .button-style:hover {
                background-color: #218838;
            }
        </style>
    """, unsafe_allow_html=True)

    # Dashboard Overview Page  
    if options == "Dashboard":  
        st.markdown('<div class="blue-menubar">Dashboard</div>', unsafe_allow_html=True)

        # Greeting message
        st.write(f"Hi {st.session_state['current_user']}, here's the latest analysis of your inventory and sales.")

        # Alerts & Notifications
        st.subheader("Alerts & Notifications")

        # Filter products with low stock
        low_stock_products = data[data['Stock levels'] < data['Reorder Levels']]

        if not low_stock_products.empty:
            # Group by 'Product Sold' and sum stock levels and reorder levels
            grouped_low_stock = low_stock_products.groupby('Product Sold').agg(
                Total_Current_Stock=('Stock levels', 'sum'),
                Total_Reorder_Level=('Reorder Levels', 'sum')
            ).reset_index()

            st.markdown('<p class="notification">⚠ Low stock for the following products:</p>', unsafe_allow_html=True)
            for index, row in grouped_low_stock.iterrows():
                st.markdown(f"- **{row['Product Sold']}**: Total Current Stock = {row['Total_Current_Stock']}, Total Reorder Level = {row['Total_Reorder_Level']}")
        else:
            st.success("No alerts currently. All stock levels are sufficient!")


        # Dashboard Statistics
        st.subheader("Dashboard Statistics")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="dashboard-stat"><h4>Total Products</h4><p>{}</p></div>'.format(data['Product Sold'].nunique()), unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="dashboard-stat"><h4>Pending Reorders</h4><p>{}</p></div>'.format(data[data['Stock levels'] <= data['Reorder Levels']].shape[0]), unsafe_allow_html=True)

        # Charts for sales trends, predicted sales, product PEI, and current stock levels
        st.subheader("Sales Trends")
        sales_data = data.groupby('Month')['Total Revenue'].sum().reset_index()
        st.line_chart(sales_data.set_index('Month'))

        #Predicted Sales from the dataset
        st.subheader("Predicted Sales")

        # Define the correct order of months
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                    'July', 'August', 'September', 'October', 'November', 'December']

        # Ensure 'Predicted Sales' column exists and remove NaN values
        predicted_sales = data[['Month', 'Predicted Sales']].dropna()

        # Group by 'Month' and calculate the mean of 'Predicted Sales', then reindex by month order
        predicted_sales = predicted_sales.groupby('Month')['Predicted Sales'].mean().reindex(month_order)

        # Plot the predicted sales as a line chart
        st.line_chart(predicted_sales)

        # Profit per Product (Product PEI)
        st.subheader("Profit per Product")
        product_pei = data.groupby('Product Sold')['Profit'].mean().reset_index()
        st.bar_chart(product_pei.set_index('Product Sold'))

        # Current Stock Levels
        st.subheader("Current Stock Levels")
        st.bar_chart(data[['Product Sold', 'Stock levels']].set_index('Product Sold'))

    # Inventory Monitoring and Management Page  
    elif options == "Inventory Monitoring":  
        st.title("📦 Inventory Monitoring")  
        st.write("Monitor and manage your inventory here.")


        # Filters for inventory view
        product_filter = st.selectbox("Filter by Product:", ['All'] + list(data['Product Sold'].unique()))
        location_filter = st.selectbox("Filter by Location:", ['All'] + list(data['Location'].unique()))
        reorder_filter = st.checkbox("Show only products below reorder level")

        # Apply filters independently
        filtered_data = data
        if product_filter != 'All':
            filtered_data = filtered_data[filtered_data['Product Sold'] == product_filter]
        if location_filter != 'All':
            filtered_data = filtered_data[filtered_data['Location'] == location_filter]

        # Show filtered inventory
        st.dataframe(filtered_data[['Product Sold', 'Location', 'Stock levels', 'Reorder Levels']])

        # Reorder Alerts
        st.subheader("⚠ Reorder Alerts")
        if reorder_filter:
            st.warning("The following products need restocking:")
            low_stock = filtered_data[filtered_data['Stock levels'] <= filtered_data['Reorder Levels']]
            st.dataframe(low_stock[['Product Sold','Location','Stock levels', 'Reorder Levels']])


    # Sales Trends Analysis Page
    elif options == "Sales Trends Analysis":
        st.title("📈 Sales Trends Analysis")
        st.write("Analyze your sales data over time.")

        # Monthly Sales Overview
        monthly_sales = data.groupby('Month')['Total Revenue'].sum().reset_index()
        st.bar_chart(monthly_sales.set_index('Month'))

        # Sales Growth Rate
        st.subheader("Sales Growth Rate")
        sales_growth = data.groupby('Month')['Sales Growth Rate'].mean().reset_index()
        st.line_chart(sales_growth.set_index('Month'))

        # Customer Segment Revenue Analysis
        st.subheader("Revenue by Customer Segment")
        
        # Aggregate data for customer segments
        customer_segment_data = data.groupby(['Customer Segment', 'Month']).agg({'Total Revenue': 'sum'}).reset_index()

        # Create a pivot table for stacked bar chart
        pivot_revenue = customer_segment_data.pivot(index='Month', columns='Customer Segment', values='Total Revenue').fillna(0)

        # Stacked bar chart for revenue by customer segment
        st.bar_chart(pivot_revenue)

        # Purchase Frequency Analysis
        st.subheader("Purchase Frequency by Customer Segment")
        
        # Aggregate purchase frequency data
        purchase_frequency_data = data.groupby(['Customer Segment', 'Month']).agg({'Purchase Frequency(Monthly)': 'sum'}).reset_index()

        # Create a pivot table for purchase frequency
        pivot_frequency = purchase_frequency_data.pivot(index='Month', columns='Customer Segment', values='Purchase Frequency(Monthly)').fillna(0)

        # Stacked bar chart for purchase frequency by customer segment
        st.bar_chart(pivot_frequency)


    # User Settings Page
    elif options == "User Settings":
        st.title("⚙ User Settings")
        st.write("Manage user-specific settings and thresholds here.")

        # Stock threshold adjustment
        new_reorder_level = st.number_input("Set new reorder threshold level:", min_value=1)
        if st.button("Update Reorder Level"):
            data['Reorder Levels'] = new_reorder_level
            st.success(f"Reorder level updated to {new_reorder_level} for all products")

        # Manage product categories
        st.write("### Manage Product Categories")
        categories = st.text_input("Enter product categories (comma-separated):")
        if st.button("Save Categories"):
            if categories:
                # Save categories to a persistent location in the 'data' folder
                with open("data/categories.txt", "w") as f:
                    f.write(categories)
                st.success("Product categories saved successfully.")
            else:
                st.error("Please enter valid categories.")

        # Add new product to stock
        st.write("### Add New Product")
        product_name = st.text_input("Product Name:")
        quantity = st.number_input("Quantity:", min_value=1)
        price = st.number_input("Price per Product:", min_value=0.0)
        
        if st.button("Add Product"):
            if product_name and quantity > 0 and price >= 0:
                new_product = {
                    "Product Sold": product_name,
                    "quantity sold": quantity,
                    "Total Revenue": quantity * price,
                    "Location": "Default Location"  # or any default you want
                }
                # Append new product to data
                data = pd.concat([data, pd.DataFrame([new_product])], ignore_index=True)
                st.success(f"Product '{product_name}' added successfully.")
            else:
                st.error("Please fill in all fields correctly.")

            # Save updated data to a persistent location in the 'data' folder
            data.to_csv("data/inventory_data.csv", index=False)  # Update to use the 'data' folder
            

    # Reporting Page
    if options == "Reporting":
        st.title("📑 Reporting")

        # Filters with "All" option
        all_months = ['All'] + list(data['Month'].unique())
        all_seasons = ['All'] + list(data['Season'].unique())
        all_locations = ['All'] + list(data['Location'].unique())

        selected_month = st.selectbox("Select Month", all_months)
        selected_season = st.selectbox("Select Season", all_seasons)
        selected_location = st.selectbox("Select Location", all_locations)

        # Generate reports
        st.write("### Generate Sales Report")
        report_type = st.selectbox("Select Report Type", ["Monthly", "Seasonal", "Yearly", "Inventory Performance"])

        if st.button("Generate Report"):
            # Filter data based on selected criteria
            filtered_data = data.copy()

            if selected_month != 'All':
                filtered_data = filtered_data[filtered_data['Month'] == selected_month]
            if selected_season != 'All':
                filtered_data = filtered_data[filtered_data['Season'] == selected_season]
            if selected_location != 'All':
                filtered_data = filtered_data[filtered_data['Location'] == selected_location]

            # Ensure there's data to work with
            if filtered_data.empty:
                st.warning("No data available for the selected filters.")
            else:
                if report_type == "Monthly":
                    sales_summary = filtered_data.groupby(['Month', 'Location']).agg({
                        'Total Revenue': 'sum',
                        'quantity sold': 'sum',
                        'Product Sold': 'count'
                    }).reset_index()

                    # Visualize monthly sales
                    plt.figure(figsize=(10, 5))
                    plt.bar(sales_summary['Month'], sales_summary['Total Revenue'], color='blue')
                    plt.title('Monthly Sales Revenue')
                    plt.xlabel('Month')
                    plt.ylabel('Total Revenue')
                    st.pyplot(plt)

                elif report_type == "Seasonal":
                    sales_summary = filtered_data.groupby(['Season', 'Location']).agg({
                        'Total Revenue': 'sum',
                        'quantity sold': 'sum',
                        'Product Sold': 'count'
                    }).reset_index()

                    # Visualize seasonal sales
                    plt.figure(figsize=(10, 5))
                    plt.bar(sales_summary['Season'], sales_summary['Total Revenue'], color='green')
                    plt.title('Seasonal Sales Revenue')
                    plt.xlabel('Season')
                    plt.ylabel('Total Revenue')
                    st.pyplot(plt)

                elif report_type == "Yearly":
                    st.write("### 📅 Yearly Sales Report")
                    total_revenue_2023 = filtered_data[filtered_data['Date Sold'].dt.year == 2023]['Total Revenue'].sum()
                    total_revenue_2024 = total_revenue_2023 * 1.1  # Simulate 10% growth for the next year
                    sales_summary = pd.DataFrame({
                        'Year': [2023, 2024],
                        'Total Revenue': [total_revenue_2023, total_revenue_2024]
                    })

                    # Visualize yearly sales
                    plt.figure(figsize=(10, 5))
                    plt.bar(sales_summary['Year'], sales_summary['Total Revenue'], color='orange')
                    plt.title('Yearly Sales Revenue')
                    plt.xlabel('Year')
                    plt.ylabel('Total Revenue')
                    st.pyplot(plt)

                elif report_type == "Inventory Performance":
                    sales_summary = filtered_data.groupby(['Product Sold']).agg({
                        'quantity sold': 'sum',
                        'Total Revenue': 'sum'
                    }).reset_index()

                    # Visualize inventory performance
                    plt.figure(figsize=(10, 5))
                    plt.bar(sales_summary['Product Sold'], sales_summary['Total Revenue'], color='purple')
                    plt.title('Inventory Performance')
                    plt.xlabel('Product Sold')
                    plt.ylabel('Total Revenue')
                    st.pyplot(plt)

                # Sort the report by 'Total Revenue' in descending order
                sales_summary = sales_summary.sort_values(by='Total Revenue', ascending=False)

                # Display the report
                st.dataframe(sales_summary)

                # CSV download
                csv_data = sales_summary.to_csv(index=False).encode('utf-8')
                st.download_button("Download Report as CSV", data=csv_data, file_name=f"{report_type}_sales_report.csv", mime='text/csv')

                # Download as PDF
                if st.button("Download Report as PDF"):
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)

                    # Add title
                    pdf.cell(200, 10, txt=f"{report_type} Sales Report", ln=True, align='C')

                    # Add table headers
                    for col in sales_summary.columns:
                        pdf.cell(40, 10, col, 1)
                    pdf.ln()

                    # Add table data
                    for i in range(len(sales_summary)):
                        for col in sales_summary.columns:
                            pdf.cell(40, 10, str(sales_summary[col].iloc[i]), 1)
                        pdf.ln()

                    pdf_file_path = f"{report_type}_sales_report.pdf"
                    pdf.output(pdf_file_path)

                    with open(pdf_file_path, "rb") as f:
                        st.download_button(
                            label="Download Report as PDF",
                            data=f,
                            file_name=pdf_file_path,
                            mime='application/pdf'
                        )    

                # Real-time Recommendations
                st.write("### Recommendations")
                st.info("To balance product performance:")
                st.write("- Analyze sales trends to identify high-performing product categories.")
                st.write("- Allocate marketing resources accordingly to boost sales for underperforming categories.")
                st.write("- Regularly review inventory to avoid overstocking products with low demand.")

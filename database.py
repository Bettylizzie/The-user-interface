import pandas as pd
import mysql.connector
import streamlit as st

# Function to insert CSV data into the MySQL table
def insert_data_from_csv(df):
    # Connect to MySQL
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",  
        database="inventory_db"
    )
    cursor = conn.cursor()

    # Function to insert data into the table
    def insert_data(row):
        sql = """INSERT INTO inventory_data (
            Transaction_ID, Date_Sold, Product_ID, customer_id, Gender, Age, Product_Sold, quantity_sold, price_per_product,
            Unit_Cost, Total_Cost, Total_Revenue, Profit, Availability, Stock_levels, Reorder_Levels, Order_quantities, 
            Location, Restock_Date, Restock_Quantity, invoice_no, payment_method, invoice_date, Purchase_Frequency_Monthly, 
            Season, Month, Restock_Needed, previous_sales, sales_moving_avg, Days_Since_Last_Restock, Sales_Growth_Rate, 
            Lead_Time, Promotion_Flag, Customer_Segment, Holiday_Season_Flag, Predicted_Sales, Current_Stock, 
            Trained_M_Restock_Quantity
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        data = (
            row['Transaction ID'], row['Date Sold'], row['Product ID'], row['customer_id'], row['Gender'], row['Age'], 
            row['Product Sold'], row['quantity sold'], row['price per product'], row['Unit Cost'], row['Total_Cost'], 
            row['Total Revenue'], row['Profit'], row['Availability'], row['Stock levels'], row['Reorder Levels'], 
            row['Order quantities'], row['Location'], row['Restock Date'], row['Restock Quantity'], row['invoice_no'], 
            row['payment_method'], row['invoice_date'], row['Purchase Frequency(Monthly)'], row['Season'], row['Month'], 
            row['Restock Needed'], row['previous_sales'], row['sales_moving_avg'], row['Days Since Last Restock'], 
            row['Sales Growth Rate'], row['Lead Time'], row['Promotion Flag'], row['Customer Segment'], 
            row['Holiday Season Flag'], row['Predicted Sales'], row['Current Stock'], row['Trained M.Restock Quantity']
        )
        cursor.execute(sql, data)

    # Insert each row from the CSV into the MySQL table
    for index, row in df.iterrows():
        insert_data(row)

    conn.commit()
    cursor.close()
    conn.close()
    st.success("CSV data has been successfully added to the database.")

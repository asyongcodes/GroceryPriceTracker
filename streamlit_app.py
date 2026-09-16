import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import json
import os

# Securely grab the API key from Streamlit's Cloud Secrets
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("API Key missing! Please add GEMINI_API_KEY to your Streamlit Secrets.")
    st.stop()

# Initialize the Gemini Client using the secret key
client = genai.Client(api_key=api_key)

DB_FILE = "grocery_history.csv"

# Load or initialize database
if os.path.exists(DB_FILE):
    df_history = pd.read_csv(DB_FILE)
else:
    df_history = pd.DataFrame(columns=["Date", "Item", "Quantity", "Price"])

# Define the structure for Structured Outputs
class GroceryItem(BaseModel):
    Item: str = Field(description="The clean name of the grocery item")
    Quantity: int = Field(description="The quantity bought, default to 1 if not clear")
    Price: float = Field(description="The total price paid for this item")

class ReceiptData(BaseModel):
    items: list[GroceryItem]

st.title("🛒 Smart Grocery Tracker & Price Comparator")

tab1, tab2 = st.tabs(["Scan New Receipt", "History & Price Comparison"])

with tab1:
    st.header("Upload Receipt")
    uploaded_file = st.file_uploader("Choose a receipt image...", type=["jpg", "jpeg", "png"])
    purchase_date = st.date_input("Date of purchase")

    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Receipt", use_container_width=True)
        
        # 1. FIXED: We use the button to control the parsing logic cleanly
        if st.button("Extract & Save Items"):
            with st.spinner("Gemini is reading your receipt..."):
                bytes_data = uploaded_file.getvalue()
                
                # Prompt Gemini to extract details
                prompt = "Analyze this grocery receipt image. Extract all items purchased including item name, quantity, and total price paid."
                
                try:
                    # 2. FIXED: Use config to enforce native JSON object matching our Pydantic schema
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[
                            types.Part.from_bytes(data=bytes_data, mime_type=uploaded_file.type),
                            prompt
                        ],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=ReceiptData,
                        ),
                    )
                    
                    # 3. Parse structured schema output
                    result_json = json.loads(response.text)
                    items_list = result_json.get("items", [])
                    
                    if items_list:
                        new_records = pd.DataFrame(items_list)
                        new_records["Date"] = str(purchase_date)
                        
                        # Consolidate and save
                        df_history = pd.concat([df_history, new_records], ignore_index=True)
                        df_history.to_csv(DB_FILE, index=False)
                        
                        st.success(f"Successfully added {len(new_records)} items to history!")
                        st.dataframe(new_records)
                        
                        # Rerun app state to update the history tab seamlessly
                        st.rerun()
                    else:
                        st.warning("No items were found on the receipt text.")
                        
                except Exception as e:
                    st.error(f"Failed to parse receipt data: {e}")
                    if 'response' in locals() and response.text:
                        st.text(response.text)

with tab2:
    st.header("Analyze Past Groceries")
    if not df_history.empty:
        # Search & Filter
        search_item = st.text_input("Search for a specific item to compare prices (e.g., Milk):")
        
        if search_item:
            filtered_df = df_history[df_history['Item'].str.contains(search_item, case=False, na=False)]
            if not filtered_df.empty:
                st.write(f"Price history for '{search_item}':")
                # Plot price over time
                fig = px.line(filtered_df, x="Date", y="Price", text="Quantity", title=f"Price Trend: {search_item}")
                st.plotly_chart(fig)
                st.dataframe(filtered_df)
            else:
                st.warning("No historical match found for that item.")
        
        st.subheader("All Consolidated Groceries")
        st.dataframe(df_history.sort_values(by="Date", ascending=False))
    else:
        st.info("No data logged yet. Upload your first receipt in the other tab!")
        

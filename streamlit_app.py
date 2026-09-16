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

# Load or initialize database with the Store column
if os.path.exists(DB_FILE):
    df_history = pd.read_csv(DB_FILE)
    if "Store" not in df_history.columns:
        df_history["Store"] = "Unknown"
else:
    df_history = pd.DataFrame(columns=["Date", "Store", "Item", "Quantity", "Price"])

# Define the structure for Structured Outputs
class GroceryItem(BaseModel):
    Item: str = Field(description="The clean name of the grocery item")
    Quantity: int = Field(description="The quantity bought, default to 1 if not clear")
    Price: float = Field(description="The total price paid for this item")

class ReceiptData(BaseModel):
    store_name: str = Field(description="The name of the store or supermarket from the receipt header, or leave empty if not found")
    items: list[GroceryItem]

st.title("🛒 Smart Grocery Tracker & Price Comparator")

tab1, tab2 = st.tabs(["Scan New Receipt", "History & Price Comparison"])

with tab1:
    st.header("Upload Receipt")
    uploaded_file = st.file_uploader("Choose a receipt image...", type=["jpg", "jpeg", "png"])
    
    # Organize entry selectors cleanly using layout columns
    col1, col2 = st.columns(2)
    with col1:
        purchase_date = st.date_input("Date of purchase")
    with col2:
        # ADDED: Checkbox toggle for manual entry selection
        manual_store_toggle = st.checkbox("Manually enter/select store name")
        
        final_manual_store = ""
        if manual_store_toggle:
            # Get sorted unique list of previously saved stores from history
            existing_stores = sorted(df_history["Store"].dropna().unique().tolist())
            if "Unknown" in existing_stores:
                existing_stores.remove("Unknown")
            
            # Create dropdown options array with custom addition choice at index 0
            dropdown_options = ["➕ Add New Store..."] + existing_stores
            
            selected_option = st.selectbox("Select Store", options=dropdown_options)
            
            # If they choose to type a new store, show a text field
            if selected_option == "➕ Add New Store...":
                new_store_input = st.text_input("Type New Store Name", placeholder="e.g., Walmart, Costco")
                final_manual_store = new_store_input.strip()
            else:
                final_manual_store = selected_option

    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Receipt", use_container_width=True)
        
        if st.button("Extract & Save Items"):
            # Validation logic checking manual option requirements
            if manual_store_toggle and not final_manual_store:
                st.error("Please select an existing store or type a new store name before scanning.")
            else:
                with st.spinner("Gemini is reading your receipt..."):
                    bytes_data = uploaded_file.getvalue()
                    
                    prompt = "Analyze this grocery receipt image. Extract all items purchased including item name, quantity, and total price paid."
                    if not manual_store_toggle:
                        prompt += " Also extract the name of the store from the header."
                    
                    try:
                        response = client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=[
                                types.Part.from_bytes(data=bytes_data, mime_type=uploaded_file.type),
                                prompt
                            ],
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                response_schema=ReceiptData,
                            ),
                        )
                        
                        result_json = json.loads(response.text)
                        items_list = result_json.get("items", [])
                        
                        # Use manual selection or let Gemini figure it out
                        if manual_store_toggle:
                            final_store = final_manual_store
                        else:
                            final_store = result_json.get("store_name", "Unknown Store")
                        
                        if items_list:
                            new_records = pd.DataFrame(items_list)
                            new_records["Date"] = str(purchase_date)
                            new_records["Store"] = final_store
                            
                            new_records = new_records[["Date", "Store", "Item", "Quantity", "Price"]]
                            
                            df_history = pd.concat([df_history, new_records], ignore_index=True)
                            df_history.to_csv(DB_FILE, index=False)
                            
                            st.success(f"Successfully added {len(new_records)} items from **{final_store}** to history!")
                            st.dataframe(new_records)
                            
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
        search_item = st.text_input("Search for a specific item to compare prices (e.g., Milk):")
        
        if search_item:
            filtered_df = df_history[df_history['Item'].str.contains(search_item, case=False, na=False)]
            if not filtered_df.empty:
                st.write(f"Price history for '{search_item}':")
                fig = px.line(
                    filtered_df, 
                    x="Date", 
                    y="Price", 
                    color="Store", 
                    text="Quantity", 
                    title=f"Price Trend by Store: {search_item}"
                )
                st.plotly_chart(fig)
                st.dataframe(filtered_df)
            else:
                st.warning("No historical match found for that item.")
        
        st.subheader("All Consolidated Groceries")
        st.dataframe(df_history.sort_values(by="Date", ascending=False))
    else:
        st.info("No data logged yet. Upload your first receipt in the other tab!")
        

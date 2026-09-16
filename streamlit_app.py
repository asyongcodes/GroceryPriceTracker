import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from google.genai import types
import json
import os

st.set_page_config(page_title="SCOTTY Grocery Tracker", page_icon="🛒")

# Securely grab the API key from Streamlit's Cloud Secrets
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("API Key missing! Please add GEMINI_API_KEY to your Streamlit Secrets.")
    st.stop()

# Initialize the Gemini Client using the secret key
client = genai.Client(api_key=api_key)

DB_FILE = "grocery_history.csv"

# Persistent storage check for local app run state 
if "df_history" not in st.session_state:
    if os.path.exists(DB_FILE):
        st.session_state.df_history = pd.read_csv(DB_FILE)
    else:
        st.session_state.df_history = pd.DataFrame(columns=["Date", "Item", "Quantity", "Price"])

st.title("🛒 SCOTTY Grocery Tracker")

tab1, tab2 = st.tabs(["📸 Scan New Receipt", "📊 History & Pricing"])

with tab1:
    st.header("Upload Receipt")
    
    # Using st.file_uploader opens your mobile camera or photo gallery
    uploaded_file = st.file_uploader("Take a photo or choose a receipt file...", type=["jpg", "jpeg", "png"])
    purchase_date = st.date_input("Date of purchase")

    if uploaded_file is not None:
        st.success("✅ File loaded successfully!")
        
        # Display the image safely for mobile browsers without container width constraints
        st.image(uploaded_file, caption="Uploaded Receipt")
        
        if st.button("🚀 Process & Extract Items", use_container_width=True):
            with st.spinner("Gemini is analyzing your receipt photo now..."):
                try:
                    # Extract the raw file bytes correctly for processing
                    bytes_data = uploaded_file.getvalue()
                    
                    prompt = """
                    Analyze this grocery receipt image. Extract all items purchased. 
                    For each item, identify the item name, quantity, and total price paid.
                    Return the data strictly as a JSON array of objects with the keys: 
                    "Item", "Quantity", "Price". Do not include markdown formatting tags or any extra text.
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[
                            types.Part.from_bytes(data=bytes_data, mime_type=uploaded_file.type),
                            prompt
                        ]
                    )
                    
                    # Parse extracted text to JSON safely
                    cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
                    items = json.loads(cleaned_text)
                    
                    new_records = pd.DataFrame(items)
                    new_records["Date"] = str(purchase_date)
                    
                    # Consolidate into active session state
                    st.session_state.df_history = pd.concat([st.session_state.df_history, new_records], ignore_index=True)
                    
                    # Attempt a local save backup
                    st.session_state.df_history.to_csv(DB_FILE, index=False)
                    
                    st.balloons()
                    st.success(f"Successfully added {len(new_records)} items to history!")
                    st.dataframe(new_records)
                    
                except json.JSONDecodeError:
                    st.error("Failed to parse receipt data. Gemini returned raw text instead of clean database entries.")
                    st.text("Raw Response from AI:")
                    st.code(response.text)
                except Exception as e:
                    st.error(f"An unexpected tracking error occurred: {e}")

with tab2:
    st.header("Analyze Past Groceries")
    df_active = st.session_state.df_history
    
    if not df_active.empty:
        search_item = st.text_input("Search for a specific item to compare prices (e.g., Milk):")
        
        if search_item:
            filtered_df = df_active[df_active['Item'].str.contains(search_item, case=False, na=False)]
            if not filtered_df.empty:
                st.write(f"Price history for '{search_item}':")
                fig = px.line(filtered_df, x="Date", y="Price", text="Quantity", title=f"Price Trend: {search_item}")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(filtered_df)
            else:
                st.warning("No historical match found for that item.")
        
        st.subheader("All Consolidated Groceries")
        st.dataframe(df_active.sort_values(by="Date", ascending=False))
    else:
        st.info("No data logged yet. Upload your first receipt in the other tab!")
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[
                            types.Part.from_bytes(data=bytes_data, mime_type=uploaded_file.type),
                            prompt
                        ]
                    )
                    
                    # Parse extracted text to JSON
                    cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
                    items = json.loads(cleaned_text)
                    
                    new_records = pd.DataFrame(items)
                    new_records["Date"] = str(purchase_date)
                    
                    # Consolidate into active session state
                    st.session_state.df_history = pd.concat([st.session_state.df_history, new_records], ignore_index=True)
                    
                    # Attempt a local save backup
                    st.session_state.df_history.to_csv(DB_FILE, index=False)
                    
                    st.balloons()
                    st.success(f"Successfully added {len(new_records)} items to history!")
                    st.dataframe(new_records)
                    
                except json.JSONDecodeError:
                    st.error("Failed to parse receipt data. Gemini returned raw text instead of clean database entries.")
                    st.text("Raw Response from AI:")
                    st.code(response.text)
                except Exception as e:
                    st.error(f"An unexpected tracking error occurred: {e}")

with tab2:
    st.header("Analyze Past Groceries")
    df_active = st.session_state.df_history
    
    if not df_active.empty:
        search_item = st.text_input("Search for a specific item to compare prices (e.g., Milk):")
        
        if search_item:
            filtered_df = df_active[df_active['Item'].str.contains(search_item, case=False, na=False)]
            if not filtered_df.empty:
                st.write(f"Price history for '{search_item}':")
                fig = px.line(filtered_df, x="Date", y="Price", text="Quantity", title=f"Price Trend: {search_item}")
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(filtered_df)
            else:
                st.warning("No historical match found for that item.")
        
        st.subheader("All Consolidated Groceries")
        st.dataframe(df_active.sort_values(by="Date", ascending=False))
    else:
        st.info("No data logged yet. Upload your first receipt in the other tab!")
        st.image(uploaded_file, caption="Uploaded Receipt", use_container_width=True)
        
        if st.button("Extract & Save Items"):
            with st.spinner("Gemini is reading your receipt..."):
                bytes_data = uploaded_file.getvalue()
                
                # Prompt Gemini to return clean, structured data
                prompt = """
                Analyze this grocery receipt image. Extract all items purchased. 
                For each item, identify the item name, quantity, and total price paid.
                Return the data strictly as a JSON array of objects with the keys: 
                "Item", "Quantity", "Price". Do not include markdown formatting tags.
                """
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[
                        types.Part.from_bytes(data=bytes_data, mime_type=uploaded_file.type),
                        prompt
                    ]
                )
                
                try:
                    # Parse extracted text to JSON and save to database
                    items = json.loads(response.text)
                    new_records = pd.DataFrame(items)
                    new_records["Date"] = str(purchase_date)
                    
                    # Consolidate and save
                    df_history = pd.concat([df_history, new_records], ignore_index=True)
                    df_history.to_csv(DB_FILE, index=False)
                    
                    st.success(f"Successfully added {len(new_records)} items to history!")
                    st.dataframe(new_records)
                except Exception as e:
                    st.error("Failed to parse receipt data. Please check the API response.")
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
      

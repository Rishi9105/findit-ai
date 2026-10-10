
import streamlit as st
import sqlite3
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
st.set_page_config(page_title="FindIt AI ", page_icon="🔎")
st.title("🔎 FindIt AI ")
st.caption("AI-powered campus lost and found assistant using Gemma 4")

db = sqlite3.connect("lost_found.db", check_same_thread=False)
db.execute("""CREATE TABLE IF NOT EXISTS items
(id INTEGER PRIMARY KEY, kind TEXT, name TEXT, location TEXT, details TEXT)""")

with st.sidebar:
    st.header("📝 Report an Item")
    kind = st.selectbox("Report type", ["Found", "Lost"])
    name = st.text_input("Item name", placeholder="Black wallet")
    location = st.text_input("Campus location", placeholder="Library")
    details = st.text_area("Description")
    if st.button("Submit Report"):
        if name and location:
            db.execute("INSERT INTO items(kind,name,location,details) VALUES(?,?,?,?)",
                       (kind, name, location, details))
            db.commit()
            st.success("Report saved!")
        else:
            st.warning("Enter item name and location.")

st.subheader("🤖 Gemma 4 Smart Search")
query = st.text_input("Describe the item you lost",
                      placeholder="I lost a black wallet near the library")
if st.button("Search with AI"):
    rows = db.execute(
        "SELECT name, location, details FROM items WHERE kind='Found'"
    ).fetchall()
    if not rows:
        st.info("No found-item reports yet. Add a Found report in the sidebar first.")
    elif not os.getenv("GEMINI_API_KEY"):
        st.error("Add your GEMINI_API_KEY in the .env file.")
    else:
        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            prompt = f"""You help match lost items with reported found items.
User query: {query}
Found item records: {rows}
Only use records provided. Suggest possible matches and explain why.
Never claim a match is certain. If none match, say so."""
            with st.spinner("Gemma 4 is checking possible matches..."):
                response = client.models.generate_content(
                    model=os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it"),
                    contents=prompt
                )
            st.markdown("### 💡 Gemma 4's Response")
            st.write(response.text)
        except Exception as e:
            st.error(f"AI error: {e}")

st.divider()
st.subheader("📋 Recent Reports")
reports = db.execute(
    "SELECT kind, name, location, details FROM items ORDER BY id DESC"
).fetchall()
if reports:
    for kind, name, location, details in reports:
        st.write(f"**{kind}: {name}** — 📍 {location}")
        if details:
            st.caption(details)
        st.divider()
else:
    st.info("No reports yet. Add a sample report using the sidebar.")

import streamlit as st 
import wikipedia
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image

# --- CONFIG ---
st.set_page_config(page_title="🔍 IntelliBot – Smart Search Assistant", layout="wide")

# Sidebar for chat history
st.sidebar.title("🕒 Chat History")
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_query" not in st.session_state:
    st.session_state.selected_query = None

# --- BOT LOGIC ---
def google_search(query):
    """Scrape Google search results (text + images)."""
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # Normal search for snippets
    search_url = f"https://www.google.com/search?q={query}"
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    snippets = [span.get_text() for span in soup.find_all("span")][:3]
    
    # Image search
    image_url = f"https://www.google.com/search?q={query}&tbm=isch"
    img_response = requests.get(image_url, headers=headers)
    img_soup = BeautifulSoup(img_response.text, "html.parser")

    valid_images = []
    for img in img_soup.find_all("img"):
        if "src" in img.attrs:
            src = img["src"]
            if src.startswith("http"):  # keep only absolute URLs
                valid_images.append(src)

    images = valid_images[:3]
    
    return snippets, images


def chatbot_response(user_input):
    user_input = user_input.lower()
    responses = []
    images = []

    # Rule-based
    if "hello" in user_input or "hi" in user_input:
        return ["Hello! 👋 How can I assist you today?"], []
    elif "your name" in user_input:
        return ["I'm **IntelliBot – Smart Search Assistant** 🤖"], []
    elif "bye" in user_input:
        return ["Goodbye! 👋 Have a great day."], []

    # Wikipedia
    try:
        summary = wikipedia.summary(user_input, sentences=2)
        responses.append(f"📖 **Wikipedia**:\n\n{summary}")
    except wikipedia.exceptions.DisambiguationError as e:
        responses.append(f"⚠️ Too broad. Did you mean: {', '.join(e.options[:5])}?")
    except wikipedia.exceptions.PageError:
        responses.append("❌ No Wikipedia results found.")
    except Exception as e:
        responses.append(f"⚠️ Wiki error: {e}")

    # Google
    snippets, images = google_search(user_input)
    if snippets:
        responses.append("🔎 **Google says**:\n- " + "\n- ".join(snippets))

    return responses, images


# --- SIDEBAR HISTORY BUTTONS ---
st.sidebar.subheader("Click a query to reload:")
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        if st.sidebar.button(msg["content"], key=f"hist_{i}"):
            st.session_state.selected_query = msg["content"]

# --- USER INPUT OR HISTORY SELECTION ---
user_input = st.chat_input("Type your message...")
if st.session_state.selected_query:
    user_input = st.session_state.selected_query
    st.session_state.selected_query = None  # reset after using it

if user_input:
    # Save user input
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Get bot response
    response_texts, response_images = chatbot_response(user_input)
    for text in response_texts:
        st.session_state.messages.append({"role": "bot", "content": text, "images": []})

    if response_images:
        # Store images as part of the last bot message
        st.session_state.messages.append({"role": "bot", "content": "🖼️ Images:", "images": response_images})

# --- DISPLAY CHAT ---
st.title("🔍 IntelliBot – Smart Search Assistant")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if "images" in msg and msg["images"]:
            for img_url in msg["images"]:
                try:
                    img_data = requests.get(img_url, timeout=5).content
                    st.image(Image.open(BytesIO(img_data)), width=200)
                except Exception as e:
                    st.warning(f"⚠️ Could not load image: {e}")

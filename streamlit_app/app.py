"""
Learning Advisor Chatbot - Streamlit Frontend
A professional, ChatGPT-style interface for the Rasa chatbot.
"""

import os
import streamlit as st
import requests
import uuid
import time

# ============================================================================
# Configuration
# ============================================================================

RASA_API_URL = os.getenv(
    "RASA_API_URL",
    "https://personalized-learning-advisor-rasa.onrender.com/webhooks/rest/webhook"
)
APP_TITLE = "Learning Advisor"
APP_ICON = "🎓"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# Custom CSS (ChatGPT-like styling)
# ============================================================================

st.markdown("""
<style>
    /* Import Inter font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Center the chat container (ChatGPT-like width) */
    .block-container {
        max-width: 680px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        margin: 0 auto;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e9ecef;
    }

    /* Chat Message Styling */
    [data-testid="stChatMessage"] {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }

    /* User Message - Transparent/White */
    [data-testid="stChatMessage"][aria-label="user"] {
        background-color: transparent;
        margin-left: 15%;
    }

    /* Assistant Message - Light Gray */
    [data-testid="stChatMessage"][aria-label="assistant"] {
        background-color: #f3f4f6;
        margin-right: 15%;
    }

    /* Chat wrapper container */
    .chat-wrapper {
        width: 100%;
        max-width: 100%;
    }

    /* Custom message container */
    .message-row {
        display: flex;
        margin-bottom: 1rem;
        align-items: flex-end;
        gap: 10px;
        width: 100%;
        clear: both;
    }

    .message-row.user {
        justify-content: flex-end;
        padding-left: 15%;
    }

    .message-row.bot {
        justify-content: flex-start;
        padding-right: 15%;
    }

    .message-bubble {
        padding: 0.75rem 1rem;
        border-radius: 16px;
        font-size: 0.95rem;
        line-height: 1.5;
        word-wrap: break-word;
        max-width: 70%;
    }

    .message-bubble.user {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border-bottom-right-radius: 6px;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
    }

    .message-bubble.bot {
        background: #f3f4f6;
        color: #1f2937;
        border-bottom-left-radius: 6px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }

    .avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.9rem;
        flex-shrink: 0;
    }

    .avatar.user { background: #dbeafe; }
    .avatar.bot { background: #f3e8ff; }
    
    /* Input container styling (ChatGPT-style fixed bottom bar) */
    .stChatInputContainer {
        padding: 6px 8px 16px 8px;
        position: sticky;
        bottom: 12px;
        background: transparent;
        z-index: 10;
    }

    /* Chat input row: align input and send button inline */
    .stChatInputContainer .chat-input-row {
        display: flex;
        gap: 8px;
        align-items: center;
    }

    /* Message input: taller, rounded, not full-width so it feels like a bar */
    .stChatInputContainer textarea,
    .stChatInputContainer input,
    .stTextInput > div > div > textarea,
    .stTextInput > div > div > input {
        /* taller and slightly wider input for a modern look */
        height: 72px !important;
        max-height: 84px !important;
        padding: 12px 18px !important;
        font-size: 1.02rem !important;
        border-radius: 32px !important;
        box-shadow: 0 10px 24px rgba(16,24,40,0.07) !important;
        border: 1px solid rgba(16,24,40,0.06) !important;
        /* make the input about 62% of the container width so it's a prominent bar */
        width: 55% !important;
        background: white !important;
    }

    /* Send button: match height to input and sit inline */
    .stButton > button {
        padding: 0 18px !important;
        font-size: 1rem !important;
        height: 72px !important; /* match input height */
        border-radius: 20px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* Placeholder styling for the input */
    .stChatInputContainer textarea::placeholder,
    .stChatInputContainer input::placeholder {
        color: #9aa4ad !important;
        font-size: 0.98rem !important;
    }
    
    /* Status indicator */
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }
    .status-online { background-color: #10b981; box-shadow: 0 0 4px #10b981; }
    .status-offline { background-color: #ef4444; }

</style>
""", unsafe_allow_html=True)

# ============================================================================
# Session State
# ============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# ============================================================================
# Helper Functions
# ============================================================================

def check_server_status():
    """Check if Rasa server is online."""
    try:
        # Ping the Rasa server base URL (not the webhook path) to check availability
        ping_url = RASA_API_URL
        # If webhook path present, try root
        if ping_url.endswith('/webhooks/rest/webhook'):
            ping_url = ping_url.replace('/webhooks/rest/webhook', '/')
        requests.get(ping_url, timeout=2)
        return True
    except:
        return False

def send_message_to_rasa(message: str) -> list:
    """Send message to Rasa and get response."""
    try:
        payload = {
            "sender": st.session_state.session_id,
            "message": message
        }
        response = requests.post(RASA_API_URL, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return [{"text": "⚠️ Error: Unable to connect to the Learning Advisor server."}]

def is_closing_message(text: str) -> bool:
    """Detect common 'thank you' / closing phrases so we can handle them locally.

    This prevents the bot from re-sending the same 'profile ready' message when the
    user just says thanks or a similar closing line.
    """
    if not text:
        return False
    t = text.strip().lower()
    # Common one-word or short closers
    closers = ["thank", "thanks", "thankyou", "thank you", "thx", "ty", "thanks!", "thank u"]
    closers_short = ["its okay", "it's okay", "i'm okay", "im okay", "i am okay", "its fine", "no thanks", "no thank you"]
    for c in closers:
        if c in t:
            return True
    for c in closers_short:
        if c in t:
            return True
    return False


def handle_user_message(message: str) -> list:
    """Central handler for outgoing user messages.

    If the message is a closing/thank-you phrase, handle it locally and return
    a synthetic response list in the same format Rasa returns. Otherwise forward
    to Rasa.
    """
    # Intercept thank-you / closing phrases
    if is_closing_message(message):
        # Find last assistant message to tailor the reply a bit
        last_bot = None
        for m in reversed(st.session_state.messages):
            if m.get("role") == "assistant":
                last_bot = m.get("content", "")
                break

        # Craft polite local replies to avoid hitting Rasa and repeating the same utterance
        if last_bot and "personalized learning path" in last_bot.lower():
            reply = "You're welcome! Glad the learning path helped — anything else I can do?"
        elif last_bot and "here is a recommended learning path" in last_bot.lower():
            reply = "You're welcome! Happy learning — ask me for project ideas or resources anytime."
        else:
            reply = "You're welcome — happy to help! Let me know if you'd like anything else."

        return [{"text": reply}]

    # Not a closing phrase — forward to Rasa
    return send_message_to_rasa(message)

def clear_chat():
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())

# ============================================================================
# Sidebar
# ============================================================================

with st.sidebar:
    st.title(f"{APP_ICON} {APP_TITLE}")
    
    # Server Status
    is_online = check_server_status()
    status_html = f"""
    <div style="padding: 10px 0; font-size: 0.9rem; color: #4b5563;">
        <span class="status-indicator {'status-online' if is_online else 'status-offline'}"></span>
        {'System Online' if is_online else 'System Offline'}
    </div>
    """
    st.markdown(status_html, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick Actions
    st.subheader("Quick Actions")
    if st.button("🔄 New Chat", use_container_width=True):
        clear_chat()
        st.rerun()
        
    st.markdown("### Suggested Prompts")
    if st.button("🎓 Start Profile", use_container_width=True):
        user_msg = "I want to start my profile"
        st.session_state.messages.append({"role": "user", "content": user_msg})
        # Trigger response generation immediately (use central handler)
        with st.spinner("Thinking..."):
            responses = handle_user_message(user_msg)
            for r in responses:
                if "text" in r:
                    st.session_state.messages.append({"role": "assistant", "content": r["text"]})
        st.rerun()

    if st.button("🗺️ Learning Path", use_container_width=True):
        user_msg = "What should I learn next?"
        st.session_state.messages.append({"role": "user", "content": user_msg})
        with st.spinner("Thinking..."):
            responses = handle_user_message(user_msg)
            for r in responses:
                if "text" in r:
                    st.session_state.messages.append({"role": "assistant", "content": r["text"]})
        st.rerun()

    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.8rem; color: #6b7280;">
    <strong>About</strong><br>
    This AI Advisor helps you create personalized learning paths for your career goals.
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# Main Chat Interface
# ============================================================================

# Display chat messages
if not st.session_state.messages:
    # Welcome Screen
    st.markdown(f"""
    <div style="text-align: center; padding: 3rem 0;">
        <h1 style="font-size: 2.5rem; margin-bottom: 1rem;">{APP_ICON}</h1>
        <h2 style="font-weight: 600; color: #1f2937;">How can I help you learn today?</h2>
        <p style="color: #6b7280;">I can create personalized learning paths, recommend courses, and guide your career.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)
for message in st.session_state.messages:
    role = message.get("role", "assistant")
    content = message.get("content", "").replace("\n", "<br>")
    
    if role == "user":
        st.markdown(f"""
        <div class="message-row user">
            <div class="message-bubble user">{content}</div>
            <div class="avatar user">👤</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="message-row bot">
            <div class="avatar bot">🎓</div>
            <div class="message-bubble bot">{content}</div>
        </div>
        """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Chat Input
if prompt := st.chat_input("Message Learning Advisor..."):
    # Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant", avatar="🎓"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("Thinking..."):
            responses = handle_user_message(prompt)

            for r in responses:
                if "text" in r:
                    text_chunk = r["text"]
                    full_response += text_chunk + "\n\n"
                    # Simulate typing effect
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.01)

                if "image" in r:
                    st.image(r["image"])

            message_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

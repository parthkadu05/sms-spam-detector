import streamlit as st
import pickle
import psycopg2
import nltk
import string
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

# ---------------- NLP SETUP ----------------
ps = PorterStemmer()

def transform_text(text):
    text = text.lower()
    text = text.split()

    y = []
    for i in text:
        if i.isalnum():
            y.append(i)

    text = y[:]
    y.clear()

    for i in text:
        if i not in stopwords.words('english'):
            y.append(i)

    text = y[:]
    y.clear()

    for i in text:
        y.append(ps.stem(i))

    return " ".join(y)


# ---------------- LOAD MODEL ----------------
tfidf = pickle.load(open("vectorizer.pkl", "rb"))
model = pickle.load(open("model.pkl", "rb"))


# ---------------- DATABASE CONNECTION ----------------
def get_connection():
    return psycopg2.connect(
        "postgresql://neondb_owner:npg_C0geFHncuiB5@ep-quiet-thunder-anvyn2fb-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    )


def create_users_table():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


def register_user(username, password):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, password)
        )
        conn.commit()
        success = True
    except:
        success = False

    cur.close()
    conn.close()
    return success


def login_user(username, password):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (username, password)
    )

    user = cur.fetchone()

    cur.close()
    conn.close()

    return user is not None


# ---------------- SESSION STATE ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# ---------------- CREATE TABLE ----------------
create_users_table()


# ---------------- LOGIN / REGISTER PAGE ----------------
if not st.session_state.logged_in:

    st.title("🔐 Login / Register")

    menu = st.radio("Select Option", ["Login", "Register"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if menu == "Register":
        if st.button("Create Account"):
            if register_user(username, password):
                st.success("Account created! Please login.")
            else:
                st.error("Username already exists.")

    else:  # Login
        if st.button("Login"):
            if login_user(username, password):
                st.session_state.logged_in = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")


# ---------------- MAIN APP AFTER LOGIN ----------------
else:

    st.title("📩 SMS Spam Detection System")

    # Logout button
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    input_sms = st.text_area("Enter the message")

    if st.button("Predict"):
        if input_sms.strip() == "":
            st.warning("Please enter a message.")
        else:
            transformed_sms = transform_text(input_sms)
            vector_input = tfidf.transform([transformed_sms]).toarray()
            result = model.predict(vector_input)[0]

            if result == 1:
                st.header("🚫 Spam")
            else:
                st.header("✅ Ham")

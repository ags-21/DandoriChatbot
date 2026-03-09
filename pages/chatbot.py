import sys
import csv
import json
import os
import requests
import chromadb
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from chromadb import Documents, EmbeddingFunction, Embeddings

# --- Environment Setup ---
if sys.platform == "linux":
    try:
        import pysqlite3

        sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
    except ImportError:
        pass

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
endpoint = os.getenv("ENDPOINT")


# --- Data Utilities ---

def get_classes_json():
    """Converts the source CSV to JSON if not already present."""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(BASE_DIR, "..", "classes.csv")
    json_path = os.path.join(BASE_DIR, "..", "classes.json")

    if os.path.exists(csv_path):
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2)


@st.cache_resource
def load_class_data():
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "classes.json")
    if not os.path.exists(json_path):
        get_classes_json()
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Security Guardrails ---

def run_safety_check(content, system_instruction):
    client = OpenAI(api_key=api_key, base_url=endpoint)
    try:
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-lite-001",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": content}
            ],
            temperature=0,
            max_tokens=10
        )
        return "SAFE" in response.choices[0].message.content.strip().upper()
    except Exception as e:
        st.error(f"Safety Check Error: {e}")
        return False


def is_prompt_safe(user_query):
    instruction = ("You are a gatekeeper for School of Dandori (wellbeing company). "
                   "Determine if the query relates to classes, instructors, locations, or company info. "
                   "Reply ONLY 'SAFE' or 'UNSAFE'.")
    return run_safety_check(f"User: {user_query}", instruction)


def is_output_safe(llm_response):
    instruction = ("You are a security gatekeeper. Mark UNSAFE if response contains profanity, "
                   "violence, medical advice, or non-company info. Reply ONLY 'SAFE' or 'UNSAFE'.")
    return run_safety_check(f"AI: {llm_response}", instruction)


# --- Vector Database Logic ---

class Embedder(EmbeddingFunction):
    def __init__(self, model="text-embedding-3-small"):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = os.getenv("ENDPOINT")

    def __call__(self, inputs: Documents) -> Embeddings:
        resp = requests.post(
            f"{self.base_url}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "input": list(inputs)},
            timeout=60
        )
        resp.raise_for_status()
        return [item["embedding"] for item in resp.json()["data"]]


@st.cache_resource
def init_collection():
    class_data = load_class_data()
    chunks = []
    for item in class_data:
        text = f"Class: {item.get('Class Name')} (ID: {item.get('Class ID')})\nCost: {item.get('Cost')}\nLocation: {item.get('Location')}\nInstructor: {item.get('Instructor')}\nDescription: {item.get('Description')}"
        chunks.append({
            "id": f"{item.get('Class ID')}_{item.get('Location')}_{item.get('Instructor').replace(' ', '_')}",
            "text": text,
            "metadata": item
        })

    client = chromadb.Client()
    collection = client.get_or_create_collection(
        name="dandori_v3",
        embedding_function=Embedder()
    )
    collection.add(
        ids=[i['id'] for i in chunks],
        documents=[i['text'] for i in chunks],
        metadatas=[i['metadata'] for i in chunks]
    )
    return collection


# --- Advanced Filtering Logic ---

def filter_data(user_query):
    data = load_class_data()
    q = user_query.lower()

    # 1. Price Filtering
    is_cheap = any(w in q for w in ["cheapest", "lowest", "affordable", "budget", "least expensive"])
    is_expensive = any(w in q for w in ["expensive", "priciest", "highest cost", "most expensive"])

    if is_cheap or is_expensive:
        def get_price(x): return float(x["Cost"].replace("£", "").replace(",", ""))

        sorted_data = sorted(data, key=get_price, reverse=is_expensive)
        res = "Most affordable" if is_cheap else "Highest priced"
        return f"{res} classes:\n\n" + "\n".join(
            [f"- **{x['Class Name']}** with **{x['Instructor']}**: {x['Location']}, {x['Cost']}" for x in sorted_data[:5]])

    # 2. Location Filtering (with nearby groups)
    groups = {"harrogate": ["harrogate", "york", "leeds"], "york": ["york", "harrogate", "leeds"],
              "brighton": ["brighton"]}
    for loc, neighbors in groups.items():
        if loc in q:
            matches = [x for x in data if x["Location"].lower() in neighbors]
            return f"Classes in/near {loc.title()}:\n\n" + "\n".join(
                [f"- **{x['Class Name']}** with **{x['Instructor']}**: {x['Location']}, {x['Cost']}" for x in matches])

    # 3. Instructor Filtering
    for x in data:
        if x["Instructor"].lower() in q:
            matches = [c for c in data if c["Instructor"].lower() == x["Instructor"].lower()]
            return f"Classes by {x['Instructor']}:\n\n" + "\n".join([f"- **{c['Class Name']}**: {c['Location']}, {c['Cost']}" for c in matches])

    return None  # Fallback to RAG


# --- Streamlit UI ---

st.title("🌱 School of Dandori: Unified Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("How can I help you reconnect with your carefree self?"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    if not is_prompt_safe(user_input):
        response_text = "I'm sorry, I can only answer questions regarding the School of Dandori classes."
    else:
        with st.spinner("Consulting the archives..."):
            # Attempt hardcoded filters first (more accurate for price/location)
            context = filter_data(user_input)

            # If no hard filter matches, use RAG
            if not context:
                collection = init_collection()
                results = collection.query(query_texts=[user_input], n_results=5)
                context = "\n\n---\n\n".join(results["documents"][0])

            # Generate response
            try:
                chat_client = OpenAI(api_key=api_key, base_url=endpoint)
                response = chat_client.chat.completions.create(
                    model="google/gemini-2.0-flash-lite-001",
                    messages=[
                        {"role": "system",
                         "content": "You are a friendly School of Dandori assistant. Use the context provided to answer accurately and warmly."},
                        {"role": "user", "content": f"Context: {context}\n\nQuestion: {user_input}"}
                    ]
                )
                response_text = response.choices[0].message.content

                if not is_output_safe(response_text):
                    response_text = "I apologize, but I cannot provide that specific information. Please ask about our class offerings!"
            except Exception as e:
                response_text = f"I encountered an error: {e}"

    with st.chat_message("assistant"):
        st.markdown(response_text)
    st.session_state.messages.append({"role": "assistant", "content": response_text})
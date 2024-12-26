import invoke_agent as agenthelper
import streamlit as st
import json
import pandas as pd
from PIL import Image, ImageOps, ImageDraw
import uuid
import fitz

# Streamlit page configuration
st.set_page_config(page_title="Remote Jobs Copilot", page_icon=":robot_face:", layout="wide")

# Function to crop image into a circle
def crop_to_circle(image):
    mask = Image.new('L', image.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0) + image.size, fill=255)
    result = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    result.putalpha(mask)
    return result

# Title
st.title("Remote Jobs Copilot")

# Display a text box for input
prompt = st.text_input("What can I help with?", max_chars=2000)
prompt = prompt.strip()

uploaded_file = st.file_uploader("Or upload a resume PDF file:", type="pdf")

# Display a primary button for submission
submit_button = st.button("Submit", type="primary")

# Display a button to end the session
end_session_button = st.button("End Session")

# Sidebar for user input
# st.sidebar.title("Trace Data")

# Session State Management
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = str(uuid.uuid4())

# Function to parse and format response
def format_response(response_body):
    try:
        data = json.loads(response_body)
        if isinstance(data, list):
            return pd.DataFrame(data)
        else:
            return data
    except json.JSONDecodeError:
        return response_body

def extract_text_from_pdf(file):
    text = []
    pdf_document = fitz.open(stream=file.read(), filetype="pdf")
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text.append(page.get_text())
    return '\n'.join(text)


if submit_button:
    if prompt:
        prompt_start = f"Do an internet search and looking up up-to-date information and current events: \n {prompt}"
        pdf_input = ''
        if uploaded_file:
            pdf_input = extract_text_from_pdf(uploaded_file)
            start_with = "Instruction: Always use the most relevant information from the knowledge base to respond to user queries. If the knowledge base lacks the necessary information, acknowledge the limitation and avoid guessing."
            pdf_input = f"{start_with}: \n {pdf_input}"
            st.success('PDF processed successfully.')

        question = f"{prompt_start} \n {pdf_input}"
        event = {
            "sessionId": st.session_state["session_id"],
            "question": question
        }
        
        try:
            response, trace_date = agenthelper.lambda_handler(event, None)
            # Extract the response and trace data
            all_data = trace_date
            the_response = response.strip() if response else response
        except Exception as e:
            all_data = "..." 
            the_response = "Apologies, but an error occurred. Please rerun the application" 

        # st.sidebar.text_area("", value=str(all_data), height=300)
        st.session_state['history'].append({"question": prompt, "answer": the_response})
    else:
        st.error("Please enter a query before submitting.")

if end_session_button:
    st.session_state['history'].append({"question": "Session Ended", "answer": "Thank you for using Signiance AI Agent!"})
    event = {
        "sessionId": st.session_state["session_id"],
        "question": "placeholder to end session",
        "endSession": True
    }
    agenthelper.lambda_handler(event, None)
    st.session_state['history'].clear()


st.write("## Conversation History")
for index, chat in enumerate(reversed(st.session_state['history'])):
    col1, col2 = st.columns([2, 10])
    with col1:
        st.image(Image.open("human_face.png"), width=125)
    with col2:
        st.text_area("Q:", value=chat["question"], height=68, key=f"question_{index}", disabled=True)
        st.text_area("A:", value=chat["answer"], height=100, key=f"answer_{index}")

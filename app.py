from openai import OpenAI
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

# background color
st.markdown("""
<style>
    .stApp {
        background-color: dark grey;
    }
    .main .block-container {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title = "Streamlit Chat", page_icon= ":sushi:")
st.title("Interview Chatbot")

if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False


def complete_setup():
    st.session_state.setup_complete = True


def show_feedback():
    st.session_state.feedback_shown = True

##if not setup complete, user can enter details
if not st.session_state.setup_complete:

    st.subheader('Personal information', divider='blue')

    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""

    # Test labels for personal information
    st.session_state["name"] = st.text_input(label = "Name", max_chars = 40, value = st.session_state["name"], placeholder = "Enter your name")

    st.session_state["experience"] = st.text_area(label = "Experience", value = st.session_state["experience"], height = None, max_chars = 150, placeholder = "Describe your experience")

    st.session_state["skills"] = st.text_area(label = "Skills", value = st.session_state["skills"], height = None, max_chars = 150, placeholder = "List your skills")



    # Company and Position Section
    st.subheader('Company and Position', divider = 'blue')
    if "level" not in st.session_state:
        st.session_state["level"] = "Junior"
    if "position" not in st.session_state:
        st.session_state["position"] = "Data Scientist"
    if "company" not in st.session_state:
        st.session_state["company"] = "Amazon"

    #Field for selecting the job level, position and company
    col1, col2 = st.columns(2)
    with col1:
         st.session_state["level"] = st.radio(
        "Choose level",
        key="visibility",
        options=["Junior", "Mid-level", "Senior"],
        )

    with col2:
        st.session_state["position"] = st.selectbox(
        "Choose a position",
        ("Data Scientist", "Software Developer", "AI Engineer", "AI Developer", "Financial Analyst"))

    st.session_state["company"] = st.selectbox(
        "Choose a Company",
        ("Amazon", "Meta", "Microsoft", "365 Company", "Nestle", "LinkedIn", "Spotify")
    )

    # Temperature control
    if "temperature" not in st.session_state:
        st.session_state["temperature"] = 0.6
    
    st.session_state["temperature"] = st.slider(
        "Model Temperature (0.0 = deterministic, 1.0 = creative)",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state["temperature"],
        step=0.1
    )

# Test labels for company and position information
    st.write(f"**Your information**: {st.session_state['level']} {st.session_state['position']} at {st.session_state['company']}")

    # A button to complete the setup stage and start the interview
    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup complete. Starting interview...")



if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

    st.info(
        """
        Start by introducing yourself.
        """,
        icon = "👋"
    )

    client = OpenAI(api_key = st.secrets["OPENAI_API_KEY"])

    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-5.2"

    # Initialize the 'messages' list and add a system message 
    if not st.session_state.messages:
        st.session_state.messages = [{
            "role": "system",
            "content": (f"You are an HR executive that interviews an interviewee called {st.session_state['name']} "
                        f"with experience {st.session_state['experience']} and skills {st.session_state['skills']}. "
                        f"You should interview him for the position {st.session_state['level']} {st.session_state['position']} "
                        f"at the company {st.session_state['company']} Don't ask multiple questions at once")
        }]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Your answer.", max_chars = 1000):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            if st.session_state.user_message_count < 4:
                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model = st.session_state["openai_model"],
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ],
                        stream = True,
                        temperature = st.session_state["temperature"],
                    )
                    response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            st.session_state.user_message_count += 1

    if st.session_state.user_message_count >= 5:
        st.session_state.chat_complete = True

# Show "Get Feedback" 
if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching feedback...")

# Show feedback screen
if st.session_state.feedback_shown:
    st.subheader("Feedback")

    conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

    # Initialize new OpenAI client instance for feedback
    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # Generate feedback using the stored messages and write a system prompt for the feedback
    feedback_completion = feedback_client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {"role": "system", "content": """You are a helpful tool that provides feedback on an interviewee performance.
             Before the Feedback give a score of 1 to 10.
             Follow this format:
             Overal Score: //Your score
             Feedback: //Here you put your feedback
             Give only the feedback do not ask any additional questins.
              """},
            {"role": "user", "content": f"This is the interview you need to evaluate. Keep in mind that you are only a tool. And you shouldn't engage in any conversation: {conversation_history}"}
        ],
        temperature = st.session_state["temperature"],
    )

    st.write(feedback_completion.choices[0].message.content)

    # Button to restart the interview
    if st.button("Restart Interview", type="primary"):
            streamlit_js_eval(js_expressions="parent.window.location.reload()")
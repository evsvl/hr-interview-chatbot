import streamlit as st
from openai import OpenAI
from streamlit_js_eval import streamlit_js_eval

# Setting up the Streamlit page configuration
st.set_page_config(page_title="ChatMessageHistory", page_icon="💬")
st.title("HR Chatbot")

# Constants
MAX_USER_MESSAGES = 5          # number of user messages that get LLM replies
MAX_CHAT_CHARS = 1000                
MAX_FIELD_CHARS = 500

INTERVIEW_MODEL = "gpt-4o"
FEEDBACK_MODEL = "gpt-4o"

DEFAULT_LEVEL = "Junior"
DEFAULT_POSITION = "Data Scientist"
DEFAULT_COMPANY = "Amazon"

# Initialize session state variables
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False
if "restart" not in st.session_state:
    st.session_state.restart = False

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []


# Helper functions for building prompts

def build_interview_system_prompt():
    return (
        f"You are an HR executive that interviews an interviewee called {st.session_state['name']} "
        f"with experience {st.session_state['experience']} and skills {st.session_state['skills']}. "
        f"You should interview him for the position {st.session_state['level']} {st.session_state['position']} "
        f"at the company {st.session_state['company']}. "
        "Be strict, if a person does not have skills or attitude say so!"
    )

def build_last_turn_system_prompt():
    return (
        """If you are reading this then it is your final response in this conversation.
        First, fully answer the user's last message. Then clearly tell the user that this is your last
        message and that they cannot ask further questions in this chat. 
        Also always tell the user that any additional context or information can be shared below,
        that information will be analyzed in the feedback too."""
    )
def build_feedback_model_system_prompt():
    return (
        """You are a helpful tool that provides feedback on an interviewee performance.
        Before the Feedback give a score of 1 to 10.
        Follow this format:
        Overal Score: //Your score
        Feedback: //Here you put your feedback
        Give only the feedback do not ask any additional questins. 
        Be strict, if a user don't have the needed skills say so!"""
    )
def build_feedback_model_messages_prompt(conversation_history: str):
    return (
        f"This is the interview you need to evaluate. Keep in mind that you are only a tool. "
        f"And you shouldn't engage in any converstation: {conversation_history}"
    )

# Helper functions for LLM calls

def _create_chat_completion(messages, model: str, stream: bool):
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    try:
        return client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream,
        )
    except Exception:
        st.error("Error calling the language model. Please try again later", icon="🚨")
        st.stop()

def stream_interview_completion(messages):
    return _create_chat_completion(
        messages=messages,
        model=INTERVIEW_MODEL,
        stream=True
    )

def get_feedback_completion(messages):
    return _create_chat_completion(
        messages=messages,
        model=FEEDBACK_MODEL,
        stream=False
    )

# Helper functions to update session state
def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

# Setup stage for collecting user details
if not st.session_state.setup_complete:
    st.subheader('Personal Information')

    # Initialize session state for personal information
    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""

   
    # Get personal information input
    st.session_state["name"] = st.text_input(label="Name", value=st.session_state["name"], placeholder="Enter your name", max_chars=MAX_FIELD_CHARS)
    st.session_state["experience"] = st.text_area(label="Experience", value=st.session_state["experience"], placeholder="Describe your experience", max_chars=MAX_FIELD_CHARS)
    st.session_state["skills"] = st.text_area(label="Skills", value=st.session_state["skills"], placeholder="List your skills", max_chars=MAX_FIELD_CHARS)

    
    # Company and Position Section
    st.subheader('Company and Position')

    # Initialize session state for company and position information and setting default values 
    if "level" not in st.session_state:
        st.session_state["level"] = DEFAULT_LEVEL
    if "position" not in st.session_state:
        st.session_state["position"] = DEFAULT_POSITION
    if "company" not in st.session_state:
        st.session_state["company"] = DEFAULT_COMPANY

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.radio(
            "Choose level",
            key="visibility",
            options=["Junior", "Mid-level", "Senior"],
            index=["Junior", "Mid-level", "Senior"].index(st.session_state["level"])
        )

    with col2:
        st.session_state["position"] = st.selectbox(
            "Choose a position",
            ("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst"),
            index=("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst").index(st.session_state["position"])
        )

    st.session_state["company"] = st.selectbox(
        "Select a Company",
        ("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify"),
        index=("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify").index(st.session_state["company"])
    )



    # Button to complete setup
    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup complete. Starting interview...")

# Interview phase
if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

    st.info(
        f"Start by introducing yourself. Pls note that this interview is limited to {MAX_USER_MESSAGES} messages",
    icon="👋",
    )

    # Initializing the system prompt for the chatbot
    if not st.session_state.messages:
        st.session_state.messages = [{
            "role": "system",
            "content": (build_interview_system_prompt())
        }]

    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Handle user input and OpenAI response
    # Put a max_chars limit
    if st.session_state.user_message_count < MAX_USER_MESSAGES + 1:
        if prompt := st.chat_input("Your response", max_chars=MAX_CHAT_CHARS):
            st.session_state.messages.append({"role": "user", "content": prompt})
            # Display user message
            with st.chat_message("user"):
                # Render message content
                st.markdown(prompt)

            if st.session_state.user_message_count  < MAX_USER_MESSAGES:
                
                # Add a system instruction so LLM knows this is the final reply
                if st.session_state.user_message_count  == MAX_USER_MESSAGES - 1:
                    st.session_state.messages.append(
                                {
                                    "role": "system",
                                    "content": (build_last_turn_system_prompt())
                                }
                            )
    
                # Quering LLM with all messages as a context
                with st.chat_message("assistant"):
                    stream = stream_interview_completion(
                        [
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ]
                    )
                    response = st.write_stream(stream)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )

                
            else:
                st.info(
                        """
                        Thanks, click to get your feedback:
                        """
                        )

            # Increment the user message count
            st.session_state.user_message_count += 1



    # Check if the user message count reaches maximum amount
    if st.session_state.user_message_count >= MAX_USER_MESSAGES + 1:
        st.session_state.chat_complete = True

# Show "Get Feedback" 
if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click=show_feedback):
        st.write("Fetching feedback...")

# Show feedback screen
if st.session_state.feedback_shown:
    st.subheader("Feedback")
    if not st.session_state.restart:
        conversation_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])

        # Generate feedback using the stored messages and write a system prompt for the feedback
        feedback_completion = get_feedback_completion(
            [
                {
                    "role": "system",
                    "content": build_feedback_model_system_prompt(),
                },
                {
                    "role": "user",
                    "content": build_feedback_model_messages_prompt(conversation_history),
                }
            ]
        )

        st.write(feedback_completion.choices[0].message.content)
        st.session_state.restart = True
        
    # Button to restart the interview
    if st.button("Restart Interview", type="primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")

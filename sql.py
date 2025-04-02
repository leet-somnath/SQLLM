from dotenv import load_dotenv
load_dotenv()  # Load environment variables

import streamlit as st
import os
import sqlite3
import pandas as pd
import altair as alt
import google.generativeai as genai
import speech_recognition as sr
import pyaudio

# Configure the API key for Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

###############################################################################
# Helper Functions
###############################################################################
def get_gemini_response(question, prompt):
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    full_prompt = prompt[0] + "\nUser's request: " + question
    response = model.generate_content(full_prompt)
    return response.text

def explain_query(query):
    explanation_prompt = f"Explain in plain English what the following SQL query does:\n{query}"
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    response = model.generate_content(explanation_prompt)
    return response.text

def read_sql_query(sql, db):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    col_names = [desc[0] for desc in cur.description]
    conn.commit()
    conn.close()
    return rows, col_names


def calculate_basic_statistics(df):
    """Calculates and returns basic statistics for the DataFrame."""
    if df is None or df.empty:
        return "No data to generate statistics."

    stats = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):  # Process only numeric columns
            stats[col] = {}
            stats[col]['Max'] = df[col].max()
            stats[col]['Min'] = df[col].min()
            stats[col]['Mean'] = df[col].mean()
            stats[col]['Sum'] = df[col].sum()

            #Find associated NAME for Max and Min marks
            if col == 'MARKS':
                max_name = df.loc[df['MARKS'] == df['MARKS'].max(), 'NAME'].tolist()
                min_name = df.loc[df['MARKS'] == df['MARKS'].min(), 'NAME'].tolist()
                stats[col]['Name with Max Marks'] = ', '.join(max_name)
                stats[col]['Name with Min Marks'] = ', '.join(min_name)

            stats[col]['Count'] = df[col].count()
            stats[col]['Unique'] = df[col].nunique()
            stats[col]['Percentage_of_Total'] = (df[col].sum() / df['MARKS'].sum()) * 100 if 'MARKS' in df.columns and df['MARKS'].sum() != 0 else 0
            if stats[col].get('Min', 0) != 0:
                stats[col]['Max_to_Min_Ratio'] = stats[col]['Max'] / stats[col]['Min']
            else:
                stats[col]['Max_to_Min_Ratio'] = "Undefined (Min is 0)"

    stats_df = pd.DataFrame(stats)
    return stats_df



def recognize_speech():
    r = sr.Recognizer()
    
    # Check for available microphones
    try:
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(1)
        numdevices = info.get('deviceCount')
        
        if numdevices == 0:
            st.error("No microphones detected. Please connect a microphone.")
            return None
        
        for i in range(0, numdevices):
            if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                st.info(f"Using microphone: {p.get_device_info_by_host_api_device_index(0, i).get('name')}")
                break # Use the first available microphone

        with sr.Microphone() as source:
            st.info("Say something!")  # Using st.info for a less intrusive prompt
            r.adjust_for_ambient_noise(source) # Adjust for background noise
            audio = r.listen(source, phrase_time_limit=10)  # Listen for up to 10 seconds
    
        try:
            text = r.recognize_google(audio)
            st.success("You said: {}".format(text)) # Using st.success to indicate successful recognition
            return text
        except sr.UnknownValueError:
            st.warning("Google Speech Recognition could not understand audio") # Using st.warning for a gentler message
            return None
        except sr.RequestError as e:
            st.error("Could not request results from Google Speech Recognition service; {0}".format(e))
            return None
    
    except OSError as e:
        st.error(f"Audio Error: {e}.  Make sure you have a microphone connected and that it is properly configured in your system settings.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

###############################################################################
# Initialize Session State
###############################################################################
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Initialize display flags in session state for each chat entry
if "display" not in st.session_state:
    st.session_state.display = {}  # Dictionary to store the display state
###############################################################################
# Prompt
###############################################################################
prompt = [
    """
    You are an expert in converting English questions to SQL queries!
    The SQL database is named STUDENT and has these columns:
      - NAME (text)
      - CLASS (text)
      - SECTION (text)
      - MARKS (numeric)

    CRITICAL RULES:
    1) For TEXT columns (NAME, CLASS, SECTION):
       - Use case-insensitive partial matching (LIKE).
    2) For the NUMERIC column (MARKS):
       - Use numeric comparisons (>, <, =, BETWEEN, etc.) 
         depending on phrasing (e.g., "marks more than 55" => WHERE MARKS > 55).
    3) Column Mapping:
       - "section" => SECTION (LIKE)
       - "class"   => CLASS   (LIKE)
       - "name"    => NAME    (LIKE)
       - "marks"   => numeric comparisons
    4) Selecting Columns:
       - If the user says "display NAME or give Name or tell name," select only NAME. 
         Otherwise SELECT * FROM STUDENT.
    5) For counting => SELECT COUNT(*).
    6) No triple backticks or the word "sql" in the output.
    """
]

###############################################################################
# Streamlit UI
###############################################################################
st.set_page_config(page_title="DATACHAT")
st.header("Chat with SQL Project ")

# Speech Recognition Button
if st.button("Speak"):
    speech_text = recognize_speech()
    if speech_text:
        st.session_state.speech_text = speech_text  # Store in session state
    else:
        st.session_state.speech_text = None  # Clear previous speech text if recognition fails
else:
    st.session_state.speech_text = None


# Chat input area
if st.session_state.speech_text:
     user_message = st.text_input("Type your message here...", value=st.session_state.speech_text) # Use text_input instead
else:
    user_message = st.chat_input("Type your message here...")

if user_message:
    # Add user's message to the chat
    st.session_state.chat_history.append({
        "role": "user",
        "message": user_message
    })
    
    # Generate the SQL query and retrieve data
    sql_query = get_gemini_response(user_message, prompt)
    rows, columns = read_sql_query(sql_query, "student.db")
    
    if rows:
        df = pd.DataFrame(rows, columns=columns)
        assistant_reply = (
            "I've generated a SQL query and retrieved the data successfully. "
            "Use the buttons below to view the query, show the output, explain the query, or edit it."
        )
    else:
        df = None
        assistant_reply = (
            "I generated a SQL query, but no data was returned. "
            "Please check your input or your database."
        )
    
    # Store assistant message
    st.session_state.chat_history.append({
        "role": "assistant",
        "message": assistant_reply,
        "sql_query": sql_query,
        "df": df
    })

# Display the chat
for idx, chat in enumerate(st.session_state.chat_history):
    if idx not in st.session_state.display:
        st.session_state.display[idx] = {
            "sql_query": False,
            "output": False,
            "explanation": False,
            "stats": False
        }

    with st.chat_message(chat["role"]):  # Determine if it's user or assistant
        st.markdown(chat["message"])  # Display the message

        if chat["role"] == "assistant" and "sql_query" in chat:
            col1, col2, col3, col4 = st.columns(4)

            # Show SQL Query
            with col1:
                if st.button("Show SQL Query", key=f"show_sql_{idx}"):
                    st.session_state.display[idx]["sql_query"] = not st.session_state.display[idx]["sql_query"]

                if st.session_state.display[idx]["sql_query"]:
                    st.code(chat["sql_query"], language="sql")

            # Show DataFrame
            with col2:
                if chat.get("df") is not None:
                    if st.button("Show Output", key=f"show_output_{idx}"):
                        st.session_state.display[idx]["output"] = not st.session_state.display[idx]["output"]
                    if st.session_state.display[idx]["output"]:
                        st.dataframe(chat["df"], use_container_width=True)
                else:
                    st.write("No data to show.")

            # Explain Query
            with col3:
                if st.button("Explain Query", key=f"explain_{idx}"):
                     st.session_state.display[idx]["explanation"] = not st.session_state.display[idx]["explanation"]
                if st.session_state.display[idx]["explanation"]:
                    explanation = explain_query(chat["sql_query"])
                    st.write(explanation)


            # Edit Query
            with col4:
                if st.checkbox("Edit Query", key=f"edit_{idx}"):
                    edited_query = st.text_area(
                        "Edit Query:",
                        value=chat["sql_query"],
                        key=f"edit_text_{idx}",
                        height=200
                    )
                    if st.button("Run Edited Query", key=f"run_edit_{idx}"):
                        try:
                            rows_edited, cols_edited = read_sql_query(edited_query, "student.db")
                            if rows_edited:
                                edited_df = pd.DataFrame(rows_edited, columns=cols_edited)
                                st.dataframe(edited_df, use_container_width=True)
                            else:
                                st.warning("Edited query returned no data.")
                        except Exception as e:
                            st.error(f"Error executing edited query: {e}")


# Visualization Section with Additional Chart Options
st.divider()
st.subheader("Advanced Visualization Options")

# Check if we have any DataFrame to visualize
df_for_viz = None
for msg in reversed(st.session_state.chat_history):
    if msg.get("df") is not None:
        df_for_viz = msg["df"]
        break

viz_col1, viz_col2 = st.columns(2)

if df_for_viz is not None:
    chart_type = st.selectbox(
        "Select Chart Type", 
        ["Bar Chart", "Line Chart", "Scatter Chart", "Pie Chart", "Histogram", "Area Chart"], 
        key="chart_type"
    )
    x_axis = st.selectbox("Select X-Axis", df_for_viz.columns, key="x_axis")
    y_axis = st.selectbox("Select Y-Axis", df_for_viz.columns, key="y_axis")

    with viz_col1:
        if st.button("Generate Visualization", key="visualize_btn"):
            if chart_type == "Bar Chart":
                chart = alt.Chart(df_for_viz).mark_bar().encode(
                    x=alt.X(x_axis, type='nominal'),
                    y=alt.Y(y_axis, type='quantitative')
                )
            elif chart_type == "Line Chart":
                chart = alt.Chart(df_for_viz).mark_line().encode(
                    x=alt.X(x_axis, type='nominal'),
                    y=alt.Y(y_axis, type='quantitative')
                )
            elif chart_type == "Scatter Chart":
                chart = alt.Chart(df_for_viz).mark_circle(size=60).encode(
                    x=alt.X(x_axis, type='nominal'),
                    y=alt.Y(y_axis, type='quantitative'),
                    tooltip=list(df_for_viz.columns)
                )
            elif chart_type == "Pie Chart":
                # For Pie Chart, interpret x_axis as category, y_axis as numeric measure
                chart = alt.Chart(df_for_viz).mark_arc().encode(
                    theta=alt.Theta(field=y_axis, type='quantitative'),
                    color=alt.Color(field=x_axis, type='nominal')
                )
            elif chart_type == "Histogram":
                chart = alt.Chart(df_for_viz).mark_bar().encode(
                    x=alt.X(x_axis, bin=True),
                    y='count()'
                )
            elif chart_type == "Area Chart":
                chart = alt.Chart(df_for_viz).mark_area().encode(
                    x=alt.X(x_axis, type='ordinal'),
                    y=alt.Y(y_axis, type='quantitative')
                )

            st.altair_chart(chart, use_container_width=True)

    with viz_col2:
        if st.button("Generate Stats", key="stats_viz"):
             st.session_state.display[idx]["stats"] = not st.session_state.display[idx]["stats"]

        if  st.session_state.display[idx]["stats"]:
            stats_df = calculate_basic_statistics(df_for_viz)
            with st.expander("Statistics",expanded = True):
                st.dataframe(stats_df, use_container_width=True)

else:
    st.write("No DataFrame available for visualization yet.")
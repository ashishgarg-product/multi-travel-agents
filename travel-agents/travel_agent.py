import streamlit as st
import json
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_community.chat_models import ChatOllama
from dotenv import load_dotenv
import os
from agents import generate_itinerary, recommend_activities, fetch_useful_links
from utils_export import export_to_pdf

# Load environment variables
load_dotenv()

# Initialize LLM
st.set_page_config(page_title="AI Travel Planner", layout="wide")
try:
    llm = ChatOllama(model="llama3.2", base_url="http://localhost:11434")
except Exception as e:
    st.error(f"LLM initialization failed: {str(e)}")
    st.stop()

# Define state
class GraphState(TypedDict):
    preferences_text: str
    preferences: dict
    itinerary: str
    activity_suggestions: str
    useful_links: list[dict]

# ------------------- LangGraph -------------------

workflow = StateGraph(GraphState)
workflow.add_node("generate_itinerary", generate_itinerary.generate_itinerary)
workflow.set_entry_point("generate_itinerary")
workflow.add_edge("generate_itinerary", END)
graph = workflow.compile()

# ------------------- UI -------------------

st.markdown("# AI-Powered Travel Itinerary Planner")

if "state" not in st.session_state:
    st.session_state.state = {
        "preferences_text": "",
        "preferences": {},
        "itinerary": "",
        "activity_suggestions": "",
        "useful_links": []
    }

with st.form("travel_form"):
    col1, col2 = st.columns(2)
    with col1:
        destination = st.text_input("Destination")
        month = st.selectbox("Month of Travel", ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
        duration = st.slider("Number of Days", 1, 30, 7)
        num_people = st.selectbox("Number of People", ["1", "2", "3", "4-6", "7-10", "10+"])
    with col2:
        holiday_type = st.selectbox("Holiday Type", ["Any", "Party", "Skiing", "Backpacking", "Family", "Beach", "Festival", "Adventure", "City Break", "Romantic", "Cruise"])
        budget_type = st.selectbox("Budget Type", ["Budget", "Mid-Range", "Luxury", "Backpacker", "Family"])
        comments = st.text_area("Additional Comments")
    submit_btn = st.form_submit_button("Generate Itinerary")

if submit_btn:
    preferences_text = f"Destination: {destination}\nMonth: {month}\nDuration: {duration} days\nPeople: {num_people}\nType: {holiday_type}\nBudget: {budget_type}\nComments: {comments}"
    preferences = {
        "destination": destination,
        "month": month,
        "duration": duration,
        "num_people": num_people,
        "holiday_type": holiday_type,
        "budget_type": budget_type,
        "comments": comments
    }
    st.session_state.state.update({
        "preferences_text": preferences_text,
        "preferences": preferences,
        "activity_suggestions": "",
        "useful_links": [],
        "itinerary": ""
    })
    with st.spinner("Generating itinerary..."):
        result = graph.invoke(st.session_state.state)
        st.session_state.state.update(result)
        if result.get("itinerary"):
            st.success("Itinerary Created")
        else:
            st.error("Failed to generate itinerary.")

# Layout
if st.session_state.state.get("itinerary"):
    st.markdown("### Travel Itinerary")
    st.markdown(st.session_state.state["itinerary"])

    # Activity Suggestions button
    if st.button("Get Activity Suggestions"):
        with st.spinner("Fetching activity suggestions..."):
            result = recommend_activities.recommend_activities(st.session_state.state)
            st.session_state.state.update(result)

    # Useful Links button
    if st.button("Get Useful Links"):
        with st.spinner("Fetching useful links..."):
            result = fetch_useful_links.fetch_useful_links(st.session_state.state)
            st.session_state.state.update(result)

    # Display activity suggestions if available
    if st.session_state.state.get("activity_suggestions"):
        with st.expander("🏄 Activity Suggestions", expanded=False):
            st.markdown(st.session_state.state["activity_suggestions"])

    # Display useful links if available
    if st.session_state.state.get("useful_links"):
        with st.expander("🔗 Useful Links", expanded=False):
            for link in st.session_state.state["useful_links"]:
                st.markdown(f"- [{link['title']}]({link['link']})")

    # Export PDF button
    if st.button("Export as PDF"):
        pdf_path = export_to_pdf(st.session_state.state["itinerary"])
        if pdf_path:
            with open(pdf_path, "rb") as f:
                st.download_button("Download Itinerary PDF", f, file_name="itinerary.pdf")

else:
    st.info("Fill the form and generate an itinerary to begin.")
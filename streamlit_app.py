"""
Mental Health Agent - Streamlit Cloud Version
This is the main entry point for Streamlit Cloud deployment.
"""

import streamlit as st
import json
import requests
import os
from datetime import datetime, timedelta

# Configuration for Streamlit Cloud
API_BASE = os.environ.get(
    "API_BASE", "https://ot173x9io1.execute-api.us-west-2.amazonaws.com"
)
BUCKET = os.environ.get("MH_BUCKET", "mental-health-agent")


def invoke_api(path: str, payload: dict):
    """Helper function to invoke API endpoints"""
    try:
        url = f"{API_BASE}{path}"
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None


def main():
    st.set_page_config(page_title="Mental Health Agent", page_icon="🧠", layout="wide")

    st.title("🧠 Mental Health Agent")
    st.markdown("A supportive AI companion for your mental health journey")

    # Sidebar for user configuration
    st.sidebar.header("User Configuration")
    user_id = st.sidebar.text_input(
        "User ID", value="demo_user_123", help="Unique identifier for the user"
    )

    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "💬 Chat",
            "📊 Daily Check-in",
            "📈 Evaluation",
            "🎯 Recommendations",
            "⏰ Companion",
        ]
    )

    with tab1:
        st.header("💬 Chat with Mental Health Agent")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Chat interface
            st.subheader("Chat Interface")

            # Mood context
            mood_context = {}
            with st.expander("Mood Context (Optional)"):
                mood_context["current_mood"] = st.selectbox(
                    "Current Mood",
                    [
                        "neutral",
                        "happy",
                        "sad",
                        "anxious",
                        "stressed",
                        "tired",
                        "excited",
                        "calm",
                    ],
                    index=0,
                    key="chat_mood_select",
                )
                mood_context["stress_level"] = st.slider(
                    "Stress Level (1-10)", 1, 10, 5
                )

            # Message input
            user_message = st.text_area(
                "Your Message",
                placeholder="How are you feeling today? What's on your mind?",
                height=100,
            )

            if st.button("Send Message", type="primary"):
                if user_message.strip():
                    payload = {
                        "user_id": user_id,
                        "message": user_message,
                        "mood_context": (
                            mood_context
                            if mood_context["current_mood"] != "neutral"
                            or mood_context["stress_level"] != 5
                            else {}
                        ),
                    }

                    with st.spinner("Getting response..."):
                        result = invoke_api("/chat", payload)

                    if result:
                        st.success("Response received!")
                        # Clean up the response display
                        clean_result = {}
                        if "response" in result:
                            clean_result["response"] = result["response"]
                        if "suggestions" in result:
                            clean_result["suggestions"] = result["suggestions"]
                        if "follow_up_questions" in result:
                            clean_result["follow_up_questions"] = result[
                                "follow_up_questions"
                            ]
                        if "mood_detected" in result:
                            clean_result["mood_detected"] = result["mood_detected"]
                        st.json(clean_result)
                    else:
                        st.error("Failed to get response")
                else:
                    st.warning("Please enter a message")

        with col2:
            st.subheader("Quick Actions")

            # Quick message buttons
            quick_messages = [
                "I'm feeling overwhelmed with work",
                "I had a great day today!",
                "I'm struggling with anxiety",
                "I need some motivation",
                "I can't sleep well lately",
            ]

            for msg in quick_messages:
                if st.button(f"💬 {msg}", key=f"quick_{msg}"):
                    st.session_state.quick_message = msg

            if hasattr(st.session_state, "quick_message"):
                st.text_area(
                    "Selected Message",
                    value=st.session_state.quick_message,
                    disabled=True,
                )

    with tab2:
        st.header("📊 Daily Mental Health Check-in")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Check-in Questions")

            checkin_type = st.selectbox(
                "Check-in Type",
                ["morning", "evening", "after-work"],
                help="When are you doing this check-in?",
                key="checkin_type_select",
            )

            # Rating questions
            responses = {}
            responses["mood_rating"] = st.slider(
                "How is your overall mood today? (1-10)", 1, 10, 5
            )
            responses["energy_level"] = st.slider(
                "How is your energy level? (1-10)", 1, 10, 5
            )
            responses["sleep_quality"] = st.slider(
                "How was your sleep quality? (1-10)", 1, 10, 5
            )
            responses["stress_level"] = st.slider(
                "How stressed do you feel? (1-10)", 1, 10, 5
            )
            responses["anxiety_level"] = st.slider(
                "How anxious do you feel? (1-10)", 1, 10, 5
            )
            responses["social_connection"] = st.slider(
                "How connected do you feel to others? (1-10)", 1, 10, 5
            )
            responses["productivity"] = st.slider(
                "How productive do you feel? (1-10)", 1, 10, 5
            )

        with col2:
            st.subheader("Reflection Questions")

            responses["gratitude"] = st.text_input(
                "What's one thing you're grateful for today?",
                placeholder="e.g., Having a good cup of coffee",
            )

            responses["challenges"] = st.text_input(
                "What's your main challenge or concern today?",
                placeholder="e.g., Work presentation tomorrow",
            )

            responses["goals"] = st.text_input(
                "What's one goal you have for today?",
                placeholder="e.g., Finish the presentation",
            )

            additional_notes = st.text_area(
                "Any additional thoughts or feelings?",
                placeholder="Share anything else that's on your mind...",
                height=100,
            )

            if st.button("Submit Check-in", type="primary"):
                payload = {
                    "user_id": user_id,
                    "checkin_type": checkin_type,
                    "responses": responses,
                    "additional_notes": additional_notes,
                }

                with st.spinner("Processing check-in..."):
                    result = invoke_api("/daily-checkin", payload)

                if result:
                    st.success("Check-in completed!")
                    st.json(result)
                else:
                    st.error("Failed to process check-in")

    with tab3:
        st.header("📈 Mental Health Evaluation")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Evaluation Settings")

            evaluation_period = st.selectbox(
                "Evaluation Period",
                ["week", "month", "quarter", "year"],
                help="Time period to analyze",
                key="evaluation_period_select",
            )

            include_chat_analysis = st.checkbox("Include Chat Analysis", value=True)
            include_checkin_data = st.checkbox("Include Check-in Data", value=True)

            if st.button("Run Evaluation", type="primary"):
                payload = {
                    "user_id": user_id,
                    "evaluation_period": evaluation_period,
                    "include_chat_analysis": include_chat_analysis,
                    "include_checkin_data": include_checkin_data,
                }

                with st.spinner("Analyzing mental health data..."):
                    result = invoke_api("/evaluate-mental-health", payload)

                if result:
                    st.success("Evaluation completed!")
                    st.json(result)
                else:
                    st.error("Failed to run evaluation")

        with col2:
            st.subheader("Evaluation Info")
            st.info(
                """
            The mental health evaluation analyzes your:
            - Check-in responses over time
            - Chat conversation patterns
            - Mood trends and changes
            - Risk factors and strengths
            
            This helps provide personalized insights and recommendations.
            """
            )

    with tab4:
        st.header("🎯 Personalized Recommendations")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Recommendation Settings")

            recommendation_type = st.selectbox(
                "Recommendation Type",
                [
                    "immediate",
                    "daily",
                    "weekly",
                    "stress_relief",
                    "mood_boost",
                    "sleep_aid",
                ],
                help="What type of recommendations do you need?",
                key="recommendation_type_select",
            )

            current_mood = st.selectbox(
                "Current Mood",
                [
                    "neutral",
                    "happy",
                    "sad",
                    "anxious",
                    "stressed",
                    "tired",
                    "excited",
                    "calm",
                ],
                index=0,
                key="recommendations_mood_select",
            )

            urgency_level = st.selectbox(
                "Urgency Level",
                ["low", "medium", "high"],
                index=1,
                key="urgency_level_select",
            )

            st.subheader("Preferences")
            content_types = st.multiselect(
                "Preferred Content Types",
                ["video", "audio", "text", "interactive"],
                default=["video", "audio"],
            )

            duration = st.selectbox(
                "Preferred Duration",
                ["short", "medium", "long"],
                index=1,
                key="duration_select",
            )

            activity_level = st.selectbox(
                "Preferred Activity Level",
                ["low", "moderate", "high"],
                index=1,
                key="activity_level_select",
            )

            if st.button("Get Recommendations", type="primary"):
                payload = {
                    "user_id": user_id,
                    "recommendation_type": recommendation_type,
                    "current_mood": current_mood,
                    "urgency_level": urgency_level,
                    "preferences": {
                        "content_types": content_types,
                        "duration": duration,
                        "activity_level": activity_level,
                    },
                }

                with st.spinner("Generating personalized recommendations..."):
                    result = invoke_api("/recommendations", payload)

                if result:
                    st.success("Recommendations generated!")
                    st.json(result)
                else:
                    st.error("Failed to generate recommendations")

        with col2:
            st.subheader("Recommendation Types")
            st.info(
                """
            **Immediate**: Quick relief for current feelings
            **Daily**: Activities for regular mental health maintenance
            **Weekly**: Longer-term wellness activities
            **Stress Relief**: Specifically for stress and anxiety
            **Mood Boost**: Activities to improve mood
            **Sleep Aid**: Help with sleep and relaxation
            """
            )

    with tab5:
        st.header("⏰ Schedule a Companion")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Schedule Settings")

            mental_health_score = st.slider(
                "Mental Health Score (0-100)",
                0,
                100,
                50,
                help="Overall mental health score from evaluation",
            )

            risk_level = st.selectbox(
                "Risk Level",
                ["low", "moderate", "high", "critical"],
                index=1,
                key="risk_level_select",
            )

            st.subheader("User Preferences")

            preferred_times = st.multiselect(
                "Preferred Check-in Times",
                ["06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
                default=["09:00", "18:00"],
            )

            max_checkins_per_week = st.slider("Maximum Check-ins per Week", 1, 7, 5)

            notification_methods = st.multiselect(
                "Notification Methods", ["email", "sms"], default=["email"]
            )

            last_checkin_date = st.date_input(
                "Last Check-in Date", value=datetime.now().date() - timedelta(days=1)
            )

            if st.button("Schedule Companion", type="primary"):
                payload = {
                    "user_id": user_id,
                    "mental_health_score": mental_health_score,
                    "risk_level": risk_level,
                    "user_preferences": {
                        "preferred_checkin_times": preferred_times,
                        "max_checkins_per_week": max_checkins_per_week,
                        "notification_methods": notification_methods,
                    },
                    "last_checkin_date": last_checkin_date.isoformat() + "T09:00:00Z",
                }

                with st.spinner("Scheduling companion..."):
                    result = invoke_api("/schedule-checkin", payload)

                if result:
                    st.success("Companion scheduled!")
                    st.json(result)
                else:
                    st.error("Failed to schedule companion")

        with col2:
            st.subheader("Companion Logic")
            st.info(
                """
            The agent schedules companions based on:
            
            **Mental Health Score**:
            - < 30: Daily companions
            - 30-50: Every 2 days
            - 50-70: Every 3 days
            - > 70: Weekly companions
            
            **Risk Level**:
            - Critical/High: More frequent companions
            - Moderate: Regular companions
            - Low: Less frequent companions
            
            **User Preferences**: Respects your preferred times and frequency limits
            """
            )

    # Footer
    st.markdown("---")
    st.markdown("**Mental Health Agent** - Built with AWS Bedrock and Lambda")
    st.markdown(
        "💡 **Tip**: This is a demo version. For production use, please deploy your own instance."
    )


if __name__ == "__main__":
    main()

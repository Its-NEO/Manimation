import streamlit as st
import requests
import time
import os
from PIL import Image
import base64

API_URL = "http://localhost:8000"  

st.set_page_config(page_title="Math Visualizer", page_icon="🧮", layout="wide")

st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-bottom: 0.5rem;
    }
    .info-text {
        font-size: 1rem;
        color: #424242;
    }
    .status-pending {
        color: #FFA000;
        font-weight: bold;
    }
    .status-complete {
        color: #2E7D32;
        font-weight: bold;
    }
    .status-error {
        color: #C62828;
        font-weight: bold;
    }
    .status-retry {
        color: #9C27B0;
        font-weight: bold;
    }
    .chat-user {
        background-color: #E3F2FD;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .chat-assistant {
        background-color: #F5F5F5;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .log-container {
        background-color: #F5F5F5;
        padding: 10px;
        border-radius: 5px;
        font-family: monospace;
        max-height: 200px;
        overflow-y: auto;
        margin-top: 10px;
        margin-bottom: 10px;
    }
</style>
""",
    unsafe_allow_html=True,
)


def get_video_download_link(video_path, link_text="Download Video"):
    with open(video_path, "rb") as file:
        video_bytes = file.read()
        b64 = base64.b64encode(video_bytes).decode()
        href = f'<a href="data:video/mp4;base64,{b64}" download="math_visualization.mp4">{link_text}</a>'
        return href


def poll_job_status(job_id):
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    log_placeholder = st.empty()

    retry_count = 0
    last_error = None

    stages = {
        "queued": "Job is queued",
        "generating_code": "Generating Manim code",
        "rendering_video": "Rendering visualization video",
        "processing_video": "Processing video file",
        "completed": "Visualization complete!",
        "failed": "Visualization failed",
    }

    progress_values = {
        "queued": 0.1,
        "generating_code": 0.3,
        "rendering_video": 0.7,
        "processing_video": 0.9,
        "completed": 1.0,
        "failed": 1.0,
    }

    current_status = "queued"
    error_message = None
    video_path = None

    start_time = time.time()

    while current_status not in ["completed", "failed"]:
        try:
            response = requests.get(f"{API_URL}/status/{job_id}")
            log_response = requests.get(f"{API_URL}/logs/{job_id}")

            # Always try to parse the responses, even if not 200
            try:
                data = response.json() if response.status_code == 200 else {"status": "error", "error": response.text}
                log_data = log_response.json() if log_response.status_code == 200 else {"error": log_response.text}
            except Exception as json_error:
                data = {"status": "error", "error": f"Invalid response: {str(json_error)}"}
                log_data = {"error": str(json_error)}
                
            # Continue if we at least got a status
            current_status = data["status"]
            error_message = data.get("error", "")
            video_path = data.get("video_path", "")
            
            # Handle special statuses first
            if data["status"] == "not_found":
                status_placeholder.markdown(
                    f"<div class='status-error'>⚠️ Job not found. The job may have expired or been deleted.</div>",
                    unsafe_allow_html=True,
                )
                # Set current_status to stop the polling
                current_status = "failed"
                error_message = "Job not found or expired"
                break
            elif data["status"] == "error":
                status_placeholder.markdown(
                    f"<div class='status-error'>⚠️ Error checking status: {data.get('error', 'Unknown error')}</div>",
                    unsafe_allow_html=True,
                )
                # Set current_status to stop the polling
                current_status = "failed"
                error_message = data.get('error', 'Unknown error')
                break
                
            # Handle explicit retry status formats and progress details from backend
            if current_status.startswith("retry_"):
                import re
                retry_match = re.search(r"retry_(\d+)_of_\d+", current_status)
                if retry_match:
                    retry_count = int(retry_match.group(1))
                else:
                    retry_count += 1
            elif (
                current_status in ["generating_code", "rendering_video"]
                and "attempt" in error_message.lower()
            ):
                import re
                retry_match = re.search(r"attempt (\d+)", error_message.lower())
                if retry_match:
                    retry_count = int(retry_match.group(1))
                else:
                    retry_count += 1

            elapsed_time = time.time() - start_time
            elapsed_str = f"{int(elapsed_time // 60)}m {int(elapsed_time % 60)}s"

            progress_value = progress_values.get(current_status, 0)
            if retry_count > 0 and (current_status.startswith("retry_") or current_status in [
                "generating_code",
                "rendering_video",
            ]):
                progress_value = max(0.2, progress_value - 0.1)
            progress_bar.progress(progress_value)

            # Extract meaningful status message from retry format
            if current_status.startswith("retry_"):
                base_status = "Retrying visualization generation"
                status_message = f"{base_status} ({current_status})"
            else:
                status_message = stages.get(current_status, current_status)

            if retry_count > 0 and current_status not in ["completed", "failed"]:
                status_placeholder.markdown(
                    f"<div class='status-retry'>🔄 {status_message} (Retry {retry_count}) - Elapsed: {elapsed_str}</div>",
                    unsafe_allow_html=True,
                )
            elif current_status == "failed":
                status_placeholder.markdown(
                    f"<div class='status-error'>⚠️ {status_message}: {error_message}</div>",
                    unsafe_allow_html=True,
                )
            elif current_status == "completed":
                status_placeholder.markdown(
                    f"<div class='status-complete'>✅ {status_message} - Total time: {elapsed_str}</div>",
                    unsafe_allow_html=True,
                )
            else:
                status_placeholder.markdown(
                    f"<div class='status-pending'>⏳ {status_message} - Elapsed: {elapsed_str}</div>",
                    unsafe_allow_html=True,
                )

            if error_message:
                log_placeholder.markdown(
                    f"<div class='log-container'>{error_message}</div>",
                    unsafe_allow_html=True,
                )

            if current_status == "completed":
                break

            time.sleep(3)
        except Exception as e:
            status_placeholder.markdown(
                f"<div class='status-error'>⚠️ Error: {str(e)}</div>",
                unsafe_allow_html=True,
            )
            break

    return current_status, video_path, error_message


def main():
    st.markdown(
        "<div class='main-header'>Mathematical Visualization Tool</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='info-text'>Create visualizations of mathematical concepts using Manim</div>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(
        ["Generate Visualization", "Chat with Assistant", "View Previous Jobs"]
    )

    with tab1:
        st.markdown(
            "<div class='sub-header'>Generate Math Visualization</div>",
            unsafe_allow_html=True,
        )
        st.markdown("Enter a mathematical topic or expression to visualize:")

        with st.form("visualization_form"):
            topic = st.text_area(
                "Mathematical Topic/Expression",
                placeholder="Example: Fourier series, Taylor expansion, Binary search, etc.",
            )
            submitted = st.form_submit_button("Generate Visualization")

        if submitted and topic:
            st.markdown(
                "<div class='sub-header'>Visualization Status</div>",
                unsafe_allow_html=True,
            )

            try:
                response = requests.post(f"{API_URL}/generate", json={"topic": topic})

                if response.status_code == 200:
                    data = response.json()
                    job_id = data["job_id"]

                    st.info(f"Visualization generation started (Job ID: {job_id})")

                    status, video_path, error = poll_job_status(job_id)

                    if status == "completed":
                        st.markdown(
                            "<div class='sub-header'>Visualization Result</div>",
                            unsafe_allow_html=True,
                        )

                        video_url = f"{API_URL}/video/{job_id}"
                        st.video(video_url)

                        st.markdown(
                            f"[Download Video]({video_url})", unsafe_allow_html=False
                        )

                        if "job_history" not in st.session_state:
                            st.session_state.job_history = []

                        st.session_state.job_history.append(
                            {
                                "job_id": job_id,
                                "topic": topic,
                                "status": status,
                                "video_url": video_url,
                            }
                        )
                    elif status == "failed":
                        st.error("Visualization failed to generate.")
                        st.markdown(
                            "<div class='sub-header'>Error Details</div>",
                            unsafe_allow_html=True,
                        )
                        st.code(error)

                else:
                    st.error(f"Failed to submit job: {response.text}")

            except Exception as e:
                st.error(f"Error: {str(e)}")

    with tab2:
        st.markdown(
            "<div class='sub-header'>Chat with Math Visualization Assistant</div>",
            unsafe_allow_html=True,
        )
        st.markdown("Ask questions about Manim code or mathematical visualizations:")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(
                    f"<div class='chat-user'>🧑‍💻 <b>You:</b> {message['content']}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='chat-assistant'>🤖 <b>Assistant:</b> {message['content']}</div>",
                    unsafe_allow_html=True,
                )

        with st.form("chat_form"):
            chat_message = st.text_area(
                "Your message",
                placeholder="Ask me anything about math visualizations or Manim code...",
            )
            chat_submitted = st.form_submit_button("Send Message")

        if chat_submitted and chat_message:
            st.session_state.chat_history.append(
                {"role": "user", "content": chat_message}
            )

            st.markdown(
                f"<div class='chat-user'>🧑‍💻 <b>You:</b> {chat_message}</div>",
                unsafe_allow_html=True,
            )

            with st.spinner("Thinking..."):
                try:
                    response = requests.post(
                        f"{API_URL}/chat", json={"message": chat_message}
                    )

                    if response.status_code == 200:
                        assistant_response = response.json()["response"]

                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": assistant_response}
                        )

                        st.markdown(
                            f"<div class='chat-assistant'>🤖 <b>Assistant:</b> \n{assistant_response}</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.error(f"Failed to get response: {response.text}")

                except Exception as e:
                    st.error(f"Error: {str(e)}")

            st.rerun()

    with tab3:
        st.markdown(
            "<div class='sub-header'>Previous Visualizations</div>",
            unsafe_allow_html=True,
        )

        if "job_history" not in st.session_state:
            st.session_state.job_history = []

        if st.button("Refresh Job List"):
            try:
                response = requests.get(f"{API_URL}/list-jobs")
                if response.status_code == 200:
                    jobs = response.json()["jobs"]
                    if not jobs:
                        st.info("No previous jobs found")
                    else:
                        st.session_state.job_history = []
                        for job in jobs:
                            job_id = job["job_id"]
                            status_response = requests.get(f"{API_URL}/status/{job_id}")
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                st.session_state.job_history.append(
                                    {
                                        "job_id": job_id,
                                        "topic": job["topic"],
                                        "status": status_data["status"],
                                        "video_url": (
                                            f"{API_URL}/video/{job_id}"
                                            if status_data["status"] == "completed"
                                            else None
                                        ),
                                    }
                                )
                        st.success(f"Retrieved {len(jobs)} jobs")
                        st.rerun()
                else:
                    st.error(f"Failed to get job list: {response.text}")
            except Exception as e:
                st.error(f"Error refreshing jobs: {str(e)}")

        if not st.session_state.job_history:
            st.info("No previous jobs found or loaded")
        else:
            for idx, job in enumerate(st.session_state.job_history):
                with st.expander(f"Job {idx+1}: {job['topic']} ({job['status']})"):
                    st.write(f"**Job ID:** {job['job_id']}")
                    st.write(f"**Topic:** {job['topic']}")
                    st.write(f"**Status:** {job['status']}")

                    if st.button(f"View Logs", key=f"logs_{job['job_id']}"):
                        try:
                            log_response = requests.get(
                                f"{API_URL}/logs/{job['job_id']}"
                            )
                            if log_response.status_code == 200:
                                log_data = log_response.json()
                                st.json(log_data)
                        except Exception as e:
                            st.error(f"Error fetching logs: {str(e)}")

                    if job["status"] == "completed" and job.get("video_url"):
                        st.video(job["video_url"])
                        st.markdown(
                            f"[Download Video]({job['video_url']})",
                            unsafe_allow_html=False,
                        )


if __name__ == "__main__":
    main()

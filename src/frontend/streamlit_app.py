"""Streamlit frontend application."""

import time
from typing import Optional
from datetime import datetime

import httpx
import streamlit as st

from src.shared.config import settings

# Page configuration
st.set_page_config(
    page_title="Marketing Crew - Multi-Agent System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API base URL
API_BASE_URL = f"http://{settings.backend_host}:{settings.backend_port}"


def check_backend_health() -> tuple[bool, str]:
    """Check if backend is available. Returns (is_healthy, error_message)."""
    try:
        # Use a shorter timeout but allow retries
        response = httpx.get(f"{API_BASE_URL}/health", timeout=2.0, follow_redirects=True)
        if response.status_code == 200:
            return True, ""
        else:
            return False, f"Backend returned status code {response.status_code}"
    except httpx.ConnectError as e:
        return False, f"Could not connect to {API_BASE_URL}. Is the server running? Error: {str(e)}"
    except httpx.TimeoutException:
        # Try one more time with a longer timeout
        try:
            response = httpx.get(f"{API_BASE_URL}/health", timeout=10.0, follow_redirects=True)
            if response.status_code == 200:
                return True, ""
            else:
                return False, f"Backend returned status code {response.status_code}"
        except Exception as e2:
            return False, f"Connection timeout. Backend may be slow to respond. Error: {str(e2)}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def create_task(topic: str, language: Optional[str] = None) -> Optional[dict]:
    """Create a new marketing task via API."""
    try:
        # Task creation should be fast - only creates DB record
        response = httpx.post(
            f"{API_BASE_URL}/tasks",
            json={"topic": topic, "language": language},
            timeout=10.0,
        )
        response.raise_for_status()
        result = response.json()
        # Verify we got a valid response
        if result and "task_id" in result:
            return result
        else:
            return None
    except httpx.TimeoutException:
        # Task might have been created, return None but don't show error
        # User will be redirected to View Tasks where they can check
        return None
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to backend at {API_BASE_URL}. Make sure the server is running.")
        st.session_state["backend_ok"] = False
        return None
    except httpx.HTTPStatusError as e:
        error_detail = "Unknown error"
        try:
            error_detail = e.response.json().get("detail", str(e.response.text))
        except:
            error_detail = str(e.response.text)
        st.error(f"❌ Server error ({e.response.status_code}): {error_detail}")
        return None
    except Exception as e:
        st.error(f"❌ Error creating task: {str(e)}")
        return None


def get_task(task_id: str) -> Optional[dict]:
    """Get task details via API."""
    try:
        response = httpx.get(f"{API_BASE_URL}/tasks/{task_id}", timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException:
        st.warning(f"⚠️ Request timed out while fetching task {task_id}")
        return None
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to backend at {API_BASE_URL}")
        st.session_state["backend_ok"] = False
        return None
    except httpx.HTTPStatusError as e:
        st.error(f"❌ Server error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        st.error(f"❌ Error fetching task: {str(e)}")
        return None


def list_tasks() -> list[dict]:
    """List all tasks via API."""
    try:
        response = httpx.get(f"{API_BASE_URL}/tasks", timeout=10.0)
        response.raise_for_status()
        tasks = response.json()
        # Ensure we return a list
        if isinstance(tasks, list):
            return tasks
        else:
            st.warning("⚠️ Unexpected response format from server")
            return []
    except httpx.TimeoutException:
        # Don't show error on timeout for list - just return empty
        # User can retry with refresh button
        return []
    except httpx.ConnectError:
        # Only show error once, not on every refresh
        if st.session_state.get("show_connection_error", True):
            st.error(f"❌ Cannot connect to backend at {API_BASE_URL}")
            st.session_state["show_connection_error"] = False
        st.session_state["backend_ok"] = False
        return []
    except httpx.HTTPStatusError as e:
        st.error(f"❌ Server error: {e.response.status_code}")
        return []
    except Exception as e:
        # Don't spam errors on every refresh
        return []


def cancel_task(task_id: str) -> Optional[dict]:
    """Cancel a task via API."""
    try:
        response = httpx.post(
            f"{API_BASE_URL}/tasks/{task_id}/cancel", timeout=10.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException:
        st.warning(f"⚠️ Request timed out while cancelling task {task_id}")
        return None
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to backend at {API_BASE_URL}")
        st.session_state["backend_ok"] = False
        return None
    except httpx.HTTPStatusError as e:
        st.error(f"❌ Server error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        st.error(f"❌ Error cancelling task: {str(e)}")
        return None


def delete_task(task_id: str) -> bool:
    """Delete a task via API."""
    try:
        response = httpx.delete(
            f"{API_BASE_URL}/tasks/{task_id}", timeout=10.0
        )
        response.raise_for_status()
        return True
    except httpx.TimeoutException:
        st.warning(f"⚠️ Request timed out while deleting task {task_id}")
        return False
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to backend at {API_BASE_URL}")
        st.session_state["backend_ok"] = False
        return False
    except httpx.HTTPStatusError as e:
        st.error(f"❌ Server error: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        st.error(f"❌ Error deleting task: {str(e)}")
        return False


def _render_task_card(task: dict, show_detailed_progress: bool = False):
    """Render a task card with progress information."""
    status = task['status']
    status_emoji = {
        "pending": "⏳",
        "in_progress": "🔄",
        "completed": "✅",
        "failed": "❌",
        "cancelled": "🚫"
    }.get(status, "📋")
    
    # Create a container for the task
    with st.container():
        # Header with status
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"### {status_emoji} {task['topic']}")
        with col2:
            st.markdown(f"**Status:** {status.upper()}")
        with col3:
            if task.get("created_at"):
                try:
                    created = datetime.fromisoformat(task["created_at"].replace("Z", "+00:00"))
                    elapsed = datetime.now(created.tzinfo) - created
                    minutes = int(elapsed.total_seconds() / 60)
                    seconds = int(elapsed.total_seconds() % 60)
                    st.caption(f"⏱️ {minutes}m {seconds}s")
                except:
                    st.caption(f"Created: {task['created_at'][:10]}")
        
        # Show detailed progress for in-progress tasks
        if show_detailed_progress and status in ["pending", "in_progress"]:
            st.markdown("---")
            st.markdown("#### 🤖 AI Agents Working (Sequential Process)")
            
            # Progress steps that simulate terminal output
            progress_steps = [
                {
                    "agent": "Marketing Strategist",
                    "emoji": "📊",
                    "description": "Developing comprehensive marketing strategy",
                    "details": [
                        "Analyzing market trends and competitive landscape",
                        "Identifying target audience segments",
                        "Defining key messaging and positioning",
                        "Recommending marketing channels"
                    ]
                },
                {
                    "agent": "Content Creator",
                    "emoji": "✍️",
                    "description": "Creating engaging content",
                    "details": [
                        "Developing blog post outlines",
                        "Crafting key messaging points",
                        "Creating content themes and topics",
                        "Designing content calendar suggestions"
                    ]
                },
                {
                    "agent": "Social Media Specialist",
                    "emoji": "📱",
                    "description": "Generating social media content",
                    "details": [
                        "Creating Instagram posts (visual-focused)",
                        "Crafting Twitter/X posts (concise, engaging)",
                        "Developing LinkedIn posts (professional, B2B)",
                        "Optimizing for platform-specific best practices"
                    ]
                },
                {
                    "agent": "Campaign Manager",
                    "emoji": "📅",
                    "description": "Coordinating campaign plan",
                    "details": [
                        "Planning timeline and milestones",
                        "Defining success metrics (KPIs)",
                        "Creating implementation steps",
                        "Assessing resource requirements"
                    ]
                }
            ]
            
            # Show progress in a terminal-like style
            for i, step in enumerate(progress_steps):
                # Simulate which step is currently active based on elapsed time
                elapsed_minutes = 0
                if task.get("created_at"):
                    try:
                        created = datetime.fromisoformat(task["created_at"].replace("Z", "+00:00"))
                        elapsed = datetime.now(created.tzinfo) - created
                        elapsed_minutes = elapsed.total_seconds() / 60
                    except:
                        pass
                
                # Estimate which agent is working (rough estimate: ~2-3 min per agent)
                current_step = min(int(elapsed_minutes / 2.5), len(progress_steps) - 1)
                
                if i < current_step:
                    # Completed step
                    st.markdown(f"✅ **{step['emoji']} {step['agent']}** - Completed")
                elif i == current_step:
                    # Current step
                    st.markdown(f"🔄 **{step['emoji']} {step['agent']}** - Working...")
                    with st.expander(f"📋 {step['description']}", expanded=True):
                        for detail in step['details']:
                            st.markdown(f"  • {detail}")
                else:
                    # Pending step
                    st.markdown(f"⏳ **{step['emoji']} {step['agent']}** - Pending")
            
            st.markdown("---")
        
        # Task metadata
        with st.expander("📋 Task Details", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Task ID:** `{task['task_id']}`")
                st.write(f"**Status:** {status}")
                st.write(f"**Created:** {task['created_at']}")
            with col2:
                if task.get("completed_at"):
                    st.write(f"**Completed:** {task['completed_at']}")
                if task.get("language"):
                    st.write(f"**Language:** {task['language']}")
                if task.get("error_message"):
                    st.error(f"**Error:** {task['error_message']}")
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("👁️ View Details", key=f"view_{task['task_id']}", use_container_width=True):
                st.session_state["selected_task_id"] = task["task_id"]
                st.session_state["page"] = "Task Details"
                st.rerun()
        
        with col2:
            can_cancel = status in ["pending", "in_progress"]
            if can_cancel:
                if st.button("❌ Cancel", key=f"cancel_{task['task_id']}", use_container_width=True):
                    with st.spinner("Cancelling task..."):
                        result = cancel_task(task["task_id"])
                        if result:
                            st.success("✅ Task cancelled successfully!")
                            st.rerun()
        
        with col3:
            can_delete = status in ["completed", "failed", "cancelled"]
            if can_delete:
                if st.button("🗑️ Delete", key=f"delete_{task['task_id']}", use_container_width=True):
                    if delete_task(task["task_id"]):
                        st.success("✅ Task deleted successfully!")
                        st.rerun()
        
        with col4:
            if status in ["pending", "in_progress"]:
                if st.button("🔄 Refresh", key=f"refresh_{task['task_id']}", use_container_width=True):
                    st.rerun()
        
        st.markdown("---")


def main():
    """Main Streamlit application."""
    st.title("🚀 Multi-Agent Marketing Crew")
    st.markdown("Create and manage marketing campaigns using AI agents")
    # Simple, non-blocking backend check
    backend_ok = st.session_state.get("backend_ok", None)
    if backend_ok is None:
        # Quick check without blocking
        try:
            response = httpx.get(f"{API_BASE_URL}/health", timeout=2.0)
            backend_ok = response.status_code == 200
        except:
            backend_ok = False
        st.session_state["backend_ok"] = backend_ok
    
    # Show minimal warning if backend is not available
    if not backend_ok:
        with st.expander("⚠️ Backend Connection Issue", expanded=False):
            st.warning(
                f"Backend at `{API_BASE_URL}` is not responding.\n\n"
                "**To start the backend:**\n"
                "```bash\n"
                "uv run uvicorn src.backend.main:app --reload --host 127.0.0.1 --port 8000\n"
                "```\n\n"
                "You can still try to use the app - it may work if the backend starts."
            )
            if st.button("🔄 Check Backend Again", key="check_backend"):
                st.session_state.pop("backend_ok", None)
                st.rerun()

    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        # Get current page from session state or default
        current_page = st.session_state.get("page", "Create Task")
        
        # Radio button for page selection
        page = st.radio(
            "Select Page",
            ["Create Task", "View Tasks", "Task Details"],
            index=["Create Task", "View Tasks", "Task Details"].index(current_page) if current_page in ["Create Task", "View Tasks", "Task Details"] else 0,
            key="page_selector",
        )
        
        # Update session state when page changes via radio button (without rerun to avoid loops)
        if page != current_page:
            st.session_state["page"] = page

        st.divider()
        st.markdown("### Settings")
        st.info(f"Backend: {API_BASE_URL}")
        st.info(f"Language: {settings.app_language}")

    # Main content area
    if page == "Create Task":
        st.header("Create New Marketing Task")
        st.markdown("Enter a topic and let our AI marketing team work on it!")

        # Show success message if task was just created (before form)
        if st.session_state.get("task_created_success", False):
            topic = st.session_state.get("task_created_topic", "")
            st.success("✅ **Task created successfully!**")
            st.info(f"⏳ **Please wait while the AI marketing team processes '{topic}'.**\n\n💡 **Tip:** Check the backend terminal to see the agents working in real-time. Once completed, go to 'View Tasks' to see the results.")
            st.markdown("---")

        with st.form("create_task_form", clear_on_submit=True):
            topic = st.text_input(
                "Marketing Topic",
                placeholder="e.g., Launch a new eco-friendly product line",
                help="Enter the topic or theme for the marketing campaign",
            )

            language = st.selectbox(
                "Output Language",
                ["en", "es", "fr", "de", "it", "pt"],
                index=0,
                help="Select the language for the marketing content",
            )

            submitted = st.form_submit_button("🚀 Create Task", use_container_width=True)

            if submitted:
                if not topic:
                    st.error("Please enter a marketing topic")
                else:
                    with st.spinner("Creating task..."):
                        task = create_task(topic, language)
                    
                    # Store success state for next render
                    if task and "task_id" in task:
                        st.session_state["last_task_id"] = task["task_id"]
                        st.session_state["task_created_success"] = True
                        st.session_state["task_created_topic"] = topic
                        st.rerun()
                    else:
                        # Task might have been created but response timed out
                        st.session_state["task_created_success"] = True
                        st.session_state["task_created_topic"] = topic
                        st.rerun()

    elif page == "View Tasks":
        st.header("📋 All Marketing Tasks")
        st.markdown("View and monitor all your marketing tasks in real-time")

        # Refresh controls
        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("🔄 Refresh Tasks", use_container_width=True, type="primary"):
                st.rerun()
        with col2:
            # Show last refresh time
            if "last_refresh" in st.session_state:
                st.caption(f"Last refresh: {st.session_state['last_refresh']}")
        
        # Update last refresh time
        st.session_state["last_refresh"] = datetime.now().strftime("%H:%M:%S")

        # Reset connection error flag when user manually refreshes
        if st.session_state.get("show_connection_error") is False:
            st.session_state["show_connection_error"] = True
        
        tasks = list_tasks()
        
        # Remove duplicates based on task_id - use dict to preserve order and ensure uniqueness
        if tasks:
            unique_tasks_dict = {}
            for task in tasks:
                task_id = task.get('task_id')
                if task_id:
                    # Only keep the first occurrence of each task_id
                    if task_id not in unique_tasks_dict:
                        unique_tasks_dict[task_id] = task
            tasks = list(unique_tasks_dict.values())

        if not tasks:
            st.info("📭 No tasks found. Create a new task to get started!")
            # Show hint if we just created a task
            if "last_task_id" in st.session_state:
                task_id = st.session_state["last_task_id"]
                st.warning(f"💡 **Task created but not visible yet.** Task ID: `{task_id}`")
                st.info("**Possible reasons:**")
                st.markdown("""
                - The task is being saved to the database
                - The backend is processing the request
                - Network delay
                
                **Try:** Click '🔄 Refresh Tasks' button again in a few seconds.
                """)
        else:
            # Separate tasks by status
            in_progress_tasks = [t for t in tasks if t['status'] in ["pending", "in_progress"]]
            completed_tasks = [t for t in tasks if t['status'] == "completed"]
            failed_tasks = [t for t in tasks if t['status'] == "failed"]
            cancelled_tasks = [t for t in tasks if t['status'] == "cancelled"]
            
            # Show in-progress tasks first with detailed progress
            if in_progress_tasks:
                st.markdown("### 🔄 Tasks In Progress")
                for task in in_progress_tasks:
                    _render_task_card(task, show_detailed_progress=True)
                st.markdown("---")
            
            # Show completed tasks
            if completed_tasks:
                st.markdown("### ✅ Completed Tasks")
                for task in completed_tasks:
                    _render_task_card(task, show_detailed_progress=False)
                st.markdown("---")
            
            # Show failed tasks
            if failed_tasks:
                st.markdown("### ❌ Failed Tasks")
                for task in failed_tasks:
                    _render_task_card(task, show_detailed_progress=False)
                st.markdown("---")
            
            # Show cancelled tasks
            if cancelled_tasks:
                st.markdown("### 🚫 Cancelled Tasks")
                for task in cancelled_tasks:
                    _render_task_card(task, show_detailed_progress=False)
            
            # Show info for in-progress tasks
            if in_progress_tasks:
                st.info("🔄 **Tasks in progress** - Click '🔄 Refresh Tasks' button above to see updates")

    elif page == "Task Details":
        st.header("Task Details")

        # Get task ID from session state or allow manual input
        task_id = st.session_state.get("selected_task_id") or st.session_state.get(
            "last_task_id"
        )

        if not task_id:
            task_id = st.text_input("Enter Task ID", placeholder="task-uuid-here")
            if st.button("Load Task", use_container_width=True):
                if task_id:
                    st.session_state["selected_task_id"] = task_id
                    st.rerun()
        else:
            st.info(f"**Task ID:** `{task_id}`")

            # Auto-refresh for pending/in_progress tasks
            task = get_task(task_id)
            if task:
                # Display task details
                col1, col2, col3 = st.columns(3)
                with col1:
                    status_emoji = {
                        "pending": "⏳",
                        "in_progress": "🔄",
                        "completed": "✅",
                        "failed": "❌",
                        "cancelled": "🚫"
                    }.get(task["status"], "📋")
                    st.metric("Status", f"{status_emoji} {task['status'].upper()}")
                with col2:
                    st.metric("Topic", task["topic"])
                with col3:
                    if task.get("completed_at"):
                        st.metric("Completed", task["completed_at"][:10])
                    elif task.get("created_at"):
                        st.metric("Created", task["created_at"][:10])

                st.divider()

                # Show progress for in-progress tasks
                if task["status"] in ["pending", "in_progress"]:
                    st.info("⏳ **Task is being processed by the AI marketing team...**")
                    
                    # Progress indicators with visual feedback
                    progress_steps = [
                        ("Marketing Strategist", "📊", "Developing comprehensive marketing strategy..."),
                        ("Content Creator", "✍️", "Creating engaging content and blog outlines..."),
                        ("Social Media Specialist", "📱", "Generating platform-optimized social media posts..."),
                        ("Campaign Manager", "📅", "Planning campaign timeline and metrics..."),
                    ]
                    
                    # Show progress steps
                    st.markdown("### 🚀 AI Agents Working")
                    progress_container = st.container()
                    with progress_container:
                        for agent_name, emoji, description in progress_steps:
                            st.markdown(f"{emoji} **{agent_name}**: {description}")
                    
                    # Show elapsed time
                    if task.get("created_at"):
                        try:
                            created = datetime.fromisoformat(task["created_at"].replace("Z", "+00:00"))
                            elapsed = datetime.now(created.tzinfo) - created
                            minutes = int(elapsed.total_seconds() / 60)
                            seconds = int(elapsed.total_seconds() % 60)
                            st.caption(f"⏱️ Elapsed time: {minutes}m {seconds}s")
                        except:
                            pass
                    
                    # Cancel button
                    st.markdown("---")
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("❌ Cancel Task", use_container_width=True, type="primary"):
                            with st.spinner("Cancelling task..."):
                                result = cancel_task(task_id)
                                if result:
                                    st.success("✅ Task cancelled successfully!")
                                    st.rerun()
                    with col2:
                        if st.button("🔄 Refresh Now", use_container_width=True):
                            st.rerun()
                    
                    # Note: Auto-refresh removed to prevent UI blocking
                    # Use the refresh button to manually update

                # Display results
                elif task["status"] == "completed":
                    st.success("✅ Task completed successfully!")

                    # Content Strategy
                    if task.get("content_strategy"):
                        st.subheader("📝 Content Strategy")
                        st.markdown(task["content_strategy"])

                    # Blog Outline
                    if task.get("blog_outline"):
                        st.subheader("📄 Blog Outline")
                        st.markdown(task["blog_outline"])

                    # Social Media Posts
                    if task.get("social_media_posts"):
                        st.subheader("📱 Social Media Posts")
                        for i, post in enumerate(task["social_media_posts"], 1):
                            with st.expander(f"Post {i}"):
                                st.markdown(post)

                    # Campaign Ideas
                    if task.get("campaign_ideas"):
                        st.subheader("💡 Campaign Ideas")
                        for i, idea in enumerate(task["campaign_ideas"], 1):
                            st.markdown(f"{i}. {idea}")

                    # Full Result
                    if task.get("result"):
                        st.subheader("📊 Full Result")
                        with st.expander("View Full Result"):
                            st.text(task["result"])

                elif task["status"] == "failed":
                    st.error("❌ Task failed")
                    if task.get("error_message"):
                        st.error(f"**Error:** {task['error_message']}")
                
                elif task["status"] == "cancelled":
                    st.info("🚫 Task was cancelled")
                    if task.get("error_message"):
                        st.info(f"**Reason:** {task['error_message']}")

                # Action buttons
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Refresh", use_container_width=True):
                        st.rerun()
                with col2:
                    # Allow deletion for completed, failed, or cancelled tasks
                    can_delete = task["status"] in ["completed", "failed", "cancelled"]
                    if can_delete:
                        if st.button("🗑️ Delete Task", use_container_width=True, type="secondary"):
                            if delete_task(task_id):
                                st.success("✅ Task deleted successfully!")
                                # Clear session state and redirect
                                st.session_state.pop("selected_task_id", None)
                                st.session_state.pop("last_task_id", None)
                                st.session_state["page"] = "View Tasks"
                                st.rerun()
            else:
                st.error("Task not found")


if __name__ == "__main__":
    main()


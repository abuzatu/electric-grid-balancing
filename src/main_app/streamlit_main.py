import streamlit as st
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def main():
    st.set_page_config(
        page_title="Electric Grid Optimization Suite",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialize session state
    if "current_app" not in st.session_state:
        st.session_state.current_app = "home"

    # Sidebar navigation
    with st.sidebar:
        st.title("⚡ Grid Optimization Suite")
        st.markdown("---")

        # Navigation buttons
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_app = "home"
            st.rerun()

        if st.button("⚡ Unit Commitment", use_container_width=True):
            st.session_state.current_app = "unit_commitment"
            st.rerun()

        if st.button("🔋 Virtual Power Plant", use_container_width=True):
            st.session_state.current_app = "vpp"
            st.rerun()

        st.markdown("---")
        st.markdown("**Current Module:**")
        if st.session_state.current_app == "home":
            st.info("🏠 Home")
        elif st.session_state.current_app == "unit_commitment":
            st.success("⚡ Unit Commitment")
        elif st.session_state.current_app == "vpp":
            st.success("🔋 Virtual Power Plant")

    # Main content area
    if st.session_state.current_app == "home":
        show_home_page()
    elif st.session_state.current_app == "unit_commitment":
        show_unit_commitment_app()
    elif st.session_state.current_app == "vpp":
        show_vpp_app()


def show_home_page():
    """Display the home/landing page"""
    st.title("⚡ Electric Grid Optimization Suite")

    st.markdown(
        """
    Welcome to the Electric Grid Optimization Suite! This application provides advanced 
    optimization tools for power system operations and planning.
    """
    )

    # App selection cards
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ⚡ Unit Commitment Optimizer")
        st.markdown(
            """
        **Optimize power plant operations:**
        - Multi-period unit scheduling
        - Cost minimization
        - Constraint satisfaction
        - Ramp rate limitations
        - Reserve requirements
        """
        )

        if st.button(
            "Launch Unit Commitment →", key="uc_launch", use_container_width=True
        ):
            st.session_state.current_app = "unit_commitment"
            st.rerun()

    with col2:
        st.markdown("### 🔋 Virtual Power Plant")
        st.markdown(
            """
        **Coordinate distributed resources:**
        - Aggregated control
        - Demand response
        - Energy storage optimization
        - Renewable integration
        - Market participation
        """
        )

        if st.button(
            "Launch VPP Optimizer →", key="vpp_launch", use_container_width=True
        ):
            st.session_state.current_app = "vpp"
            st.rerun()

    # Additional info
    st.markdown("---")

    with st.expander("ℹ️ About This Suite"):
        st.markdown(
            """
        This optimization suite provides:
        
        **🔧 Advanced Algorithms:**
        - Mixed Integer Linear Programming (MILP)
        - OR-Tools optimization engine
        - Real-time constraint solving
        
        **📊 Rich Visualizations:**
        - Interactive charts and plots
        - Real-time optimization results
        - Detailed analysis reports
        
        **⚙️ Flexible Configuration:**
        - Customizable parameters
        - Multiple constraint options
        - Scenario testing capabilities
        
        **📈 Professional Reports:**
        - CSV data export
        - Publication-ready plots
        - Detailed cost breakdowns
        """
        )


def show_unit_commitment_app():
    """Display the Unit Commitment application"""
    try:
        # Import and run the UC app
        from unit_commitment_01.streamlit_app import main as uc_main

        # Add back button
        with st.sidebar:
            st.markdown("---")
            if st.button("← Back to Home", key="uc_back"):
                st.session_state.current_app = "home"
                st.rerun()

        # Run the UC app
        uc_main()

    except ImportError as e:
        st.error(f"❌ Could not load Unit Commitment app: {e}")
        st.info("Make sure the unit_commitment_01 module is available.")


def show_vpp_app():
    """Display the Virtual Power Plant application"""
    try:
        # Import and run the VPP app
        from vpp_example_01.streamlit_app import main as vpp_main

        # Add back button
        with st.sidebar:
            st.markdown("---")
            if st.button("← Back to Home", key="vpp_back"):
                st.session_state.current_app = "home"
                st.rerun()

        # Run the VPP app
        vpp_main()

    except ImportError as e:
        st.error(f"❌ Could not load VPP app: {e}")
        st.info("Make sure the vpp_example_01 module is available.")
    except AttributeError:
        st.error("❌ VPP app does not have a main() function")
        st.info("The VPP app needs to be refactored to have a main() function.")


if __name__ == "__main__":
    main()

"""
Simulation History & Analytics Export Dashboard View
"""

import streamlit as st
import pandas as pd

from database.db_manager import db_manager
from analytics.export import (
    export_simulation_runs_to_csv,
    export_simulation_runs_to_json,
    export_telemetry_to_csv,
    export_telemetry_to_json,
)


def render_history_view():
    """Renders the historical persistence and benchmark reports view."""
    st.title("Historical Database & Analytics")
    st.caption(
        "Inspect historical simulation traces saved to SQLite, analyze longitudinal trends, "
        "and export simulation benchmarks and telemetry archives to CSV or JSON formats."
    )

    tab_runs, tab_telemetry, tab_maint = st.tabs(
        [
            "Simulation Run Records",
            "Telemetry Archive",
            "Database Maintenance",
        ]
    )

    with tab_runs:
        st.subheader("Saved Simulation Benchmark Runs")

        col_f1, col_f2 = st.columns([1.5, 1])
        with col_f1:
            cat_filter = st.selectbox(
                "Filter by Category",
                ["All Categories", "CPU Scheduling", "Memory Allocation", "Page Replacement", "Disk Scheduling"],
            )
        with col_f2:
            limit_val = st.number_input("Max Records", min_value=10, max_value=200, value=50, step=10)

        query_cat = None if cat_filter == "All Categories" else cat_filter
        runs = db_manager.get_simulation_runs(category=query_cat, limit=int(limit_val))

        if runs:
            table_rows = []
            for r in runs:
                table_rows.append(
                    {
                        "Run ID": r["run_id"],
                        "Category": r["category"],
                        "Algorithm": r["algorithm_name"],
                        "Metrics": str(r["metrics"]),
                        "Executed At": r["created_at"],
                    }
                )
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

            # Export actions
            st.divider()
            c_csv, c_json = st.columns(2)
            with c_csv:
                csv_data = export_simulation_runs_to_csv(runs)
                st.download_button(
                    " Export Runs to CSV",
                    data=csv_data,
                    file_name="os_sim_runs.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            with c_json:
                json_data = export_simulation_runs_to_json(runs)
                st.download_button(
                    " Export Runs to JSON",
                    data=json_data,
                    file_name="os_sim_runs.json",
                    mime="application/json",
                    use_container_width=True,
                )
        else:
            st.info("No saved simulation records found in database. Run simulations to log benchmarks.")

    with tab_telemetry:
        st.subheader("Archived System Telemetry Snapshots")
        snaps = db_manager.get_telemetry_snapshots(limit=100)

        if snaps:
            st.dataframe(pd.DataFrame(snaps), use_container_width=True, hide_index=True)

            c_tcsv, c_tjson = st.columns(2)
            with c_tcsv:
                t_csv = export_telemetry_to_csv(snaps)
                st.download_button(
                    " Export Telemetry to CSV",
                    data=t_csv,
                    file_name="os_sim_telemetry.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            with c_tjson:
                t_json = export_telemetry_to_json(snaps)
                st.download_button(
                    " Export Telemetry to JSON",
                    data=t_json,
                    file_name="os_sim_telemetry.json",
                    mime="application/json",
                    use_container_width=True,
                )
        else:
            st.info("No telemetry logs found in database.")

    with tab_maint:
        st.subheader("Database Maintenance")
        st.warning(" Purging the database permanently deletes all saved runs and telemetry snapshots.")

        if st.button(" Purge Database Records", type="secondary"):
            db_manager.clear_all()
            st.success("Database records successfully purged.")
            st.rerun()

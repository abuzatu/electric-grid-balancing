"""
Streamlit app for Unit Commitment Optimization
"""

import streamlit as st
import sys
import os
import tempfile
import base64
import pandas as pd
import time
from pathlib import Path

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from unit_commitment_01.solve_unit_commitment import SolveUnitCommitment
from unit_commitment_01 import configs
from ortools.linear_solver import pywraplp

def get_image_download_link(img_path, filename, text):
    """Generate a download link for an image file."""
    with open(img_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="{filename}">{text}</a>'
    return href

def create_custom_time_periods(demand_values, reserve_values):
    """Create custom time periods configuration from demand and reserve values."""
    time_periods = []
    for t in range(len(demand_values)):
        time_periods.append({
            'demand': demand_values[t],
            'reserve': reserve_values[t]
        })
    return time_periods

def main():
    st.set_page_config(
        page_title="Unit Commitment Optimizer",
        page_icon="⚡",
        layout="wide"
    )
    
    st.title("⚡ Unit Commitment Optimization")
    st.markdown("---")
    
    # Sidebar for configuration
    st.sidebar.header("🔧 Configuration")
    
    # Problem parameters
    st.sidebar.subheader("Problem Parameters")
    
    # Quick preset buttons at the top
    st.sidebar.write("**Quick Preset Problems:**")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("📚 Example Problem"):
            st.session_state.load_example = True
    with col2:
        if st.button("🏠 24h Residential"):
            st.session_state.load_24h = "residential"
    
    col3, col4 = st.sidebar.columns(2)
    with col3:
        if st.button("🏭 24h Industrial"):
            st.session_state.load_24h = "industrial"
    with col4:
        if st.button("🏖️ 24h Weekend"):
            st.session_state.load_24h = "weekend"
    
    col5, col6 = st.sidebar.columns(2)
    with col5:
        if st.button("🏢 24h Residential Large"):
            st.session_state.load_24h = "residential_large"
    with col6:
        if st.button("🏗️ 24h Residential Extra Large"):
            st.session_state.load_24h = "residential_extra_large"
    
    # Unit configuration section
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔧 Unit Configuration")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("📋 Load Current Units"):
            st.session_state.load_units = True
    
    with col2:
        if st.button("🔄 Reset to Default"):
            # Convert list of units to dictionary format for easier manipulation
            units_dict = {}
            for unit in configs.units_example:
                units_dict[unit['name']] = unit.copy()
            st.session_state.units = units_dict
            st.sidebar.success("✅ Reset to default units!")
    
    if 'load_units' in st.session_state and st.session_state.load_units:
        st.sidebar.success("✅ Loaded current units! Modify parameters below.")
        st.session_state.load_units = None
    
    # Helper functions (defined outside the conditional blocks)
    def get_default_demand(t):
        if t < len(configs.time_periods_example):
            return configs.time_periods_example[t]['demand']
        else:
            # Create a realistic 24-hour daily pattern
            hour_of_day = t % 24
            
            # Base demand varies by time of day
            if 0 <= hour_of_day <= 5:  # Night (midnight to 6 AM)
                base_demand = 120
            elif 6 <= hour_of_day <= 8:  # Early morning (6-9 AM)
                base_demand = 180
            elif 9 <= hour_of_day <= 11:  # Morning peak (9 AM - noon)
                base_demand = 250
            elif 12 <= hour_of_day <= 13:  # Lunch time (noon - 2 PM)
                base_demand = 200
            elif 14 <= hour_of_day <= 17:  # Afternoon (2-6 PM)
                base_demand = 220
            elif 18 <= hour_of_day <= 21:  # Evening peak (6-10 PM)
                base_demand = 280
            else:  # Late evening (10 PM - midnight)
                base_demand = 160
            
            return base_demand
    
    def get_default_reserve(t):
        if t < len(configs.time_periods_example):
            return configs.time_periods_example[t]['reserve']
        else:
            # Default reserve is 10 MW for additional periods
            return 10
    
    def check_constraint_feasibility(units, demand_values, reserve_values, enable_power_balance, enable_reserve_capacity, 
                                   enable_generation_limits, enable_ramp_up, enable_ramp_down, enable_min_up_time, enable_min_down_time):
        """
        Check if the problem is likely to be feasible with the given constraints.
        Returns a list of potential issues.
        """
        issues = []
        
        # Convert units to list if it's a dictionary
        if isinstance(units, dict):
            units_list = list(units.values())
        else:
            units_list = units
        
        # 1. Power Balance Constraint Check
        if enable_power_balance:
            total_max_power = sum(unit['P_max'] for unit in units_list)
            # Exclude t=0 from demand analysis (optimization horizon is t=1 to t=T)
            max_demand = max(demand_values[1:])  # Skip t=0
            if total_max_power < max_demand:
                issues.append(f"❌ **Power Balance Constraint:** Total maximum power ({total_max_power} MW) < Maximum demand ({max_demand} MW)")
            
            # Note: We don't check total_min_power vs min_demand because:
            # - Units can be turned OFF to produce 0 MW
            # - The solver can match any demand by turning units on/off
            # - Only the maximum capacity constraint matters
        
        # 2. Reserve Capacity Constraint Check
        if enable_reserve_capacity:
            total_max_power = sum(unit['P_max'] for unit in units_list)
            # Exclude t=0 from demand+reserve analysis
            max_demand_plus_reserve = max(demand_values[i] + reserve_values[i] for i in range(1, len(demand_values)))
            if total_max_power < max_demand_plus_reserve:
                issues.append(f"❌ **Reserve Capacity Constraint:** Total maximum power ({total_max_power} MW) < Maximum demand+reserve ({max_demand_plus_reserve} MW)")
        
        # 3. Generation Limits Constraint Check
        if enable_generation_limits:
            for i, unit in enumerate(units_list):
                if unit['P_min'] > unit['P_max']:
                    issues.append(f"❌ **Generation Limits Constraint:** Unit {unit['name']} - P_min ({unit['P_min']} MW) > P_max ({unit['P_max']} MW)")
        
        # 4. Ramp Constraints Check
        if enable_ramp_up or enable_ramp_down:
            for i, unit in enumerate(units_list):
                if unit['RU'] > unit['P_max']:
                    issues.append(f"❌ **Ramp Up Constraint:** Unit {unit['name']} - Ramp Up ({unit['RU']} MW/h) > P_max ({unit['P_max']} MW)")
                if unit['RD'] > unit['P_max']:
                    issues.append(f"❌ **Ramp Down Constraint:** Unit {unit['name']} - Ramp Down ({unit['RD']} MW/h) > P_max ({unit['P_max']} MW)")
        
        # 5. Min Up/Down Time Constraint Check
        if enable_min_up_time or enable_min_down_time:
            for i, unit in enumerate(units_list):
                if unit['TU'] > len(demand_values) - 1:
                    issues.append(f"❌ **Min Up Time Constraint:** Unit {unit['name']} - Min up time ({unit['TU']} h) > Planning horizon ({len(demand_values)-1} h)")
                if unit['TD'] > len(demand_values) - 1:
                    issues.append(f"❌ **Min Down Time Constraint:** Unit {unit['name']} - Min down time ({unit['TD']} h) > Planning horizon ({len(demand_values)-1} h)")
        
        # 6. Initial State Consistency Check
        for i, unit in enumerate(units_list):
            # Check if initial state is consistent
            if unit['u0'] and unit['p0'] < unit['P_min']:
                issues.append(f"❌ **Initial State Constraint:** Unit {unit['name']} - ON at t=0 but p0 ({unit['p0']} MW) < P_min ({unit['P_min']} MW)")
            if not unit['u0'] and unit['p0'] > 0:
                issues.append(f"❌ **Initial State Constraint:** Unit {unit['name']} - OFF at t=0 but p0 ({unit['p0']} MW) > 0")
            if unit['su0'] and unit['u0']:
                issues.append(f"❌ **Initial State Constraint:** Unit {unit['name']} - Cannot be both ON (u0=True) and starting up (su0=True) at t=0")
            if unit['sd0'] and not unit['u0']:
                issues.append(f"❌ **Initial State Constraint:** Unit {unit['name']} - Cannot be shutting down (sd0=True) when OFF (u0=False) at t=0")
        
        # 7. Startup/Shutdown Ramp Check
        for i, unit in enumerate(units_list):
            if unit['SU'] > unit['P_max']:
                issues.append(f"❌ **Startup Ramp Constraint:** Unit {unit['name']} - Startup ramp ({unit['SU']} MW) > P_max ({unit['P_max']} MW)")
            if unit['SD'] > unit['P_max']:
                issues.append(f"❌ **Shutdown Ramp Constraint:** Unit {unit['name']} - Shutdown ramp ({unit['SD']} MW) > P_max ({unit['P_max']} MW)")
        
        # 8. Ramp Rate Feasibility Check (subtle constraint)
        if enable_ramp_up or enable_ramp_down:
            for i, unit in enumerate(units_list):
                # Check if unit can ramp up from P_min to P_max within reasonable time
                if unit['P_max'] > unit['P_min']:
                    ramp_time_needed = (unit['P_max'] - unit['P_min']) / unit['RU']
                    if ramp_time_needed > len(demand_values) - 1:
                        issues.append(f"❌ **Ramp Feasibility:** Unit {unit['name']} - Needs {ramp_time_needed:.1f}h to ramp from P_min to P_max, but planning horizon is only {len(demand_values)-1}h")
        
        # 9. Initial State to Final State Feasibility
        for i, unit in enumerate(units_list):
            if unit['u0']:  # If unit is ON at t=0
                # Check if unit can reach P_max from p0 within planning horizon
                if unit['p0'] < unit['P_max']:
                    ramp_time_needed = (unit['P_max'] - unit['p0']) / unit['RU']
                    if ramp_time_needed > len(demand_values) - 1:
                        issues.append(f"❌ **Initial State Ramp:** Unit {unit['name']} - Needs {ramp_time_needed:.1f}h to ramp from p0 ({unit['p0']} MW) to P_max ({unit['P_max']} MW)")
        
        # 10. Min Up/Down Time vs Planning Horizon
        if enable_min_up_time or enable_min_down_time:
            for i, unit in enumerate(units_list):
                if unit['TU'] + unit['TD'] > len(demand_values) - 1:
                    issues.append(f"❌ **Min Up/Down Time:** Unit {unit['name']} - Combined min up ({unit['TU']}h) + min down ({unit['TD']}h) time > planning horizon ({len(demand_values)-1}h)")
        
        # 11. Reserve Margin Check (subtle constraint)
        if enable_reserve_capacity:
            total_max_power = sum(unit['P_max'] for unit in units_list)
            # Check if there's enough flexibility for reserve
            total_min_power = sum(unit['P_min'] for unit in units_list)
            max_demand = max(demand_values[1:])
            max_reserve = max(reserve_values[1:])
            
            # Reserve margin = max_power - (demand + reserve)
            reserve_margin = total_max_power - (max_demand + max_reserve)
            if reserve_margin < 0:
                issues.append(f"❌ **Reserve Margin:** Insufficient capacity for demand + reserve. Need {max_demand + max_reserve} MW, have {total_max_power} MW")
            elif reserve_margin < 10:  # Warning if very tight
                issues.append(f"⚠️ **Tight Reserve Margin:** Only {reserve_margin:.1f} MW margin between max capacity and demand+reserve")
        
        return issues
    
    def analyze_unit_usage(units, demand_values, reserve_values, solution):
        """
        Analyze why certain units might not be used in the solution.
        Returns a list of insights about unit usage.
        """
        insights = []
        
        # Convert units to list if it's a dictionary
        if isinstance(units, dict):
            units_list = list(units.values())
        else:
            units_list = units
        
        # 1. Check if low-cost units are being used
        units_by_cost = sorted(units_list, key=lambda x: x['c'])  # Sort by variable cost
        cheapest_unit = units_by_cost[0]
        most_expensive_unit = units_by_cost[-1]
        
        insights.append(f"💰 **Cost Analysis:**")
        insights.append(f"   - Cheapest unit: {cheapest_unit['name']} (${cheapest_unit['c']}/MWh)")
        insights.append(f"   - Most expensive unit: {most_expensive_unit['name']} (${most_expensive_unit['c']}/MWh)")
        
        # 2. Check if cheapest unit is actually being used
        if solution and 'unit_power' in solution:
            cheapest_used = False
            total_cheapest_power = 0
            for t in range(1, len(demand_values)):  # Skip t=0
                if cheapest_unit['name'] in solution['unit_power'] and t in solution['unit_power'][cheapest_unit['name']]:
                    power = solution['unit_power'][cheapest_unit['name']][t]
                    if power > 0:
                        cheapest_used = True
                        total_cheapest_power += power
            
            if cheapest_used:
                insights.append(f"   ✅ {cheapest_unit['name']} IS being used (total: {total_cheapest_power:.1f} MWh)")
            else:
                insights.append(f"   ❌ {cheapest_unit['name']} is NOT being used despite being cheapest!")
                
                # 3. Analyze why cheapest unit might not be used
                insights.append(f"🔍 **Why {cheapest_unit['name']} might not be used:**")
                
                # Check capacity constraints
                if cheapest_unit['P_max'] < max(demand_values[1:]):
                    insights.append(f"   - P_max ({cheapest_unit['P_max']} MW) < max demand ({max(demand_values[1:])} MW)")
                
                # Check ramp constraints
                if cheapest_unit['RU'] < cheapest_unit['P_max'] - cheapest_unit['P_min']:
                    insights.append(f"   - Ramp up ({cheapest_unit['RU']} MW/h) might be too slow")
                
                # Check min up/down time constraints
                if cheapest_unit['TU'] > len(demand_values) - 1:
                    insights.append(f"   - Min up time ({cheapest_unit['TU']} h) > planning horizon ({len(demand_values)-1} h)")
                
                # Check initial state constraints
                if cheapest_unit['u0'] and cheapest_unit['p0'] < cheapest_unit['P_min']:
                    insights.append(f"   - Initial state: ON but p0 ({cheapest_unit['p0']} MW) < P_min ({cheapest_unit['P_min']} MW)")
                
                # Check if other units are forced to be on due to initial state
                forced_units = []
                for unit in units_list:
                    if unit['u0'] and unit['p0'] > 0:
                        forced_units.append(f"{unit['name']} (p0={unit['p0']} MW)")
                if forced_units:
                    insights.append(f"   - Other units forced ON: {', '.join(forced_units)}")
        
        # 4. Check total system capacity vs demand
        total_max_power = sum(unit['P_max'] for unit in units_list)
        max_demand = max(demand_values[1:])
        insights.append(f"📊 **Capacity vs Demand:**")
        insights.append(f"   - Total max power: {total_max_power} MW")
        insights.append(f"   - Max demand: {max_demand} MW")
        insights.append(f"   - Capacity margin: {total_max_power - max_demand} MW")
        
        # 5. Check if there are startup/shutdown costs preventing switching
        startup_costs = [(unit['name'], unit['SU_cost']) for unit in units_list]
        startup_costs.sort(key=lambda x: x[1])
        insights.append(f"🚀 **Startup Costs (lowest to highest):**")
        for name, cost in startup_costs:
            insights.append(f"   - {name}: ${cost}")
        
        return insights
    
    # Initialize default values
    if 'planning_horizon' not in st.session_state:
        st.session_state.planning_horizon = 7  # Default value (7 planning periods)
    
    if 'demand_values' not in st.session_state:
        st.session_state.demand_values = []
    if 'reserve_values' not in st.session_state:
        st.session_state.reserve_values = []
    
    # Initialize units in session state if not present
    if 'units' not in st.session_state:
        # Convert list of units to dictionary format for easier manipulation
        units_dict = {}
        for unit in configs.units_example:
            units_dict[unit['name']] = unit.copy()
        st.session_state.units = units_dict
    else:
        # Safety check: ensure units is a dictionary, not a list
        if isinstance(st.session_state.units, list):
            # Convert list to dictionary format
            units_dict = {}
            for unit in st.session_state.units:
                units_dict[unit['name']] = unit.copy()
            st.session_state.units = units_dict
    
    demand_values = st.session_state.demand_values
    reserve_values = st.session_state.reserve_values
    
    # Handle pattern loading first
    if 'load_example' in st.session_state and st.session_state.load_example:
        # Load example problem (7 periods from original config)
        num_periods = 7
        st.session_state.planning_horizon = 6  # 6 planning periods
        st.session_state.demand_values = [configs.time_periods_example[t]['demand'] for t in range(num_periods)]
        st.session_state.reserve_values = [configs.time_periods_example[t]['reserve'] for t in range(num_periods)]
        demand_values = st.session_state.demand_values
        reserve_values = st.session_state.reserve_values
        st.sidebar.success("✅ Loaded Example Problem (6-period planning horizon: t=1 to t=6)!")
        st.session_state.load_example = None
    elif 'load_24h' in st.session_state and st.session_state.load_24h:
        # Load 24-hour pattern
        pattern_type = st.session_state.load_24h
        st.sidebar.write(f"🔍 Debug: Loading pattern type: {pattern_type}")
        
        if pattern_type == "residential":
            pattern_data = configs.time_periods_24h
        elif pattern_type == "industrial":
            pattern_data = configs.time_periods_24h_industrial
        elif pattern_type == "weekend":
            pattern_data = configs.time_periods_24h_weekend
        elif pattern_type == "residential_large":
            pattern_data = configs.time_periods_24h_large
        elif pattern_type == "residential_extra_large":
            pattern_data = configs.time_periods_24h_extra_large
        else:
            pattern_data = configs.time_periods_24h
        
        # Set number of periods to match the pattern length (25 periods: t=0 to t=24)
        num_periods = len(pattern_data)
        st.session_state.planning_horizon = num_periods - 1  # 24 planning periods
        st.session_state.demand_values = [period['demand'] for period in pattern_data]
        st.session_state.reserve_values = [period['reserve'] for period in pattern_data]
        demand_values = st.session_state.demand_values
        reserve_values = st.session_state.reserve_values
        
        st.sidebar.write(f"🔍 Debug: Pattern loaded - num_periods={num_periods}, planning_horizon={num_periods-1}")
        st.sidebar.write(f"🔍 Debug: Loaded {len(demand_values)} periods, first demand: {demand_values[0]}")
        st.sidebar.write(f"🔍 Debug: All demand values: {demand_values}")
        st.sidebar.success(f"✅ Loaded {pattern_type.capitalize()} {num_periods-1}-period planning horizon (t=1 to t={num_periods-1})!")
        st.session_state.load_24h = None
    
    # Always show the slider (after pattern loading)
    st.sidebar.write("**Number of Time Periods:**")
    # Show planning horizon length (excluding t=0) in the slider
    planning_horizon = st.sidebar.slider("Planning Horizon", min_value=3, max_value=47, value=st.session_state.planning_horizon, 
                                        help="Number of planning periods (t=1 to t=T). Total periods will be T+1 (including t=0)")
    # Update session state
    st.session_state.planning_horizon = planning_horizon
    # Convert back to total periods
    num_periods = planning_horizon + 1
    
    # Debug: Show what the slider is doing
    st.sidebar.write(f"🔍 Debug: Slider set planning_horizon={planning_horizon}, num_periods={num_periods}")
    
    # Always create the input widgets with current values
    st.sidebar.write("**Demand and Reserve by Period:**")
    
    # Ensure demand_values and reserve_values have the right length
    while len(demand_values) < num_periods:
        t = len(demand_values)
        demand_values.append(get_default_demand(t))
    while len(reserve_values) < num_periods:
        t = len(reserve_values)
        reserve_values.append(get_default_reserve(t))
    
    # Truncate if needed
    demand_values = demand_values[:num_periods]
    reserve_values = reserve_values[:num_periods]
    
    for t in range(num_periods):
        col1, col2 = st.sidebar.columns(2)
        with col1:
            demand = col1.number_input(f"Demand t={t}", min_value=0, max_value=800, 
                                     value=demand_values[t] if t < len(demand_values) else 0,
                                     key=f"demand_{t}",
                                     help=f"Demand for period {t}")
        with col2:
            reserve = col2.number_input(f"Reserve t={t}", min_value=0, max_value=50, 
                                      value=reserve_values[t] if t < len(reserve_values) else 0,
                                      key=f"reserve_{t}",
                                      help=f"Reserve for period {t}")
        
        # Update the values list with the widget values
        if t >= len(demand_values):
            demand_values.append(demand)
        else:
            demand_values[t] = demand
            
        if t >= len(reserve_values):
            reserve_values.append(reserve)
        else:
            reserve_values[t] = reserve
    
    # Update session state with current values
    st.session_state.demand_values = demand_values
    st.session_state.reserve_values = reserve_values
    
    # Constraint toggles
    st.sidebar.subheader("Constraints")
    enable_power_balance = st.sidebar.checkbox("Power Balance", value=True, help="Ensure power production equals demand")
    enable_reserve_capacity = st.sidebar.checkbox("Reserve Capacity", value=True, help="Ensure sufficient reserve capacity")
    enable_logical_consistency = st.sidebar.checkbox("Logical Consistency", value=True, help="Enforce logical consistency between unit states")
    enable_generation_limits = st.sidebar.checkbox("Generation Limits", value=True, help="Enforce minimum and maximum generation limits")
    enable_ramp_up = st.sidebar.checkbox("Ramp Up", value=True, help="Enforce ramp up constraints")
    enable_ramp_down = st.sidebar.checkbox("Ramp Down", value=True, help="Enforce ramp down constraints")
    enable_min_up_time = st.sidebar.checkbox("Minimum Up Time", value=True, help="Enforce minimum up time constraints")
    enable_min_down_time = st.sidebar.checkbox("Minimum Down Time", value=True, help="Enforce minimum down time constraints")
    
    # Test scenarios
    st.sidebar.subheader("Test Scenarios")
    st.sidebar.write("💡 **Tip:** Try disabling 'Reserve Capacity' to see a different solution!")
    st.sidebar.write("💡 **Tip:** Try enabling 'Min Up/Down Time' to see if it affects the solution!")
    
    # Display current configuration
    st.sidebar.subheader("Current Settings")
    st.sidebar.write(f"**Planning Horizon:** {num_periods-1} periods (t=1 to t={num_periods-1})")
    st.sidebar.write(f"**Total Periods:** {num_periods} (including t=0)")
    st.sidebar.write(f"**Units:** {len(st.session_state.units)}")
    
    # Show demand summary
    total_demand = sum(demand_values)
    avg_demand = total_demand / len(demand_values) if demand_values else 0
    st.sidebar.write(f"**Total Demand:** {total_demand} MW")
    st.sidebar.write(f"**Average Demand:** {avg_demand:.1f} MW")
    
    # Performance warning for large problems - REMOVED
    # Users can now run large problems without warnings
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 Problem Overview")
        
        # Display time periods
        st.write("**Time Periods Configuration:**")
        time_df = pd.DataFrame([{'demand': demand_values[i], 'reserve': reserve_values[i]} 
                               for i in range(len(demand_values))])
        time_df.index = [f"t={i}" for i in range(len(demand_values))]
        # Rename columns to show units
        time_df = time_df.rename(columns={
            'demand': 'Demand (MW)',
            'reserve': 'Reserve (MW)'
        })
        st.dataframe(time_df, use_container_width=True)
        
        # Unit configuration section
        st.write("**Unit Configuration:**")
        
        # Display current units with modification capabilities
        for i, (unit_name, unit_config) in enumerate(st.session_state.units.items()):
            with st.expander(f"📊 {unit_name}", expanded=False):
                col1_inner, col2_inner = st.columns(2)
                
                with col1_inner:
                    # Basic parameters
                    st.write("**Basic Parameters:**")
                    unit_config['P_min'] = st.number_input(
                        f"P_min (MW) - {unit_name}",
                        min_value=0.0,
                        max_value=1000.0,
                        value=float(unit_config['P_min']),
                        step=0.1,
                        key=f"p_min_{i}"
                    )
                    unit_config['P_max'] = st.number_input(
                        f"P_max (MW) - {unit_name}",
                        min_value=0.0,
                        max_value=1000.0,
                        value=float(unit_config['P_max']),
                        step=0.1,
                        key=f"p_max_{i}"
                    )
                    unit_config['RU'] = st.number_input(
                        f"Ramp Up (MW/h) - {unit_name}",
                        min_value=0.0,
                        max_value=1000.0,
                        value=float(unit_config['RU']),
                        step=0.1,
                        key=f"ramp_up_{i}"
                    )
                    unit_config['RD'] = st.number_input(
                        f"Ramp Down (MW/h) - {unit_name}",
                        min_value=0.0,
                        max_value=1000.0,
                        value=float(unit_config['RD']),
                        step=0.1,
                        key=f"ramp_down_{i}"
                    )
                    unit_config['SU'] = st.number_input(
                        f"Startup Ramp (MW) - {unit_name}",
                        min_value=0.0,
                        max_value=1000.0,
                        value=float(unit_config['SU']),
                        step=0.1,
                        key=f"startup_ramp_{i}"
                    )
                    unit_config['SD'] = st.number_input(
                        f"Shutdown Ramp (MW) - {unit_name}",
                        min_value=0.0,
                        max_value=1000.0,
                        value=float(unit_config['SD']),
                        step=0.1,
                        key=f"shutdown_ramp_{i}"
                    )
                
                with col2_inner:
                    # Cost parameters
                    st.write("**Cost Parameters:**")
                    unit_config['SU_cost'] = st.number_input(
                        f"Startup Cost ($) - {unit_name}",
                        min_value=0.0,
                        max_value=10000.0,
                        value=float(unit_config['SU_cost']),
                        step=1.0,
                        key=f"startup_cost_{i}"
                    )
                    unit_config['SD_cost'] = st.number_input(
                        f"Shutdown Cost ($) - {unit_name}",
                        min_value=0.0,
                        max_value=10000.0,
                        value=float(unit_config['SD_cost']),
                        step=1.0,
                        key=f"shutdown_cost_{i}"
                    )
                    unit_config['c'] = st.number_input(
                        f"Variable Cost ($/MWh) - {unit_name}",
                        min_value=0.0,
                        max_value=1000.0,
                        value=float(unit_config['c']),
                        step=0.1,
                        key=f"variable_cost_{i}"
                    )
                    unit_config['cU'] = st.number_input(
                        f"Fixed Cost ($/h) - {unit_name}",
                        min_value=0.0,
                        max_value=10000.0,
                        value=float(unit_config['cU']),
                        step=1.0,
                        key=f"fixed_cost_{i}"
                    )
                
                # Minimum up/down time parameters
                col3_inner, col4_inner = st.columns(2)
                with col3_inner:
                    st.write("**Minimum Up/Down Times:**")
                    unit_config['TU'] = st.number_input(
                        f"Min Up Time (h) - {unit_name}",
                        min_value=1,
                        max_value=24,
                        value=int(unit_config['TU']),
                        key=f"min_up_time_{i}"
                    )
                    unit_config['TD'] = st.number_input(
                        f"Min Down Time (h) - {unit_name}",
                        min_value=1,
                        max_value=24,
                        value=int(unit_config['TD']),
                        key=f"min_down_time_{i}"
                    )
                
                with col4_inner:
                    st.write("**Initial State:**")
                    unit_config['U0'] = st.number_input(
                        f"U0 (required ON time at start) - {unit_name}",
                        min_value=0,
                        max_value=24,
                        value=int(unit_config['U0']),
                        key=f"u0_{i}"
                    )
                    unit_config['D0'] = st.number_input(
                        f"D0 (required OFF time at start) - {unit_name}",
                        min_value=0,
                        max_value=24,
                        value=int(unit_config['D0']),
                        key=f"d0_{i}"
                    )
                    unit_config['p0'] = st.number_input(
                        f"p0 (power at t=0) - {unit_name}",
                        min_value=0.0,
                        max_value=1000.0,
                        value=float(unit_config['p0']),
                        step=0.1,
                        key=f"p0_{i}"
                    )
                    unit_config['u0'] = st.checkbox(
                        f"u0 (ON at t=0) - {unit_name}",
                        value=bool(unit_config['u0']),
                        key=f"u0_checkbox_{i}"
                    )
                    unit_config['su0'] = st.checkbox(
                        f"su0 (startup at t=0) - {unit_name}",
                        value=bool(unit_config['su0']),
                        key=f"su0_checkbox_{i}"
                    )
                    unit_config['sd0'] = st.checkbox(
                        f"sd0 (shutdown at t=0) - {unit_name}",
                        value=bool(unit_config['sd0']),
                        key=f"sd0_checkbox_{i}"
                    )
        
        # Display units summary table
        st.write("**Units Summary:**")
        units_data = []
        for unit_name, unit_config in st.session_state.units.items():
            units_data.append({
                'Unit': unit_name,
                'P_min (MW)': unit_config['P_min'],
                'P_max (MW)': unit_config['P_max'],
                'Fixed Cost ($/h)': unit_config['cU'],
                'Variable Cost ($/MWh)': unit_config['c'],
                'Startup Cost ($)': unit_config['SU_cost'],
                'Shutdown Cost ($)': unit_config['SD_cost'],
                'Ramp Up (MW/h)': unit_config['RU'],
                'Ramp Down (MW/h)': unit_config['RD'],
                'Startup Ramp (MW)': unit_config['SU'],
                'Shutdown Ramp (MW)': unit_config['SD'],
                'Min Up Time (h)': unit_config['TU'],
                'Min Down Time (h)': unit_config['TD'],
                'U0': unit_config['U0'],
                'D0': unit_config['D0'],
                'p0 (MW)': unit_config['p0'],
                'ON at t=0': 'Yes' if unit_config['u0'] else 'No'
            })
        units_df = pd.DataFrame(units_data)
        st.dataframe(units_df, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Objective")
        st.write("Minimize total system cost")
        
        st.subheader("📋 Constraints")
        if enable_power_balance:
            st.write("• **Power balance** ✅")
        else:
            st.write("• Power balance ❌")
        if enable_reserve_capacity:
            st.write("• **Reserve capacity** ✅")
        else:
            st.write("• Reserve capacity ❌")
        if enable_logical_consistency:
            st.write("• **Logical consistency** ✅")
        else:
            st.write("• Logical consistency ❌")
        if enable_generation_limits:
            st.write("• **Generation limits** ✅")
        else:
            st.write("• Generation limits ❌")
        if enable_ramp_up:
            st.write("• **Ramp up** ✅")
        else:
            st.write("• Ramp up ❌")
        if enable_ramp_down:
            st.write("• **Ramp down** ✅")
        else:
            st.write("• Ramp down ❌")
        if enable_min_up_time:
            st.write("• **Minimum up time** ✅")
        else:
            st.write("• Minimum up time ❌")
        if enable_min_down_time:
            st.write("• **Minimum down time** ✅")
        else:
            st.write("• Minimum down time ❌")
    
    # Add new unit section (separate from main columns)
    st.markdown("---")
    st.subheader("➕ Add New Unit")
    
    with st.form("add_new_unit"):
        new_unit_name = st.text_input("Unit Name:", key="new_unit_name")
        
        col1_form, col2_form = st.columns(2)
        with col1_form:
            st.write("**Basic Parameters:**")
            new_p_min = st.number_input("P_min (MW):", min_value=0.0, max_value=1000.0, value=50.0, step=0.1)
            new_p_max = st.number_input("P_max (MW):", min_value=0.0, max_value=1000.0, value=200.0, step=0.1)
            new_ramp_up = st.number_input("Ramp Up (MW/h):", min_value=0.0, max_value=1000.0, value=50.0, step=0.1)
            new_ramp_down = st.number_input("Ramp Down (MW/h):", min_value=0.0, max_value=1000.0, value=50.0, step=0.1)
            new_startup_ramp = st.number_input("Startup Ramp (MW):", min_value=0.0, max_value=1000.0, value=50.0, step=0.1)
            new_shutdown_ramp = st.number_input("Shutdown Ramp (MW):", min_value=0.0, max_value=1000.0, value=50.0, step=0.1)
        
        with col2_form:
            st.write("**Cost Parameters:**")
            new_startup_cost = st.number_input("Startup Cost ($):", min_value=0.0, max_value=10000.0, value=1000.0, step=1.0)
            new_shutdown_cost = st.number_input("Shutdown Cost ($):", min_value=0.0, max_value=10000.0, value=500.0, step=1.0)
            new_variable_cost = st.number_input("Variable Cost ($/MWh):", min_value=0.0, max_value=1000.0, value=50.0, step=0.1)
            new_fixed_cost = st.number_input("Fixed Cost ($/h):", min_value=0.0, max_value=10000.0, value=100.0, step=1.0)
        
        col3_form, col4_form = st.columns(2)
        with col3_form:
            st.write("**Minimum Up/Down Times:**")
            new_min_up_time = st.number_input("Min Up Time (h):", min_value=1, max_value=24, value=4)
            new_min_down_time = st.number_input("Min Down Time (h):", min_value=1, max_value=24, value=2)
        
        with col4_form:
            st.write("**Initial State:**")
            new_u0 = st.number_input("U0 (required ON time at start):", min_value=0, max_value=24, value=0)
            new_d0 = st.number_input("D0 (required OFF time at start):", min_value=0, max_value=24, value=0)
            new_p0 = st.number_input("p0 (power at t=0):", min_value=0.0, max_value=1000.0, value=0.0, step=0.1)
            new_u0_status = st.checkbox("u0 (ON at t=0):", value=False)
            new_su0 = st.checkbox("su0 (startup at t=0):", value=False)
            new_sd0 = st.checkbox("sd0 (shutdown at t=0):", value=False)
        
        if st.form_submit_button("➕ Add Unit"):
            if new_unit_name and new_unit_name not in st.session_state.units:
                st.session_state.units[new_unit_name] = {
                    'name': new_unit_name,
                    'P_min': new_p_min,
                    'P_max': new_p_max,
                    'RU': new_ramp_up,
                    'RD': new_ramp_down,
                    'SU': new_startup_ramp,
                    'SD': new_shutdown_ramp,
                    'SU_cost': new_startup_cost,
                    'SD_cost': new_shutdown_cost,
                    'c': new_variable_cost,
                    'cU': new_fixed_cost,
                    'TU': new_min_up_time,
                    'TD': new_min_down_time,
                    'U0': new_u0,
                    'D0': new_d0,
                    'u0': new_u0_status,
                    'p0': new_p0,
                    'su0': new_su0,
                    'sd0': new_sd0
                }
                st.success(f"✅ Added unit: {new_unit_name}")
                st.rerun()
            elif new_unit_name in st.session_state.units:
                st.error(f"❌ Unit '{new_unit_name}' already exists!")
            else:
                st.error("❌ Please provide a unit name!")
    
    # Remove unit section
    st.markdown("---")
    st.subheader("🗑️ Remove Unit")
    
    if len(st.session_state.units) > 1:  # Keep at least one unit
        unit_to_remove = st.selectbox(
            "Select unit to remove:",
            list(st.session_state.units.keys()),
            key="remove_unit_select"
        )
        
        if st.button("🗑️ Remove Selected Unit"):
            del st.session_state.units[unit_to_remove]
            st.success(f"✅ Removed unit: {unit_to_remove}")
            st.rerun()
    else:
        st.info("ℹ️ At least one unit must remain in the system.")
    
    # Solve button
    st.markdown("---")
    if st.button("🚀 Solve Optimization Problem", type="primary", use_container_width=True):
        
        with st.spinner("Solving the optimization problem..."):
            try:
                # Create custom time periods configuration
                custom_time_periods = create_custom_time_periods(demand_values, reserve_values)
                
                # Debug: Show what values are being used
                st.write("🔍 **Debug: Values being used by solver:**")
                st.write(f"  Number of periods: {num_periods}")
                st.write(f"  Demand values: {demand_values}")
                st.write(f"  Reserve values: {reserve_values}")
                st.write(f"  Custom time periods length: {len(custom_time_periods)}")
                
                # Debug: Show unit configuration being used
                st.write("🔍 **Debug: Unit configuration being used:**")
                units_debug_data = []
                for unit_name, unit_config in st.session_state.units.items():
                    units_debug_data.append({
                        'Unit': unit_name,
                        'P_min (MW)': unit_config['P_min'],
                        'P_max (MW)': unit_config['P_max'],
                        'RU (MW/h)': unit_config['RU'],
                        'RD (MW/h)': unit_config['RD'],
                        'SU (MW)': unit_config['SU'],
                        'SD (MW)': unit_config['SD'],
                        'Fixed Cost ($/h)': unit_config['cU'],
                        'Variable Cost ($/MWh)': unit_config['c'],
                        'Startup Cost ($)': unit_config['SU_cost'],
                        'Shutdown Cost ($)': unit_config['SD_cost'],
                        'Min Up Time (h)': unit_config['TU'],
                        'Min Down Time (h)': unit_config['TD'],
                        'U0': unit_config['U0'],
                        'D0': unit_config['D0'],
                        'p0 (MW)': unit_config['p0'],
                        'u0 (ON)': 'Yes' if unit_config['u0'] else 'No',
                        'su0': 'Yes' if unit_config['su0'] else 'No',
                        'sd0': 'Yes' if unit_config['sd0'] else 'No'
                    })
                units_debug_df = pd.DataFrame(units_debug_data)
                st.dataframe(units_debug_df, use_container_width=True)
                
                # Pre-solver constraint feasibility check
                st.write("🔍 **Pre-solver constraint check:**")
                issues = check_constraint_feasibility(st.session_state.units, demand_values, reserve_values, enable_power_balance, enable_reserve_capacity, 
                                                   enable_generation_limits, enable_ramp_up, enable_ramp_down, enable_min_up_time, enable_min_down_time)
                if issues:
                    st.warning("⚠️ **Potential constraint issues detected:**")
                    for issue in issues:
                        st.write(f"  • {issue}")
                    st.write("💡 **Tip:** Fix these issues before running the solver to avoid infeasibility.")
                else:
                    st.success("✅ **No obvious constraint issues detected.**")
                
                # Create solver with custom constraints and configuration
                run_id = int(time.time() * 1000)  # Unique run identifier
                st.write(f"🔄 **Starting optimization run #{run_id}**")
                st.write(f"📊 **Problem Size:** {num_periods} periods, {len(st.session_state.units)} units")
                
                # Convert session state units to list format expected by solver
                units_list = []
                for unit_name, unit_config in st.session_state.units.items():
                    # Ensure all required fields are present
                    unit_dict = {
                        'name': unit_name,
                        'P_min': unit_config['P_min'],
                        'P_max': unit_config['P_max'],
                        'RU': unit_config['RU'],
                        'RD': unit_config['RD'],
                        'SU': unit_config['SU'],
                        'SD': unit_config['SD'],
                        'SU_cost': unit_config['SU_cost'],
                        'SD_cost': unit_config['SD_cost'],
                        'c': unit_config['c'],
                        'cU': unit_config['cU'],
                        'TU': unit_config['TU'],
                        'TD': unit_config['TD'],
                        'U0': unit_config['U0'],
                        'D0': unit_config['D0'],
                        'u0': unit_config['u0'],
                        'p0': unit_config['p0'],
                        'su0': unit_config['su0'],
                        'sd0': unit_config['sd0']
                    }
                    units_list.append(unit_dict)
                
                solver = SolveUnitCommitment(
                    enable_power_balance=enable_power_balance,
                    enable_reserve_capacity=enable_reserve_capacity,
                    enable_logical_consistency=enable_logical_consistency,
                    enable_generation_limits=enable_generation_limits,
                    enable_ramp_up=enable_ramp_up,
                    enable_ramp_down=enable_ramp_down,
                    enable_min_up_time=enable_min_up_time,
                    enable_min_down_time=enable_min_down_time,
                    time_periods=custom_time_periods,
                    units=units_list
                )
                
                # Solve
                solver.fit()
                status = solver.solver.Solve()
                
                if status == pywraplp.Solver.OPTIMAL:
                    st.success("✅ OPTIMAL SOLUTION FOUND!")
                else:
                    st.error("❌ NO SOLUTION FOUND!")
                    st.write("🔍 **Debug: Unit configuration that caused the failure:**")
                    units_debug_data = []
                    for unit_name, unit_config in st.session_state.units.items():
                        units_debug_data.append({
                            'Unit': unit_name,
                            'P_min (MW)': unit_config['P_min'],
                            'P_max (MW)': unit_config['P_max'],
                            'RU (MW/h)': unit_config['RU'],
                            'RD (MW/h)': unit_config['RD'],
                            'SU (MW)': unit_config['SU'],
                            'SD (MW)': unit_config['SD'],
                            'Fixed Cost ($/h)': unit_config['cU'],
                            'Variable Cost ($/MWh)': unit_config['c'],
                            'Startup Cost ($)': unit_config['SU_cost'],
                            'Shutdown Cost ($)': unit_config['SD_cost'],
                            'Min Up Time (h)': unit_config['TU'],
                            'Min Down Time (h)': unit_config['TD'],
                            'U0': unit_config['U0'],
                            'D0': unit_config['D0'],
                            'p0 (MW)': unit_config['p0'],
                            'u0 (ON)': 'Yes' if unit_config['u0'] else 'No',
                            'su0': 'Yes' if unit_config['su0'] else 'No',
                            'sd0': 'Yes' if unit_config['sd0'] else 'No'
                        })
                    units_debug_df = pd.DataFrame(units_debug_data)
                    st.dataframe(units_debug_df, use_container_width=True)
                    
                    # Show potential issues
                    st.write("🔍 **Potential issues to check:**")
                    total_max_power = sum(unit_config['P_max'] for unit_config in st.session_state.units.values())
                    max_demand = max(demand_values[1:])  # Skip t=0
                    st.write(f"  • Total maximum power: {total_max_power} MW")
                    st.write(f"  • Maximum demand (t=1 to t=T): {max_demand} MW")
                    if total_max_power < max_demand:
                        st.write(f"  ⚠️ **Problem:** Total maximum power ({total_max_power} MW) < Maximum demand ({max_demand} MW)")
                    
                    # Check ramp constraints
                    for unit_name, unit_config in st.session_state.units.items():
                        if unit_config['RU'] > unit_config['P_max']:
                            st.write(f"  ⚠️ **Problem:** Unit {unit_name} - Ramp Up ({unit_config['RU']} MW/h) > P_max ({unit_config['P_max']} MW)")
                        if unit_config['RD'] > unit_config['P_max']:
                            st.write(f"  ⚠️ **Problem:** Unit {unit_name} - Ramp Down ({unit_config['RD']} MW/h) > P_max ({unit_config['P_max']} MW)")
                    
                                        # Check constraint feasibility
                    issues = check_constraint_feasibility(st.session_state.units, demand_values, reserve_values, enable_power_balance, enable_reserve_capacity, 
                                                       enable_generation_limits, enable_ramp_up, enable_ramp_down, enable_min_up_time, enable_min_down_time)
                    if issues:
                        st.write("🔍 **Potential constraint issues:**")
                        for issue in issues:
                            st.write(f"  • {issue}")
                    
                    # Additional debugging for when no obvious issues are found
                    st.write("🔍 **Additional debugging info:**")
                    
                    # Check solver status details
                    if hasattr(solver.solver, 'NumConstraints'):
                        st.write(f"  • Number of constraints: {solver.solver.NumConstraints()}")
                    if hasattr(solver.solver, 'NumVariables'):
                        st.write(f"  • Number of variables: {solver.solver.NumVariables()}")
                    
                    # Check if any units have very large P_max values that might cause numerical issues
                    for unit_name, unit_config in st.session_state.units.items():
                        if unit_config['P_max'] > 10000:
                            st.write(f"  ⚠️ **Large P_max:** Unit {unit_name} has P_max = {unit_config['P_max']} MW (might cause numerical issues)")
                    
                    # Check for potential logical inconsistencies
                    for unit_name, unit_config in st.session_state.units.items():
                        if unit_config['P_min'] == unit_config['P_max'] and unit_config['P_min'] > 0:
                            st.write(f"  ⚠️ **Fixed Output Unit:** Unit {unit_name} has P_min = P_max = {unit_config['P_min']} MW (no flexibility)")
                        
                        if unit_config['RU'] == 0 and unit_config['RD'] == 0:
                            st.write(f"  ⚠️ **No Ramp Flexibility:** Unit {unit_name} has RU = RD = 0 (cannot change output)")
                    
                    # Check if the problem might be too complex
                    total_vars_estimate = len(st.session_state.units) * num_periods * 4  # u, p, su, sd variables per unit per period
                    if total_vars_estimate > 10000:
                        st.write(f"  ⚠️ **Large Problem:** Estimated {total_vars_estimate} variables (might be computationally challenging)")
                    
                    return
                
                # Calculate metrics
                total_cost = solver.solver.Objective().Value()
                total_power = sum(solver.p[j, t].solution_value() 
                                for j in range(solver.num_units) 
                                for t in range(1, solver.num_periods))
                total_units = sum(solver.u[j, t].solution_value() 
                                for j in range(solver.num_units) 
                                for t in range(1, solver.num_periods))
                solver_time = solver.solver.wall_time()
                
                # Calculate detailed cost breakdown
                fixed_costs = sum(solver.configs_units[j]['cU'] * solver.u[j, t].solution_value() 
                                for j in range(solver.num_units) 
                                for t in range(1, solver.num_periods))
                variable_costs = sum(solver.configs_units[j]['c'] * solver.p[j, t].solution_value() 
                                   for j in range(solver.num_units) 
                                   for t in range(1, solver.num_periods))
                startup_costs = sum(solver.configs_units[j]['SU_cost'] * solver.su[j, t].solution_value() 
                                  for j in range(solver.num_units) 
                                  for t in range(1, solver.num_periods))
                shutdown_costs = sum(solver.configs_units[j]['SD_cost'] * solver.sd[j, t].solution_value() 
                                   for j in range(solver.num_units) 
                                   for t in range(1, solver.num_periods))
                
                # Display results with debugging info
                st.write(f"🔍 **Debug Info:** Cost={total_cost:.2f}, Power={total_power:.1f}, Units={total_units:.0f}, Time={solver_time:.2f}s")
                st.write(f"💰 **Cost Breakdown:** Fixed=${fixed_costs:.2f}, Variable=${variable_costs:.2f}, Startup=${startup_costs:.2f}, Shutdown=${shutdown_costs:.2f}")
                
                # Test constraint configuration
                st.write(f"🔧 **Active Constraints:** Power Balance={solver.enable_power_balance}, Reserve={solver.enable_reserve_capacity}, Logic={solver.enable_logical_consistency}, Limits={solver.enable_generation_limits}, Ramp Up={solver.enable_ramp_up}, Ramp Down={solver.enable_ramp_down}, Min Up={solver.enable_min_up_time}, Min Down={solver.enable_min_down_time}")
                
                # Show constraint changes
                st.write(f"🔧 **Constraint Changes:** Power Balance={enable_power_balance}, Reserve={enable_reserve_capacity}, Logic={enable_logical_consistency}, Limits={enable_generation_limits}, Ramp Up={enable_ramp_up}, Ramp Down={enable_ramp_down}, Min Up={enable_min_up_time}, Min Down={enable_min_down_time}")
                
                # Show some key solution values to verify they're different
                st.write("🔍 **Solution Verification:**")
                for t in range(1, min(4, solver.num_periods)):  # Show first 3 periods
                    total_p = sum(solver.p[j, t].solution_value() for j in range(solver.num_units))
                    total_units = sum(solver.u[j, t].solution_value() for j in range(solver.num_units))
                    st.write(f"  t={t}: Total Power={total_p:.1f} MW, Units ON={total_units:.0f}")
                
                # Check if this is a different solution from a "baseline"
                st.write("🔍 **Solution Analysis:**")
                if not enable_reserve_capacity:
                    st.write("  ⚠️ **Reserve Capacity disabled** - This should allow more flexible unit scheduling!")
                if enable_min_up_time or enable_min_down_time:
                    st.write("  ⚠️ **Min Up/Down Time enabled** - This should force units to stay on/off longer!")
                if not enable_ramp_up and not enable_ramp_down:
                    st.write("  ⚠️ **Ramp constraints disabled** - This should allow faster power changes!")
                if not enable_generation_limits:
                    st.write("  ⚠️ **Generation limits disabled** - This should allow more extreme power outputs!")
                
                # Analyze unit usage to understand why low-cost units might not be used
                st.write("🔍 **Unit Usage Analysis:**")
                # Create solution dictionary for analysis
                solution_dict = {
                    'unit_power': {},
                    'unit_status': {},
                    'startup': {},
                    'shutdown': {}
                }
                
                # Extract solution data
                for j in range(solver.num_units):
                    unit_name = solver.configs_units[j]['name']
                    solution_dict['unit_power'][unit_name] = {}
                    solution_dict['unit_status'][unit_name] = {}
                    solution_dict['startup'][unit_name] = {}
                    solution_dict['shutdown'][unit_name] = {}
                    
                    for t in range(solver.num_periods):
                        solution_dict['unit_power'][unit_name][t] = solver.p[j, t].solution_value()
                        solution_dict['unit_status'][unit_name][t] = solver.u[j, t].solution_value()
                        solution_dict['startup'][unit_name][t] = solver.su[j, t].solution_value()
                        solution_dict['shutdown'][unit_name][t] = solver.sd[j, t].solution_value()
                
                # Run unit usage analysis
                usage_insights = analyze_unit_usage(st.session_state.units, demand_values, reserve_values, solution_dict)
                for insight in usage_insights:
                    st.write(insight)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Cost", f"${total_cost:.2f}")
                with col2:
                    st.metric("Total Power", f"{total_power:.1f} MW")
                with col3:
                    st.metric("Total Unit-Hours", f"{total_units:.0f}")
                with col4:
                    st.metric("Solver Time", f"{solver_time:.2f}s")
                
                # Create visualizations
                st.subheader("📈 Results Visualization")
                
                # Import visualization functions
                from unit_commitment_01.visualize_results import (
                    create_power_balance_plot,
                    create_unit_status_plot,
                    create_enhanced_power_balance_plot,
                    create_total_power_plot,
                    create_detailed_analysis_plot,
                    print_decision_variables_table,
                    export_to_csv
                )
                
                # Create temporary directory for plots
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    
                    # Generate plots
                    plot_files = {}
                    
                    with st.spinner("Generating visualizations..."):
                        # Power balance plot
                        fig1 = create_power_balance_plot(solver, str(temp_path / "power_balance.png"))
                        plot_files["Power Balance"] = temp_path / "power_balance.png"
                        
                        # Unit status plot
                        fig2 = create_unit_status_plot(solver, str(temp_path / "unit_status.png"))
                        plot_files["Unit Status"] = temp_path / "unit_status.png"
                        
                        # Enhanced power balance plot
                        fig3 = create_enhanced_power_balance_plot(solver, str(temp_path / "enhanced_power_balance.png"))
                        plot_files["Enhanced Power Balance"] = temp_path / "enhanced_power_balance.png"
                        
                        # Total power plot
                        fig4 = create_total_power_plot(solver, str(temp_path / "total_power.png"))
                        plot_files["Total Power"] = temp_path / "total_power.png"
                        
                        # Analysis plot
                        fig5 = create_detailed_analysis_plot(solver, str(temp_path / "analysis.png"))
                        plot_files["Detailed Analysis"] = temp_path / "analysis.png"
                        
                        # Export CSV
                        csv_path = temp_path / "results.csv"
                        export_to_csv(solver, str(csv_path))
                    
                    # Display plots
                    tab1, tab2, tab3, tab4, tab5 = st.tabs([
                        "Unit Status", "Detailed Analysis", "Power Balance", 
                        "Enhanced Power Balance", "Total Power"
                    ])
                    
                    with tab1:
                        st.image(str(plot_files["Unit Status"]), use_column_width=True)
                        st.download_button(
                            label="Download Unit Status Plot",
                            data=open(plot_files["Unit Status"], "rb").read(),
                            file_name="unit_status.png",
                            mime="image/png"
                        )
                    
                    with tab2:
                        st.image(str(plot_files["Detailed Analysis"]), use_column_width=True)
                        st.download_button(
                            label="Download Analysis Plot",
                            data=open(plot_files["Detailed Analysis"], "rb").read(),
                            file_name="analysis.png",
                            mime="image/png"
                        )
                    
                    with tab3:
                        st.image(str(plot_files["Power Balance"]), use_column_width=True)
                        st.download_button(
                            label="Download Power Balance Plot",
                            data=open(plot_files["Power Balance"], "rb").read(),
                            file_name="power_balance.png",
                            mime="image/png"
                        )
                    
                    with tab4:
                        st.image(str(plot_files["Enhanced Power Balance"]), use_column_width=True)
                        st.download_button(
                            label="Download Enhanced Power Balance Plot",
                            data=open(plot_files["Enhanced Power Balance"], "rb").read(),
                            file_name="enhanced_power_balance.png",
                            mime="image/png"
                        )
                    
                    with tab5:
                        st.image(str(plot_files["Total Power"]), use_column_width=True)
                        st.download_button(
                            label="Download Total Power Plot",
                            data=open(plot_files["Total Power"], "rb").read(),
                            file_name="total_power.png",
                            mime="image/png"
                        )
                    
                    # Download CSV
                    st.subheader("📊 Data Export")
                    st.download_button(
                        label="📥 Download Results CSV",
                        data=open(csv_path, "rb").read(),
                        file_name="unit_commitment_results.csv",
                        mime="text/csv"
                    )
                    
                    # Display decision variables table
                    st.subheader("📋 Decision Variables")
                    with st.expander("View detailed decision variables and costs"):
                        # Capture the print output
                        import io
                        from contextlib import redirect_stdout
                        
                        f = io.StringIO()
                        with redirect_stdout(f):
                            print_decision_variables_table(solver)
                        output = f.getvalue()
                        
                        st.text(output)
                
            except Exception as e:
                st.error(f"❌ Error during optimization: {str(e)}")
                st.exception(e)

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Virtual Power Plant (VPP) Streamlit App
Interactive demo of VPP optimization with distributed energy resources
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vpp_example_01.vpp_configs import (
    distributed_resources, market_prices, market_parameters,
    uncertainty_scenarios, base_demand_profile, vpp_parameters
)
from vpp_example_01.vpp_optimizer import VPPOptimizer

def main():
    st.set_page_config(
        page_title="Virtual Power Plant (VPP) Demo",
        page_icon="⚡",
        layout="wide"
    )
    
    st.title("⚡ Virtual Power Plant (VPP) Optimization Demo")
    st.markdown("---")
    
    # Sidebar configuration
    st.sidebar.header("🔧 VPP Configuration")
    
    # Display VPP overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Capacity", f"{vpp_parameters['total_capacity']} MW")
    with col2:
        st.metric("Renewable Penetration", f"{vpp_parameters['renewable_penetration']*100:.0f}%")
    with col3:
        st.metric("Flexibility Score", f"{vpp_parameters['flexibility_score']*100:.0f}%")
    with col4:
        st.metric("Planning Horizon", f"{market_parameters['time_periods']} hours")
    
    # Resource overview
    st.subheader("🔋 Distributed Energy Resources")
    
    resource_data = []
    for resource in distributed_resources:
        resource_data.append({
            'Name': resource['name'],
            'Type': resource['type'],
            'Capacity (MW)': resource['capacity'],
            'Owner': resource['owner'],
            'Variable Cost ($/MWh)': resource['variable_cost'],
            'Fixed Cost ($/MW/h)': resource['fixed_cost']
        })
    
    resource_df = pd.DataFrame(resource_data)
    st.dataframe(resource_df, use_container_width=True)
    
    # Market price scenarios
    st.subheader("💰 Market Price Scenarios")
    
    price_data = []
    for scenario, data in market_prices.items():
        for t, price in enumerate(data['prices']):
            price_data.append({
                'Scenario': scenario,
                'Probability': data['probability'],
                'Hour': t,
                'Price ($/MWh)': price
            })
    
    price_df = pd.DataFrame(price_data)
    
    # Plot market prices
    fig = px.line(price_df, x='Hour', y='Price ($/MWh)', color='Scenario',
                   title='Market Price Scenarios Over Time',
                   labels={'Hour': 'Time Period', 'Price ($/MWh)': 'Market Price ($/MWh)'})
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Run optimization
    st.subheader("🚀 VPP Optimization")
    
    if st.button("Run VPP Optimization", type="primary", use_container_width=True):
        with st.spinner("Running VPP optimization..."):
            # Create configuration
            configs = {
                'distributed_resources': distributed_resources,
                'market_prices': market_prices,
                'market_parameters': market_parameters,
                'uncertainty_scenarios': uncertainty_scenarios,
                'base_demand_profile': base_demand_profile,
                'vpp_parameters': vpp_parameters
            }
            
            # Run optimizer
            vpp_optimizer = VPPOptimizer(configs)
            success = vpp_optimizer.solve()
            
            if success:
                st.success("✅ VPP Optimization Completed Successfully!")
                
                # Display results
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 Financial Results")
                    metrics = vpp_optimizer.results['financial_metrics']
                    
                    st.metric("Expected Revenue", f"${metrics['expected_revenue']:.2f}")
                    st.metric("Expected Costs", f"${metrics['expected_costs']:.2f}")
                    st.metric("Carbon Credits", f"${metrics['expected_carbon_credits']:.2f}")
                    st.metric("Market Fees", f"${metrics['expected_fees']:.2f}")
                    st.metric("Expected Profit", f"${metrics['expected_profit']:.2f}")
                    st.metric("ROI", f"{metrics['roi']*100:.1f}%")
                
                with col2:
                    st.subheader("📈 Resource Utilization")
                    
                    # Expected power generation
                    for resource_name, expected_power in vpp_optimizer.results['expected_power'].items():
                        total_power = sum(expected_power)
                        avg_power = total_power / len(expected_power)
                        st.metric(f"{resource_name} Total", f"{total_power:.1f} MWh")
                        st.metric(f"{resource_name} Average", f"{avg_power:.1f} MW")
                
                # Detailed results tabs
                tab1, tab2, tab3, tab4 = st.tabs(["Power Generation", "Market Participation", "Battery Operation", "Financial Analysis"])
                
                with tab1:
                    st.subheader("Power Generation by Resource")
                    
                    # Create power generation plot
                    power_data = []
                    for resource_name, expected_power in vpp_optimizer.results['expected_power'].items():
                        for t, power in enumerate(expected_power):
                            power_data.append({
                                'Resource': resource_name,
                                'Hour': t,
                                'Power (MW)': power
                            })
                    
                    power_df = pd.DataFrame(power_data)
                    
                    fig = px.line(power_df, x='Hour', y='Power (MW)', color='Resource',
                                 title='Expected Power Generation Over Time')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Power generation table
                    st.subheader("Power Generation Details")
                    power_table = power_df.pivot(index='Hour', columns='Resource', values='Power (MW)')
                    st.dataframe(power_table, use_container_width=True)
                
                with tab2:
                    st.subheader("Market Participation")
                    
                    # Market bids plot
                    bid_data = []
                    for scenario, bids in vpp_optimizer.results['market_bids'].items():
                        for t, bid in enumerate(bids):
                            bid_data.append({
                                'Scenario': scenario,
                                'Hour': t,
                                'Market Bid (MW)': bid
                            })
                    
                    bid_df = pd.DataFrame(bid_data)
                    
                    fig = px.line(bid_df, x='Hour', y='Market Bid (MW)', color='Scenario',
                                 title='Market Participation Bids Over Time')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Expected market bids
                    st.subheader("Expected Market Bids")
                    expected_bids = []
                    for t in range(market_parameters['time_periods']):
                        expected_bid = sum(
                            vpp_optimizer.results['market_bids'][s][t] * market_prices[s]['probability']
                            for s in market_prices.keys()
                        )
                        expected_bids.append(expected_bid)
                    
                    expected_bid_df = pd.DataFrame({
                        'Hour': range(market_parameters['time_periods']),
                        'Expected Bid (MW)': expected_bids
                    })
                    
                    fig = px.bar(expected_bid_df, x='Hour', y='Expected Bid (MW)',
                                title='Expected Market Participation')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                with tab3:
                    st.subheader("Battery Operation Analysis")
                    
                    if 'battery_soc' in vpp_optimizer.results:
                        # Battery power plot
                        battery_power_data = []
                        for battery_name, power_data in vpp_optimizer.results['power_generation'].items():
                            if 'battery' in battery_name.lower():
                                for scenario, power_values in power_data.items():
                                    for t, power in enumerate(power_values):
                                        battery_power_data.append({
                                            'Battery': battery_name,
                                            'Scenario': scenario,
                                            'Hour': t,
                                            'Power (MW)': power,
                                            'Operation': 'Charging' if power < 0 else 'Discharging' if power > 0 else 'Idle'
                                        })
                        
                        if battery_power_data:
                            battery_power_df = pd.DataFrame(battery_power_data)
                            
                            # Battery power plot
                            fig = px.line(battery_power_df, x='Hour', y='Power (MW)', color='Scenario',
                                         title='Battery Power Operation (Negative = Charging, Positive = Discharging)')
                            fig.update_layout(height=400)
                            fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Zero Line")
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Battery operation summary
                            st.subheader("Battery Operation Summary")
                            for battery_name in set(battery_power_df['Battery']):
                                battery_data = battery_power_df[battery_power_df['Battery'] == battery_name]
                                st.write(f"**{battery_name}:**")
                                
                                for scenario in set(battery_data['Scenario']):
                                    scenario_data = battery_data[battery_data['Scenario'] == scenario]
                                    power_values = scenario_data['Power (MW)'].values
                                    
                                    charging_periods = sum(1 for p in power_values if p < 0)
                                    discharging_periods = sum(1 for p in power_values if p > 0)
                                    idle_periods = sum(1 for p in power_values if p == 0)
                                    
                                    total_charging = sum(p for p in power_values if p < 0)
                                    total_discharging = sum(p for p in power_values if p > 0)
                                    
                                    st.write(f"  - **{scenario}**:")
                                    st.write(f"    - Charging: {charging_periods} periods, {total_charging:.1f} MWh total")
                                    st.write(f"    - Discharging: {discharging_periods} periods, {total_discharging:.1f} MWh total")
                                    st.write(f"    - Idle: {idle_periods} periods")
                        
                        # Battery SOC plot
                        soc_data = []
                        for battery_name, soc_data_scenarios in vpp_optimizer.results['battery_soc'].items():
                            for scenario, soc_values in soc_data_scenarios.items():
                                for t, soc in enumerate(soc_values):
                                    soc_data.append({
                                        'Battery': battery_name,
                                        'Scenario': scenario,
                                        'Hour': t,
                                        'State of Charge': soc
                                    })
                        
                        soc_df = pd.DataFrame(soc_data)
                        
                        fig = px.line(soc_df, x='Hour', y='State of Charge', color='Scenario',
                                     title='Battery State of Charge Over Time')
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                        
                    else:
                        st.info("No battery resources in this VPP configuration.")
                
                with tab4:
                    st.subheader("Financial Analysis")
                    
                    # Financial breakdown pie chart
                    metrics = vpp_optimizer.results['financial_metrics']
                    
                    financial_data = {
                        'Component': ['Revenue', 'Costs', 'Carbon Credits', 'Market Fees'],
                        'Amount ($)': [
                            metrics['expected_revenue'],
                            -metrics['expected_costs'],
                            metrics['expected_carbon_credits'],
                            -metrics['expected_fees']
                        ]
                    }
                    
                    financial_df = pd.DataFrame(financial_data)
                    
                    fig = px.pie(financial_df, values='Amount ($)', names='Component',
                                title='Financial Breakdown')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Profit by scenario
                    st.subheader("Profit by Market Scenario")
                    scenario_profits = []
                    for scenario in market_prices.keys():
                        # Calculate profit for this scenario (simplified)
                        total_revenue = sum(
                            market_prices[scenario]['prices'][t] * vpp_optimizer.results['market_bids'][scenario][t]
                            for t in range(market_parameters['time_periods'])
                        )
                        scenario_profits.append({
                            'Scenario': scenario,
                            'Probability': market_prices[scenario]['probability'],
                            'Revenue ($)': total_revenue
                        })
                    
                    scenario_df = pd.DataFrame(scenario_profits)
                    
                    fig = px.bar(scenario_df, x='Scenario', y='Revenue ($)',
                                title='Revenue by Market Scenario')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.error("❌ VPP Optimization Failed!")
                st.write("Check the configuration and constraints.")
    
    # VPP concept explanation
    st.sidebar.markdown("---")
    st.sidebar.subheader("ℹ️ About VPPs")
    st.sidebar.markdown("""
    **Virtual Power Plants** aggregate distributed energy resources to:
    
    - ⚡ Provide grid services
    - 💰 Maximize market revenue
    - 🌱 Support renewable integration
    - 🔄 Enable demand flexibility
    
    **Key Features:**
    - Stochastic optimization
    - Market participation
    - Multiple resource types
    - Environmental incentives
    """)

if __name__ == "__main__":
    main() 
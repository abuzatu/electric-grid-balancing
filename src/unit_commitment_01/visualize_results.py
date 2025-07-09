"""
Script to visualize unit commitment results with bar charts.
"""

import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import csv
from matplotlib.patches import Patch

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Change to the main project directory for consistent file paths
os.chdir(os.path.join(os.path.dirname(__file__), '../..'))

from unit_commitment_01.solve_unit_commitment import SolveUnitCommitment
from unit_commitment_01 import configs
from ortools.linear_solver import pywraplp

def create_power_balance_plot(solver, save_path='data/results/unit_commitment/unit_commitment_power_balance.png'):
    """
    Create a stacked bar chart showing demand vs power production.
    
    Args:
        solver: The solved unit commitment solver instance
        save_path: Path to save the plot file
    """
    
    # Get time periods and unit names
    time_periods = list(range(solver.num_periods))
    unit_names = [solver.configs_units[j]['name'] for j in range(solver.num_units)]
    
    # Get demand for each time period
    demand = [solver.configs_time_periods[t]['demand'] for t in time_periods]
    
    # Get power production for each unit and time period
    power_production = {}
    for j in range(solver.num_units):
        unit_power = []
        for t in time_periods:
            if t == 0:
                # Initial state
                unit_power.append(solver.configs_units[j]['p0'])
            else:
                # Optimization results
                unit_power.append(solver.p[j, t].solution_value())
        power_production[unit_names[j]] = unit_power
    
    # Create the plot
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Set up the data for stacked bar chart
    x = np.arange(len(time_periods))
    width = 0.8
    
    # Colors for each unit
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    # Plot: Power Production vs Demand
    # Create stacked bars for power production
    bottom = np.zeros(len(time_periods))
    bars = []
    
    for i, unit_name in enumerate(unit_names):
        power = power_production[unit_name]
        bar = ax1.bar(x, power, width, bottom=bottom, 
                     label=unit_name, color=colors[i % len(colors)], alpha=0.8)
        bars.append(bar)
        bottom += power
    
    # Plot demand line
    demand_line = ax1.plot(x, demand, 'r-', linewidth=3, marker='o', 
                          markersize=8, label='Demand', color='red')
    
    # Customize the plot
    ax1.set_xlabel('Time Period')
    ax1.set_ylabel('Power (MW)')
    ax1.set_title('Unit Commitment: Power Production vs Demand')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f't={t}' for t in time_periods])
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar in bars:
        for rect in bar:
            height = rect.get_height()
            if height > 0:
                ax1.text(rect.get_x() + rect.get_width()/2., rect.get_y() + height/2.,
                        f'{height:.0f}', ha='center', va='center', fontsize=8)
    
    # Add demand values
    for i, d in enumerate(demand):
        ax1.text(i, d + 10, f'{d:.0f}', ha='center', va='bottom', 
                fontsize=10, fontweight='bold', color='red')
    
    # Add 10% padding at the top
    y_max = ax1.get_ylim()[1]
    ax1.set_ylim(0, y_max * 1.1)
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Power balance plot saved as: {save_path}")
    
    return fig

def create_unit_status_plot(solver, save_path='data/results/unit_commitment/unit_commitment_unit_status.png'):
    """
    Create a heatmap showing unit status (ON/OFF) over time.
    
    Args:
        solver: The solved unit commitment solver instance
        save_path: Path to save the plot file
    """
    
    # Get time periods and unit names
    time_periods = list(range(solver.num_periods))
    unit_names = [solver.configs_units[j]['name'] for j in range(solver.num_units)]
    
    # Create a heatmap-like visualization of unit status
    status_data = []
    for j in range(solver.num_units):
        unit_status = []
        for t in time_periods:
            if t == 0:
                # Initial state
                unit_status.append(solver.configs_units[j]['u0'])
            else:
                # Optimization results
                unit_status.append(solver.u[j, t].solution_value())
        status_data.append(unit_status)
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Create heatmap
    im = ax.imshow(status_data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
    
    # Customize the heatmap
    ax.set_xlabel('Time Period')
    ax.set_ylabel('Unit')
    ax.set_title('Unit Status: ON (Green) / OFF (Red)')
    ax.set_xticks(range(len(time_periods)))
    ax.set_xticklabels([f't={t}' for t in time_periods])
    ax.set_yticks(range(len(unit_names)))
    ax.set_yticklabels(unit_names)
    
    # Add status labels
    for i in range(len(unit_names)):
        for j in range(len(time_periods)):
            status = status_data[i][j]
            text = 'ON' if status > 0.5 else 'OFF'
            color = 'white' if status > 0.5 else 'black'
            ax.text(j, i, text, ha='center', va='center', 
                    fontsize=10, fontweight='bold', color=color)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, ticks=[0, 1])
    cbar.set_ticklabels(['OFF', 'ON'])
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Unit status plot saved as: {save_path}")
    
    return fig

def create_enhanced_power_balance_plot(solver, save_path='data/results/unit_commitment/unit_commitment_enhanced_power_balance.png'):
    """
    Create an enhanced stacked bar chart showing demand, demand+reserve, delivered and committed power.
    
    Args:
        solver: The solved unit commitment solver instance
        save_path: Path to save the plot file
    """
    
    # Get time periods and unit names
    time_periods = list(range(solver.num_periods))
    unit_names = [solver.configs_units[j]['name'] for j in range(solver.num_units)]
    
    # Get demand and reserve for each time period
    demand = [solver.configs_time_periods[t]['demand'] for t in time_periods]
    reserve = [solver.configs_time_periods[t]['reserve'] for t in time_periods]
    demand_plus_reserve = [demand[t] + reserve[t] for t in time_periods]
    
    # Get power production and committed (p_bar) for each unit and time period
    power_production = {}
    committed_power = {}
    for j in range(solver.num_units):
        unit_power = []
        unit_committed = []
        for t in time_periods:
            if t == 0:
                unit_power.append(solver.configs_units[j]['p0'])
                unit_committed.append(solver.configs_units[j]['p0'])
            else:
                unit_power.append(solver.p[j, t].solution_value())
                unit_committed.append(solver.p_bar[j, t].solution_value())
        power_production[unit_names[j]] = unit_power
        committed_power[unit_names[j]] = unit_committed
    
    # Colors for each unit
    base_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    light_colors = ['#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5', '#c49c94']
    
    # Create the plot
    fig, ax1 = plt.subplots(figsize=(14, 7))
    x = np.arange(len(time_periods))
    width = 0.8
    
    # Plot stacked bars in the correct order
    bottom = np.zeros(len(time_periods))
    bars = []
    
    # First stack all delivered power (p(t)) for all units
    for i, unit_name in enumerate(unit_names):
        power = power_production[unit_name]
        bar = ax1.bar(x, power, width, bottom=bottom, label=f"{unit_name} delivered", color=base_colors[i % len(base_colors)], alpha=0.85)
        bars.append(bar)
        bottom += power
    
    # Then stack all committed (not delivered) power (p_bar(t) - p(t)) for all units
    for i, unit_name in enumerate(unit_names):
        power = power_production[unit_name]
        committed = committed_power[unit_name]
        diff = [max(committed[t] - power[t], 0) for t in range(len(power))]
        bar = ax1.bar(x, diff, width, bottom=bottom, label=f"{unit_name} committed (not delivered)", color=light_colors[i % len(light_colors)], alpha=0.6, hatch='//', edgecolor=base_colors[i % len(base_colors)])
        bars.append(bar)
        bottom += diff
    
    # Plot demand as solid black line
    ax1.plot(x, demand, color='black', linewidth=2.5, marker='o', label='Demand')
    # Plot demand+reserve as dotted black line
    ax1.plot(x, demand_plus_reserve, color='black', linewidth=2, linestyle=':', marker='o', label='Demand + Reserve')
    
    # Customize the plot
    ax1.set_xlabel('Time Period')
    ax1.set_ylabel('Power (MW)')
    ax1.set_title('Unit Commitment: Power Production, Committed Power, Demand, and Reserve')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f't={t}' for t in time_periods])
    ax1.legend(loc='upper left', bbox_to_anchor=(1.01, 1.0))
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on delivered bars
    for bar in bars:
        for rect in bar:
            height = rect.get_height()
            if height > 0:
                ax1.text(rect.get_x() + rect.get_width()/2., rect.get_y() + height/2.,
                        f'{height:.0f}', ha='center', va='center', fontsize=8)
    
    # Add demand values
    for i, d in enumerate(demand):
        ax1.text(i, d + 10, f'{d:.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold', color='black')
    for i, dr in enumerate(demand_plus_reserve):
        ax1.text(i, dr + 10, f'{dr:.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold', color='gray')
    
    # Add 10% padding at the top
    y_max = ax1.get_ylim()[1]
    ax1.set_ylim(0, y_max * 1.1)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Enhanced plot saved as: {save_path}")
    return fig

def create_total_power_plot(solver, save_path='data/results/unit_commitment/unit_commitment_total_power.png'):
    """
    Create a plot showing total delivered and committed power across all units.
    
    Args:
        solver: The solved unit commitment solver instance
        save_path: Path to save the plot file
    """
    
    # Get time periods
    time_periods = list(range(solver.num_periods))
    
    # Get demand and reserve for each time period
    demand = [solver.configs_time_periods[t]['demand'] for t in time_periods]
    reserve = [solver.configs_time_periods[t]['reserve'] for t in time_periods]
    demand_plus_reserve = [demand[t] + reserve[t] for t in time_periods]
    
    # Calculate total delivered power and total committed power for each time period
    total_delivered = np.zeros(len(time_periods))
    total_committed = np.zeros(len(time_periods))
    
    for t in range(len(time_periods)):
        for j in range(solver.num_units):
            if t == 0:
                total_delivered[t] += solver.configs_units[j]['p0']
                total_committed[t] += solver.configs_units[j]['p0']
            else:
                total_delivered[t] += solver.p[j, t].solution_value()
                total_committed[t] += solver.p_bar[j, t].solution_value()
    
    # Create the plot
    fig, ax1 = plt.subplots(figsize=(14, 7))
    x = np.arange(len(time_periods))
    width = 0.8
    
    # Plot total delivered power as solid bar
    delivered_bar = ax1.bar(x, total_delivered, width, label='Total Delivered Power', color='#1f77b4', alpha=0.85)
    
    # Plot total committed (not delivered) power as hatched bar on top
    committed_not_delivered = total_committed - total_delivered
    committed_bar = ax1.bar(x, committed_not_delivered, width, bottom=total_delivered, 
                           label='Total Committed (not delivered)', color='#aec7e8', alpha=0.6, 
                           hatch='//', edgecolor='#1f77b4')
    
    # Plot demand as solid black line
    ax1.plot(x, demand, color='black', linewidth=2.5, marker='o', label='Demand')
    # Plot demand+reserve as dotted black line
    ax1.plot(x, demand_plus_reserve, color='black', linewidth=2, linestyle=':', marker='o', label='Demand + Reserve')
    
    # Customize the plot
    ax1.set_xlabel('Time Period')
    ax1.set_ylabel('Power (MW)')
    ax1.set_title('Unit Commitment: Total Power Production, Committed Power, Demand, and Reserve')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f't={t}' for t in time_periods])
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for rect in delivered_bar:
        height = rect.get_height()
        if height > 0:
            ax1.text(rect.get_x() + rect.get_width()/2., rect.get_y() + height/2.,
                    f'{height:.0f}', ha='center', va='center', fontsize=10, fontweight='bold')
    
    for rect in committed_bar:
        height = rect.get_height()
        if height > 0:
            ax1.text(rect.get_x() + rect.get_width()/2., rect.get_y() + height/2.,
                    f'{height:.0f}', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Add demand values
    for i, d in enumerate(demand):
        ax1.text(i, d + 10, f'{d:.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold', color='black')
    for i, dr in enumerate(demand_plus_reserve):
        ax1.text(i, dr + 10, f'{dr:.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold', color='gray')
    
    # Add 10% padding at the top
    y_max = ax1.get_ylim()[1]
    ax1.set_ylim(0, y_max * 1.1)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Total power plot saved as: {save_path}")
    return fig

def create_detailed_analysis_plot(solver, save_path='data/results/unit_commitment/unit_commitment_analysis.png'):
    """
    Create a detailed analysis plot with multiple subplots.
    
    Args:
        solver: The solved unit commitment solver instance
        save_path: Path to save the plot file
    """
    
    time_periods = list(range(solver.num_periods))
    unit_names = [solver.configs_units[j]['name'] for j in range(solver.num_units)]
    
    # Get data
    demand = [solver.configs_time_periods[t]['demand'] for t in time_periods]
    reserve = [solver.configs_time_periods[t]['reserve'] for t in time_periods]
    
    # Get power production and status
    power_data = {}
    status_data = {}
    startup_data = {}
    shutdown_data = {}
    
    for j in range(solver.num_units):
        power = []
        status = []
        startup = []
        shutdown = []
        
        for t in time_periods:
            if t == 0:
                power.append(solver.configs_units[j]['p0'])
                status.append(solver.configs_units[j]['u0'])
                startup.append(solver.configs_units[j]['su0'])
                shutdown.append(solver.configs_units[j]['sd0'])
            else:
                power.append(solver.p[j, t].solution_value())
                status.append(solver.u[j, t].solution_value())
                startup.append(solver.su[j, t].solution_value())
                shutdown.append(solver.sd[j, t].solution_value())
        
        power_data[unit_names[j]] = power
        status_data[unit_names[j]] = status
        startup_data[unit_names[j]] = startup
        shutdown_data[unit_names[j]] = shutdown
    
    # Create subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: Power Production Stacked
    x = np.arange(len(time_periods))
    width = 0.8
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    bottom = np.zeros(len(time_periods))
    for i, unit_name in enumerate(unit_names):
        power = power_data[unit_name]
        ax1.bar(x, power, width, bottom=bottom, 
               label=unit_name, color=colors[i % len(colors)], alpha=0.8)
        bottom += power
    
    ax1.plot(x, demand, 'r-', linewidth=3, marker='o', markersize=8, label='Demand')
    ax1.set_xlabel('Time Period')
    ax1.set_ylabel('Power (MW)')
    ax1.set_title('Power Production vs Demand')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f't={t}' for t in time_periods])
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Unit Status Timeline
    for i, unit_name in enumerate(unit_names):
        status = status_data[unit_name]
        ax2.plot(x, status, 'o-', linewidth=2, markersize=8, 
                label=unit_name, color=colors[i % len(colors)])
    
    ax2.set_xlabel('Time Period')
    ax2.set_ylabel('Status (1=ON, 0=OFF)')
    ax2.set_title('Unit Commitment Status')
    ax2.set_xticks(x)
    ax2.set_xticklabels([f't={t}' for t in time_periods])
    ax2.set_ylim(-0.1, 1.1)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Startup Events
    for i, unit_name in enumerate(unit_names):
        startup = startup_data[unit_name]
        ax3.plot(x, startup, 'o-', linewidth=2, markersize=8, 
                label=unit_name, color=colors[i % len(colors)])
    
    ax3.set_xlabel('Time Period')
    ax3.set_ylabel('Startup (1=Yes, 0=No)')
    ax3.set_title('Unit Startup Events')
    ax3.set_xticks(x)
    ax3.set_xticklabels([f't={t}' for t in time_periods])
    ax3.set_ylim(-0.1, 1.1)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Shutdown Events
    for i, unit_name in enumerate(unit_names):
        shutdown = shutdown_data[unit_name]
        ax4.plot(x, shutdown, 'o-', linewidth=2, markersize=8, 
                label=unit_name, color=colors[i % len(colors)])
    
    ax4.set_xlabel('Time Period')
    ax4.set_ylabel('Shutdown (1=Yes, 0=No)')
    ax4.set_title('Unit Shutdown Events')
    ax4.set_xticks(x)
    ax4.set_xticklabels([f't={t}' for t in time_periods])
    ax4.set_ylim(-0.1, 1.1)
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # Add 10% padding at the top for all subplots
    for ax in [ax1, ax2, ax3, ax4]:
        y_max = ax.get_ylim()[1]
        y_min = ax.get_ylim()[0]
        y_range = y_max - y_min
        ax.set_ylim(y_min, y_max + y_range * 0.1)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Analysis plot saved as: {save_path}")
    
    return fig

def print_decision_variables_table(solver):
    """
    Print all decision variables and cost breakdown in a formatted table.
    
    Args:
        solver: The solved unit commitment solver instance
    """
    print("\n" + "="*120)
    print("DECISION VARIABLES AND COST BREAKDOWN")
    print("="*120)
    
    # Get unit names
    unit_names = [solver.configs_units[j]['name'] for j in range(solver.num_units)]
    
    # Create headers
    headers = ["Time", "Unit", "p(t) [MW]", "p̄(t) [MW]", "u(t)", "su(t)", "sd(t)", "Fixed Cost", "Var Cost", "Startup", "Shutdown", "Total Cost"]
    
    # Print header
    print(f"{headers[0]:<6} {headers[1]:<8} {headers[2]:<12} {headers[3]:<12} {headers[4]:<6} {headers[5]:<6} {headers[6]:<6} {headers[7]:<10} {headers[8]:<9} {headers[9]:<8} {headers[10]:<9} {headers[11]:<10}")
    print("-" * 120)
    
    # Track total costs (excluding initial state t=0)
    total_fixed_cost = 0
    total_var_cost = 0
    total_startup_cost = 0
    total_shutdown_cost = 0
    
    # Print data for each time period and unit
    for t in range(solver.num_periods):
        period_fixed_cost = 0
        period_var_cost = 0
        period_startup_cost = 0
        period_shutdown_cost = 0
        
        for j in range(solver.num_units):
            if t == 0:
                # Initial state
                p_val = solver.configs_units[j]['p0']
                p_bar_val = solver.configs_units[j]['p0']  # Initial p_bar same as p0
                u_val = solver.configs_units[j]['u0']
                su_val = solver.configs_units[j]['su0']
                sd_val = solver.configs_units[j]['sd0']
            else:
                # Optimization results
                p_val = solver.p[j, t].solution_value()
                p_bar_val = solver.p_bar[j, t].solution_value()
                u_val = solver.u[j, t].solution_value()
                su_val = solver.su[j, t].solution_value()
                sd_val = solver.sd[j, t].solution_value()
            
            # Calculate costs (only for optimization periods t>=1)
            if t == 0:
                # Initial state - no costs for optimization
                fixed_cost = 0
                var_cost = 0
                startup_cost = 0
                shutdown_cost = 0
                unit_total_cost = 0
            else:
                # Optimization results - include costs
                fixed_cost = u_val * solver.configs_units[j]['cU']
                var_cost = p_val * solver.configs_units[j]['c']
                startup_cost = su_val * solver.configs_units[j]['SU_cost']
                shutdown_cost = sd_val * solver.configs_units[j]['SD_cost']
                unit_total_cost = fixed_cost + var_cost + startup_cost + shutdown_cost
            
            # Accumulate period costs
            period_fixed_cost += fixed_cost
            period_var_cost += var_cost
            period_startup_cost += startup_cost
            period_shutdown_cost += shutdown_cost
            
            # Format values
            p_str = f"{p_val:.1f}" if p_val > 0 else "0.0"
            p_bar_str = f"{p_bar_val:.1f}" if p_bar_val > 0 else "0.0"
            u_str = "1" if u_val > 0.5 else "0"
            su_str = "1" if su_val > 0.5 else "0"
            sd_str = "1" if sd_val > 0.5 else "0"
            
            print(f"{t:<6} {unit_names[j]:<8} {p_str:<12} {p_bar_str:<12} {u_str:<6} {su_str:<6} {sd_str:<6} "
                  f"${fixed_cost:<9.2f} ${var_cost:<8.2f} ${startup_cost:<7.2f} ${shutdown_cost:<8.2f} ${unit_total_cost:<9.2f}")
        
        # Print period totals
        period_total = period_fixed_cost + period_var_cost + period_startup_cost + period_shutdown_cost
        print(f"{'':<6} {'PERIOD':<8} {'':<12} {'':<12} {'':<6} {'':<6} {'':<6} "
              f"${period_fixed_cost:<9.2f} ${period_var_cost:<8.2f} ${period_startup_cost:<7.2f} ${period_shutdown_cost:<8.2f} ${period_total:<9.2f}")
        
        # Accumulate total costs
        total_fixed_cost += period_fixed_cost
        total_var_cost += period_var_cost
        total_startup_cost += period_startup_cost
        total_shutdown_cost += period_shutdown_cost
        
        # Add separator between time periods
        if t < solver.num_periods - 1:
            print("-" * 120)
    
    print("="*120)
    
    # Print total cost breakdown
    print("\nTOTAL COST BREAKDOWN:")
    print("-" * 50)
    print(f"Fixed Costs:     ${total_fixed_cost:.2f}")
    print(f"Variable Costs:  ${total_var_cost:.2f}")
    print(f"Startup Costs:   ${total_startup_cost:.2f}")
    print(f"Shutdown Costs:  ${total_shutdown_cost:.2f}")
    print(f"TOTAL COST:      ${total_fixed_cost + total_var_cost + total_startup_cost + total_shutdown_cost:.2f}")
    print("-" * 50)
    
    # Print summary statistics
    print("\nSUMMARY STATISTICS:")
    print("-" * 50)
    
    # Calculate totals for each time period
    for t in range(solver.num_periods):
        total_p = 0
        total_p_bar = 0
        total_units_on = 0
        
        for j in range(solver.num_units):
            if t == 0:
                total_p += solver.configs_units[j]['p0']
                total_p_bar += solver.configs_units[j]['p0']
                total_units_on += solver.configs_units[j]['u0']
            else:
                total_p += solver.p[j, t].solution_value()
                total_p_bar += solver.p_bar[j, t].solution_value()
                total_units_on += solver.u[j, t].solution_value()
        
        demand = solver.configs_time_periods[t]['demand']
        reserve = solver.configs_time_periods[t]['reserve']
        
        print(f"t={t}: Total p(t)={total_p:.1f} MW, Total p̄(t)={total_p_bar:.1f} MW, "
              f"Demand={demand} MW, Demand+Reserve={demand+reserve} MW, Units ON={total_units_on:.0f}")
    
    print("-" * 50)

def export_to_csv(solver, save_path='data/results/unit_commitment/unit_commitment_results.csv'):
    """
    Export decision variables and cost breakdown to CSV file.
    
    Args:
        solver: The solved unit commitment solver instance
        save_path: Path to save the CSV file
    """
    # Get unit names
    unit_names = [solver.configs_units[j]['name'] for j in range(solver.num_units)]
    
    # Prepare data for CSV
    csv_data = []
    
    # Add header
    headers = ["Time", "Unit", "p(t) [MW]", "p̄(t) [MW]", "u(t)", "su(t)", "sd(t)", 
               "Fixed Cost ($)", "Variable Cost ($)", "Startup Cost ($)", "Shutdown Cost ($)", "Total Cost ($)"]
    csv_data.append(headers)
    
    # Add data for each time period and unit
    for t in range(solver.num_periods):
        for j in range(solver.num_units):
            if t == 0:
                # Initial state
                p_val = solver.configs_units[j]['p0']
                p_bar_val = solver.configs_units[j]['p0']
                u_val = solver.configs_units[j]['u0']
                su_val = solver.configs_units[j]['su0']
                sd_val = solver.configs_units[j]['sd0']
            else:
                # Optimization results
                p_val = solver.p[j, t].solution_value()
                p_bar_val = solver.p_bar[j, t].solution_value()
                u_val = solver.u[j, t].solution_value()
                su_val = solver.su[j, t].solution_value()
                sd_val = solver.sd[j, t].solution_value()
            
            # Calculate costs (only for optimization periods t>=1)
            if t == 0:
                # Initial state - no costs for optimization
                fixed_cost = 0
                var_cost = 0
                startup_cost = 0
                shutdown_cost = 0
                unit_total_cost = 0
            else:
                # Optimization results - include costs
                fixed_cost = u_val * solver.configs_units[j]['cU']
                var_cost = p_val * solver.configs_units[j]['c']
                startup_cost = su_val * solver.configs_units[j]['SU_cost']
                shutdown_cost = sd_val * solver.configs_units[j]['SD_cost']
                unit_total_cost = fixed_cost + var_cost + startup_cost + shutdown_cost
            
            # Add row to CSV data
            row = [t, unit_names[j], round(p_val, 1), round(p_bar_val, 1), 
                   int(u_val > 0.5), int(su_val > 0.5), int(sd_val > 0.5),
                   round(fixed_cost, 2), round(var_cost, 2), round(startup_cost, 2), 
                   round(shutdown_cost, 2), round(unit_total_cost, 2)]
            csv_data.append(row)
        
        # Add period summary row
        period_fixed_cost = sum(csv_data[-solver.num_units:][i][7] for i in range(solver.num_units))
        period_var_cost = sum(csv_data[-solver.num_units:][i][8] for i in range(solver.num_units))
        period_startup_cost = sum(csv_data[-solver.num_units:][i][9] for i in range(solver.num_units))
        period_shutdown_cost = sum(csv_data[-solver.num_units:][i][10] for i in range(solver.num_units))
        period_total = period_fixed_cost + period_var_cost + period_startup_cost + period_shutdown_cost
        
        summary_row = [t, "PERIOD TOTAL", "", "", "", "", "", 
                      round(period_fixed_cost, 2), round(period_var_cost, 2), 
                      round(period_startup_cost, 2), round(period_shutdown_cost, 2), 
                      round(period_total, 2)]
        csv_data.append(summary_row)
        
        # Add empty row for separation
        csv_data.append([""] * len(headers))
    
    # Add total summary
    total_fixed_cost = sum(row[7] for row in csv_data if row[1] == "PERIOD TOTAL")
    total_var_cost = sum(row[8] for row in csv_data if row[1] == "PERIOD TOTAL")
    total_startup_cost = sum(row[9] for row in csv_data if row[1] == "PERIOD TOTAL")
    total_shutdown_cost = sum(row[10] for row in csv_data if row[1] == "PERIOD TOTAL")
    total_cost = total_fixed_cost + total_var_cost + total_startup_cost + total_shutdown_cost
    
    csv_data.append([""] * len(headers))
    csv_data.append(["TOTAL", "ALL PERIODS", "", "", "", "", "", 
                    round(total_fixed_cost, 2), round(total_var_cost, 2), 
                    round(total_startup_cost, 2), round(total_shutdown_cost, 2), 
                    round(total_cost, 2)])
    
    # Write to CSV file
    with open(save_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(csv_data)
    
    print(f"CSV file saved as: {save_path}")

def main():
    """Run the solver and create visualizations."""
    print("=" * 60)
    print("UNIT COMMITMENT VISUALIZATION")
    print("=" * 60)
    
    # Create and solve the problem
    print("\n1. Creating solver instance...")
    solver = SolveUnitCommitment()
    
    print("\n2. Setting up constraints and objective...")
    solver.fit()
    
    print("\n3. Solving the optimization problem...")
    status = solver.solver.Solve()
    
    if status == pywraplp.Solver.OPTIMAL:
        print(f"\n✅ OPTIMAL SOLUTION FOUND!")
        print(f"Total Cost: ${solver.solver.Objective().Value():.2f}")
        
        # Print decision variables table
        print_decision_variables_table(solver)
        
        # Export to CSV
        export_to_csv(solver)
        
        # Create visualizations
        print("\n4. Creating visualizations...")
        
        # Create power balance plot (separate)
        fig1 = create_power_balance_plot(solver, 'data/results/unit_commitment/unit_commitment_power_balance.png')
        
        # Create unit status plot (separate)
        fig2 = create_unit_status_plot(solver, 'data/results/unit_commitment/unit_commitment_unit_status.png')
        
        # Create enhanced power balance plot (individual units)
        fig3 = create_enhanced_power_balance_plot(solver, 'data/results/unit_commitment/unit_commitment_enhanced_power_balance.png')
        
        # Create total power plot (summed across units)
        fig4 = create_total_power_plot(solver, 'data/results/unit_commitment/unit_commitment_total_power.png')
        
        # Create detailed analysis plot
        fig5 = create_detailed_analysis_plot(solver, 'data/results/unit_commitment/unit_commitment_analysis.png')
        
        print("\n📊 Visualizations created successfully!")
        print("- data/results/unit_commitment/unit_commitment_power_balance.png: Power production vs demand")
        print("- data/results/unit_commitment/unit_commitment_unit_status.png: Unit status (ON/OFF) heatmap")
        print("- data/results/unit_commitment/unit_commitment_enhanced_power_balance.png: Enhanced plot with individual units")
        print("- data/results/unit_commitment/unit_commitment_total_power.png: Total power (summed across units)")
        print("- data/results/unit_commitment/unit_commitment_analysis.png: Detailed analysis with multiple views")
        
        # Show the plots
        plt.show()
        
    else:
        print("❌ No optimal solution found!")

if __name__ == "__main__":
    main() 
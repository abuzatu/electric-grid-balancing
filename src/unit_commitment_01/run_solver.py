"""
Script to run the unit commitment solver and display results.
"""

import sys
import os
# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Change to the main project directory for consistent file paths
os.chdir(os.path.join(os.path.dirname(__file__), '../..'))

from unit_commitment_01.solve_unit_commitment import SolveUnitCommitment
from unit_commitment_01 import configs
from ortools.linear_solver import pywraplp

# === SELECT DEMAND PATTERN HERE ===
# Options:
# configs.time_periods_example (default 6-period example)
# configs.time_periods_24h
# configs.time_periods_24h_large
# configs.time_periods_24h_extra_large
# configs.time_periods_24h_weekend
# configs.time_periods_24h_industrial
selected_time_periods = configs.time_periods_example  # Change this line to select a different pattern

def main():
    """Run the unit commitment solver and display results."""
    print("=" * 60)
    print("UNIT COMMITMENT OPTIMIZATION")
    print("=" * 60)
    
    # Create and solve the problem
    print("\n1. Creating solver instance...")
    solver = SolveUnitCommitment(time_periods=selected_time_periods, units=configs.units_example)
    
    print("\n2. Setting up constraints and objective...")
    solver.fit()
    
    print("\n3. Solving the optimization problem...")
    status = solver.solver.Solve()
    
    # Display results
    print("\n" + "=" * 60)
    print("SOLUTION RESULTS")
    print("=" * 60)
    
    if status == pywraplp.Solver.OPTIMAL:
        print(f"✅ OPTIMAL SOLUTION FOUND!")
        print(f"Total Cost: ${solver.solver.Objective().Value():.2f}")
        
        print("\n📊 UNIT SCHEDULE:")
        print("-" * 60)
        
        # Header
        header = "Time |"
        for j in range(solver.num_units):
            header += f" Unit{j+1} |"
        print(header)
        print("-" * 60)
        
        # Results for each time period (t=0 to t=6)
        for t in range(solver.num_periods):
            row = f"  {t}  |"
            for j in range(solver.num_units):
                if t == 0:
                    # Initial state (fixed values)
                    status = "ON " if solver.configs_units[j]['u0'] == 1 else "OFF"
                    power = solver.configs_units[j]['p0']
                else:
                    # Optimization results
                    status = "ON " if solver.u[j, t].solution_value() > 0.5 else "OFF"
                    power = solver.p[j, t].solution_value()
                row += f" {status}({power:4.0f})|"
            print(row)
        
        print("\n📈 DETAILED RESULTS:")
        print("-" * 60)
        for j in range(solver.num_units):
            print(f"\nUnit {j+1} ({solver.configs_units[j]['name']}):")
            # All time periods including initial state
            for t in range(solver.num_periods):
                if t == 0:
                    # Initial state
                    u_val = solver.configs_units[j]['u0']
                    p_val = solver.configs_units[j]['p0']
                    p_bar_val = solver.configs_units[j]['p0']  # Same as p0 for initial state
                    su_val = solver.configs_units[j]['su0']
                    sd_val = solver.configs_units[j]['sd0']
                    print(f"  t={t}: ON={u_val:.0f}, P={p_val:.1f}MW, P_bar={p_bar_val:.1f}MW, "
                          f"SU={su_val:.0f}, SD={sd_val:.0f} (initial state)")
                else:
                    # Optimization results
                    u_val = solver.u[j, t].solution_value()
                    p_val = solver.p[j, t].solution_value()
                    p_bar_val = solver.p_bar[j, t].solution_value()
                    su_val = solver.su[j, t].solution_value()
                    sd_val = solver.sd[j, t].solution_value()
                    
                    print(f"  t={t}: ON={u_val:.0f}, P={p_val:.1f}MW, P_bar={p_bar_val:.1f}MW, "
                          f"SU={su_val:.0f}, SD={sd_val:.0f}")
        
        print("\n💰 COST BREAKDOWN:")
        print("-" * 60)
        total_fixed = 0
        total_variable = 0
        total_startup = 0
        total_shutdown = 0
        
        for j in range(solver.num_units):
            unit_fixed = sum(solver.u[j, t].solution_value() * solver.configs_units[j]['cU'] 
                           for t in range(1, solver.num_periods))  # Exclude t=0 from cost
            unit_variable = sum(solver.p[j, t].solution_value() * solver.configs_units[j]['c'] 
                              for t in range(1, solver.num_periods))  # Exclude t=0 from cost
            unit_startup = sum(solver.su[j, t].solution_value() * solver.configs_units[j]['SU_cost'] 
                             for t in range(1, solver.num_periods))  # Exclude t=0 from cost
            unit_shutdown = sum(solver.sd[j, t].solution_value() * solver.configs_units[j]['SD_cost'] 
                              for t in range(1, solver.num_periods))  # Exclude t=0 from cost
            
            total_fixed += unit_fixed
            total_variable += unit_variable
            total_startup += unit_startup
            total_shutdown += unit_shutdown
            
            print(f"Unit {j+1}: Fixed=${unit_fixed:.0f}, Variable=${unit_variable:.0f}, "
                  f"Startup=${unit_startup:.0f}, Shutdown=${unit_shutdown:.0f}")
        
        print(f"\nTOTAL: Fixed=${total_fixed:.0f}, Variable=${total_variable:.0f}, "
              f"Startup=${total_startup:.0f}, Shutdown=${total_shutdown:.0f}")
        
    elif status == pywraplp.Solver.INFEASIBLE:
        print("❌ PROBLEM IS INFEASIBLE!")
        print("The constraints cannot be satisfied simultaneously.")
    elif status == pywraplp.Solver.UNBOUNDED:
        print("❌ PROBLEM IS UNBOUNDED!")
        print("The objective can be improved indefinitely.")
    else:
        print(f"❌ SOLVER FAILED with status: {status}")

if __name__ == "__main__":
    main() 
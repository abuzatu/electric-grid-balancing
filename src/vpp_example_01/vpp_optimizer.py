"""
Virtual Power Plant (VPP) Optimizer
Implements stochastic optimization for distributed energy resources
with market participation and uncertainty handling.
"""

import numpy as np
import pandas as pd
from ortools.linear_solver import pywraplp
from typing import Dict, List, Tuple, Any
import logging

class VPPOptimizer:
    """
    Virtual Power Plant Optimizer
    Handles stochastic optimization of distributed energy resources
    """
    
    def __init__(self, configs):
        self.configs = configs
        self.solver = None
        self.variables = {}
        self.constraints = {}
        self.results = {}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def create_solver(self):
        """Create the optimization solver"""
        self.solver = pywraplp.Solver.CreateSolver('SCIP')
        if not self.solver:
            raise ValueError("Could not create SCIP solver")
        
        self.logger.info("VPP Optimizer initialized with SCIP solver")
        
    def define_variables(self):
        """Define decision variables for the VPP optimization"""
        resources = self.configs['distributed_resources']
        scenarios = list(self.configs['market_prices'].keys())
        time_periods = self.configs['market_parameters']['time_periods']
        
        # Power generation/consumption variables
        self.variables['power'] = {}
        for r, resource in enumerate(resources):
            self.variables['power'][resource['name']] = {}
            for s, scenario in enumerate(scenarios):
                self.variables['power'][resource['name']][scenario] = {}
                for t in range(time_periods):
                    if resource['type'] == 'battery':
                        # Battery can charge (negative) or discharge (positive)
                        self.variables['power'][resource['name']][scenario][t] = self.solver.NumVar(
                            -resource['max_charge_rate'], resource['max_discharge_rate'], 
                            f"power_{resource['name']}_{scenario}_{t}"
                        )
                    else:
                        # Other resources can only generate (positive)
                        if 'availability_profile' in resource:
                            max_power = resource['capacity'] * resource['availability_profile'][t]
                        else:
                            max_power = resource['capacity']
                        self.variables['power'][resource['name']][scenario][t] = self.solver.NumVar(
                            0, max_power, f"power_{resource['name']}_{scenario}_{t}"
                        )
        
        # Battery state of charge variables
        self.variables['soc'] = {}
        # Battery charge and discharge variables (for proper efficiency handling)
        self.variables['charge'] = {}
        self.variables['discharge'] = {}
        for r, resource in enumerate(resources):
            if resource['type'] == 'battery':
                self.variables['soc'][resource['name']] = {}
                self.variables['charge'][resource['name']] = {}
                self.variables['discharge'][resource['name']] = {}
                for s, scenario in enumerate(scenarios):
                    self.variables['soc'][resource['name']][scenario] = {}
                    self.variables['charge'][resource['name']][scenario] = {}
                    self.variables['discharge'][resource['name']][scenario] = {}
                    for t in range(time_periods):
                        self.variables['soc'][resource['name']][scenario][t] = self.solver.NumVar(
                            resource['min_soc'], resource['max_soc'],
                            f"soc_{resource['name']}_{scenario}_{t}"
                        )
                        self.variables['charge'][resource['name']][scenario][t] = self.solver.NumVar(
                            0, resource['max_charge_rate'],
                            f"charge_{resource['name']}_{scenario}_{t}"
                        )
                        self.variables['discharge'][resource['name']][scenario][t] = self.solver.NumVar(
                            0, resource['max_discharge_rate'],
                            f"discharge_{resource['name']}_{scenario}_{t}"
                        )
        
        # Market participation variables
        self.variables['market_bid'] = {}
        for s, scenario in enumerate(scenarios):
            self.variables['market_bid'][scenario] = {}
            for t in range(time_periods):
                self.variables['market_bid'][scenario][t] = self.solver.NumVar(
                    0, sum(r['capacity'] for r in resources),
                    f"market_bid_{scenario}_{t}"
                )
        
        # Reserve provision variables
        self.variables['reserve'] = {}
        for r, resource in enumerate(resources):
            self.variables['reserve'][resource['name']] = {}
            for s, scenario in enumerate(scenarios):
                self.variables['reserve'][resource['name']][scenario] = {}
                for t in range(time_periods):
                    # Calculate max reserve based on resource type
                    if resource['type'] == 'battery':
                        max_reserve = resource['max_discharge_rate']
                    elif 'availability_profile' in resource:
                        max_reserve = resource['capacity'] * resource['availability_profile'][t]
                    else:
                        max_reserve = resource['capacity']
                    
                    self.variables['reserve'][resource['name']][scenario][t] = self.solver.NumVar(
                        0, max_reserve, f"reserve_{resource['name']}_{scenario}_{t}"
                    )
        
        self.logger.info(f"Defined variables for {len(resources)} resources, {len(scenarios)} scenarios, {time_periods} time periods")
        
    def define_constraints(self):
        """Define constraints for the VPP optimization"""
        resources = self.configs['distributed_resources']
        scenarios = list(self.configs['market_prices'].keys())
        time_periods = self.configs['market_parameters']['time_periods']
        
        # 1. Power Balance Constraint (for each scenario and time period)
        for s, scenario in enumerate(scenarios):
            for t in range(time_periods):
                # Total generation must equal market bid
                total_generation = self.solver.Sum(
                    self.variables['power'][r['name']][scenario][t] 
                    for r in resources if r['type'] != 'demand_response'
                )
                # Demand response reduces demand (negative generation)
                total_dr = self.solver.Sum(
                    -self.variables['power'][r['name']][scenario][t] 
                    for r in resources if r['type'] == 'demand_response'
                )
                
                self.constraints[f'power_balance_{scenario}_{t}'] = self.solver.Add(
                    total_generation + total_dr == self.variables['market_bid'][scenario][t]
                )
        
        # 2. Battery State of Charge Constraints
        for r, resource in enumerate(resources):
            if resource['type'] == 'battery':
                for s, scenario in enumerate(scenarios):
                    # Initial SOC
                    self.constraints[f'soc_initial_{resource["name"]}_{scenario}'] = self.solver.Add(
                        self.variables['soc'][resource['name']][scenario][0] == resource['initial_soc']
                    )
                    
                    # SOC evolution over time
                    for t in range(1, time_periods):
                        # SOC(t) = SOC(t-1) - power(t-1) / energy_capacity
                        # For battery: negative power = charging (SOC increases), positive power = discharging (SOC decreases)
                        # We need to handle the efficiency properly
                        
                        # Create separate charge and discharge variables for proper efficiency handling
                        charge_var = self.variables['charge'][resource['name']][scenario][t-1]
                        discharge_var = self.variables['discharge'][resource['name']][scenario][t-1]
                        
                        # SOC evolution with efficiency
                        # SOC increases by charge * efficiency, decreases by discharge / efficiency
                        soc_change = (charge_var * resource['efficiency'] - discharge_var / resource['efficiency']) / resource['energy_capacity']
                        
                        self.constraints[f'soc_evolution_{resource["name"]}_{scenario}_{t}'] = self.solver.Add(
                            self.variables['soc'][resource['name']][scenario][t] == 
                            self.variables['soc'][resource['name']][scenario][t-1] + soc_change
                        )
                    
                    # Final SOC constraint (optional - can be removed if not needed)
                    # self.constraints[f'soc_final_{resource["name"]}_{scenario}'] = self.solver.Add(
                    #     self.variables['soc'][resource['name']][scenario][time_periods-1] >= resource['min_soc']
                    # )
                    
                    # SOC bounds for all time periods
                    for t in range(time_periods):
                        self.constraints[f'soc_min_{resource["name"]}_{scenario}_{t}'] = self.solver.Add(
                            self.variables['soc'][resource['name']][scenario][t] >= resource['min_soc']
                        )
                        self.constraints[f'soc_max_{resource["name"]}_{scenario}_{t}'] = self.solver.Add(
                            self.variables['soc'][resource['name']][scenario][t] <= resource['max_soc']
                        )
                    
                    # Link power variable with charge and discharge variables
                    for t in range(time_periods):
                        # power = discharge - charge (positive = discharging, negative = charging)
                        self.constraints[f'power_charge_discharge_{resource["name"]}_{scenario}_{t}'] = self.solver.Add(
                            self.variables['power'][resource['name']][scenario][t] == 
                            self.variables['discharge'][resource['name']][scenario][t] - 
                            self.variables['charge'][resource['name']][scenario][t]
                        )
        
        # 3. Reserve Capacity Constraints
        reserve_margin = self.configs['market_parameters']['reserve_margin']
        for s, scenario in enumerate(scenarios):
            for t in range(time_periods):
                total_reserve = self.solver.Sum(
                    self.variables['reserve'][r['name']][scenario][t] for r in resources
                )
                required_reserve = self.variables['market_bid'][scenario][t] * reserve_margin
                
                self.constraints[f'reserve_capacity_{scenario}_{t}'] = self.solver.Add(
                    total_reserve >= required_reserve
                )
        
        # 4. Resource Capacity Constraints
        for r, resource in enumerate(resources):
            for s, scenario in enumerate(scenarios):
                for t in range(time_periods):
                    # Calculate max available capacity based on resource type
                    if resource['type'] == 'battery':
                        max_available = resource['max_discharge_rate']
                    elif 'availability_profile' in resource:
                        max_available = resource['capacity'] * resource['availability_profile'][t]
                    else:
                        max_available = resource['capacity']
                    
                    if resource['type'] == 'battery':
                        # Battery: discharge + reserve <= max_discharge_rate, charge <= max_charge_rate
                        self.constraints[f'capacity_discharge_{resource["name"]}_{scenario}_{t}'] = self.solver.Add(
                            self.variables['discharge'][resource['name']][scenario][t] + 
                            self.variables['reserve'][resource['name']][scenario][t] <= 
                            resource['max_discharge_rate']
                        )
                        self.constraints[f'capacity_charge_{resource["name"]}_{scenario}_{t}'] = self.solver.Add(
                            self.variables['charge'][resource['name']][scenario][t] <= 
                            resource['max_charge_rate']
                        )
                    else:
                        # Other resources: power + reserve <= max_available
                        self.constraints[f'capacity_{resource["name"]}_{scenario}_{t}'] = self.solver.Add(
                            self.variables['power'][resource['name']][scenario][t] + 
                            self.variables['reserve'][resource['name']][scenario][t] <= 
                            max_available
                        )
        
        # 5. Ramp Rate Constraints
        for r, resource in enumerate(resources):
            for s, scenario in enumerate(scenarios):
                for t in range(1, time_periods):
                    power_change = self.variables['power'][resource['name']][scenario][t] - \
                                 self.variables['power'][resource['name']][scenario][t-1]
                    
                    self.constraints[f'ramp_up_{resource["name"]}_{scenario}_{t}'] = self.solver.Add(
                        power_change <= resource['ramp_up']
                    )
                    self.constraints[f'ramp_down_{resource["name"]}_{scenario}_{t}'] = self.solver.Add(
                        power_change >= -resource['ramp_down']
                    )
        
        self.logger.info(f"Defined constraints for VPP optimization")
        
    def define_objective(self):
        """Define the objective function for VPP optimization"""
        resources = self.configs['distributed_resources']
        scenarios = list(self.configs['market_prices'].keys())
        time_periods = self.configs['market_parameters']['time_periods']
        
        objective_terms = []
        
        # 1. Revenue from market participation
        for s, scenario in enumerate(scenarios):
            scenario_prob = self.configs['market_prices'][scenario]['probability']
            for t in range(time_periods):
                market_price = self.configs['market_prices'][scenario]['prices'][t]
                revenue = market_price * self.variables['market_bid'][scenario][t] * scenario_prob
                objective_terms.append(revenue)
        
        # 2. Operating costs
        for r, resource in enumerate(resources):
            for s, scenario in enumerate(scenarios):
                scenario_prob = self.configs['market_prices'][scenario]['probability']
                for t in range(time_periods):
                    # Variable costs
                    if resource['type'] != 'demand_response':
                        var_cost = resource['variable_cost'] * self.variables['power'][resource['name']][scenario][t] * scenario_prob
                        objective_terms.append(-var_cost)
                    else:
                        # Demand response incentive (negative cost)
                        dr_incentive = resource['variable_cost'] * self.variables['power'][resource['name']][scenario][t] * scenario_prob
                        objective_terms.append(dr_incentive)
                    
                    # Fixed costs (simplified - based on capacity)
                    fixed_cost = resource['fixed_cost'] * resource['capacity'] * scenario_prob / time_periods
                    objective_terms.append(-fixed_cost)
        
        # 3. Carbon credits for renewable generation
        for r, resource in enumerate(resources):
            if resource['type'] in ['solar', 'wind']:
                for s, scenario in enumerate(scenarios):
                    scenario_prob = self.configs['market_prices'][scenario]['probability']
                    for t in range(time_periods):
                        carbon_credit = self.configs['market_parameters']['renewable_credit'] * \
                                      self.variables['power'][resource['name']][scenario][t] * scenario_prob
                        objective_terms.append(carbon_credit)
        
        # 4. Market participation fees
        for s, scenario in enumerate(scenarios):
            scenario_prob = self.configs['market_prices'][scenario]['probability']
            for t in range(time_periods):
                participation_fee = self.configs['market_parameters']['market_participation_fee'] * \
                                  self.variables['market_bid'][scenario][t] * scenario_prob
                objective_terms.append(-participation_fee)
        
        # Note: Battery energy balance will be checked in post-processing
        
        # Set objective to maximize net revenue
        self.solver.Maximize(self.solver.Sum(objective_terms))
        
        self.logger.info("Defined objective function for VPP optimization")
        
    def solve(self):
        """Solve the VPP optimization problem"""
        self.logger.info("Starting VPP optimization...")
        
        # Create solver and define problem
        self.create_solver()
        self.define_variables()
        self.define_constraints()
        self.define_objective()
        
        # Solve the problem
        status = self.solver.Solve()
        
        if status == pywraplp.Solver.OPTIMAL:
            self.logger.info("VPP optimization completed successfully!")
            self.extract_results()
            return True
        else:
            self.logger.error(f"VPP optimization failed with status: {status}")
            return False
    
    def extract_results(self):
        """Extract and format optimization results"""
        resources = self.configs['distributed_resources']
        scenarios = list(self.configs['market_prices'].keys())
        time_periods = self.configs['market_parameters']['time_periods']
        
        # Extract power generation results
        self.results['power_generation'] = {}
        for r, resource in enumerate(resources):
            self.results['power_generation'][resource['name']] = {}
            for s, scenario in enumerate(scenarios):
                self.results['power_generation'][resource['name']][scenario] = []
                for t in range(time_periods):
                    power = self.variables['power'][resource['name']][scenario][t].solution_value()
                    self.results['power_generation'][resource['name']][scenario].append(power)
        
        # Extract battery SOC results
        self.results['battery_soc'] = {}
        # Extract battery charge and discharge results
        self.results['battery_charge'] = {}
        self.results['battery_discharge'] = {}
        for r, resource in enumerate(resources):
            if resource['type'] == 'battery':
                self.results['battery_soc'][resource['name']] = {}
                self.results['battery_charge'][resource['name']] = {}
                self.results['battery_discharge'][resource['name']] = {}
                for s, scenario in enumerate(scenarios):
                    self.results['battery_soc'][resource['name']][scenario] = []
                    self.results['battery_charge'][resource['name']][scenario] = []
                    self.results['battery_discharge'][resource['name']][scenario] = []
                    for t in range(time_periods):
                        soc = self.variables['soc'][resource['name']][scenario][t].solution_value()
                        charge = self.variables['charge'][resource['name']][scenario][t].solution_value()
                        discharge = self.variables['discharge'][resource['name']][scenario][t].solution_value()
                        self.results['battery_soc'][resource['name']][scenario].append(soc)
                        self.results['battery_charge'][resource['name']][scenario].append(charge)
                        self.results['battery_discharge'][resource['name']][scenario].append(discharge)
        
        # Extract market bids
        self.results['market_bids'] = {}
        for s, scenario in enumerate(scenarios):
            self.results['market_bids'][scenario] = []
            for t in range(time_periods):
                bid = self.variables['market_bid'][scenario][t].solution_value()
                self.results['market_bids'][scenario].append(bid)
        
        # Extract reserve provision
        self.results['reserve_provision'] = {}
        for r, resource in enumerate(resources):
            self.results['reserve_provision'][resource['name']] = {}
            for s, scenario in enumerate(scenarios):
                self.results['reserve_provision'][resource['name']][scenario] = []
                for t in range(time_periods):
                    reserve = self.variables['reserve'][resource['name']][scenario][t].solution_value()
                    self.results['reserve_provision'][resource['name']][scenario].append(reserve)
        
        # Calculate expected values (weighted by scenario probabilities)
        self.results['expected_power'] = {}
        for r, resource in enumerate(resources):
            self.results['expected_power'][resource['name']] = []
            for t in range(time_periods):
                expected_power = sum(
                    self.results['power_generation'][resource['name']][scenario][t] * 
                    self.configs['market_prices'][scenario]['probability']
                    for scenario in scenarios
                )
                self.results['expected_power'][resource['name']].append(expected_power)
        
        # Calculate financial metrics
        self.calculate_financial_metrics()
        
        self.logger.info("Results extracted successfully")
        
        # Debug: Show battery operation pattern
        if 'battery_soc' in self.results:
            self.logger.info("🔋 Battery Operation Analysis:")
            for battery_name, soc_data in self.results['battery_soc'].items():
                for scenario, soc_values in soc_data.items():
                    charge_values = self.results['battery_charge'][battery_name][scenario]
                    discharge_values = self.results['battery_discharge'][battery_name][scenario]
                    
                    # Calculate energy balance using separate charge/discharge variables
                    total_charge = sum(charge_values)
                    total_discharge = sum(discharge_values)
                    
                    # Find battery resource for efficiency
                    battery_resource = next(r for r in self.configs['distributed_resources'] if r['name'] == battery_name)
                    efficiency = battery_resource['efficiency']
                    
                    # Check energy balance with proper efficiency
                    max_discharge = total_charge * efficiency  # Energy stored * efficiency
                    energy_violation = total_discharge - max_discharge
                    
                    self.logger.info(f"  {battery_name} ({scenario}):")
                    self.logger.info(f"    SOC range: {min(soc_values):.2f} - {max(soc_values):.2f}")
                    self.logger.info(f"    Charge range: {min(charge_values):.2f} to {max(charge_values):.2f} MW")
                    self.logger.info(f"    Discharge range: {min(discharge_values):.2f} to {max(discharge_values):.2f} MW")
                    self.logger.info(f"    Charging periods: {sum(1 for c in charge_values if c > 0)}")
                    self.logger.info(f"    Discharging periods: {sum(1 for d in discharge_values if d > 0)}")
                    self.logger.info(f"    Energy balance: Charged {total_charge:.1f} MWh, Discharged {total_discharge:.1f} MWh")
                    self.logger.info(f"    Max allowed discharge: {max_discharge:.1f} MWh")
                    
                    if energy_violation > 0:
                        self.logger.warning(f"    ⚠️ ENERGY BALANCE VIOLATION: {energy_violation:.1f} MWh excess discharge!")
                    else:
                        self.logger.info(f"    ✅ Energy balance OK")
    
    def calculate_financial_metrics(self):
        """Calculate financial performance metrics"""
        scenarios = list(self.configs['market_prices'].keys())
        time_periods = self.configs['market_parameters']['time_periods']
        
        # Calculate expected revenue
        expected_revenue = 0
        for s, scenario in enumerate(scenarios):
            scenario_prob = self.configs['market_prices'][scenario]['probability']
            for t in range(time_periods):
                market_price = self.configs['market_prices'][scenario]['prices'][t]
                bid = self.results['market_bids'][scenario][t]
                expected_revenue += market_price * bid * scenario_prob
        
        # Calculate expected costs
        expected_costs = 0
        resources = self.configs['distributed_resources']
        for r, resource in enumerate(resources):
            for s, scenario in enumerate(scenarios):
                scenario_prob = self.configs['market_prices'][scenario]['probability']
                for t in range(time_periods):
                    power = self.results['power_generation'][resource['name']][scenario][t]
                    if resource['type'] != 'demand_response':
                        expected_costs += resource['variable_cost'] * power * scenario_prob
                    else:
                        expected_costs -= resource['variable_cost'] * power * scenario_prob  # Incentive
                    expected_costs += resource['fixed_cost'] * resource['capacity'] * scenario_prob / time_periods
        
        # Calculate expected carbon credits
        expected_carbon_credits = 0
        for r, resource in enumerate(resources):
            if resource['type'] in ['solar', 'wind']:
                for s, scenario in enumerate(scenarios):
                    scenario_prob = self.configs['market_prices'][scenario]['probability']
                    for t in range(time_periods):
                        power = self.results['power_generation'][resource['name']][scenario][t]
                        expected_carbon_credits += self.configs['market_parameters']['renewable_credit'] * power * scenario_prob
        
        # Calculate market participation fees
        expected_fees = 0
        for s, scenario in enumerate(scenarios):
            scenario_prob = self.configs['market_prices'][scenario]['probability']
            for t in range(time_periods):
                bid = self.results['market_bids'][scenario][t]
                expected_fees += self.configs['market_parameters']['market_participation_fee'] * bid * scenario_prob
        
        # Store financial metrics
        self.results['financial_metrics'] = {
            'expected_revenue': expected_revenue,
            'expected_costs': expected_costs,
            'expected_carbon_credits': expected_carbon_credits,
            'expected_fees': expected_fees,
            'expected_profit': expected_revenue - expected_costs + expected_carbon_credits - expected_fees,
            'roi': (expected_revenue - expected_costs + expected_carbon_credits - expected_fees) / expected_costs if expected_costs > 0 else 0
        }
        
        self.logger.info(f"Financial metrics calculated: Expected profit = ${self.results['financial_metrics']['expected_profit']:.2f}")
    
    def get_summary(self):
        """Get a summary of the VPP optimization results"""
        if not self.results:
            return "No results available. Run solve() first."
        
        summary = []
        summary.append("=" * 60)
        summary.append("VIRTUAL POWER PLANT (VPP) OPTIMIZATION RESULTS")
        summary.append("=" * 60)
        
        # Financial summary
        metrics = self.results['financial_metrics']
        summary.append(f"💰 Financial Performance:")
        summary.append(f"   Expected Revenue: ${metrics['expected_revenue']:.2f}")
        summary.append(f"   Expected Costs: ${metrics['expected_costs']:.2f}")
        summary.append(f"   Carbon Credits: ${metrics['expected_carbon_credits']:.2f}")
        summary.append(f"   Market Fees: ${metrics['expected_fees']:.2f}")
        summary.append(f"   Expected Profit: ${metrics['expected_profit']:.2f}")
        summary.append(f"   ROI: {metrics['roi']*100:.1f}%")
        
        # Resource utilization
        summary.append(f"\n📊 Resource Utilization (Expected Values):")
        for resource_name, expected_power in self.results['expected_power'].items():
            total_power = sum(expected_power)
            avg_power = total_power / len(expected_power)
            summary.append(f"   {resource_name}: {total_power:.1f} MWh total, {avg_power:.1f} MW avg")
        
        # Market participation
        summary.append(f"\n🏪 Market Participation:")
        for scenario, bids in self.results['market_bids'].items():
            total_bid = sum(bids)
            avg_bid = total_bid / len(bids)
            prob = self.configs['market_prices'][scenario]['probability']
            summary.append(f"   {scenario} (p={prob}): {total_bid:.1f} MWh total, {avg_bid:.1f} MW avg")
        
        summary.append("=" * 60)
        
        return "\n".join(summary) 
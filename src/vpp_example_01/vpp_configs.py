"""
Virtual Power Plant (VPP) Configuration
Demonstrates key differences from traditional Unit Commitment:
- Distributed Energy Resources (DERs)
- Market participation and price signals
- Stochastic optimization with uncertainty
- Longer planning horizons
- Aggregation of diverse resources

BATTERY STATE OF CHARGE (SOC) MODELING:
========================================
The VPP includes comprehensive battery SOC modeling with the following features:

1. SOC Variables:
   - SOC(t): State of charge at time t (0.1 to 0.9, i.e., 10% to 90%)
   - charge(t): Charging power at time t (0 to max_charge_rate)
   - discharge(t): Discharging power at time t (0 to max_discharge_rate)

2. SOC Evolution Equation:
   SOC(t) = SOC(t-1) + (charge(t-1) * efficiency - discharge(t-1) / efficiency) / energy_capacity
   
   Where:
   - efficiency = 0.9 (90% round-trip efficiency)
   - energy_capacity = 80 MWh (total battery capacity)

3. SOC Constraints:
   - min_soc <= SOC(t) <= max_soc (10% to 90%)
   - SOC(0) = initial_soc (50% at start)
   - Energy balance enforced through separate charge/discharge variables

4. SOC Analysis:
   - Track SOC history over 24 hours
   - Calculate energy balance (charged vs discharged)
   - Warn on energy balance violations
   - Report SOC range and final state

5. Battery Configuration:
   - min_soc: 0.1 (10% minimum)
   - max_soc: 0.9 (90% maximum)  
   - initial_soc: 0.5 (50% initial)
   - efficiency: 0.9 (90% efficiency)
   - energy_capacity: 80 MWh
"""

# Market price scenarios (stochastic)
market_prices = {
    'scenario_1': {  # High price scenario
        'probability': 0.3,
        'prices': [45, 52, 58, 65, 72, 68, 55, 48, 42, 38, 35, 32, 30, 28, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17]
    },
    'scenario_2': {  # Medium price scenario
        'probability': 0.5,
        'prices': [35, 38, 42, 45, 48, 45, 40, 35, 32, 30, 28, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14]
    },
    'scenario_3': {  # Low price scenario
        'probability': 0.2,
        'prices': [25, 28, 32, 35, 38, 35, 30, 25, 22, 20, 18, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4]
    }
}

# Distributed Energy Resources (DERs)
distributed_resources = [
    {
        'name': 'Solar_Farm_1',
        'type': 'solar',
        'capacity': 50.0,  # MW
        'location': 'Zone_A',
        'owner': 'Residential_Cooperative',
        'variable_cost': 0.0,  # $/MWh (solar has no fuel cost)
        'fixed_cost': 5.0,  # $/MW/h (maintenance)
        'availability_profile': [0, 0, 0, 0, 0, 0, 0.1, 0.3, 0.6, 0.8, 0.9, 1.0, 1.0, 0.9, 0.8, 0.6, 0.3, 0.1, 0, 0, 0, 0, 0, 0],  # Solar availability by hour
        'ramp_up': 10.0,  # MW/h
        'ramp_down': 10.0,  # MW/h
        'min_up_time': 1,  # hours
        'min_down_time': 1,  # hours
        'startup_cost': 0.0,  # $ (solar has no startup cost)
        'shutdown_cost': 0.0,  # $ (solar has no shutdown cost)
        'initial_state': {'on': True, 'power': 0.0}
    },
    {
        'name': 'Wind_Farm_1',
        'type': 'wind',
        'capacity': 30.0,  # MW
        'location': 'Zone_B',
        'owner': 'Commercial_Investor',
        'variable_cost': 0.0,  # $/MWh
        'fixed_cost': 8.0,  # $/MW/h
        'availability_profile': [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3],  # Wind availability
        'ramp_up': 15.0,  # MW/h
        'ramp_down': 15.0,  # MW/h
        'min_up_time': 1,
        'min_down_time': 1,
        'startup_cost': 0.0,
        'shutdown_cost': 0.0,
        'initial_state': {'on': True, 'power': 12.0}
    },
    {
        'name': 'Battery_Storage_1',
        'type': 'battery',
        'capacity': 20.0,  # MW (power rating)
        'energy_capacity': 80.0,  # MWh (energy storage capacity)
        'location': 'Zone_C',
        'owner': 'Utility_Company',
        'variable_cost': 2.0,  # $/MWh (degradation cost)
        'fixed_cost': 3.0,  # $/MW/h
        
        # SOC (State of Charge) Parameters
        'min_soc': 0.1,  # 10% minimum state of charge (prevents deep discharge)
        'max_soc': 0.9,  # 90% maximum state of charge (prevents overcharging)
        'initial_soc': 0.5,  # 50% initial state of charge
        
        # Battery Efficiency Parameters
        'efficiency': 0.9,  # 90% round-trip efficiency (charge and discharge)
        'efficiency_charging': 0.9,   # 90% charging efficiency
        'efficiency_discharging': 0.9, # 90% discharging efficiency
        
        # Battery Power Rate Limits
        'min_charge_rate': 0.0,  # MW (minimum charging power)
        'max_charge_rate': 20.0,  # MW (maximum charging power)
        'min_discharge_rate': 0.0,  # MW (minimum discharging power)
        'max_discharge_rate': 20.0,  # MW (maximum discharging power)
        
        # Operational Constraints
        'ramp_up': 20.0,  # MW/h (maximum power increase per hour)
        'ramp_down': 20.0,  # MW/h (maximum power decrease per hour)
        'startup_cost': 0.0,  # $ (no startup cost for battery)
        'shutdown_cost': 0.0,  # $ (no shutdown cost for battery)
        
        # Initial State
        'initial_state': {'on': True, 'power': 0.0, 'soc': 0.5}
    },
    {
        'name': 'Demand_Response_1',
        'type': 'demand_response',
        'capacity': 15.0,  # MW (reduction capacity)
        'location': 'Zone_A',
        'owner': 'Industrial_Customer',
        'variable_cost': 15.0,  # $/MWh (incentive payment)
        'fixed_cost': 0.0,  # $/MW/h
        'availability_profile': [0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.9, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 0.8, 0.8, 0.8, 0.8, 0.8],  # DR availability
        'ramp_up': 5.0,  # MW/h
        'ramp_down': 5.0,  # MW/h
        'min_up_time': 2,  # hours
        'min_down_time': 1,  # hours
        'startup_cost': 0.0,
        'shutdown_cost': 0.0,
        'initial_state': {'on': False, 'power': 0.0}
    },
    {
        'name': 'EV_Charging_Station_1',
        'type': 'ev_charging',
        'capacity': 10.0,  # MW
        'location': 'Zone_B',
        'owner': 'Municipal_Utility',
        'variable_cost': 25.0,  # $/MWh (grid charging cost)
        'fixed_cost': 1.0,  # $/MW/h
        'availability_profile': [0.2, 0.1, 0.1, 0.1, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.1, 0.1, 0.1, 0.2],  # EV charging pattern
        'ramp_up': 5.0,  # MW/h
        'ramp_down': 5.0,  # MW/h
        'min_up_time': 1,
        'min_down_time': 1,
        'startup_cost': 0.0,
        'shutdown_cost': 0.0,
        'initial_state': {'on': False, 'power': 0.0}
    }
]

# Network constraints (simplified)
network_constraints = {
    'zones': ['Zone_A', 'Zone_B', 'Zone_C'],
    'transmission_capacity': {
        ('Zone_A', 'Zone_B'): 25.0,  # MW
        ('Zone_B', 'Zone_C'): 30.0,  # MW
        ('Zone_A', 'Zone_C'): 20.0,  # MW
    },
    'loss_factor': 0.02  # 2% transmission losses
}

# Market participation parameters
market_parameters = {
    'planning_horizon': 24,  # hours
    'time_periods': 24,  # hours
    'reserve_margin': 0.15,  # 15% reserve margin
    'market_participation_fee': 0.5,  # $/MW/h
    'balancing_market_penalty': 50.0,  # $/MWh for deviations
    'carbon_price': 30.0,  # $/ton CO2
    'renewable_credit': 15.0,  # $/MWh for renewable generation
}

# Uncertainty scenarios
uncertainty_scenarios = {
    'demand_uncertainty': {
        'scenario_1': {'probability': 0.3, 'multiplier': 1.2},  # High demand
        'scenario_2': {'probability': 0.5, 'multiplier': 1.0},  # Normal demand
        'scenario_3': {'probability': 0.2, 'multiplier': 0.8},  # Low demand
    },
    'renewable_uncertainty': {
        'scenario_1': {'probability': 0.4, 'multiplier': 1.1},  # High renewable output
        'scenario_2': {'probability': 0.4, 'multiplier': 1.0},  # Normal renewable output
        'scenario_3': {'probability': 0.2, 'multiplier': 0.8},  # Low renewable output
    }
}

# Base demand profile (24 hours)
base_demand_profile = [
    120, 110, 100, 95, 90, 85, 80, 85, 100, 120, 140, 160, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290
]  # MW

# Battery State of Charge (SOC) Configuration
battery_soc_config = {
    'default_min_soc': 0.1,      # 10% minimum state of charge (prevents deep discharge)
    'default_max_soc': 0.9,      # 90% maximum state of charge (prevents overcharging)
    'default_initial_soc': 0.5,  # 50% initial state of charge
    'soc_evolution_method': 'efficiency_based',  # How SOC evolves over time
    'efficiency_charging': 0.9,   # 90% charging efficiency
    'efficiency_discharging': 0.9, # 90% discharging efficiency
    'round_trip_efficiency': 0.81, # 0.9 * 0.9 = 81% round-trip efficiency
    'soc_constraints': {
        'enforce_min_soc': True,   # Enforce minimum SOC constraint
        'enforce_max_soc': True,   # Enforce maximum SOC constraint
        'enforce_energy_balance': True,  # Enforce energy balance constraint
        'allow_soc_violation_penalty': False,  # Don't allow SOC violations
    },
    'soc_analysis': {
        'track_soc_history': True,  # Track SOC over time
        'calculate_energy_balance': True,  # Calculate energy balance
        'warn_on_energy_violation': True,  # Warn on energy balance violations
        'soc_reporting_interval': 1,  # Report SOC every hour
    }
}

# VPP aggregation parameters
vpp_parameters = {
    'aggregator_name': 'GreenGrid_VPP',
    'total_capacity': sum(resource['capacity'] for resource in distributed_resources),
    'renewable_penetration': 0.6,  # 60% renewable energy
    'flexibility_score': 0.8,  # 80% flexibility (battery + DR)
    'market_clearing_interval': 1,  # hours
    'settlement_period': 24,  # hours
    'performance_bonus': 0.05,  # 5% bonus for meeting commitments
    'penalty_rate': 0.1,  # 10% penalty for deviations
} 
# Virtual Power Plant (VPP) Example

## 🏭 Overview

This Virtual Power Plant (VPP) example demonstrates how distributed energy resources can be coordinated to act as a single power plant, optimizing market participation and grid services.

## 🎯 What is a Virtual Power Plant?

A VPP is a **network of distributed energy resources** that are coordinated to act like a single power plant. Unlike traditional power plants that exist in one location, a VPP aggregates resources across multiple locations and optimizes their operation for maximum value.

### Key Characteristics:
- **Distributed Resources**: Solar, wind, batteries, demand response
- **Market Participation**: Optimized bidding in electricity markets
- **Stochastic Optimization**: Handles price uncertainty
- **Grid Services**: Provides flexibility and stability
- **Revenue Maximization**: Optimizes timing of generation/consumption

## 👥 Business Model & Actors

### 1. VPP Aggregator (The "Orchestrator")
```
Name: GreenGrid_VPP
Role: Coordinates all distributed resources
Revenue: Market participation and optimization services
```

**Responsibilities:**
- Coordinate all distributed resources
- Optimize when each resource generates/consumes
- Participate in electricity markets
- Manage contracts with resource owners
- Handle market settlements and payments

### 2. Resource Owners (The "Suppliers")

#### Private Households
```
Example: Home with solar panels + battery
- Solar panels: 5 kW capacity
- Home battery: 10 kWh storage
- Owner: Individual homeowner
- Contract: Sell excess power to VPP aggregator
```

#### Commercial Entities
```
Example: Industrial facility with demand response
- Factory with flexible load
- Can reduce consumption during high-price periods
- Owner: Industrial company
- Contract: Get paid for load reduction
```

#### Utility Companies
```
Example: Large battery storage facility
- 20 MW battery system
- Owner: Utility company
- Contract: Provide storage services to VPP
```

#### Renewable Energy Developers
```
Example: Solar farm
- 50 MW solar farm
- Owner: Renewable energy company
- Contract: Sell power through VPP
```

## 💰 Revenue Streams & Profit Distribution

### Market Revenue Example
```
High Price Period: $72/MWh
- Solar farm generates: 50 MW × $72 = $3,600/hour
- Battery discharges: 20 MW × $72 = $1,440/hour
- Total revenue: $5,040/hour

Low Price Period: $4/MWh  
- Battery charges: 20 MW × $4 = $80/hour
- Net profit from arbitrage
```

### Profit Distribution
```
VPP Aggregator Revenue: $5,040/hour
- Payment to solar farm: $3,200/hour (negotiated rate)
- Payment to battery: $1,200/hour (negotiated rate)
- Market fees: $50/hour
- Aggregator profit: $590/hour ✅
```

## 🏗️ Technical Implementation

### Resource Types in Our VPP

#### 1. Solar Farm
```python
{
    'name': 'Solar_Farm_1',
    'type': 'solar',
    'capacity': 50.0,  # MW
    'owner': 'Residential_Cooperative',
    'availability_profile': [0, 0, 0, 0, 0, 0, 0.1, 0.3, 0.6, 0.8, 0.9, 1.0, ...]
}
```

#### 2. Wind Farm
```python
{
    'name': 'Wind_Farm_1',
    'type': 'wind', 
    'capacity': 30.0,  # MW
    'owner': 'Commercial_Investor',
    'availability_profile': [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, ...]
}
```

#### 3. Battery Storage
```python
{
    'name': 'Battery_Storage_1',
    'type': 'battery',
    'capacity': 20.0,  # MW (power rating)
    'energy_capacity': 80.0,  # MWh (energy storage)
    
    # SOC (State of Charge) Parameters
    'min_soc': 0.1,  # 10% minimum state of charge
    'max_soc': 0.9,  # 90% maximum state of charge
    'initial_soc': 0.5,  # 50% initial state of charge
    'efficiency': 0.9,  # 90% round-trip efficiency
}
```

#### 4. Demand Response
```python
{
    'name': 'Demand_Response_1',
    'type': 'demand_response',
    'capacity': 15.0,  # MW (reduction capacity)
    'owner': 'Industrial_Customer',
    'variable_cost': 15.0,  # $/MWh (incentive payment)
}
```

### Battery State of Charge (SOC) Modeling

The VPP includes comprehensive battery SOC modeling:

#### SOC Variables:
- **SOC(t)**: State of charge at time t (0.1 to 0.9, i.e., 10% to 90%)
- **charge(t)**: Charging power at time t (0 to max_charge_rate)
- **discharge(t)**: Discharging power at time t (0 to max_discharge_rate)

#### SOC Evolution Equation:
```
SOC(t) = SOC(t-1) + (charge(t-1) * efficiency - discharge(t-1) / efficiency) / energy_capacity
```

Where:
- efficiency = 0.9 (90% round-trip efficiency)
- energy_capacity = 80 MWh (total battery capacity)

#### SOC Constraints:
- min_soc ≤ SOC(t) ≤ max_soc (10% to 90%)
- SOC(0) = initial_soc (50% at start)
- Energy balance enforced through separate charge/discharge variables

## 📊 Market Scenarios

The VPP optimizes across multiple price scenarios:

### Scenario 1: High Price (30% probability)
```
Prices: [45, 52, 58, 65, 72, 68, 55, 48, 42, 38, 35, 32, 30, 28, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17]
Strategy: Maximize generation during peak hours
```

### Scenario 2: Medium Price (50% probability)
```
Prices: [35, 38, 42, 45, 48, 45, 40, 35, 32, 30, 28, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14]
Strategy: Balanced generation and storage
```

### Scenario 3: Low Price (20% probability)
```
Prices: [25, 28, 32, 35, 38, 35, 30, 25, 22, 20, 18, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4]
Strategy: Charge batteries during low-price periods
```

## 🚀 How to Run the VPP Example

### 1. Command Line Demo
```bash
cd src/vpp_example_01
python run_vpp_demo.py
```

### 2. Streamlit Interactive App
```bash
cd src/vpp_example_01
streamlit run streamlit_vpp_app.py
```

### 3. Expected Output
```
VIRTUAL POWER PLANT (VPP) OPTIMIZATION RESULTS
===============================================
💰 Financial Performance:
   Expected Revenue: $2,847.60
   Expected Costs: $1,234.50
   Carbon Credits: $456.30
   Market Fees: $89.20
   Expected Profit: $1,980.20
   ROI: 160.5%

📊 Resource Utilization (Expected Values):
   Solar_Farm_1: 876.5 MWh total, 36.5 MW avg
   Wind_Farm_1: 432.1 MWh total, 18.0 MW avg
   Battery_Storage_1: 156.8 MWh total, 6.5 MW avg
   Demand_Response_1: 89.2 MWh total, 3.7 MW avg

🔋 Battery Operation Analysis:
   Battery_Storage_1 (scenario_1):
     SOC range: 0.10 - 0.90
     Charging periods: 8
     Discharging periods: 16
     Energy balance: Charged 45.2 MWh, Discharged 36.7 MWh
     ✅ Energy balance OK
```

## 🎯 Key Benefits

### For Resource Owners:
- **Higher revenue** than selling individually
- **Risk sharing** through aggregation
- **Technical support** from aggregator
- **Market access** they couldn't get alone

### For the Grid:
- **Flexibility** from diverse resources
- **Stability** from coordinated operation
- **Efficiency** from optimized dispatch
- **Renewable integration** support

### For the Aggregator:
- **Market expertise** monetization
- **Optimization** value creation
- **Risk management** services
- **Technology platform** licensing

## 🌍 Real-World Examples

### Tesla Virtual Power Plant (Australia)
- **50,000+ homes** with solar + Powerwall batteries
- **Coordinated** by Tesla to provide grid services
- **Homeowners** get paid for participating
- **Grid** gets stability and peak shaving

### Next Kraftwerke (Germany)
- **10,000+ distributed resources**
- **Wind, solar, biogas, batteries, demand response**
- **Aggregates** small resources into marketable units
- **Trades** in European electricity markets

## 📁 File Structure

```
src/vpp_example_01/
├── README_VPP.md              # This file
├── vpp_configs.py             # VPP configuration and parameters
├── vpp_optimizer.py           # Core optimization engine
├── run_vpp_demo.py            # Command-line demo runner
├── streamlit_vpp_app.py       # Interactive Streamlit app
└── __init__.py
```

## 🔧 Technical Features

### Optimization Features:
- **Stochastic optimization** with multiple price scenarios
- **Battery SOC modeling** with efficiency constraints
- **Market participation** optimization
- **Reserve capacity** provision
- **Ramp rate** constraints
- **Energy balance** enforcement

### Analysis Features:
- **Financial metrics** calculation
- **Resource utilization** analysis
- **Battery operation** tracking
- **Energy balance** verification
- **Market participation** analysis

## 🎓 Learning Objectives

This VPP example demonstrates:

1. **Distributed Energy Resource** coordination
2. **Stochastic optimization** under uncertainty
3. **Battery energy storage** modeling
4. **Market participation** strategies
5. **Revenue optimization** techniques
6. **Grid service** provision
7. **Business model** analysis

## 📈 Future Enhancements

Potential improvements to the VPP model:

- **Network constraints** modeling
- **Transmission losses** calculation
- **More resource types** (biogas, hydro, etc.)
- **Advanced market** participation strategies
- **Risk management** tools
- **Real-time optimization** capabilities
- **Machine learning** price forecasting

---

*This VPP example shows how distributed energy resources can be coordinated to create value for all participants while supporting grid stability and renewable energy integration.* 
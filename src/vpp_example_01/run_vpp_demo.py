#!/usr/bin/env python3
"""
Virtual Power Plant (VPP) Demo Runner
Demonstrates stochastic optimization of distributed energy resources
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vpp_example_01.vpp_configs import (
    distributed_resources, market_prices, market_parameters,
    uncertainty_scenarios, base_demand_profile, vpp_parameters
)
from vpp_example_01.vpp_optimizer import VPPOptimizer

def main():
    """Run VPP optimization demo"""
    print("=" * 60)
    print("VIRTUAL POWER PLANT (VPP) OPTIMIZATION DEMO")
    print("=" * 60)
    
    # Create configuration dictionary
    configs = {
        'distributed_resources': distributed_resources,
        'market_prices': market_prices,
        'market_parameters': market_parameters,
        'uncertainty_scenarios': uncertainty_scenarios,
        'base_demand_profile': base_demand_profile,
        'vpp_parameters': vpp_parameters
    }
    
    # Display VPP configuration
    print("\n📊 VPP Configuration:")
    print(f"   Aggregator: {vpp_parameters['aggregator_name']}")
    print(f"   Total Capacity: {vpp_parameters['total_capacity']} MW")
    print(f"   Renewable Penetration: {vpp_parameters['renewable_penetration']*100:.0f}%")
    print(f"   Flexibility Score: {vpp_parameters['flexibility_score']*100:.0f}%")
    
    print("\n🔋 Distributed Energy Resources:")
    for resource in distributed_resources:
        print(f"   {resource['name']} ({resource['type']}): {resource['capacity']} MW - {resource['owner']}")
    
    print("\n💰 Market Price Scenarios:")
    for scenario, data in market_prices.items():
        prob = data['probability']
        avg_price = sum(data['prices']) / len(data['prices'])
        print(f"   {scenario} (p={prob}): ${avg_price:.1f}/MWh average")
    
    # Create and run VPP optimizer
    print("\n🚀 Starting VPP Optimization...")
    vpp_optimizer = VPPOptimizer(configs)
    
    success = vpp_optimizer.solve()
    
    if success:
        print("\n✅ VPP Optimization Completed Successfully!")
        print("\n" + vpp_optimizer.get_summary())
        
        # Display detailed results
        print("\n📈 Detailed Results:")
        
        # Show expected power generation by resource
        print("\nExpected Power Generation (MW):")
        for resource_name, expected_power in vpp_optimizer.results['expected_power'].items():
            total_power = sum(expected_power)
            max_power = max(expected_power)
            print(f"   {resource_name}: {total_power:.1f} MWh total, {max_power:.1f} MW peak")
        
        # Show market participation
        print("\nMarket Participation (Expected Bids):")
        for scenario, bids in vpp_optimizer.results['market_bids'].items():
            total_bid = sum(bids)
            max_bid = max(bids)
            prob = configs['market_prices'][scenario]['probability']
            print(f"   {scenario} (p={prob}): {total_bid:.1f} MWh total, {max_bid:.1f} MW peak")
        
        # Show battery operation
        if 'battery_soc' in vpp_optimizer.results:
            print("\nBattery State of Charge:")
            for battery_name, soc_data in vpp_optimizer.results['battery_soc'].items():
                for scenario, soc_values in soc_data.items():
                    min_soc = min(soc_values)
                    max_soc = max(soc_values)
                    final_soc = soc_values[-1]
                    print(f"   {battery_name} ({scenario}): {min_soc:.2f} - {max_soc:.2f} SOC range, final: {final_soc:.2f}")
        
        # Show financial breakdown
        metrics = vpp_optimizer.results['financial_metrics']
        print(f"\n💰 Financial Breakdown:")
        print(f"   Revenue: ${metrics['expected_revenue']:.2f}")
        print(f"   Costs: ${metrics['expected_costs']:.2f}")
        print(f"   Carbon Credits: ${metrics['expected_carbon_credits']:.2f}")
        print(f"   Market Fees: ${metrics['expected_fees']:.2f}")
        print(f"   Net Profit: ${metrics['expected_profit']:.2f}")
        print(f"   ROI: {metrics['roi']*100:.1f}%")
        
    else:
        print("\n❌ VPP Optimization Failed!")
        print("Check the configuration and constraints.")
    
    print("\n" + "=" * 60)
    print("VPP Demo Completed!")
    print("=" * 60)

if __name__ == "__main__":
    main() 
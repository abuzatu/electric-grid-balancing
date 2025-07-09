"""Configs for the unit commitment problem."""

# Generator parameters as a list of dictionaries for easier extension and web app integration
units_example = [
    {
        'name': 'Unit 1',
        'P_min': 80,
        'P_max': 300,
        'cU': 800,   # Fixed cost per hour
        'c': 5,      # Variable cost per MWh
        'SU': 100,   # Startup ramp limit (MW)
        'SD': 80,    # Shutdown ramp limit (MW)
        'SU_cost': 100,  # Startup cost ($)
        'SD_cost': 80,   # Shutdown cost ($)
        'RU': 50,    # Ramp up limit (MW/h)
        'RD': 30,    # Ramp down limit (MW/h)
        'TU': 2,     # Min up time (h)
        'TD': 2,     # Min down time (h)
        'u0': 1,     # ON at t=0
        'su0': 0,    # Not starting up at t=0
        'sd0': 0,    # Not shutting down at t=0
        'p0': 120,   # Output at t=0
        'U0': 2,     # Required to stay ON for 2 time units at start of planning horizon
        'D0': 0      # Required to stay OFF for 0 time units at start of planning horizon
    },
    {
        'name': 'Unit 2',
        'P_min': 50,
        'P_max': 200,
        'cU': 500,
        'c': 15,
        'SU': 70,    # Startup ramp limit (MW)
        'SD': 50,    # Shutdown ramp limit (MW)
        'SU_cost': 70,   # Startup cost ($)
        'SD_cost': 50,   # Shutdown cost ($)
        'RU': 60,
        'RD': 40,
        'TU': 2,
        'TD': 2,
        'u0': 0,     # OFF at t=0
        'su0': 0,    # Not starting up at t=0
        'sd0': 0,    # Not shutting down at t=0
        'p0': 0,     # Output at t=0
        'U0': 0,     # Required to stay ON for 0 time units at start of planning horizon
        'D0': 0      # Required to stay OFF for 0 time units at start of planning horizon
    },
    {
        'name': 'Unit 3',
        'P_min': 30,
        'P_max': 100,
        'cU': 250,
        'c': 30,
        'SU': 40,    # Startup ramp limit (MW)
        'SD': 30,    # Shutdown ramp limit (MW)
        'SU_cost': 40,   # Startup cost ($)
        'SD_cost': 30,   # Shutdown cost ($)
        'RU': 70,
        'RD': 50,
        'TU': 1,
        'TD': 2,
        'u0': 0,     # OFF at t=0
        'su0': 0,    # Not starting up at t=0
        'sd0': 0,    # Not shutting down at t=0
        'p0': 0,     # Output at t=0
        'U0': 0,     # Required to stay ON for 0 time units at start of planning horizon
        'D0': 0      # Required to stay OFF for 0 time units at start of planning horizon
    }
]

# 24-hour realistic demand patterns for different scenarios
time_periods_24h = [
    {'demand': 0, 'reserve': 0},     # t=0: Initial state (no demand/reserve)
    {'demand': 120, 'reserve': 8},   # t=1: 12 AM - 1 AM (Night - lowest)
    {'demand': 110, 'reserve': 8},   # t=2: 1 AM - 2 AM (Night)
    {'demand': 105, 'reserve': 7},   # t=3: 2 AM - 3 AM (Night)
    {'demand': 100, 'reserve': 7},   # t=4: 3 AM - 4 AM (Night)
    {'demand': 95, 'reserve': 7},    # t=5: 4 AM - 5 AM (Night)
    {'demand': 90, 'reserve': 6},    # t=6: 5 AM - 6 AM (Night)
    {'demand': 150, 'reserve': 10},  # t=7: 6 AM - 7 AM (Early morning - rising)
    {'demand': 200, 'reserve': 12},  # t=8: 7 AM - 8 AM (Early morning)
    {'demand': 250, 'reserve': 15},  # t=9: 8 AM - 9 AM (Early morning)
    {'demand': 280, 'reserve': 17},  # t=10: 9 AM - 10 AM (Morning peak)
    {'demand': 290, 'reserve': 18},  # t=11: 10 AM - 11 AM (Morning peak)
    {'demand': 300, 'reserve': 18},  # t=12: 11 AM - 12 PM (Morning peak)
    {'demand': 280, 'reserve': 17},  # t=13: 12 PM - 1 PM (Lunch time - dip)
    {'demand': 260, 'reserve': 16},  # t=14: 1 PM - 2 PM (Lunch time)
    {'demand': 270, 'reserve': 16},  # t=15: 2 PM - 3 PM (Afternoon)
    {'demand': 280, 'reserve': 17},  # t=16: 3 PM - 4 PM (Afternoon)
    {'demand': 290, 'reserve': 17},  # t=17: 4 PM - 5 PM (Afternoon)
    {'demand': 310, 'reserve': 19},  # t=18: 5 PM - 6 PM (Afternoon)
    {'demand': 350, 'reserve': 21},  # t=19: 6 PM - 7 PM (Evening peak - highest)
    {'demand': 360, 'reserve': 22},  # t=20: 7 PM - 8 PM (Evening peak)
    {'demand': 340, 'reserve': 20},  # t=21: 8 PM - 9 PM (Evening peak)
    {'demand': 320, 'reserve': 19},  # t=22: 9 PM - 10 PM (Evening peak)
    {'demand': 280, 'reserve': 17},  # t=23: 10 PM - 11 PM (Late evening - declining)
    {'demand': 200, 'reserve': 12},  # t=24: 11 PM - 12 AM (Late evening)
]

# Time periods configuration - each dictionary represents one time period
# t=0: Initial state (before planning horizon)
# t=1 to t=6: Planning periods
# Renamed from time_periods to time_periods_example
time_periods_example = [
    {'demand': 0, 'reserve': 0},      # t=0: Initial state (no demand/reserve)
    {'demand': 230, 'reserve': 10},   # t=1
    {'demand': 250, 'reserve': 10},   # t=2
    {'demand': 200, 'reserve': 10},   # t=3
    {'demand': 170, 'reserve': 10},   # t=4
    {'demand': 230, 'reserve': 10},   # t=5
    {'demand': 190, 'reserve': 10}    # t=6
]

# 24-hour residential large pattern (50% larger than regular residential)
time_periods_24h_large = [
    {'demand': 0, 'reserve': 0},     # t=0: Initial state (no demand/reserve)
    {'demand': 180, 'reserve': 12},  # t=1: 12 AM - 1 AM (Night - lowest)
    {'demand': 165, 'reserve': 12},  # t=2: 1 AM - 2 AM (Night)
    {'demand': 158, 'reserve': 11},  # t=3: 2 AM - 3 AM (Night)
    {'demand': 150, 'reserve': 11},  # t=4: 3 AM - 4 AM (Night)
    {'demand': 143, 'reserve': 11},  # t=5: 4 AM - 5 AM (Night)
    {'demand': 135, 'reserve': 9},   # t=6: 5 AM - 6 AM (Night)
    {'demand': 225, 'reserve': 15},  # t=7: 6 AM - 7 AM (Early morning - rising)
    {'demand': 300, 'reserve': 18},  # t=8: 7 AM - 8 AM (Early morning)
    {'demand': 375, 'reserve': 23},  # t=9: 8 AM - 9 AM (Early morning)
    {'demand': 420, 'reserve': 26},  # t=10: 9 AM - 10 AM (Morning peak)
    {'demand': 435, 'reserve': 27},  # t=11: 10 AM - 11 AM (Morning peak)
    {'demand': 450, 'reserve': 27},  # t=12: 11 AM - 12 PM (Morning peak)
    {'demand': 420, 'reserve': 26},  # t=13: 12 PM - 1 PM (Lunch time - dip)
    {'demand': 390, 'reserve': 24},  # t=14: 1 PM - 2 PM (Lunch time)
    {'demand': 405, 'reserve': 24},  # t=15: 2 PM - 3 PM (Afternoon)
    {'demand': 420, 'reserve': 26},  # t=16: 3 PM - 4 PM (Afternoon)
    {'demand': 435, 'reserve': 26},  # t=17: 4 PM - 5 PM (Afternoon)
    {'demand': 465, 'reserve': 29},  # t=18: 5 PM - 6 PM (Afternoon)
    {'demand': 525, 'reserve': 32},  # t=19: 6 PM - 7 PM (Evening peak - highest)
    {'demand': 540, 'reserve': 33},  # t=20: 7 PM - 8 PM (Evening peak)
    {'demand': 510, 'reserve': 30},  # t=21: 8 PM - 9 PM (Evening peak)
    {'demand': 480, 'reserve': 29},  # t=22: 9 PM - 10 PM (Evening peak)
    {'demand': 420, 'reserve': 26},  # t=23: 10 PM - 11 PM (Late evening - declining)
    {'demand': 300, 'reserve': 18},  # t=24: 11 PM - 12 AM (Late evening)
]

# 24-hour residential extra large pattern (40% larger than regular residential - 1.4x)
time_periods_24h_extra_large = [
    {'demand': 0, 'reserve': 0},     # t=0: Initial state (no demand/reserve)
    {'demand': 168, 'reserve': 11},  # t=1: 12 AM - 1 AM (Night - lowest)
    {'demand': 154, 'reserve': 11},  # t=2: 1 AM - 2 AM (Night)
    {'demand': 147, 'reserve': 10},  # t=3: 2 AM - 3 AM (Night)
    {'demand': 140, 'reserve': 10},  # t=4: 3 AM - 4 AM (Night)
    {'demand': 133, 'reserve': 10},  # t=5: 4 AM - 5 AM (Night)
    {'demand': 126, 'reserve': 9},   # t=6: 5 AM - 6 AM (Night)
    {'demand': 210, 'reserve': 14},  # t=7: 6 AM - 7 AM (Early morning - rising)
    {'demand': 280, 'reserve': 17},  # t=8: 7 AM - 8 AM (Early morning)
    {'demand': 350, 'reserve': 21},  # t=9: 8 AM - 9 AM (Early morning)
    {'demand': 392, 'reserve': 24},  # t=10: 9 AM - 10 AM (Morning peak)
    {'demand': 406, 'reserve': 25},  # t=11: 10 AM - 11 AM (Morning peak)
    {'demand': 420, 'reserve': 25},  # t=12: 11 AM - 12 PM (Morning peak)
    {'demand': 392, 'reserve': 24},  # t=13: 12 PM - 1 PM (Lunch time - dip)
    {'demand': 364, 'reserve': 23},  # t=14: 1 PM - 2 PM (Lunch time)
    {'demand': 378, 'reserve': 23},  # t=15: 2 PM - 3 PM (Afternoon)
    {'demand': 392, 'reserve': 24},  # t=16: 3 PM - 4 PM (Afternoon)
    {'demand': 406, 'reserve': 24},  # t=17: 4 PM - 5 PM (Afternoon)
    {'demand': 434, 'reserve': 26},  # t=18: 5 PM - 6 PM (Afternoon)
    {'demand': 490, 'reserve': 30},  # t=19: 6 PM - 7 PM (Evening peak - highest)
    {'demand': 502, 'reserve': 31},  # t=20: 7 PM - 8 PM (Evening peak)
    {'demand': 476, 'reserve': 28},  # t=21: 8 PM - 9 PM (Evening peak)
    {'demand': 448, 'reserve': 26},  # t=22: 9 PM - 10 PM (Evening peak)
    {'demand': 392, 'reserve': 24},  # t=23: 10 PM - 11 PM (Late evening - declining)
    {'demand': 280, 'reserve': 17},  # t=24: 11 PM - 12 AM (Late evening)
]

# Weekend pattern (more relaxed, less variation)
time_periods_24h_weekend = [
    {'demand': 0, 'reserve': 0},     # t=0: Initial state (no demand/reserve)
    {'demand': 130, 'reserve': 8},   # t=1: 12 AM - 1 AM
    {'demand': 120, 'reserve': 8},   # t=2: 1 AM - 2 AM
    {'demand': 115, 'reserve': 7},   # t=3: 2 AM - 3 AM
    {'demand': 110, 'reserve': 7},   # t=4: 3 AM - 4 AM
    {'demand': 105, 'reserve': 7},   # t=5: 4 AM - 5 AM
    {'demand': 100, 'reserve': 6},   # t=6: 5 AM - 6 AM
    {'demand': 120, 'reserve': 8},   # t=7: 6 AM - 7 AM
    {'demand': 140, 'reserve': 9},   # t=8: 7 AM - 8 AM
    {'demand': 160, 'reserve': 10},  # t=9: 8 AM - 9 AM
    {'demand': 180, 'reserve': 11},  # t=10: 9 AM - 10 AM
    {'demand': 200, 'reserve': 12},  # t=11: 10 AM - 11 AM
    {'demand': 220, 'reserve': 13},  # t=12: 11 AM - 12 PM
    {'demand': 240, 'reserve': 14},  # t=13: 12 PM - 1 PM
    {'demand': 250, 'reserve': 15},  # t=14: 1 PM - 2 PM
    {'demand': 260, 'reserve': 16},  # t=15: 2 PM - 3 PM
    {'demand': 270, 'reserve': 16},  # t=16: 3 PM - 4 PM
    {'demand': 280, 'reserve': 17},  # t=17: 4 PM - 5 PM
    {'demand': 290, 'reserve': 17},  # t=18: 5 PM - 6 PM
    {'demand': 320, 'reserve': 19},  # t=19: 6 PM - 7 PM
    {'demand': 330, 'reserve': 20},  # t=20: 7 PM - 8 PM
    {'demand': 310, 'reserve': 19},  # t=21: 8 PM - 9 PM
    {'demand': 290, 'reserve': 17},  # t=22: 9 PM - 10 PM
    {'demand': 250, 'reserve': 15},  # t=23: 10 PM - 11 PM
    {'demand': 180, 'reserve': 11},  # t=24: 11 PM - 12 AM
]

# Industrial pattern (higher base demand, less variation)
time_periods_24h_industrial = [
    {'demand': 0, 'reserve': 0},     # t=0: Initial state (no demand/reserve)
    {'demand': 200, 'reserve': 12},  # t=1: 12 AM - 1 AM (Night shift)
    {'demand': 190, 'reserve': 11},  # t=2: 1 AM - 2 AM (Night shift)
    {'demand': 185, 'reserve': 11},  # t=3: 2 AM - 3 AM (Night shift)
    {'demand': 180, 'reserve': 11},  # t=4: 3 AM - 4 AM (Night shift)
    {'demand': 175, 'reserve': 10},  # t=5: 4 AM - 5 AM (Night shift)
    {'demand': 170, 'reserve': 10},  # t=6: 5 AM - 6 AM (Night shift)
    {'demand': 250, 'reserve': 15},  # t=7: 6 AM - 7 AM (Shift change)
    {'demand': 350, 'reserve': 21},  # t=8: 7 AM - 8 AM (Day shift starts)
    {'demand': 400, 'reserve': 24},  # t=9: 8 AM - 9 AM (Full production)
    {'demand': 420, 'reserve': 25},  # t=10: 9 AM - 10 AM (Full production)
    {'demand': 430, 'reserve': 26},  # t=11: 10 AM - 11 AM (Full production)
    {'demand': 440, 'reserve': 26},  # t=12: 11 AM - 12 PM (Full production)
    {'demand': 420, 'reserve': 25},  # t=13: 12 PM - 1 PM (Lunch break)
    {'demand': 400, 'reserve': 24},  # t=14: 1 PM - 2 PM (Lunch break)
    {'demand': 430, 'reserve': 26},  # t=15: 2 PM - 3 PM (Full production)
    {'demand': 440, 'reserve': 26},  # t=16: 3 PM - 4 PM (Full production)
    {'demand': 450, 'reserve': 27},  # t=17: 4 PM - 5 PM (Full production)
    {'demand': 460, 'reserve': 28},  # t=18: 5 PM - 6 PM (Full production)
    {'demand': 400, 'reserve': 24},  # t=19: 6 PM - 7 PM (Shift change)
    {'demand': 350, 'reserve': 21},  # t=20: 7 PM - 8 PM (Evening shift)
    {'demand': 320, 'reserve': 19},  # t=21: 8 PM - 9 PM (Evening shift)
    {'demand': 300, 'reserve': 18},  # t=22: 9 PM - 10 PM (Evening shift)
    {'demand': 250, 'reserve': 15},  # t=23: 10 PM - 11 PM (Evening shift)
    {'demand': 220, 'reserve': 13},  # t=24: 11 PM - 12 AM (Evening shift)
]
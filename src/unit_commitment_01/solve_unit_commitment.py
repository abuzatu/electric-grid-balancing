"""
Python module to solve the unit commitment problem using OR-Tools and SCIP solver.

This module implements a comprehensive unit commitment optimization model that determines
the optimal schedule for power generation units to meet demand while minimizing total costs.

SOLVER FRAMEWORK:
- OR-Tools: Google's open-source optimization library providing Python interface
- SCIP: The specific solver engine (Solving Constraint Integer Programs)
- Relationship: OR-Tools provides modeling capabilities, SCIP performs optimization

OR-TOOLS ROLE:
- Variable creation (BoolVar, NumVar)
- Objective functions (solver.Minimize())
- Constraint building (solver.Add())
- Multiple solver backends support

SCIP SOLVER ROLE:
- Mixed-Integer Linear Programming (MILP) solver
- Developed by Zuse Institute Berlin (ZIB)
- One of the fastest open-source MILP solvers
- Advanced algorithms: Branch-and-Bound, Cutting Planes, Heuristics

ALTERNATIVE SOLVERS AVAILABLE:
- GLOP: Google's Linear Optimization (LP only)
- GLPK: GNU Linear Programming Kit
- CBC: COIN-OR Branch and Cut (MILP)
- GUROBI/CPLEX: Commercial solvers (require licenses)

PROBLEM CHARACTERISTICS:
- Type: Mixed-Integer Programming (MIP)
- Variables: Binary (commitment decisions) + Continuous (power output)
- Objective: Linear cost minimization
- Constraints: Linear inequalities and equalities
- Complexity: NP-hard optimization problem

VARIABLES:
- u_{j,t}: Binary commitment status (ON/OFF)
- su_{j,t}: Binary startup indicator
- sd_{j,t}: Binary shutdown indicator  
- p_{j,t}: Continuous power output (MW)
- p_bar_{j,t}: Continuous maximum available power (MW)

CONSTRAINTS:
- Power balance: sum_j p_{j,t} = D_t
- Reserve capacity: sum_j p_bar_{j,t} >= D_t + R_t
- Generation limits: P_min <= p_{j,t} <= p_bar_{j,t} <= P_max
- Ramp constraints: Academic formulas (6) and (7)
- Minimum up/down time: Logical constraints
- Startup/shutdown logic: Consistency constraints
"""

# python modules

# our modules
# our modules
import sys
sys.path.append('../../src')
import unit_commitment_01.configs as configs
from ortools.linear_solver import pywraplp

class SolveUnitCommitment:
    """
    Class that solves unit commitment optimisation.

    Variables:
        - u_{j,t} (binary): 1 if unit j is ON at time t, 0 otherwise (commitment variable)
        - su_{j,t} (binary): 1 if unit j starts up at time t, 0 otherwise (startup indicator)
        - sd_{j,t} (binary): 1 if unit j shuts down at time t, 0 otherwise (shutdown indicator)
        - p_{j,t} (continuous): Power produced by unit j at time t (MW)

    Generator configuration parameters (from config):
        - name: Name of the unit (for identification)
        - P_min: Minimum output of unit j (MW)
        - P_max: Maximum output of unit j (MW)
        - cU: Fixed cost for unit j per period ($/h)
        - c: Variable cost for unit j per MWh ($/MWh)
        - SU: Startup cost for unit j ($)
        - SD: Shutdown cost for unit j ($)
        - RU: Ramp up limit for unit j (MW/h)
        - RD: Ramp down limit for unit j (MW/h)
        - TU: Minimum up time for unit j (hours)
        - TD: Minimum down time for unit j (hours)
    """
    def __init__(
        self,
        enable_power_balance=True,
        enable_reserve_capacity=True,
        enable_logical_consistency=True,
        enable_generation_limits=True,
        enable_ramp_up=True,
        enable_ramp_down=True,
        enable_min_up_time=True,
        enable_min_down_time=True,
        time_periods=None,
        units=None,
    ) -> None:
        """Initialize with configurable constraints and optional custom configuration."""
        # Use custom configs if provided, otherwise use default configs
        if time_periods is not None:
            self.configs_time_periods = time_periods
        else:
            self.configs_time_periods = configs.time_periods_example
            
        if units is not None:
            self.configs_units = units
        else:
            self.configs_units = configs.units_example
            
        self.num_units = len(self.configs_units)
        self.num_periods = len(self.configs_time_periods)
        
        # Constraint configuration
        self.enable_power_balance = enable_power_balance
        self.enable_reserve_capacity = enable_reserve_capacity
        self.enable_logical_consistency = enable_logical_consistency
        self.enable_generation_limits = enable_generation_limits
        self.enable_ramp_up = enable_ramp_up
        self.enable_ramp_down = enable_ramp_down
        self.enable_min_up_time = enable_min_up_time
        self.enable_min_down_time = enable_min_down_time
        
        # Setup solver and create decision variables
        self.setup_solver_and_variables()

    def setup_solver_and_variables(self):
        """
        Initialize the SCIP solver and create all decision variables for the unit commitment problem.
        
        Solver Type: SCIP (Solving Constraint Integer Programs)
        - Mixed-Integer Linear Programming (MILP) solver
        - Developed by Zuse Institute Berlin (ZIB)
        - One of the fastest open-source MILP solvers
        - Excellent for problems with both binary and continuous variables
        
        Variable Types Created:
        1. Binary Variables (BoolVar):
           - u_{j,t}: Commitment status (1 if unit j is ON at time t, 0 otherwise)
           - su_{j,t}: Startup indicator (1 if unit j starts up at time t, 0 otherwise)
           - sd_{j,t}: Shutdown indicator (1 if unit j shuts down at time t, 0 otherwise)
        
        2. Continuous Variables (NumVar):
           - p_{j,t}: Power output of unit j at time t (MW) [0, P_max_j]
           - p_bar_{j,t}: Maximum available power of unit j at time t (MW) [0, P_max_j]
        
        Time Indexing:
        - t=0: Initial state (before planning horizon) - variables created but fixed to initial values
        - t=1,2,...,T: Planning periods (optimization variables)
        
        Problem Characteristics:
        - Objective: Linear (minimize total operational cost)
        - Constraints: Linear inequalities and equalities
        - Variables: Mixed (binary + continuous)
        - Complexity: NP-hard optimization problem
        
        SCIP Algorithm Features:
        - Branch-and-Bound for integer variables
        - Cutting Planes to strengthen formulation
        - Heuristics for quick good solutions
        - Preprocessing to reduce problem size
        """
        # OR-Tools solver
        self.solver = pywraplp.Solver.CreateSolver('SCIP')
        
        # Decision variables
        # Three binary variables
        self.u = {}  # Commitment (on/off)
        self.su = {} # Startup
        self.sd = {} # Shutdown
        # Two continuous variables
        self.p = {}  # Power output
        self.p_bar = {}  # Maximum available power in the time interval t
        
        # Create variables for t=0,1,2,...,T (including initial state)
        for j in range(self.num_units):
            for t in range(self.num_periods):
                self.u[j, t] = self.solver.BoolVar(f'u_{j}_{t}')
                self.su[j, t] = self.solver.BoolVar(f'su_{j}_{t}')
                self.sd[j, t] = self.solver.BoolVar(f'sd_{j}_{t}')
                self.p[j, t] = self.solver.NumVar(0, self.configs_units[j]['P_max'], f'p_{j}_{t}')
                self.p_bar[j, t] = self.solver.NumVar(0, self.configs_units[j]['P_max'], f'p_bar_{j}_{t}')
        
        # Fix initial state constraints for t=0
        self.set_initial_state_constraints()

    def set_initial_state_constraints(self):
        """
        Set the initial state constraints for t=0 based on the configuration.
        
        These constraints fix the values of variables at t=0 to match the initial
        state specified in the unit configuration. This ensures the optimization
        starts from a realistic initial condition.
        
        Variables Fixed:
        - u_{j,0}: Initial commitment status (ON/OFF)
        - su_{j,0}: Initial startup status (usually 0)
        - sd_{j,0}: Initial shutdown status (usually 0)  
        - p_{j,0}: Initial power output (MW)
        """
        for j in range(self.num_units):
            self.solver.Add(self.u[j, 0] == self.configs_units[j]['u0'])
            self.solver.Add(self.su[j, 0] == self.configs_units[j]['su0'])
            self.solver.Add(self.sd[j, 0] == self.configs_units[j]['sd0'])
            self.solver.Add(self.p[j, 0] == self.configs_units[j]['p0'])

    def fit(self) -> None:
        """Do the action with configurable constraints."""
        print("Solving the unit commitment.")
        print(self.configs_time_periods)
        self.add_objective()
        
        if self.enable_power_balance:
            print("Adding power balance constraint (demand satisfaction).")
            self.add_power_balance_constraint()
        
        if self.enable_reserve_capacity:
            print("Adding reserve capacity constraint (demand + reserve satisfaction).")
            self.add_reserve_capacity_constraint()
        
        if self.enable_logical_consistency:
            print("Adding logical consistency constraint.")
            self.add_logical_consistency_constraint()
        
        if self.enable_generation_limits:
            print("Adding generation and ramping limits constraints (professor's formulation, p_bar on LHS).")
            self.add_generation_limits_constraint()
        
        if self.enable_ramp_up:
            print("Adding ramp up constraint (academic formula with RU and SU).")
            self.add_ramp_up_constraint()
        
        if self.enable_ramp_down:
            print("Adding ramp down constraint (academic formula with RD and SD).")
            self.add_ramp_down_constraint()
        
        if self.enable_min_up_time:
            print("Adding minimum up time constraint.")
            self.add_min_up_time_constraint()
        
        if self.enable_min_down_time:
            print("Adding minimum down time constraint.")
            self.add_min_down_time_constraint()

    def add_objective(self):
        """
        Add the objective function to minimize total system cost:
            Minimize sum_{j,t=1}^T [cU_j * u_{j,t} + c_j * p_{j,t} + SU_cost_j * su_{j,t} + SD_cost_j * sd_{j,t}]
        Where:
            cU_j: Fixed cost for unit j per period
            c_j: Variable cost for unit j per MWh
            SU_cost_j: Startup cost for unit j
            SD_cost_j: Shutdown cost for unit j
            u_{j,t}: 1 if unit j is ON at time t, 0 otherwise
            p_{j,t}: Power produced by unit j at time t
            su_{j,t}: 1 if unit j starts up at time t, 0 otherwise
            sd_{j,t}: 1 if unit j shuts down at time t, 0 otherwise
        Note: t=0 is excluded from cost calculation as it represents initial state.
        """
        print("Adding objective function (minimize total cost).")
        objective = self.solver.Sum(
            self.configs_units[j]['cU'] * self.u[j, t] +
            self.configs_units[j]['c'] * self.p[j, t] +
            self.configs_units[j]['SU_cost'] * self.su[j, t] +
            self.configs_units[j]['SD_cost'] * self.sd[j, t]
            for j in range(self.num_units) for t in range(1, self.num_periods)
        )
        self.solver.Minimize(objective)

    def add_power_balance_constraint(self):
        """
        Add the power balance constraint:
            For all t: sum_j p_{j,t} = D_t
        Where:
            p_{j,t}: Power produced by unit j at time t
            D_t: Demand at time t
        """
        print("Adding power balance constraint (demand satisfaction).")
        for t in range(1, self.num_periods):
            self.solver.Add(
                self.solver.Sum(self.p[j, t] for j in range(self.num_units)) == self.configs_time_periods[t]['demand']
            )

    def add_reserve_capacity_constraint(self):
        """
        Add the reserve capacity constraint:
            For all t: sum_j p_bar_{j,t} >= D_t + R_t
        Where:
            p_bar_{j,t}: Maximum available power for unit j at time t
            D_t: Demand at time t
            R_t: Reserve requirement at time t
        """
        print("Adding reserve capacity constraint (demand + reserve satisfaction).")
        for t in range(1, self.num_periods):
            self.solver.Add(
                self.solver.Sum(self.p_bar[j, t] for j in range(self.num_units)) >= 
                self.configs_time_periods[t]['demand'] + self.configs_time_periods[t]['reserve']
            )

    def add_logical_consistency_constraint(self):
        """
        Add logical consistency constraint following professor's formula (5):
            For all j, t: v_{j, t-1} - v_{j, t} + y_{j, t} - z_{j, t} = 0
        Where:
            v_{j, t}: 1 if unit j is ON at time t, 0 otherwise
            y_{j, t}: 1 if unit j starts up at time t, 0 otherwise
            z_{j, t}: 1 if unit j shuts down at time t, 0 otherwise
        """
        print("Adding logical consistency constraint.")
        for j in range(self.num_units):
            for t in range(1, self.num_periods):
                self.solver.Add(
                    self.u[j, t-1] - self.u[j, t] + self.su[j, t] - self.sd[j, t] == 0
                )

    def add_generation_limits_constraint(self):
        """
        Add generation and ramping limits for each unit, following the professor's equations:
            (10) P_min_j * u_{j,t} <= p_{j,t} <= p_bar_{j,t} <= P_max_j * u_{j,t}
            (11) p_bar_{j,t} <= p_{j,t-1} + RU_j * u_{j,t-1} + SU_j * su_{j,t}
            (12) p_bar_{j,t} <= P_max_j * u_{j,t} - P_max_j * sd_{j,t+1} + SD_j * sd_{j,t+1}
        """
        print("Adding generation and ramping limits constraints (professor's formulation, p_bar on LHS).")
        for j in range(self.num_units):
            for t in range(self.num_periods):
                # (10) Standard generation limits
                self.solver.Add(self.p[j, t] >= self.configs_units[j]['P_min'] * self.u[j, t])
                self.solver.Add(self.p[j, t] <= self.p_bar[j, t])
                self.solver.Add(self.p_bar[j, t] <= self.configs_units[j]['P_max'] * self.u[j, t])

            # (11) Ramp-up and startup (p_bar on LHS) - for t >= 1
            for t in range(1, self.num_periods):
                self.solver.Add(
                    self.p_bar[j, t] <= self.p[j, t-1]
                    + self.configs_units[j]['RU'] * self.u[j, t-1]
                    + self.configs_units[j]['SU'] * self.su[j, t]
                )

            # (12) Shutdown ramp (for t < T, p_bar on LHS) - for t < T
            for t in range(self.num_periods - 1):
                self.solver.Add(
                    self.p_bar[j, t] <= self.configs_units[j]['P_max'] * self.u[j, t]
                    - self.configs_units[j]['P_max'] * self.sd[j, t+1]
                    + self.configs_units[j]['SD'] * self.sd[j, t+1]
                )

    def add_ramp_up_constraint(self):
        """
        Add ramp up constraint following academic formula (6):
            For all j, t > 0: p_{j,t} - p_{j,t-1} <= RU_j * u_{j,t-1} + SU_j * su_{j,t}
        Where:
            p_{j,t}: Power produced by unit j at time t
            p_{j,t-1}: Power produced by unit j at time t-1
            u_{j,t-1}: 1 if unit j is ON at time t-1, 0 otherwise
            su_{j,t}: 1 if unit j starts up at time t, 0 otherwise
            RU_j: Ramp up limit for unit j (MW/h) - applies when unit is already ON
            SU_j: Startup ramp limit for unit j (MW) - applies when unit starts up
        """
        print("Adding ramp up constraint (academic formula with RU and SU).")
        for j in range(self.num_units):
            for t in range(1, self.num_periods):
                self.solver.Add(
                    self.p[j, t] - self.p[j, t-1] <= 
                    self.configs_units[j]['RU'] * self.u[j, t-1] + 
                    self.configs_units[j]['SU'] * self.su[j, t]
                )

    def add_ramp_down_constraint(self):
        """
        Add ramp down constraint following academic formula (7):
            For all j, t > 0: p_{j,t-1} - p_{j,t} <= RD_j * u_{j,t} + SD_j * sd_{j,t}
        Where:
            p_{j,t}: Power produced by unit j at time t
            p_{j,t-1}: Power produced by unit j at time t-1
            u_{j,t}: 1 if unit j is ON at time t, 0 otherwise
            sd_{j,t}: 1 if unit j shuts down at time t, 0 otherwise
            RD_j: Ramp down limit for unit j (MW/h) - applies when unit is ON
            SD_j: Shutdown ramp limit for unit j (MW) - applies when unit shuts down
        """
        print("Adding ramp down constraint (academic formula with RD and SD).")
        for j in range(self.num_units):
            for t in range(1, self.num_periods):
                self.solver.Add(
                    self.p[j, t-1] - self.p[j, t] <= 
                    self.configs_units[j]['RD'] * self.u[j, t] + 
                    self.configs_units[j]['SD'] * self.sd[j, t]
                )

    def add_min_up_time_constraint(self):
        """
        Add minimum up time constraint following the mathematical formulation.
        
        MATHEMATICAL FORMULATION:
        The minimum uptime requirement is expressed as:
            sum_{k=t-TU_j+1}^{t} y_j(k) <= v_j(t)  ∀t ∈ [L_j+1, ..., |T|]  ∀j ∈ J
        
        WHERE:
        - TU_j: Minimum up time for unit j (time units)
        - U0_j: Number of time periods that unit j is required to be ON at the start 
                of the planning horizon
        - L_j = min(|T|, U0_j)
        - y_j(t): 1 if unit j starts up at time t, 0 otherwise (our su[j, t])
        - v_j(t): 1 if unit j is ON at time t, 0 otherwise (our u[j, t])
        - |T|: Number of planning periods (excluding t=0)
        
        INTERPRETATION:
        These constraints require knowledge of the operational history of unit j in the
        TU_j-1 time periods before t=1. For example, if TU_j = 3 then:
        ▶ If unit j is OFF at time t, then v_j(t) = 0, and therefore y_j(t) = 0, 
          y_j(t-1) = 0, and y_j(t-2) = 0 must hold.
        ▶ Conversely, if any one of y_j(t), y_j(t-1), or y_j(t-2) equals 1, then
          v_j(t) = 1 must hold.
        
        IMPLEMENTATION:
        1. Enforce initial required ON time: If U0_j > 0, force u[j, t] = 1 for t = 1 to U0_j
        2. Apply rolling constraint: For each t in [L_j+1, ..., num_periods-1], ensure that
           if any startup occurred in the last TU_j periods, the unit must be ON at time t
        """
        print("Adding minimum up time constraint (mathematical formulation).")
        for j in range(self.num_units):
            TU = self.configs_units[j]['TU']
            U0 = self.configs_units[j]['U0']
            L_j = min(self.num_periods - 1, U0)
            
            # Enforce initial required ON time if U0 > 0
            if U0 > 0:
                for t in range(1, U0 + 1):
                    if t < self.num_periods:
                        self.solver.Add(self.u[j, t] == 1)
            
            # Professor's rolling constraint: sum_{k=t-TU_j+1}^{t} y_j(k) <= v_j(t)
            # For all t in [L_j+1, ..., num_periods-1]
            for t in range(L_j + 1, self.num_periods):
                # Calculate the sum of startup variables from t-TU+1 to t
                startup_sum = self.solver.Sum(
                    self.su[j, k] for k in range(max(1, t-TU+1), t+1)
                )
                # Constraint: startup_sum <= u[j, t]
                self.solver.Add(startup_sum <= self.u[j, t])

    def add_min_down_time_constraint(self):
        """
        Add minimum down time constraint following the mathematical formulation.
        
        MATHEMATICAL FORMULATION:
        The minimum downtime requirement is expressed as:
            sum_{k=t-TD_j+1}^{t} z_j(k) <= 1 - v_j(t)  ∀t ∈ [L_j+1, ..., |T|]  ∀j ∈ J
        
        WHERE:
        - TD_j: Minimum down time for unit j (time units)
        - D0_j: Number of time periods that unit j is required to be OFF at the start 
                of the planning horizon
        - L_j = min(|T|, D0_j)
        - z_j(t): 1 if unit j shuts down at time t, 0 otherwise (our sd[j, t])
        - v_j(t): 1 if unit j is ON at time t, 0 otherwise (our u[j, t])
        - |T|: Number of planning periods (excluding t=0)
        
        INTERPRETATION:
        These constraints ensure that once a unit is shut down, it must remain OFF for at least
        TD_j time periods. For example, if TD_j = 2 then:
        ▶ If unit j is ON at time t, then v_j(t) = 1, and therefore z_j(t) = 0 and 
          z_j(t-1) = 0 must hold (unit cannot be shutting down).
        ▶ Conversely, if any one of z_j(t) or z_j(t-1) equals 1, then v_j(t) = 0 must hold
          (unit must be OFF).
        
        IMPLEMENTATION:
        1. Enforce initial required OFF time: If D0_j > 0, force u[j, t] = 0 for t = 1 to D0_j
        2. Apply rolling constraint: For each t in [L_j+1, ..., num_periods-1], ensure that
           if any shutdown occurred in the last TD_j periods, the unit must be OFF at time t
        """
        print("Adding minimum down time constraint (mathematical formulation).")
        for j in range(self.num_units):
            TD = self.configs_units[j]['TD']
            D0 = self.configs_units[j]['D0']
            L_j = min(self.num_periods - 1, D0)
            
            # Enforce initial required OFF time if D0 > 0
            if D0 > 0:
                for t in range(1, D0 + 1):
                    if t < self.num_periods:
                        self.solver.Add(self.u[j, t] == 0)
            
            # Professor's rolling constraint: sum_{k=t-TD_j+1}^{t} z_j(k) <= 1 - v_j(t)
            # For all t in [L_j+1, ..., num_periods-1]
            for t in range(L_j + 1, self.num_periods):
                # Calculate the sum of shutdown variables from t-TD+1 to t
                shutdown_sum = self.solver.Sum(
                    self.sd[j, k] for k in range(max(1, t-TD+1), t+1)
                )
                # Constraint: shutdown_sum <= 1 - v_j(t)
                self.solver.Add(shutdown_sum <= 1 - self.u[j, t])




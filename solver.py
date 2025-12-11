from ortools.sat.python import cp_model
from models import Employee, ShiftRequest, TimeBlock, Day, ScheduleOutput
import pandas as pd
import numpy as np

# UPDATE: Added role_constraints parameter (default empty list)
def solve_schedule(employees: list[Employee], demands: list[ShiftRequest], role_constraints: list = []) -> ScheduleOutput:
    model = cp_model.CpModel()
    
    # 1. Weights
    WEIGHT_UNASSIGNED = 1000
    WEIGHT_ROLE_MISSING = 2000  # NEW: High penalty for missing roles
    WEIGHT_CLOPEN = 500
    WEIGHT_OVERTIME = 50
    
    BLOCK_HOURS = 4
    days_list = [d.value for d in Day]
    blocks_list = [b.value for b in TimeBlock]
    
    # 2. Variables
    shifts = {}
    for emp in employees:
        for d in days_list:
            for b in blocks_list:
                shifts[(emp.id, d, b)] = model.NewBoolVar(f'shift_{emp.id}_{d}_{b}')

    # 3. Hard Constraints (Availability)
    for emp in employees:
        for d in days_list:
            for b in blocks_list:
                slot_key = f"{d}-{b}"
                if slot_key in emp.unavailable_slots:
                    model.Add(shifts[(emp.id, d, b)] == 0)

    # 4. Soft Constraints
    penalty_vars = []

    # A. Coverage
    for req in demands:
        d, b, needed = req.day.value, req.block.value, req.required_staff
        working_staff = sum(shifts[(e.id, d, b)] for e in employees)
        shortage = model.NewIntVar(0, needed, f'shortage_{d}_{b}')
        model.Add(working_staff + shortage >= needed)
        penalty_vars.append(shortage * WEIGHT_UNASSIGNED)

    # B. NEW: Role Requirements Logic
    for rc in role_constraints:
        target_role = rc.role
        min_needed = rc.min_count
        
        # Identify employees who have this role
        eligible_emps = [e for e in employees if e.role == target_role]
        
        if eligible_emps:
            for d in days_list:
                for b in blocks_list:
                    # Sum of working staff with this role
                    role_force = sum(shifts[(e.id, d, b)] for e in eligible_emps)
                    
                    role_shortage = model.NewIntVar(0, min_needed, f'role_short_{target_role}_{d}_{b}')
                    model.Add(role_force + role_shortage >= min_needed)
                    penalty_vars.append(role_shortage * WEIGHT_ROLE_MISSING)

    # C. Prevent Clopens
    for emp in employees:
        for i in range(len(days_list) - 1):
            today = days_list[i]
            tomorrow = days_list[i+1]
            dinner_var = shifts[(emp.id, today, "Dinner")]
            morning_var = shifts[(emp.id, tomorrow, "Morning")]
            
            is_clopen = model.NewBoolVar(f'clopen_{emp.id}_{today}')
            model.AddBoolAnd([dinner_var, morning_var]).OnlyEnforceIf(is_clopen)
            model.AddBoolOr([dinner_var.Not(), morning_var.Not()]).OnlyEnforceIf(is_clopen.Not())
            penalty_vars.append(is_clopen * WEIGHT_CLOPEN)

    # D. Max Hours
    for emp in employees:
        total_blocks = sum(shifts[(emp.id, d, b)] for d in days_list for b in blocks_list)
        total_hours = total_blocks * BLOCK_HOURS
        overtime = model.NewIntVar(0, 100, f'over_{emp.id}')
        model.Add(total_hours <= emp.max_hours + overtime)
        penalty_vars.append(overtime * WEIGHT_OVERTIME)

    # 5. Solve
    model.Minimize(sum(penalty_vars))
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # 6. Parse Results
    assignments = []
    emp_hours_solved = {}

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        # Calculate hours ONLY after solve
        for emp in employees:
            total_blocks = sum(solver.Value(shifts[(emp.id, d, b)]) for d in days_list for b in blocks_list)
            emp_hours_solved[emp.id] = total_blocks * BLOCK_HOURS

        for d in days_list:
            for b in blocks_list:
                assigned_names = []
                for emp in employees:
                    if solver.Value(shifts[(emp.id, d, b)]) == 1:
                        assigned_names.append(emp.name)
                
                # Format names with role hints
                staff_display = []
                for name in assigned_names:
                    role = next((e.role for e in employees if e.name == name), "")
                    short_role = f" ({role[:3]})" if role else ""
                    staff_display.append(f"{name}{short_role}")

                assignments.append({
                    "day": d, 
                    "block": b, 
                    "staff": assigned_names,
                    "staff_str": ", ".join(staff_display)
                })
        
        hours_values = list(emp_hours_solved.values())
        fairness_score = float(np.std(hours_values)) if hours_values else 0.0
        
        return ScheduleOutput(
            assignments=assignments,
            metrics={
                "fairness_std_dev": fairness_score,
                "total_penalty": solver.ObjectiveValue()
            },
            formatted_text=generate_whatsapp_export(assignments)
        )
    else:
        return ScheduleOutput(assignments=[], metrics={"total_penalty": 0.0, "fairness_std_dev": 0.0}, formatted_text="Unsolvable Error")

def generate_whatsapp_export(assignments):
    df = pd.DataFrame(assignments)
    if df.empty: return "No schedule generated."
    
    text = "*🍽️ Weekly Roster Draft*\n\n"
    for day in df['day'].unique():
        text += f"📅 *{day}*\n"
        day_data = df[df['day'] == day]
        for _, row in day_data.iterrows():
            icon = "☀️" if row['block'] == "Morning" else "🍔" if row['block'] == "Lunch" else "🌙"
            text += f"{icon} {row['block']}: {row['staff_str']}\n"
        text += "\n"
    return text
        
    text += "_Generated by ShiftHero AI_"
    return text
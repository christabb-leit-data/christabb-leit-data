import os, json, argparse, csv
from typing import List, Dict, Any
import re


def generate_subcomponent_row(subcomp: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a Subcomponent page row."""
    return {
        'Page Title': subcomp['subcomponent_title'],
        'Parent Page': subcomp['component_title'],
        'Page Type': 'Subcomponent',
        'Labels': f"blueprint;subcomponent;{subcomp['component_pattern'].split(' ')[0]}",
        'Description / Notes': f"Implementation subcomponent for {subcomp['component_pattern']}",
        'Complexity': '',
        'Mode Applicability': '',
        'Validation / Cleanup Flag': '',
        'Code / Ref': subcomp['subcomponent_code']
    }


def generate_option_row(subcomp: Dict[str, Any], option_letter: str, option_name: str) -> Dict[str, Any]:
    """Generate an Option page row."""
    option_code = f"{subcomp['subcomponent_code']}.{option_letter}"
    return {
        'Page Title': f"{option_code} – {option_name}",
        'Parent Page': subcomp['subcomponent_title'],
        'Page Type': 'Option',
        'Labels': f"blueprint;option;{subcomp['component_pattern'].split(' ')[0]}",
        'Description / Notes': f"Implementation option for {subcomp['subcomponent_title']}",
        'Complexity': 'Medium',  # Default, can be customized
        'Mode Applicability': 'MVP,Production,Enterprise',
        'Validation / Cleanup Flag': 'Pending',
        'Code / Ref': option_code
    }


def generate_tasks_row(option_code: str, parent_title: str) -> Dict[str, Any]:
    """Generate a Tasks page row."""
    return {
        'Page Title': f"Tasks – {option_code}",
        'Parent Page': parent_title,
        'Page Type': 'Tasks',
        'Labels': f"blueprint;tasks;{option_code.split('.')[0]}",
        'Description / Notes': f"Task breakdown for {option_code}",
        'Complexity': '',
        'Mode Applicability': '',
        'Validation / Cleanup Flag': '',
        'Code / Ref': option_code
    }


def generate_options_csv(plan_rows: List[Dict[str, Any]], out_dir: str):
    """Generate Blueprint_Options_With_Refs.csv from plan rows."""
    options = [row for row in plan_rows if row.get('Page Type') == 'Option']
    
    options_csv = []
    for option in options:
        options_csv.append({
            'OptionRef': option['Code / Ref'],
            'OptionTitle': option['Page Title'],
            'ParentSubcomponent': option['Parent Page'],
            'Complexity': option.get('Complexity', 'Medium'),
            'ModeApplicability': option.get('Mode Applicability', 'MVP,Production,Enterprise'),
            'ValidationFlag': option.get('Validation / Cleanup Flag', 'Pending'),
            'Description': option.get('Description / Notes', '')
        })
    
    options_path = os.path.join(out_dir, 'Blueprint_Options_With_Refs.csv')
    with open(options_path, 'w', newline='', encoding='utf-8') as f:
        if options_csv:
            writer = csv.DictWriter(f, fieldnames=options_csv[0].keys())
            writer.writeheader()
            writer.writerows(options_csv)
    
    print(f"Generated {len(options_csv)} options -> {options_path}")


def generate_tasks_csv(plan_rows: List[Dict[str, Any]], out_dir: str):
    """Generate Blueprint_Tasks_Mapped_To_OptionRefs.csv from plan rows."""
    tasks = [row for row in plan_rows if row.get('Page Type') == 'Tasks']
    
    tasks_csv = []
    for task in tasks:
        option_ref = task['Code / Ref']
        # Generate sample tasks for each option
        sample_tasks = [
            {
                'OptionRef': option_ref,
                'Task': f'Setup {option_ref} infrastructure',
                'Role': 'DevOps',
                'Complexity': 'Medium',
                'MVP': 'Yes',
                'Production': 'Yes', 
                'Enterprise': 'Yes',
                'Description': f'Initial setup and configuration for {option_ref}'
            },
            {
                'OptionRef': option_ref,
                'Task': f'Implement {option_ref} core functionality',
                'Role': 'Developer',
                'Complexity': 'High',
                'MVP': 'Yes',
                'Production': 'Yes',
                'Enterprise': 'Yes', 
                'Description': f'Core implementation of {option_ref} features'
            },
            {
                'OptionRef': option_ref,
                'Task': f'Test {option_ref} implementation',
                'Role': 'QA',
                'Complexity': 'Medium',
                'MVP': 'Yes',
                'Production': 'Yes',
                'Enterprise': 'Yes',
                'Description': f'Comprehensive testing of {option_ref}'
            },
            {
                'OptionRef': option_ref,
                'Task': f'Deploy {option_ref} to production',
                'Role': 'DevOps',
                'Complexity': 'High',
                'MVP': 'No',
                'Production': 'Yes',
                'Enterprise': 'Yes',
                'Description': f'Production deployment of {option_ref}'
            },
            {
                'OptionRef': option_ref,
                'Task': f'Monitor and optimize {option_ref}',
                'Role': 'Operations',
                'Complexity': 'Low',
                'MVP': 'No',
                'Production': 'No',
                'Enterprise': 'Yes',
                'Description': f'Ongoing monitoring and optimization of {option_ref}'
            }
        ]
        tasks_csv.extend(sample_tasks)
    
    tasks_path = os.path.join(out_dir, 'Blueprint_Tasks_Mapped_To_OptionRefs.csv')
    with open(tasks_path, 'w', newline='', encoding='utf-8') as f:
        if tasks_csv:
            writer = csv.DictWriter(f, fieldnames=tasks_csv[0].keys())
            writer.writeheader()
            writer.writerows(tasks_csv)
    
    print(f"Generated {len(tasks_csv)} tasks -> {tasks_path}")


def main():
    ap = argparse.ArgumentParser(description="Generate Confluence page creation plan and CSV files")
    ap.add_argument('--discovered', required=True, 
                   help='JSON file with discovered subcomponents from discover_subcomponents.py')
    ap.add_argument('--out-dir', default='data',
                   help='Output directory for generated files')
    ap.add_argument('--options-per-subcomponent', type=int, default=3,
                   help='Number of options to generate per subcomponent')
    args = ap.parse_args()

    # Load discovered subcomponents
    with open(args.discovered) as f:
        subcomponents = json.load(f)
    
    if not subcomponents:
        print("No subcomponents found in discovered file")
        return
    
    print(f"Processing {len(subcomponents)} discovered subcomponents...")
    
    # Generate plan rows
    plan_rows = []
    
    for subcomp in subcomponents:
        # Add subcomponent row
        plan_rows.append(generate_subcomponent_row(subcomp))
        
        # Generate options for this subcomponent
        for i in range(args.options_per_subcomponent):
            option_letter = chr(ord('A') + i)
            option_name = f"Option {option_letter} Implementation"
            
            option_row = generate_option_row(subcomp, option_letter, option_name)
            plan_rows.append(option_row)
            
            # Add corresponding tasks row
            tasks_row = generate_tasks_row(option_row['Code / Ref'], option_row['Page Title'])
            plan_rows.append(tasks_row)
    
    # Sort by component and page type
    order_map = {'Subcomponent': 0, 'Option': 1, 'Tasks': 2}
    plan_rows.sort(key=lambda r: (
        r['Parent Page'], 
        order_map.get(r.get('Page Type'), 99),
        r['Page Title']
    ))
    
    # Write plan JSON
    plan_path = os.path.join(args.out_dir, 'Confluence_Page_Creation_Plan.json')
    os.makedirs(args.out_dir, exist_ok=True)
    with open(plan_path, 'w', encoding='utf-8') as f:
        json.dump(plan_rows, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {len(plan_rows)} plan rows -> {plan_path}")
    
    # Write plan CSV
    plan_csv_path = os.path.join(args.out_dir, 'Confluence_Page_Creation_Plan.csv')
    with open(plan_csv_path, 'w', newline='', encoding='utf-8') as f:
        if plan_rows:
            writer = csv.DictWriter(f, fieldnames=plan_rows[0].keys())
            writer.writeheader()
            writer.writerows(plan_rows)
    
    print(f"Generated plan CSV -> {plan_csv_path}")
    
    # Generate supporting CSV files
    generate_options_csv(plan_rows, args.out_dir)
    generate_tasks_csv(plan_rows, args.out_dir)
    
    # Print summary
    counts = {}
    for row in plan_rows:
        page_type = row.get('Page Type', 'Unknown')
        counts[page_type] = counts.get(page_type, 0) + 1
    
    print("\nSummary:")
    for page_type, count in counts.items():
        print(f"  {page_type}: {count}")


if __name__ == '__main__':
    main()
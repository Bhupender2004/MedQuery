"""
MedQuery Drug Interaction Service Test Script

Executes validation queries on standard drug combinations (Paracetamol + Ibuprofen,
Warfarin + Aspirin, Metformin + Alcohol) and formats output.
"""

from services.drug_interaction_service import DrugInteractionService

def execute_clinical_tests():
    """
    Submits standard drug interaction test cases to the checking service.
    """
    # Sample combinations to test (including safe/no interaction pairs)
    test_cases = [
        ("Paracetamol", "Ibuprofen"),
        ("Warfarin", "Aspirin"),
        ("Metformin", "Alcohol"),
        ("Amoxicillin", "Azithromycin")  # Unrelated safe combination
    ]

    print("\n" + "=" * 60)
    print("         MEDQUERY CLINICAL DRUG ENGINE TEST CASES")
    print("=" * 60)

    for drug1, drug2 in test_cases:
        print(f"\nChecking Combination: {drug1} + {drug2}")
        report = DrugInteractionService.check_interaction(drug1, drug2)
        
        if report.get('found', False):
            severity = report.get('severity', 'Low').upper()
            description = report.get('description', '')
            
            # Print warnings and severity colors
            print("  Status:   ⚠️  INTERACTION WARNING FLAGGED")
            print(f"  Severity: [{severity}]")
            print(f"  Notes:    {description}")
        else:
            message = report.get('message', 'No interaction logs found.')
            print("  Status:   ✅  NO REGISTERED HAZARD FOUND")
            print(f"  Notes:    {message}")

    print("\n" + "=" * 60 + "\n")

if __name__ == '__main__':
    execute_clinical_tests()

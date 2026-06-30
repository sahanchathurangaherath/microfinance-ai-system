import re

with open('seed_data.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update branches
content = content.replace(
    'BRANCH_NAME = "Kalutara Branch"',
    'BRANCHES = ["Kalutara Branch", "Kurunegala Branch", "Colombo Branch", "Kandy Branch"]\nBRANCH_NAME = "Kalutara Branch" # fallback'
)

# 2. Update Locations
new_locations = """LOCATIONS = [
    ("Panadura", "Kalutara", "Western"),
    ("Horana", "Kalutara", "Western"),
    ("Matugama", "Kalutara", "Western"),
    ("Colombo 03", "Colombo", "Western"),
    ("Maharagama", "Colombo", "Western"),
    ("Moratuwa", "Colombo", "Western"),
    ("Kurunegala", "Kurunegala", "North Western"),
    ("Kuliyapitiya", "Kurunegala", "North Western"),
    ("Narammala", "Kurunegala", "North Western"),
    ("Kandy", "Kandy", "Central"),
    ("Peradeniya", "Kandy", "Central"),
    ("Gampola", "Kandy", "Central"),
]"""
content = re.sub(r'LOCATIONS = \[.*?\]', new_locations, content, flags=re.DOTALL)

# 3. Update staff creation
old_staff_creation = """    staff_users = {}
    for username, first, last, role, phone in staff_data:
        user = User.objects.create_user(
            username=username,
            password=SEED_PASSWORD,
            email=f"{username}@kalutaramicrofinance.lk",
            first_name=first,
            last_name=last,
            role=role,
            phone=phone,
            branch=BRANCH_NAME,
            is_active=True
        )
        staff_users[role] = staff_users.get(role) or user
        print(f"     ✓ {role}: {first} {last}")

    loan_officer = staff_users['loan_officer']
    branch_manager = staff_users['branch_manager']
    risk_analyst = staff_users.get('risk_analyst')
    finance = staff_users['finance_staff']"""

new_staff_creation = """    staff_users = {}
    staff_by_branch = {}
    for branch_name in BRANCHES:
        branch_prefix = branch_name.split()[0].lower()
        staff_by_branch[branch_name] = {}
        for username, first, last, role, phone in staff_data:
            user = User.objects.create_user(
                username=f"{branch_prefix}.{username}",
                password=SEED_PASSWORD,
                email=f"{username}@{branch_prefix}microfinance.lk",
                first_name=first,
                last_name=last,
                role=role,
                phone=phone,
                branch=branch_name,
                is_active=True
            )
            staff_users[role] = user # keep last for fallback
            staff_by_branch[branch_name][role] = user
        print(f"     ✓ Staff created for {branch_name}")

    loan_officer = staff_users['loan_officer']
    branch_manager = staff_users['branch_manager']
    risk_analyst = staff_users.get('risk_analyst')
    finance = staff_users['finance_staff']
    
    # Helper to get staff by city
    def get_staff_for_city(city):
        if city in ["Panadura", "Horana", "Matugama"]: b = "Kalutara Branch"
        elif city in ["Colombo 03", "Maharagama", "Moratuwa"]: b = "Colombo Branch"
        elif city in ["Kurunegala", "Kuliyapitiya", "Narammala"]: b = "Kurunegala Branch"
        elif city in ["Kandy", "Peradeniya", "Gampola"]: b = "Kandy Branch"
        else: b = "Kalutara Branch"
        return staff_by_branch[b]
"""
content = content.replace(old_staff_creation, new_staff_creation)

# 4. Inject branch staff into client creation
content = content.replace(
    'registered_by=loan_officer,',
    'registered_by=get_staff_for_city(city)["loan_officer"] if "city" in locals() else get_staff_for_city(cdata["city"])["loan_officer"],'
)

content = content.replace(
    'completed_by=loan_officer,',
    'completed_by=get_staff_for_city(city)["loan_officer"] if "city" in locals() else get_staff_for_city(cdata["city"])["loan_officer"],'
)

# Replace staff in loan applications
content = content.replace(
    "created_by=loan_officer,",
    "created_by=get_staff_for_city(client.address.first().city)['loan_officer'],"
)
content = content.replace(
    "changed_by=loan_officer,",
    "changed_by=get_staff_for_city(client.address.first().city)['loan_officer'],"
)
content = content.replace(
    "changed_by=branch_manager,",
    "changed_by=get_staff_for_city(client.address.first().city)['branch_manager'],"
)
content = content.replace(
    "changed_by=finance,",
    "changed_by=get_staff_for_city(client.address.first().city)['finance_staff'],"
)
content = content.replace(
    "reviewed_by=risk_analyst,",
    "reviewed_by=get_staff_for_city(client.address.first().city).get('risk_analyst'),"
)

# 5. Inject specific defaults/arrears (climate/inflation) into Risk Rationale for Watchlist
content = content.replace(
    'if scenario[\'status\'] == \'WATCHLIST\':',
    '''if scenario['status'] == 'WATCHLIST':
            # Inject realistic default reasons based on 2025/2026 data
            default_reasons = [
                "Severe impact from recent inflation/cost of living increase.",
                "Business downturn due to reduced consumer purchasing power.",
                "Over-indebtedness (multiple external microfinance loans).",
                "Climate shock (recent floods/drought) affected agricultural yield."
            ]
            scenario['default_reason'] = random.choice(default_reasons)'''
)

# Add default reason to AI rationale if watchlist
content = content.replace(
    'ai_rationale=f"Rule-based assessment: score {round(risk_score, 1)}/100 ({risk_cat}). "',
    'ai_rationale=f"Rule-based assessment: score {round(risk_score, 1)}/100 ({risk_cat}). {scenario.get(\'default_reason\', \'\')} "'
)

# 6. Inject expired KYC
# Change 'bank_statement_verified=random.random() > 0.3,' to simulate expired GN certs
old_kyc = '''            bank_statement_verified=random.random() > 0.3,
            aml_check_done=True,
            sanctions_check_done=True,
            business_reg_verified=True,
            is_complete=True,'''
new_kyc = '''            bank_statement_verified=random.random() > 0.3,
            aml_check_done=True,
            sanctions_check_done=True,
            business_reg_verified=True,
            is_complete=random.random() > 0.1,  # 10% have incomplete/expired KYC'''
content = content.replace(old_kyc, new_kyc)

with open('seed_data.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated seed_data.py successfully")

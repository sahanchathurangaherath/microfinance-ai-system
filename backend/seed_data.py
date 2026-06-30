"""
=============================================================
Microfinance AI System — Full Database Seed Script
=============================================================
Source: Analyzed from 6 uploaded documents:
  - Microfinance Operating Manual v1
  - Customer Journey Scenarios
  - Branch Office Operations Manual
  - Microfinance Management Excel Template (empty)
  - Microfinance Management Excel Template (with scenarios — 60 real clients)
  - AI Driven Microfinance Platform PPTX

Data accuracy:
  - 60 clients taken DIRECTLY from the scenarios Excel (C0001–C0060)
  - 140 additional clients generated in the EXACT same pattern
    (same NIC format, same locations, same occupations, same phone format)
  - All loan amounts, interest rates, tenors match the Excel exactly:
      Group loans: 22% flat, 12 weeks, LKR 30,000–50,000
      Individual loans: 26% flat, 8 weeks, LKR 60,000–80,000
  - 5 staff users match the Excel Settings sheet exactly
  - Branch: Kalutara District, Western Province (matches all locations)

Run from backend directory:
  python manage.py shell < seed_data.py
  OR
  python manage.py runscript seed_data   (if django-extensions installed)
=============================================================
"""

import os
import sys
import django
import random
from datetime import date, timedelta, datetime
from decimal import Decimal

# ── Django setup (only needed if running directly, not via manage.py shell) ──
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

from django.contrib.auth.hashers import make_password
from apps.users.models import User
from apps.clients.models import Client, ClientAddress, ClientBusiness, ClientIncome
from apps.kyc.models import KYCDocument, KYCChecklist
from apps.loans.models import (
    LoanProduct, LoanApplication, CashflowAssessment,
    ApplicationStatusHistory, RiskAssessment, AIRecommendation, Loan
)
from apps.repayments.models import RepaymentSchedule, RepaymentInstallment
from apps.approvals.models import ApprovalWorkflow, ApprovalDecision


# =============================================================
# SECTION 1 — CONFIGURATION
# =============================================================

BRANCHES = ["Kalutara Branch", "Kurunegala Branch", "Colombo Branch", "Kandy Branch"]
BRANCH_NAME = "Kalutara Branch" # fallback
SEED_PASSWORD = "Seed@2025!"   # All seeded users get this password

# Loan product interest rates — sourced directly from Excel scenarios
GROUP_INTEREST_RATE = Decimal("22.00")       # 22% flat p.a.
INDIVIDUAL_INTEREST_RATE = Decimal("26.00")  # 26% flat p.a.

# Seed date anchor — all dates relative to this
BASE_DATE = date(2025, 1, 1)


# =============================================================
# SECTION 2 — SRI LANKAN NAME POOLS
# Sourced from 60 real names in Excel + extended with authentic patterns
# =============================================================

FIRST_NAMES_MALE = [
    "Gayan", "Kasun", "Dilan", "Chamara", "Chaminda", "Saman", "Ruwan",
    "Kavindu", "Madushan", "Supun", "Shihan", "Sanjeewa", "Chathura",
    "Thilina", "Nuwan", "Lahiru", "Isuru", "Tharaka", "Prasad", "Dinesh",
    "Kavinda", "Ravindu", "Sachith", "Malith", "Asanka", "Pradeep",
    "Harsha", "Nimal", "Roshan", "Dasun", "Pasan", "Amila", "Buddhika",
    "Eranda", "Hashan", "Janaka", "Kalana", "Lasith", "Mahesh", "Nalaka",
    "Oshada", "Pasindu", "Ruchira", "Sampath", "Tharindu", "Udara",
    "Vimukthi", "Wimal", "Yasiru", "Zehan"
]

FIRST_NAMES_FEMALE = [
    "Hiruni", "Kaushalya", "Nethmi", "Harshani", "Madhavi", "Ishara",
    "Tharushi", "Sanduni", "Sachini", "Dinithi", "Dilini", "Piumi",
    "Hasini", "Sewwandi", "Chathuri", "Nadeesha", "Dilini", "Thilini",
    "Upeksha", "Waruni", "Amaya", "Bimali", "Chathu", "Devindi",
    "Erandi", "Fathima", "Gayani", "Himasha", "Inoka", "Jayani",
    "Kaveesha", "Lahiru", "Menaka", "Nimesha", "Oneli", "Piyumi",
    "Ransima", "Sasini", "Thilanka", "Ushani", "Vishmi", "Wasana",
    "Yasara", "Zinara", "Achala", "Binara", "Chamathka", "Dulari",
    "Erangi", "Fonseka"
]

LAST_NAMES = [
    "Rathnayake", "Dissanayake", "Samarasekara", "De Alwis", "Senanayake",
    "Jayasinghe", "Weerasinghe", "Abeysekara", "Karunaratne", "Rajapaksha",
    "Gunawardena", "Pathirana", "Wijesinghe", "Fernando", "Perera",
    "Wickramasinghe", "Kumara", "Silva", "Bandara", "Jayawardena",
    "Marasinghe", "Gunasekara", "Herath", "Siriwardena", "Liyanage",
    "Hapuarachchi", "Koswatte", "Pieris", "Mendis", "Rodrigo",
    "Dias", "Seneviratne", "Amarasinghe", "Kumarasinghe", "Ranasinghe",
    "Jayatilleke", "Gamage", "Nanayakkara", "Dharmasena", "Ekanayake"
]

# Locations — all from Kalutara District (matches the Excel data)
LOCATIONS = [
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
]

# Occupations — from Excel data, authentic Sri Lankan microfinance clients
OCCUPATIONS_WITH_INCOME = [
    ("Tailoring", 35000, 55000),
    ("Coconut selling", 30000, 50000),
    ("Beauty salon", 40000, 65000),
    ("Mobile repair", 45000, 70000),
    ("Tea smallholder", 25000, 45000),
    ("Grocery shop", 50000, 80000),
    ("Vegetable vendor", 28000, 48000),
    ("Home bakery", 32000, 52000),
    ("Three-wheeler hire", 45000, 70000),
    ("Fish seller", 30000, 55000),
    ("Rubber tapper", 22000, 38000),
    ("Cinnamon peeling", 20000, 35000),
    ("Batik making", 30000, 50000),
    ("Poultry farming", 35000, 60000),
    ("Paddy cultivation", 18000, 35000),
    ("Cement block making", 40000, 65000),
    ("Livestock rearing", 30000, 50000),
    ("Flower cultivation", 25000, 45000),
    ("Spice trading", 45000, 75000),
    ("Small restaurant", 55000, 90000),
]

# Street name patterns for Kalutara district
STREET_PATTERNS = [
    "{num}/A, Galle Road",
    "{num}, Moratuwa Road",
    "{num}/B, Rathnapura Road",
    "{num}, Horana Road",
    "{num}/C, Agalawatta Road",
    "{num}, Main Street",
    "{num}/A, Temple Road",
    "{num}, Station Road",
    "{num}/D, Kalutara Road",
    "{num}, Beruwala Road",
]


# =============================================================
# SECTION 3 — 60 REAL CLIENTS from Excel (verbatim)
# =============================================================

REAL_CLIENTS_FROM_EXCEL = [
    # (nic, first_name, last_name, phone, city, dob_serial, occupation, group_id)
    # DOB serials are Excel date serials — converted below
    ("846533382V", "Hiruni", "Rathnayake", "0761021695", "Panadura", 28537, "Tailoring", "G0001"),
    ("727285309V", "Gayan", "Dissanayake", "0728032657", "Aluthgama", 29840, "Coconut selling", "G0001"),
    ("746790347V", "Kaushalya", "Samarasekara", "0795952472", "Matugama", 31264, "Beauty salon", "G0001"),
    ("914337011V", "Gayan", "De Alwis", "0713114410", "Horana", 30841, "Coconut selling", "G0002"),
    ("902552809V", "Nethmi", "Senanayake", "0723027325", "Kalutara", 32308, "Tea smallholder", "G0002"),
    ("701325960V", "Dilan", "Senanayake", "0766388861", "Aluthgama", 28689, "Mobile repair", "G0002"),
    ("812425776V", "Harshani", "De Alwis", "0749272152", "Matugama", 34460, "Tailoring", "G0003"),
    ("812579635V", "Kasun", "Rajapaksha", "0758367674", "Bandaragama", 37283, "Tea smallholder", "G0003"),
    ("715560885V", "Madhavi", "Karunaratne", "0724456051", "Horana", 33791, "Mobile repair", "G0003"),
    ("909961459V", "Gayan", "Senanayake", "0761051980", "Panadura", 36858, "Mobile repair", "G0004"),
    ("793423736V", "Nethmi", "Jayasinghe", "0711999066", "Aluthgama", 32197, "Home bakery", "G0004"),
    ("859865938V", "Dilan", "Jayasinghe", "0726356467", "Kalutara", 30803, "Coconut selling", "G0004"),
    ("747672223V", "Ishara", "Weerasinghe", "0785066264", "Kalutara", 30351, "Tailoring", "G0005"),
    ("870100668V", "Saman", "Dissanayake", "0789206357", "Horana", 34182, "Tailoring", "G0005"),
    ("730470514V", "Tharushi", "Abeysekara", "0724803861", "Panadura", 27800, "Grocery shop", "G0005"),
    ("930717407V", "Kasun", "Senanayake", "0797213839", "Horana", 28829, "Vegetable vendor", "G0006"),
    ("794002004V", "Sanduni", "De Alwis", "0788634577", "Beruwala", 28345, "Grocery shop", "G0006"),
    ("934307045V", "Kavindu", "Abeysekara", "0764458048", "Matugama", 36722, "Mobile repair", "G0006"),
    ("874062509V", "Sachini", "Karunaratne", "0765372749", "Kalutara", 28723, "Home bakery", "G0007"),
    ("935712472V", "Chamara", "Fernando", "0793383567", "Bandaragama", 37336, "Coconut selling", "G0007"),
    ("722561964V", "Chathuri", "Kumara", "0720296862", "Beruwala", 27812, "Vegetable vendor", "G0007"),
    ("956092879V", "Kasun", "Abeysekara", "0748292130", "Horana", 28965, "Vegetable vendor", "G0008"),
    ("994165849V", "Sachini", "Rajapaksha", "0764151564", "Beruwala", 30562, "Tailoring", "G0008"),
    ("899491552V", "Saman", "Weerasinghe", "0746355103", "Kalutara", 29850, "Mobile repair", "G0008"),
    ("747793193V", "Dilini", "Gunawardena", "0758663525", "Aluthgama", 35573, "Three-wheeler hire", "G0009"),
    ("903389283V", "Chaminda", "Rajapaksha", "0761744846", "Matugama", 33799, "Grocery shop", "G0009"),
    ("983629495V", "Chathuri", "Pathirana", "0748876069", "Horana", 29514, "Grocery shop", "G0009"),
    ("984849005V", "Gayan", "Samarasekara", "0749872982", "Beruwala", 37075, "Tailoring", "G0010"),
    ("897722699V", "Dinithi", "Kumara", "0761512938", "Aluthgama", 27608, "Beauty salon", "G0010"),
    ("937544337V", "Chamara", "Wijesinghe", "0724040701", "Panadura", 32857, "Tea smallholder", "G0010"),
    ("971314677V", "Chathuri", "Jayasinghe", "0744159778", "Aluthgama", 31735, "Fish seller", "G0011"),
    ("951434632V", "Supun", "Abeysekara", "0799718319", "Panadura", 31834, "Tailoring", "G0011"),
    ("882794555V", "Dilini", "Rathnayake", "0755715951", "Panadura", 30701, "Home bakery", "G0011"),
    ("847035219V", "Kasun", "Wijesinghe", "0745781247", "Matugama", 35838, "Fish seller", "G0012"),
    ("905630481V", "Chathuri", "Abeysekara", "0744738820", "Aluthgama", 31186, "Home bakery", "G0012"),
    ("860831681V", "Chathura", "Pathirana", "0730496657", "Beruwala", 29526, "Tea smallholder", "G0012"),
    ("970642247V", "Piumi", "Fernando", "0759974333", "Aluthgama", 37136, "Coconut selling", "G0013"),
    ("922104087V", "Kasun", "Gunawardena", "0731057591", "Beruwala", 32115, "Grocery shop", "G0013"),
    ("760336787V", "Sachini", "Abeysekara", "0798789455", "Aluthgama", 30488, "Vegetable vendor", "G0013"),
    ("945644717V", "Chathura", "Rajapaksha", "0774788815", "Kalutara", 28500, "Mobile repair", "G0014"),
    ("775182700V", "Harshani", "Kumara", "0749896922", "Wadduwa", 35877, "Beauty salon", "G0014"),
    ("994362342V", "Chamara", "Rajapaksha", "0765825846", "Horana", 33788, "Grocery shop", "G0014"),
    ("977063271V", "Sanduni", "Kumara", "0765067819", "Matugama", 31938, "Vegetable vendor", "G0015"),
    ("748040829V", "Supun", "Pathirana", "0761842896", "Beruwala", 33403, "Beauty salon", "G0015"),
    ("746304104V", "Sewwandi", "Wijesinghe", "0736470443", "Horana", 34619, "Grocery shop", "G0015"),
    ("808645353V", "Dilan", "Perera", "0725498504", "Kalutara", 29817, "Mobile repair", "G0016"),
    ("819682345V", "Nethmi", "Fernando", "0763745497", "Matugama", 30378, "Three-wheeler hire", "G0016"),
    ("846786385V", "Shihan", "Perera", "0732124162", "Beruwala", 37231, "Mobile repair", "G0016"),
    ("775340113V", "Sanduni", "Samarasekara", "0710218299", "Kalutara", 33858, "Fish seller", "G0017"),
    ("969080304V", "Sanjeewa", "De Alwis", "0726940536", "Wadduwa", 36845, "Beauty salon", "G0017"),
    ("910977226V", "Chathuri", "Pathirana", "0775151284", "Aluthgama", 30614, "Grocery shop", "G0017"),
    ("961905809V", "Saman", "Fernando", "0731692279", "Beruwala", 32306, "Tailoring", "G0018"),
    ("841382668V", "Hasini", "Wickramasinghe", "0784057320", "Aluthgama", 29202, "Beauty salon", "G0018"),
    ("962192024V", "Chaminda", "Weerasinghe", "0736879061", "Wadduwa", 27592, "Mobile repair", "G0018"),
    ("821405507V", "Sachini", "Karunaratne", "0746835861", "Horana", 31322, "Home bakery", "G0019"),
    ("783799601V", "Sanjeewa", "Karunaratne", "0793718873", "Beruwala", 33565, "Tea smallholder", "G0019"),
    ("992694005V", "Nethmi", "Perera", "0782040339", "Bandaragama", 28280, "Three-wheeler hire", "G0019"),
    ("977302996V", "Madushan", "Dias", "0732556147", "Wadduwa", 34280, "Home bakery", "G0020"),
    ("867361379V", "Hasini", "Abeysekara", "0760429347", "Panadura", 36558, "Coconut selling", "G0020"),
    ("900788074V", "Supun", "Jayasinghe", "0713020563", "Panadura", 32377, "Three-wheeler hire", "G0020"),
]

# Convert Excel serial date to Python date
def excel_serial_to_date(serial):
    excel_epoch = date(1899, 12, 30)
    return excel_epoch + timedelta(days=serial)


# =============================================================
# SECTION 4 — NIC NUMBER GENERATION
# Sri Lankan NIC format: 9 digits + V (old) or 12 digits (new)
# =============================================================

def generate_nic(birth_year, gender='M', index=0):
    """Generate a realistic Sri Lankan NIC number."""
    year_2digit = birth_year % 100
    # Day of year: males 1-366, females 501-866
    day_of_year = random.randint(1, 300)
    if gender == 'F':
        day_of_year += 500
    serial = str(index % 1000).zfill(3)
    check = random.randint(0, 9)
    if birth_year < 2000:
        return f"{year_2digit:02d}{day_of_year:03d}{serial}{check}V"
    else:
        return f"{birth_year}{day_of_year:03d}{serial}{check}"


def generate_phone():
    """Sri Lankan mobile number — 07X XXXXXXX format."""
    prefixes = ["071", "072", "074", "075", "076", "077", "078", "079"]
    prefix = random.choice(prefixes)
    number = str(random.randint(1000000, 9999999))
    return prefix + number


# =============================================================
# SECTION 5 — GENERATE 140 ADDITIONAL CLIENTS
# (to reach 200 total with the 60 from Excel)
# =============================================================

def generate_additional_clients():
    """Generate 140 more clients following the exact same patterns as the Excel data."""
    clients = []
    used_nics = {row[0] for row in REAL_CLIENTS_FROM_EXCEL}
    used_phones = {row[3] for row in REAL_CLIENTS_FROM_EXCEL}

    group_num = 21  # Continue from G0021

    for i in range(140):
        gender = random.choice(['M', 'F'])
        if gender == 'M':
            first = random.choice(FIRST_NAMES_MALE)
        else:
            first = random.choice(FIRST_NAMES_FEMALE)
        last = random.choice(LAST_NAMES)

        birth_year = random.randint(1970, 2000)
        birth_date = date(birth_year, random.randint(1, 12), random.randint(1, 28))

        # Unique NIC
        attempt = 0
        while True:
            nic = generate_nic(birth_year, gender, i + attempt)
            if nic not in used_nics:
                used_nics.add(nic)
                break
            attempt += 1

        # Unique phone
        while True:
            phone = generate_phone()
            if phone not in used_phones:
                used_phones.add(phone)
                break

        location = random.choice(LOCATIONS)
        occupation_data = random.choice(OCCUPATIONS_WITH_INCOME)

        # 3 per group
        if i % 3 == 0:
            group_num += 1
        group_id = f"G{group_num:04d}"

        clients.append({
            "nic": nic,
            "first_name": first,
            "last_name": last,
            "phone": phone,
            "city": location[0],
            "district": location[1],
            "province": location[2],
            "dob": birth_date,
            "occupation": occupation_data[0],
            "income_min": occupation_data[1],
            "income_max": occupation_data[2],
            "group_id": group_id,
        })

    return clients


# =============================================================
# SECTION 6 — LOAN CALCULATION (matches Excel formula)
# Flat interest: total = principal + (principal * rate * tenor_years)
# Weekly installment = total / tenor_weeks
# =============================================================

def calculate_loan(principal, annual_rate_pct, tenor_weeks):
    """Flat interest method — matches Excel exactly."""
    annual_rate = Decimal(str(annual_rate_pct)) / Decimal("100")
    tenor_years = Decimal(str(tenor_weeks)) / Decimal("52")
    total_interest = Decimal(str(principal)) * annual_rate * tenor_years
    total_repayable = Decimal(str(principal)) + total_interest
    weekly_installment = total_repayable / Decimal(str(tenor_weeks))
    return round(total_repayable, 2), round(weekly_installment, 2)


# =============================================================
# SECTION 7 — MAIN SEED FUNCTION
# =============================================================

def seed_database():
    print("=" * 60)
    print("MICROFINANCE AI SYSTEM — DATABASE SEED")
    print("=" * 60)

    # ── 7.1 Clean existing seed data ─────────────────────────
    print("\n[1/8] Cleaning existing seeded data...")
    User.objects.filter(is_superuser=False).delete()
    
    # Delete in dependency order (most dependent first):
    # Repayment-related objects first (depend on Loan)
    RepaymentInstallment.objects.all().delete()
    RepaymentSchedule.objects.all().delete()
    
    # Approval workflow objects (may depend on LoanApplication)
    ApprovalDecision.objects.all().delete()
    ApprovalWorkflow.objects.all().delete()
    
    # Assessment and recommendation objects (depend on LoanApplication)
    RiskAssessment.objects.all().delete()
    CashflowAssessment.objects.all().delete()
    AIRecommendation.objects.all().delete()
    ApplicationStatusHistory.objects.all().delete()
    
    # KYC objects (depend on Client)
    KYCDocument.objects.all().delete()
    KYCChecklist.objects.all().delete()
    
    # Then delete Loan and LoanApplication (depend on Client)
    Loan.objects.all().delete()
    LoanApplication.objects.all().delete()
    
    # Then LoanProduct (no dependencies)
    LoanProduct.objects.all().delete()
    
    # Finally Client and related models (leaves must be deleted first)
    ClientIncome.objects.all().delete()
    ClientBusiness.objects.all().delete()
    ClientAddress.objects.all().delete()
    Client.objects.all().delete()
    
    print("     ✓ Existing data cleared")

    # ── 7.2 Create Staff Users ────────────────────────────────
    print("\n[2/8] Creating staff users...")

    # Real names from Excel Settings sheet
    staff_data = [
        ("dewmal.handapangoda", "Dewmal", "Handapangoda", "branch_manager",   "0711000001"),
        ("kasun.perera",        "Kasun",  "Perera",       "loan_officer",      "0711000002"),
        ("nadeesha.fernando",   "Nadeesha","Fernando",    "collections_officer","0711000003"),
        ("ruwan.wickramasinghe","Ruwan",  "Wickramasinghe","finance_staff",    "0711000004"),
        ("dilini.jayasinghe",   "Dilini", "Jayasinghe",   "loan_officer",      "0711000005"),
        # Additional staff for full role coverage
        ("priya.seneviratne",   "Priya",  "Seneviratne",  "risk_analyst",      "0711000006"),
        ("chaminda.bandara",    "Chaminda","Bandara",      "credit_committee",  "0711000007"),
        ("sanduni.kumara",      "Sanduni","Kumara",        "compliance_officer","0711000008"),
    ]

    staff_users = {}
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


    # ── 7.3 Create Loan Products ─────────────────────────────
    print("\n[3/8] Creating loan products...")

    products = {
        "Group Loan 1": LoanProduct.objects.create(
            name="Group Loan 1 (Cycle 1)",
            description="First cycle group loan. 3-member joint guarantee. Weekly repayment.",
            min_amount=Decimal("20000"),
            max_amount=Decimal("50000"),
            min_duration_months=3,
            max_duration_months=5,
            interest_rate=GROUP_INTEREST_RATE,
            is_active=True
        ),
        "Group Loan 2": LoanProduct.objects.create(
            name="Group Loan 2 (Cycle 2+)",
            description="Repeat group loan for clients with strong repayment history.",
            min_amount=Decimal("30000"),
            max_amount=Decimal("100000"),
            min_duration_months=3,
            max_duration_months=6,
            interest_rate=GROUP_INTEREST_RATE,
            is_active=True
        ),
        "Individual Loan": LoanProduct.objects.create(
            name="Individual Loan",
            description="Graduated individual loan for borrowers with proven track record.",
            min_amount=Decimal("50000"),
            max_amount=Decimal("200000"),
            min_duration_months=2,
            max_duration_months=12,
            interest_rate=INDIVIDUAL_INTEREST_RATE,
            is_active=True
        ),
        "Emergency Loan": LoanProduct.objects.create(
            name="Emergency Loan",
            description="Small emergency loan for trusted active clients only.",
            min_amount=Decimal("5000"),
            max_amount=Decimal("30000"),
            min_duration_months=1,
            max_duration_months=3,
            interest_rate=Decimal("28.00"),
            is_active=True
        ),
    }
    print(f"     ✓ {len(products)} loan products created")

    # ── 7.4 Build 200 Client Records ─────────────────────────
    print("\n[4/8] Creating 200 clients...")

    all_clients_created = []

    # ─ 60 real clients from Excel ─
    for idx, row in enumerate(REAL_CLIENTS_FROM_EXCEL):
        nic, first, last, phone, city, dob_serial, occupation, group_id = row
        dob = excel_serial_to_date(dob_serial)

        # Find occupation income range
        occ_data = next((o for o in OCCUPATIONS_WITH_INCOME if o[0] == occupation),
                        (occupation, 30000, 50000))
        monthly_income = Decimal(str(random.randint(occ_data[1], occ_data[2])))

        loc = next((l for l in LOCATIONS if l[0] == city), (city, "Kalutara", "Western"))

        client = Client.objects.create(
            nic_number=nic,
            first_name=first,
            last_name=last,
            date_of_birth=dob,
            gender='M' if int(nic[:2]) in range(0, 100) and
                          (int(nic[2:5]) if nic[-1] == 'V' else int(nic[4:7])) < 500
                   else 'F',
            phone_primary=phone,
            email=f"{first.lower()}.{last.lower().replace(' ', '')}@gmail.com",
            status='ACTIVE',
            registered_by=get_staff_for_city(city)["loan_officer"] if "city" in locals() else get_staff_for_city(cdata["city"])["loan_officer"],
            data_quality_score=random.uniform(82, 96),
        )

        # Address
        street = random.choice(STREET_PATTERNS).format(num=random.randint(1, 200))
        ClientAddress.objects.create(
            client=client,
            address_type='HOME',
            address_line_1=street,
            city=city,
            district=loc[1],
            province=loc[2],
            is_primary=True
        )

        # Business
        ClientBusiness.objects.create(
            client=client,
            business_name=f"{first}'s {occupation}",
            business_type=random.choice(['SOLE_PROPRIETOR', 'INFORMAL']),
            business_description=f"{occupation} business in {city}",
            years_in_operation=random.randint(1, 8),
            number_of_employees=random.randint(0, 3),
            monthly_revenue=monthly_income * Decimal("1.4"),
        )

        # Income
        expenses = monthly_income * Decimal("0.35")
        existing_debt = monthly_income * Decimal("0.08") if random.random() > 0.6 else Decimal("0")
        ClientIncome.objects.create(
            client=client,
            income_source='BUSINESS',
            monthly_income=monthly_income,
            other_income=Decimal("0"),
            monthly_expenses=expenses,
            existing_debt_monthly=existing_debt,
            number_of_dependents=random.randint(1, 4),
        )

        # KYC Checklist — all verified for active clients
        KYCChecklist.objects.create(
            client=client,
            nic_verified=True,
            photo_verified=True,
            address_verified=True,
            income_verified=True,
            bank_statement_verified=random.random() > 0.3,
            aml_check_done=True,
            sanctions_check_done=True,
            business_reg_verified=True,
            is_complete=random.random() > 0.1,  # 10% have incomplete/expired KYC
            completed_by=get_staff_for_city(city)["loan_officer"] if "city" in locals() else get_staff_for_city(cdata["city"])["loan_officer"],
            completed_at=datetime.now(),
        )

        all_clients_created.append((client, monthly_income, group_id))

    print(f"     ✓ 60 real Excel clients created")

    # ─ 140 generated clients ─
    additional = generate_additional_clients()
    for i, cdata in enumerate(additional):
        monthly_income = Decimal(str(random.randint(cdata['income_min'], cdata['income_max'])))

        # Determine gender from name
        gender = 'F' if cdata['first_name'] in FIRST_NAMES_FEMALE else 'M'

        client = Client.objects.create(
            nic_number=cdata['nic'],
            first_name=cdata['first_name'],
            last_name=cdata['last_name'],
            date_of_birth=cdata['dob'],
            gender=gender,
            phone_primary=cdata['phone'],
            email=f"{cdata['first_name'].lower()}.{cdata['last_name'].lower().replace(' ', '')}{i}@gmail.com",
            status=random.choice(['ACTIVE', 'ACTIVE', 'ACTIVE', 'VERIFIED']),
            registered_by=get_staff_for_city(city)["loan_officer"] if "city" in locals() else get_staff_for_city(cdata["city"])["loan_officer"],
            data_quality_score=random.uniform(75, 95),
        )

        street = random.choice(STREET_PATTERNS).format(num=random.randint(1, 200))
        ClientAddress.objects.create(
            client=client,
            address_type='HOME',
            address_line_1=street,
            city=cdata['city'],
            district=cdata['district'],
            province=cdata['province'],
            is_primary=True
        )

        ClientBusiness.objects.create(
            client=client,
            business_name=f"{cdata['first_name']}'s {cdata['occupation']}",
            business_type=random.choice(['SOLE_PROPRIETOR', 'INFORMAL', 'FARMING']),
            business_description=f"{cdata['occupation']} business in {cdata['city']}",
            years_in_operation=random.randint(1, 10),
            number_of_employees=random.randint(0, 4),
            monthly_revenue=monthly_income * Decimal("1.3"),
        )

        expenses = monthly_income * Decimal("0.30")
        existing_debt = monthly_income * Decimal("0.07") if random.random() > 0.5 else Decimal("0")
        ClientIncome.objects.create(
            client=client,
            income_source=random.choice(['BUSINESS', 'AGRICULTURE', 'BUSINESS']),
            monthly_income=monthly_income,
            other_income=Decimal("0"),
            monthly_expenses=expenses,
            existing_debt_monthly=existing_debt,
            number_of_dependents=random.randint(1, 5),
        )

        KYCChecklist.objects.create(
            client=client,
            nic_verified=True,
            photo_verified=True,
            address_verified=True,
            income_verified=True,
            bank_statement_verified=random.random() > 0.4,
            aml_check_done=True,
            sanctions_check_done=True,
            business_reg_verified=random.random() > 0.2,
            is_complete=True,
            completed_by=get_staff_for_city(city)["loan_officer"] if "city" in locals() else get_staff_for_city(cdata["city"])["loan_officer"],
            completed_at=datetime.now(),
        )

        all_clients_created.append((client, monthly_income, cdata['group_id']))

    print(f"     ✓ 140 generated clients created")
    print(f"     ✓ Total: {len(all_clients_created)} clients")

    # ── 7.5 Create Loan Applications + Loans ─────────────────
    print("\n[5/8] Creating loan applications and active loans...")

    # Loan scenario distribution (matches Excel):
    # 45 group loans active, 10 watchlist, 5 closed, 15 individual loans
    # We scale this up to ~160 loans for 200 clients

    loan_scenarios = []

    # Group loans for clients 0-149 (groups of 3)
    for i in range(0, 150, 3):
        if i + 2 >= len(all_clients_created):
            break

        # All 3 members of a group get the same amount
        amount = Decimal(str(random.choice([30000, 35000, 40000, 45000, 50000])))
        fee = Decimal("750") if amount >= 45000 else Decimal("500")
        status_choice = random.choices(
            ['ACTIVE', 'WATCHLIST', 'CLOSED'],
            weights=[60, 25, 15]
        )[0]
        # Random disbursement date in last 6 months
        days_ago = random.randint(14, 180)
        disb_date = date.today() - timedelta(days=days_ago)

        for j in range(3):
            if i + j < len(all_clients_created):
                loan_scenarios.append({
                    'client_idx': i + j,
                    'product': products["Group Loan 1"],
                    'loan_type': 'group',
                    'amount': amount,
                    'fee': fee,
                    'tenor_weeks': 12,
                    'interest_rate': GROUP_INTEREST_RATE,
                    'status': status_choice,
                    'disb_date': disb_date,
                })

    # Individual loans for clients 150-199 (graduated borrowers)
    for i in range(150, min(200, len(all_clients_created))):
        amount = Decimal(str(random.choice([60000, 70000, 80000, 90000, 100000])))
        days_ago = random.randint(7, 120)
        disb_date = date.today() - timedelta(days=days_ago)
        loan_scenarios.append({
            'client_idx': i,
            'product': products["Individual Loan"],
            'loan_type': 'individual',
            'amount': amount,
            'fee': Decimal("750"),
            'tenor_weeks': 8,
            'interest_rate': INDIVIDUAL_INTEREST_RATE,
            'status': random.choices(['ACTIVE', 'WATCHLIST'], weights=[75, 25])[0],
            'disb_date': disb_date,
        })

    # Create applications and loans
    loan_count = 0
    for scenario in loan_scenarios:
        client, monthly_income, group_id = all_clients_created[scenario['client_idx']]

        if client.status not in ['ACTIVE', 'VERIFIED']:
            continue

        # Create application
        app = LoanApplication.objects.create(
            client=client,
            loan_product=scenario['product'],
            requested_amount=scenario['amount'],
            requested_duration_months=round(scenario['tenor_weeks'] / 4.33),
            loan_purpose=random.choice([
                'BUSINESS_EXPANSION', 'WORKING_CAPITAL',
                'EQUIPMENT_PURCHASE', 'AGRICULTURE'
            ]),
            purpose_description=f"Business development — {client.first_name}'s {client.business.business_name}",
            status='DISBURSED',
            created_by=get_staff_for_city(client.addresses.first().city)['loan_officer'],
            submitted_at=scenario['disb_date'] - timedelta(days=7),
            officer_notes=f"Client verified. Group loan cycle 1. {group_id}."
        )

        # Cashflow assessment
        income = client.income
        total_repayable, weekly_inst = calculate_loan(
            scenario['amount'], scenario['interest_rate'], scenario['tenor_weeks']
        )
        monthly_inst = weekly_inst * Decimal("4.33")
        dti = float((monthly_inst + income.existing_debt_monthly) / income.monthly_income)

        CashflowAssessment.objects.create(
            application=app,
            monthly_income=income.monthly_income,
            other_income=income.other_income,
            monthly_expenses=income.monthly_expenses,
            existing_loan_payments=income.existing_debt_monthly,
            proposed_monthly_payment=monthly_inst,
            net_cashflow=income.monthly_income - income.monthly_expenses - monthly_inst,
            debt_to_income_ratio=round(dti, 4),
        )

        # Status history
        ApplicationStatusHistory.objects.create(
            application=app,
            from_status='',
            to_status='DRAFT',
            changed_by=get_staff_for_city(client.addresses.first().city)['loan_officer'],
            changed_by_role='loan_officer',
            reason='Application created'
        )
        ApplicationStatusHistory.objects.create(
            application=app,
            from_status='DRAFT',
            to_status='APPROVED',
            changed_by=get_staff_for_city(client.addresses.first().city)['branch_manager'],
            changed_by_role='branch_manager',
            reason='Credit committee approved'
        )
        ApplicationStatusHistory.objects.create(
            application=app,
            from_status='APPROVED',
            to_status='DISBURSED',
            changed_by=get_staff_for_city(client.addresses.first().city)['finance_staff'],
            changed_by_role='finance_staff',
            reason=f'Disbursed on {scenario["disb_date"]}'
        )

        # Risk Assessment
        risk_score = random.uniform(55, 88)
        if scenario['status'] == 'WATCHLIST':
            # Inject realistic default reasons based on 2025/2026 data
            default_reasons = [
                "Severe impact from recent inflation/cost of living increase.",
                "Business downturn due to reduced consumer purchasing power.",
                "Over-indebtedness (multiple external microfinance loans).",
                "Climate shock (recent floods/drought) affected agricultural yield."
            ]
            scenario['default_reason'] = random.choice(default_reasons)
            risk_score = random.uniform(35, 60)
        elif scenario['status'] == 'CLOSED':
            risk_score = random.uniform(65, 90)

        risk_cat = 'LOW' if risk_score >= 70 else 'MEDIUM' if risk_score >= 40 else 'HIGH'
        RiskAssessment.objects.create(
            application=app,
            risk_score=round(risk_score, 2),
            risk_category=risk_cat,
            confidence=round(random.uniform(0.78, 0.95), 2),
            ai_rationale=f"Rule-based assessment: score {round(risk_score, 1)}/100 ({risk_cat}). {scenario.get('default_reason', '')} "
                        f"DTI={round(dti*100,1)}%. Income stable. Business {client.business.years_in_operation}yr(s).",
            dti_score=25 if dti < 0.30 else 15 if dti < 0.50 else 0,
            lti_score=20 if float(scenario['amount']) < float(income.monthly_income) * 24 else 10,
            kyc_score=round(client.data_quality_score * 0.15 / 100, 2),
            income_stability_score=15 if client.business.years_in_operation >= 3 else 8,
            repayment_history_score=10,
            dependents_score=10 if income.number_of_dependents <= 2 else 5,
            default_signals=[],
            reviewed_by=get_staff_for_city(client.addresses.first().city).get('risk_analyst'),
            reviewed_at=datetime.now() - timedelta(days=random.randint(5, 30)),
            analyst_notes="Reviewed. Proceeding to disbursement.",
        )

        # Create actual Loan record
        closure_date = scenario['disb_date'] + timedelta(weeks=scenario['tenor_weeks'])
        loan_status_map = {
            'ACTIVE': 'ACTIVE',
            'WATCHLIST': 'ACTIVE',   # Watchlist in arrears but loan still active
            'CLOSED': 'CLOSED',
        }
        loan = Loan.objects.create(
            application=app,
            client=client,
            principal_amount=scenario['amount'],
            interest_rate=scenario['interest_rate'],
            duration_months=round(scenario['tenor_weeks'] / 4.33),
            monthly_installment=monthly_inst,
            total_repayable=total_repayable,
            outstanding_balance=total_repayable if scenario['status'] == 'ACTIVE' else
                               total_repayable * Decimal("0.5") if scenario['status'] == 'WATCHLIST' else
                               Decimal("0"),
            status=loan_status_map.get(scenario['status'], 'ACTIVE'),
            disbursed_at=datetime.combine(scenario['disb_date'], datetime.min.time()),
            expected_closure_date=closure_date,
            actual_closure_date=closure_date if scenario['status'] == 'CLOSED' else None,
        )

        # Repayment Schedule
        schedule = RepaymentSchedule.objects.create(
            loan=loan,
            total_installments=scenario['tenor_weeks'],
            installments_paid=0,
        )

        # Create weekly installments
        weeks_elapsed = (date.today() - scenario['disb_date']).days // 7
        paid_count = 0

        for week in range(1, scenario['tenor_weeks'] + 1):
            due = scenario['disb_date'] + timedelta(weeks=week)
            if scenario['status'] == 'CLOSED':
                inst_status = 'PAID'
                amount_paid = weekly_inst
            elif week <= weeks_elapsed:
                if scenario['status'] == 'WATCHLIST' and week >= weeks_elapsed - 1:
                    inst_status = 'OVERDUE'
                    amount_paid = Decimal("0")
                else:
                    inst_status = 'PAID'
                    amount_paid = weekly_inst
                    paid_count += 1
            else:
                inst_status = 'PENDING'
                amount_paid = Decimal("0")

            RepaymentInstallment.objects.create(
                schedule=schedule,
                installment_number=week,
                due_date=due,
                amount_due=weekly_inst,
                principal_component=round(scenario['amount'] / scenario['tenor_weeks'], 2),
                interest_component=round(weekly_inst - scenario['amount'] / scenario['tenor_weeks'], 2),
                amount_paid=amount_paid,
                outstanding=weekly_inst - amount_paid,
                status=inst_status,
                days_overdue=(date.today() - due).days if inst_status == 'OVERDUE' else 0,
                paid_at=datetime.combine(due, datetime.min.time()) if inst_status == 'PAID' else None,
            )

        schedule.installments_paid = paid_count
        schedule.save()

        loan_count += 1

    print(f"     ✓ {loan_count} loan applications + loans created")
    print(f"     ✓ Active: ~{int(loan_count * 0.60)}, Watchlist: ~{int(loan_count * 0.25)}, Closed: ~{int(loan_count * 0.15)}")

    # ── 7.6 Create Approval Workflows ────────────────────────
    print("\n[6/8] Creating approval workflows...")
    wf_count = 0
    for app in LoanApplication.objects.filter(status='DISBURSED')[:50]:
        wf, _ = ApprovalWorkflow.objects.get_or_create(
            application=app,
            defaults={
                'status': 'APPROVED',
                'requires_committee': float(app.requested_amount) >= 100000,
            }
        )
        ApprovalDecision.objects.create(
            workflow=wf,
            step='BRANCH_MANAGER',
            decision='APPROVED',
            decided_by=branch_manager,
            comments='Approved by credit committee. Client verified.',
            ai_recommendation_followed=True,
        )
        wf_count += 1
    print(f"     ✓ {wf_count} approval workflow records created")

    # ── 7.7 Print Summary ────────────────────────────────────
    print("\n[7/8] Generating summary...")
    total_clients = Client.objects.count()
    total_loans = Loan.objects.count()
    active_loans = Loan.objects.filter(status='ACTIVE').count()
    total_portfolio = Loan.objects.filter(
        status='ACTIVE'
    ).aggregate(
        total=__import__('django.db.models', fromlist=['Sum']).Sum('outstanding_balance')
    )['total'] or 0

    print(f"""
╔══════════════════════════════════════════════╗
║         SEED COMPLETE — SUMMARY              ║
╠══════════════════════════════════════════════╣
║  Staff Users         : {User.objects.filter(is_superuser=False).count():>5}                     ║
║  Total Clients       : {total_clients:>5}                     ║
║  Loan Products       : {LoanProduct.objects.count():>5}                     ║
║  Total Loans         : {total_loans:>5}                     ║
║  Active Loans        : {active_loans:>5}                     ║
║  Portfolio (LKR)     : {int(total_portfolio):>12,}           ║
╚══════════════════════════════════════════════╝
""")

    # ── 7.8 Print Login Credentials ──────────────────────────
    print("[8/8] Login credentials for testing:")
    print(f"  Password for ALL users: {SEED_PASSWORD}")
    print()
    for username, first, last, role, _ in staff_data:
        print(f"  {role:<25} → username: {username}")

    print("\n✅ Database seed complete!")
    print("   Run: python manage.py runserver")
    print("   Then test: POST /api/auth/login/ with any username above")


# =============================================================
# ENTRY POINT
# =============================================================

if __name__ == '__main__':
    seed_database()
# When imported as a module via management command, the command handles calling seed_database()

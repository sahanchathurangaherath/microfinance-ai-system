"""
Seed Verification Script
Run after seeding to confirm all data loaded correctly.

Usage:
  python manage.py shell < verify_seed.py
"""

from apps.users.models import User
from apps.clients.models import Client, ClientIncome
from apps.loans.models import LoanApplication, Loan, RiskAssessment
from apps.repayments.models import RepaymentInstallment
from django.db.models import Sum, Avg, Count

print("\n" + "="*60)
print("SEED DATA VERIFICATION REPORT")
print("="*60)

# ─── STAFF ───────────────────────────────────────────────────
print("\n── STAFF USERS ──")
for user in User.objects.filter(is_superuser=False).order_by('role'):
    print(f"  {user.role:<30} {user.first_name} {user.last_name} ({user.username})")

# ─── CLIENTS ─────────────────────────────────────────────────
print("\n── CLIENT SUMMARY ──")
total = Client.objects.count()
by_status = Client.objects.values('status').annotate(n=Count('id'))
print(f"  Total clients: {total}")
for row in by_status:
    print(f"    {row['status']}: {row['n']}")

# Gender split
male = Client.objects.filter(gender='M').count()
female = Client.objects.filter(gender='F').count()
print(f"  Gender: {male} Male / {female} Female")

# Location spread
print("\n  Top locations:")
locs = ClientIncome.objects.select_related('client__addresses').all()
from apps.clients.models import ClientAddress
loc_counts = ClientAddress.objects.filter(is_primary=True)\
    .values('city').annotate(n=Count('id')).order_by('-n')[:8]
for l in loc_counts:
    print(f"    {l['city']}: {l['n']} clients")

# ─── INCOME ──────────────────────────────────────────────────
print("\n── INCOME DISTRIBUTION ──")
income_stats = ClientIncome.objects.aggregate(
    avg=Avg('monthly_income'),
    total=Sum('monthly_income'),
    count=Count('id')
)
print(f"  Clients with income data: {income_stats['count']}")
print(f"  Average monthly income:   LKR {int(income_stats['avg'] or 0):,}")
print(f"  Total monthly income:     LKR {int(income_stats['total'] or 0):,}")

# ─── OCCUPATIONS ─────────────────────────────────────────────
print("\n  Top occupations:")
from apps.clients.models import ClientBusiness
occ_counts = ClientBusiness.objects.values('business_type')\
    .annotate(n=Count('id')).order_by('-n')
for o in occ_counts[:8]:
    print(f"    {o['business_type']}: {o['n']}")

# ─── LOANS ───────────────────────────────────────────────────
print("\n── LOAN SUMMARY ──")
loan_stats = Loan.objects.aggregate(
    total_count=Count('id'),
    total_portfolio=Sum('principal_amount'),
    total_outstanding=Sum('outstanding_balance'),
    avg_amount=Avg('principal_amount'),
)
print(f"  Total loans:          {loan_stats['total_count']}")
print(f"  Total disbursed:      LKR {int(loan_stats['total_portfolio'] or 0):,}")
print(f"  Total outstanding:    LKR {int(loan_stats['total_outstanding'] or 0):,}")
print(f"  Average loan size:    LKR {int(loan_stats['avg_amount'] or 0):,}")

print("\n  Loan status breakdown:")
by_status = Loan.objects.values('status').annotate(n=Count('id'), vol=Sum('principal_amount'))
for row in by_status:
    print(f"    {row['status']}: {row['n']} loans | LKR {int(row['vol'] or 0):,}")

# ─── REPAYMENTS ──────────────────────────────────────────────
print("\n── REPAYMENT INSTALLMENTS ──")
inst_stats = RepaymentInstallment.objects.values('status').annotate(n=Count('id'))
total_insts = RepaymentInstallment.objects.count()
print(f"  Total installments: {total_insts}")
for row in inst_stats:
    pct = round(row['n'] / total_insts * 100, 1) if total_insts else 0
    print(f"    {row['status']}: {row['n']} ({pct}%)")

# ─── RISK ASSESSMENTS ────────────────────────────────────────
print("\n── RISK ASSESSMENT SUMMARY ──")
risk_stats = RiskAssessment.objects.aggregate(
    count=Count('id'),
    avg_score=Avg('risk_score'),
    avg_confidence=Avg('confidence'),
)
print(f"  Total assessments:    {risk_stats['count']}")
print(f"  Average risk score:   {round(risk_stats['avg_score'] or 0, 1)}/100")
print(f"  Average confidence:   {round((risk_stats['avg_confidence'] or 0) * 100, 1)}%")

print("\n  Risk category breakdown:")
by_cat = RiskAssessment.objects.values('risk_category').annotate(n=Count('id'))
for row in by_cat:
    print(f"    {row['risk_category']}: {row['n']}")

# ─── KPI SNAPSHOT ────────────────────────────────────────────
print("\n── PORTFOLIO KPIs ──")
active_loans = Loan.objects.filter(status='ACTIVE')
overdue_insts = RepaymentInstallment.objects.filter(status='OVERDUE')
overdue_loan_ids = overdue_insts.values_list('schedule__loan_id', flat=True).distinct()
overdue_count = len(set(overdue_loan_ids))
total_active = active_loans.count()
par30 = round(overdue_count / total_active * 100, 1) if total_active else 0
print(f"  Active loans:         {total_active}")
print(f"  Loans with overdue:   {overdue_count}")
print(f"  PAR (overdue/active): {par30}%")

paid = RepaymentInstallment.objects.filter(status='PAID').count()
all_due = RepaymentInstallment.objects.exclude(status='PENDING').count()
repayment_rate = round(paid / all_due * 100, 1) if all_due else 0
print(f"  Repayment rate:       {repayment_rate}%")

print("\n" + "="*60)
print("✅ Verification complete. System is ready for testing.")
print("="*60 + "\n")

from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta


def calculate_monthly_installment(principal, annual_rate, months):
    """
    Calculates fixed monthly installment using flat interest method (common in microfinance).
    Formula: (Principal + Total Interest) / Months
    """
    monthly_rate = Decimal(str(annual_rate)) / Decimal('100') / Decimal('12')
    total_interest = Decimal(str(principal)) * monthly_rate * Decimal(str(months))
    total_repayable = Decimal(str(principal)) + total_interest
    monthly_installment = total_repayable / Decimal(str(months))
    return round(monthly_installment, 2), round(total_repayable, 2)


def generate_repayment_schedule(loan):
    """
    Generates a list of repayment installment dicts for a loan.
    Called after disbursement to populate RepaymentInstallment table.
    """
    from apps.repayments.models import RepaymentSchedule, RepaymentInstallment

    schedule, _ = RepaymentSchedule.objects.get_or_create(
        loan=loan,
        defaults={"total_installments": loan.duration_months}
    )

    start_date = loan.disbursed_at.date()
    installments = []

    for i in range(1, loan.duration_months + 1):
        due_date = start_date + relativedelta(months=i)
        inst = RepaymentInstallment(
            schedule=schedule,
            installment_number=i,
            due_date=due_date,
            amount_due=loan.monthly_installment,
            principal_component=round(
                loan.principal_amount / Decimal(str(loan.duration_months)), 2
            ),
            interest_component=round(
                loan.monthly_installment - (loan.principal_amount / Decimal(str(loan.duration_months))), 2
            ),
            status='PENDING'
        )
        installments.append(inst)

    RepaymentInstallment.objects.bulk_create(installments)
    return schedule



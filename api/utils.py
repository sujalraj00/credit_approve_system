from .models import Loan, Customer
from datetime import date

def calculate_credit_score(customer_id):
    try:
        customer = Customer.objects.get(id=customer_id)
        loans = Loan.objects.filter(customer=customer)
        total_loans = loans.count()

        # check if current_debt exceeds approved_limit
        if customer.current_debt > customer.approved_limit:
            return 0

        if total_loans == 0:
            #  giving neutral score for new customers
            return 60

        score = 0

        #  Past loans paid on time
        on_time_loans = 0
        for loan in loans:
            if loan.emis_paid_on_time >= loan.tenure * 0.9:  # if  90% EMIs  are on time
                on_time_loans += 1
        score += (on_time_loans / total_loans) * 30  # 30 points weight

        # no. of past loans
        score += min(total_loans * 2, 20)  # max 20 points

        # 4. loan activity in current year
        current_year = date.today().year
        recent_loans = loans.filter(start_date__year=current_year).count()
        score += min(recent_loans * 5, 10)  # max 10 points

        # 5. total loan volume
        total_volume = sum(loan.loan_amount for loan in loans)
        score += min((total_volume / 1000000) * 10, 20)  # max 20 points

        # remaining points can be from EMI discipline
        score = round(min(score, 100))  

        return score

    except Customer.DoesNotExist:
        return 0

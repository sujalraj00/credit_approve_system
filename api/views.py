# api/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from math import pow

from .models import Customer, Loan
from .serializers import CustomerSerializer, LoanSerializer
from .utils import calculate_credit_score

@api_view(['POST'])
def register_customer(request):
    try:
        data = request.data
        approved_limit = round((36 * int(data['monthly_income'])) / 100000) * 100000  

        customer = Customer.objects.create(
            first_name=data['first_name'],
            last_name=data['last_name'],
            age=data['age'],
            phone_number=data['phone_number'],
            monthly_salary=data['monthly_income'],
            approved_limit=approved_limit,
            current_debt=0 
        )

        response = {
            "customer_id": customer.id,
            "name": f"{customer.first_name} {customer.last_name}",
            "age": customer.age,
            "monthly_income": customer.monthly_salary,
            "approved_limit": customer.approved_limit,
            "phone_number": customer.phone_number
        }
        return Response(response, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def check_eligibility(request):
    try:
        data = request.data
        customer_id = data['customer_id']
        loan_amount = float(data['loan_amount'])
        interest_rate = float(data['interest_rate'])
        tenure = int(data['tenure'])

        customer = Customer.objects.get(id=customer_id)
        credit_score = calculate_credit_score(customer_id)

        # calculate EMI
        monthly_interest = interest_rate / (12 * 100)
        emi = loan_amount * monthly_interest * pow(1 + monthly_interest, tenure) / (pow(1 + monthly_interest, tenure) - 1)

        # check total EMI load
        current_emi_total = sum(l.monthly_repayment for l in Loan.objects.filter(customer_id=customer_id))
        if current_emi_total + emi > 0.5 * customer.monthly_salary:
            return Response({
                "customer_id": customer_id,
                "approval": False,
                "interest_rate": interest_rate,
                "corrected_interest_rate": interest_rate,
                "tenure": tenure,
                "monthly_installment": round(emi, 2),
                "message": "Loan denied: EMIs exceed 50% of income"
            }, status=status.HTTP_200_OK)

        # credit-score slabs
        corrected_rate = interest_rate
        approval = True

        if credit_score > 50:
            approval = True
        elif 30 < credit_score <= 50:
            if interest_rate < 12:
                corrected_rate = 12
        elif 10 < credit_score <= 30:
            if interest_rate < 16:
                corrected_rate = 16
        else:
            approval = False

        # if rate changed, recalc emi
        if corrected_rate != interest_rate:
            monthly_interest = corrected_rate / (12 * 100)
            emi = loan_amount * monthly_interest * pow(1 + monthly_interest, tenure) / (pow(1 + monthly_interest, tenure) - 1)

        return Response({
            "customer_id": customer_id,
            "approval": approval,
            "interest_rate": interest_rate,
            "corrected_interest_rate": corrected_rate,
            "tenure": tenure,
            "monthly_installment": round(emi, 2)
        }, status=status.HTTP_200_OK)

    except Customer.DoesNotExist:
        return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def create_loan(request):
    try:
        data = request.data
        customer_id = data['customer_id']
        loan_amount = float(data['loan_amount'])
        interest_rate = float(data['interest_rate'])
        tenure = int(data['tenure'])

        customer = Customer.objects.get(id=customer_id)
        credit_score = calculate_credit_score(customer_id)

        monthly_interest = interest_rate / (12 * 100)
        emi = loan_amount * monthly_interest * pow(1 + monthly_interest, tenure) / (pow(1 + monthly_interest, tenure) - 1)

        # check emo burden
        total_current_emi = sum([l.monthly_repayment for l in Loan.objects.filter(customer_id=customer_id)])
        if total_current_emi + emi > 0.5 * customer.monthly_salary:
            return Response({
                "loan_id": None,
                "customer_id": customer_id,
                "loan_approved": False,
                "message": "Loan denied: EMIs exceed 50% of income",
                "monthly_installment": round(emi, 2)
            }, status=200)

        corrected_rate = interest_rate
        approval = True

        if credit_score > 50:
            approval = True
        elif 30 < credit_score <= 50:
            if interest_rate < 12:
                corrected_rate = 12
        elif 10 < credit_score <= 30:
            if interest_rate < 16:
                corrected_rate = 16
        else:
            approval = False

        # recalculate EMI if rate changed
        if corrected_rate != interest_rate:
            monthly_interest = corrected_rate / (12 * 100)
            emi = loan_amount * monthly_interest * pow(1 + monthly_interest, tenure) / (pow(1 + monthly_interest, tenure) - 1)

        if not approval:
            return Response({
                "loan_id": None,
                "customer_id": customer_id,
                "loan_approved": False,
                "message": "Loan denied: low credit score",
                "monthly_installment": round(emi, 2)
            }, status=200)

        # create loan
        from datetime import date, timedelta
        start = date.today()
        end = start + timedelta(days=30 * tenure)

        loan = Loan.objects.create(
            customer=customer,
            loan_amount=loan_amount,
            tenure=tenure,
            interest_rate=corrected_rate,
            monthly_repayment=round(emi, 2),
            emis_paid_on_time=0,
            start_date=start,
            end_date=end
        )

        # update customer’s current debt
        customer.current_debt += loan_amount
        customer.save()

        return Response({
            "loan_id": loan.id,
            "customer_id": customer_id,
            "loan_approved": True,
            "message": "Loan approved",
            "monthly_installment": round(emi, 2)
        }, status=201)

    except Customer.DoesNotExist:
        return Response({"error": "Customer not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=400)



@api_view(['GET'])
def view_loan(request, loan_id):
    try:
        loan = Loan.objects.get(id=loan_id)
        customer = loan.customer

        return Response({
            "loan_id": loan.id,
            "customer": {
                "id": customer.id,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "phone_number": customer.phone_number,
                "age": customer.age
            },
            "loan_amount": loan.loan_amount,
            "interest_rate": loan.interest_rate,
            "monthly_installment": loan.monthly_repayment,
            "tenure": loan.tenure
        }, status=200)
    except Loan.DoesNotExist:
        return Response({"error": "Loan not found"}, status=404)

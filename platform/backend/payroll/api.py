from rest_framework.decorators import action
from rest_framework.response import Response

from core.scoped_api import ScopedViewSet
from core.serializers import ExactModelSerializer, JalaliDateField

from .models import Contract, Payslip
from .services import issue_payslip


class ContractSerializer(ExactModelSerializer):
    class Meta:
        model = Contract
        fields = "__all__"
        read_only_fields = ["created_by"]


class ContractViewSet(ScopedViewSet):
    module = "payroll"
    resource = "contract"
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    http_method_names = ["get", "post", "head", "options"]


class PayslipSerializer(ExactModelSerializer):
    doc_date = JalaliDateField()

    class Meta:
        model = Payslip
        fields = "__all__"
        read_only_fields = [
            "created_by",
            "gross",
            "employee_insurance",
            "employer_insurance",
            "tax",
            "net",
            "voucher",
            "policy_snapshot",
        ]


class PayslipViewSet(ScopedViewSet):
    module = "payroll"
    resource = "payslip"
    queryset = Payslip.objects.all()
    serializer_class = PayslipSerializer
    http_method_names = ["get", "post", "head", "options"]

    @action(detail=True, methods=["post"])
    def issue(self, request, pk=None):
        return Response(self.get_serializer(issue_payslip(self.get_object(), request.user)).data)

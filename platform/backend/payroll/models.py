from django.db import models


class PayrollPolicy(models.Model):
    business_unit = models.ForeignKey("core.BusinessUnit", on_delete=models.PROTECT)
    year = models.ForeignKey("accounting.FiscalYear", on_delete=models.PROTECT)
    name = models.CharField(max_length=120)
    rates = models.JSONField()


class Contract(models.Model):
    business_unit = models.ForeignKey("core.BusinessUnit", on_delete=models.PROTECT)
    employee = models.ForeignKey("crm.Party", on_delete=models.PROTECT)
    monthly_salary = models.DecimalField(max_digits=20, decimal_places=0)
    hourly_overtime = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    allowances = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    created_by = models.ForeignKey("auth.User", on_delete=models.PROTECT)


class Payslip(models.Model):
    business_unit = models.ForeignKey("core.BusinessUnit", on_delete=models.PROTECT)
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT)
    policy = models.ForeignKey(PayrollPolicy, on_delete=models.PROTECT)
    doc_date = models.DateField()
    work_days = models.PositiveSmallIntegerField(default=30)
    paid_days = models.DecimalField(max_digits=5, decimal_places=2)
    overtime_hours = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    gross = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    employee_insurance = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    employer_insurance = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    tax = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    net = models.DecimalField(max_digits=20, decimal_places=0, default=0)
    voucher = models.OneToOneField("accounting.Voucher", null=True, on_delete=models.PROTECT)
    created_by = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    policy_snapshot = models.JSONField(default=dict)

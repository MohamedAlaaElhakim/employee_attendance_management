# -*- coding: utf-8 -*-
from odoo import models, fields, api
import calendar
from datetime import date
from dateutil.relativedelta import relativedelta


class AttendanceMonthlySummary(models.Model):
    _name = "employee.attendance.summary"
    _description = "Monthly Attendance Summary"
    _order = "year desc, month desc, employee_id"
    _rec_name = "employee_id"

    employee_id = fields.Many2one("hr.employee", required=True, ondelete="cascade")
    month = fields.Integer(required=True)
    year = fields.Integer(required=True)

    month_display = fields.Char(
        compute="_compute_month_display", store=True,
    )

    total_days = fields.Integer(compute="_compute_summary", store=True)
    present_days = fields.Integer(compute="_compute_summary", store=True)
    late_days = fields.Integer(compute="_compute_summary", store=True)
    absent_days = fields.Integer(compute="_compute_summary", store=True)
    approved_days = fields.Integer(compute="_compute_summary", store=True)
    total_hours = fields.Float(compute="_compute_summary", store=True, digits=(16, 2))

    # لو عايز تشوف السجلات كـ related مش computed كل مرة
    # attendance_ids = fields.One2many('employee.attendance.record', compute='_compute_attendance_ids')

    _sql_constraints = [
        ("unique_employee_month_year", "unique(employee_id, month, year)",
         "A summary already exists for this employee and month."),
    ]

    @api.depends("month", "year")
    def _compute_month_display(self):
        for rec in self:
            if rec.month and rec.year:
                rec.month_display = f"{calendar.month_name[rec.month]} {rec.year}"
            else:
                rec.month_display = ""

    def _get_date_range(self):
        self.ensure_one()
        last_day = calendar.monthrange(self.year, self.month)[1]
        return (
            fields.Date.to_date(f"{self.year}-{self.month:02d}-01"),
            fields.Date.to_date(f"{self.year}-{self.month:02d}-{last_day:02d}"),
        )

    @api.depends("employee_id", "month", "year")
    def _compute_summary(self):
        for rec in self:
            if not all([rec.employee_id, rec.month, rec.year]):
                rec.total_days = rec.present_days = rec.late_days = \
                    rec.absent_days = rec.approved_days = 0
                rec.total_hours = 0.0
                continue

            date_from, date_to = rec._get_date_range()

            # جلب السجلات المحددة فقط (أسرع وأفضل)
            attendances = self.env["employee.attendance.record"].search([
                ("employee_id", "=", rec.employee_id.id),
                ("date", ">=", date_from),
                ("date", "<=", date_to),
            ])

            # لو عايز total_days = عدد الأيام الفعلية اللي فيها سجل أو غياب محسوب → استخدم len(attendances)
            # لكن الأفضل: عدد أيام العمل المتوقعة من الـ resource.calendar (working schedule)
            # مثال بسيط (لو مش عايز تعقيد):
            rec.total_days = (date_to - date_from).days + 1   # كل أيام الشهر

            # أو أحسن: حسب الشيديول الحقيقي (تحتاج تضيف dependency على contract/resource.calendar)

            present = attendances.filtered(lambda r: r.state == "present")
            late   = attendances.filtered(lambda r: r.state == "late")
            absent = attendances.filtered(lambda r: r.state == "absent")
            approved = attendances.filtered(lambda r: r.state == "approved")

            rec.present_days = len(present)
            rec.late_days    = len(late)
            rec.absent_days  = len(absent)
            rec.approved_days = len(approved)
            rec.total_hours  = sum(a.worked_hours for a in attendances)  # أو فقط present+late+approved

    @api.model
    def generate_monthly_summary(self):
        today = date.today()
        last_month = today.replace(day=1) - relativedelta(months=1)
        month, year = last_month.month, last_month.year

        employees = self.env["hr.employee"].search([("active", "=", True)])
        for emp in employees:
            summary = self.search([
                ("employee_id", "=", emp.id),
                ("month", "=", month),
                ("year", "=", year),
            ], limit=1)
            if summary:
                summary._compute_summary()   # force recompute
            else:
                self.create({
                    "employee_id": emp.id,
                    "month": month,
                    "year": year,
                })
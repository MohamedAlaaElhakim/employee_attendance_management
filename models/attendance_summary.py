# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AttendanceMonthlySummary(models.Model):
    _name = "employee.attendance.summary"
    _description = "Monthly Attendance Summary"
    _order = "year desc, month desc, employee_id"
    _rec_name = "employee_id"

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        ondelete="cascade",
    )

    month = fields.Integer(string="Month", required=True)
    year = fields.Integer(string="Year", required=True)

    month_display = fields.Char(
        string="Period",
        compute="_compute_month_display",
        store=True,
    )

    total_days = fields.Integer(string="Total Days", compute="_compute_summary", store=True)
    present_days = fields.Integer(string="Present Days", compute="_compute_summary", store=True)
    late_days = fields.Integer(string="Late Days", compute="_compute_summary", store=True)
    absent_days = fields.Integer(string="Absent Days", compute="_compute_summary", store=True)
    approved_days = fields.Integer(string="Approved Days", compute="_compute_summary", store=True)
    total_hours = fields.Float(string="Total Hours", compute="_compute_summary", store=True)

    attendance_ids = fields.One2many(
        "employee.attendance.record",
        compute="_compute_attendance_ids",
    )

    _sql_constraints = [
        ("unique_employee_month_year", "unique(employee_id, month, year)",
         "A summary already exists for this employee and month."),
    ]

    def _get_date_range(self, month, year):
        """✅ NEW: Helper to get date range for a month"""
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        return (
            f"{year}-{month:02d}-01",
            f"{year}-{month:02d}-{last_day:02d}"
        )

    @api.depends("month", "year")
    def _compute_month_display(self):
        import calendar
        for rec in self:
            if rec.month and rec.year:
                rec.month_display = f"{calendar.month_name[rec.month]} {rec.year}"
            else:
                rec.month_display = ""

    def _compute_attendance_ids(self):
        for rec in self:
            # ✅ FIX: نتحقق الأول
            if not rec.month or not rec.year or not rec.employee_id:
                rec.attendance_ids = self.env["employee.attendance.record"]
                continue

            import calendar
            last_day = calendar.monthrange(rec.year, rec.month)[1]
            rec.attendance_ids = self.env["employee.attendance.record"].search([
                ("employee_id", "=", rec.employee_id.id),
                ("date", ">=", f"{rec.year}-{rec.month:02d}-01"),
                ("date", "<=", f"{rec.year}-{rec.month:02d}-{last_day:02d}"),
            ])

    def _reset_summary_fields(self):
        """Helper method to reset all summary fields to zero"""
        self.total_days = 0
        self.present_days = 0
        self.late_days = 0
        self.absent_days = 0
        self.approved_days = 0
        self.total_hours = 0.0

    @api.depends("employee_id", "month", "year")
    def _compute_summary(self):
        """✅ IMPROVED: Performance optimized - single query for all records"""
        if not self:
            return
        
        import calendar
        
        # جمع كل التواريخ والموظفين مرة واحدة
        queries = []
        for rec in self:
            if rec.month and rec.year and rec.employee_id:
                last_day = calendar.monthrange(rec.year, rec.month)[1]
                queries.append((
                    rec.employee_id.id,
                    f"{rec.year}-{rec.month:02d}-01",
                    f"{rec.year}-{rec.month:02d}-{last_day:02d}",
                    rec.id
                ))
        
        # Reset fields for invalid records
        for rec in self:
            if not rec.month or not rec.year or not rec.employee_id:
                rec._reset_summary_fields()
        
        if not queries:
            return
        
        # Query واحد لكل الموظفين - أسرع بكثير!
        employee_ids = [q[0] for q in queries]
        date_from_min = min(q[1] for q in queries)
        date_to_max = max(q[2] for q in queries)
        
        all_records = self.env["employee.attendance.record"].search([
            ("employee_id", "in", employee_ids),
            ("date", ">=", date_from_min),
            ("date", "<=", date_to_max),
        ])
        
        # تجميع النتائج في dictionary حسب الموظف
        records_by_employee = {}
        for record in all_records:
            key = record.employee_id.id
            if key not in records_by_employee:
                records_by_employee[key] = []
            records_by_employee[key].append(record)
        
        # الآن نحسب لكل موظف
        for rec in self:
            if not rec.month or not rec.year or not rec.employee_id:
                continue
            
            last_day = calendar.monthrange(rec.year, rec.month)[1]
            date_from = f"{rec.year}-{rec.month:02d}-01"
            date_to = f"{rec.year}-{rec.month:02d}-{last_day:02d}"
            
            emp_records = records_by_employee.get(rec.employee_id.id, [])
            # فلترة حسب التاريخ المطلوب
            filtered = [r for r in emp_records if date_from <= r.date <= date_to]
            
            rec.total_days = len(filtered)
            rec.present_days = len([r for r in filtered if r.state == "present"])
            rec.late_days = len([r for r in filtered if r.state == "late"])
            rec.absent_days = len([r for r in filtered if r.state == "absent"])
            rec.approved_days = len([r for r in filtered if r.state == "approved"])
            rec.total_hours = sum(r.worked_hours for r in filtered)

    @api.model
    def generate_monthly_summary(self):
        """Cron: generate summary for last month automatically."""
        from datetime import date
        from dateutil.relativedelta import relativedelta

        last_month = date.today().replace(day=1) - relativedelta(months=1)
        month = last_month.month
        year = last_month.year

        employees = self.env["hr.employee"].search([("active", "=", True)])
        for employee in employees:
            existing = self.search([
                ("employee_id", "=", employee.id),
                ("month", "=", month),
                ("year", "=", year),
            ])
            if existing:
                existing._compute_summary()
            else:
                self.create({
                    "employee_id": employee.id,
                    "month": month,
                    "year": year,
                })

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import time, timedelta
import logging

_logger = logging.getLogger(__name__)

# =====================
# CONSTANTS
# =====================
WORK_START_TIME = time(9, 0)  # 9 AM
WORK_END_TIME = time(17, 0)   # 5 PM
MAX_WORK_HOURS = 24
MIN_WORK_HOURS = 0


class AttendanceRecord(models.Model):
    _name = "employee.attendance.record"
    _description = "Employee Attendance Record"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc"
    _rec_name = "employee_id"

    _sql_constraints = [
        (
            "unique_employee_date",
            "unique(employee_id, date)",
            "You already have an attendance record for this date.",
        )
    ]

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        ondelete="restrict",
        tracking=True,
        # ✅ FIX: ربط بـ hr.employee بدل res.users — أكتر احترافية وبيشمل كل الموظفين
        default=lambda self: self.env.user.employee_id,
    )

    date = fields.Date(
        string="Date",
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )

    check_in = fields.Datetime(string="Check In", tracking=True)
    check_out = fields.Datetime(string="Check Out", tracking=True)

    # ✅ NEW: Break Time
    break_start = fields.Datetime(string="Break Start", tracking=True)
    break_end = fields.Datetime(string="Break End", tracking=True)
    break_hours = fields.Float(
        string="Break Hours",
        compute="_compute_worked_hours",
        store=True,
    )

    worked_hours = fields.Float(
        string="Worked Hours",
        compute="_compute_worked_hours",
        store=True,
    )

    state = fields.Selection(
        [
            ("new", "New"),
            ("present", "Present"),
            ("late", "Late"),
            ("absent", "Absent"),
            ("approved", "Approved"),
        ],
        string="Status",
        default="new",
        tracking=True,
    )

    notes = fields.Text(string="Notes")

    # =====================
    # HELPERS
    # =====================
    def _is_manager(self):
        return self.user_has_groups("employee_attendance_management.group_attendance_manager")

    def _ensure_manager(self):
        if not self._is_manager():
            raise UserError(_("Only Attendance Managers can approve or mark absence."))

    def _is_late(self, dt_utc):
        """Compare against work start time in the user's timezone (not UTC)."""
        local_dt = fields.Datetime.context_timestamp(self, dt_utc)
        return local_dt.time() > WORK_START_TIME

    def _bypass_guards(self):
        """
        Allow module install/upgrade (XML data/demo), file import, cron/sudo operations.
        """
        ctx = self.env.context
        return bool(
            ctx.get("install_mode")  # during module install/upgrade incl. XML demo/data
            or ctx.get("import_file")  # during import
            or ctx.get("skip_attendance_guard")  # manual bypass if needed
            or self.env.su  # sudo/superuser operations (cron safe)
        )

    # =====================
    # COMPUTED METHODS
    # =====================
    @api.depends("check_in", "check_out", "break_start", "break_end")
    def _compute_worked_hours(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                total = (rec.check_out - rec.check_in).total_seconds() / 3600
                # ✅ NEW: خصم وقت الاستراحة
                break_h = 0.0
                if rec.break_start and rec.break_end and rec.break_end > rec.break_start:
                    break_h = (rec.break_end - rec.break_start).total_seconds() / 3600
                rec.break_hours = break_h
                rec.worked_hours = max(0.0, total - break_h)
            else:
                rec.break_hours = 0.0
                rec.worked_hours = 0.0

    # =====================
    # CONSTRAINTS
    # =====================
    @api.constrains("check_in", "check_out")
    def _check_dates(self):
        for rec in self:
            if rec.check_in and rec.check_out and rec.check_out < rec.check_in:
                raise UserError(_("Check-out cannot be before check-in."))

    @api.constrains("break_start", "break_end", "check_in", "check_out")
    def _check_break_times(self):
        """✅ NEW: التأكد من أن وقت الاستراحة داخل وقت العمل"""
        for rec in self:
            if rec.break_start and not rec.check_in:
                raise UserError(_("Cannot start break before checking in."))
            
            if rec.break_end and not rec.break_start:
                raise UserError(_("Cannot end break without starting it."))
            
            if rec.break_start and rec.check_in and rec.break_start < rec.check_in:
                raise UserError(_("Break cannot start before check-in time."))
            
            if rec.break_end and rec.check_out and rec.break_end > rec.check_out:
                raise UserError(_("Break cannot end after check-out time."))
            
            if rec.break_start and rec.break_end and rec.break_end <= rec.break_start:
                raise UserError(_("Break end time must be after break start time."))

    @api.constrains("worked_hours")
    def _check_worked_hours(self):
        """✅ NEW: التأكد من أن ساعات العمل منطقية"""
        for rec in self:
            if rec.worked_hours < MIN_WORK_HOURS:
                raise UserError(_("Worked hours cannot be negative."))
            if rec.worked_hours > MAX_WORK_HOURS:
                raise UserError(_(
                    "Worked hours cannot exceed %d hours in a day.\n"
                    "Current value: %.2f hours"
                ) % (MAX_WORK_HOURS, rec.worked_hours))

    # =====================
    # CREATE/WRITE GUARDS
    # =====================
    @api.model_create_multi
    def create(self, vals_list):
        # ✅ allow demo/sample XML and module install/upgrade/import/sudo/cron
        if self._bypass_guards():
            return super().create(vals_list)

        today = fields.Date.context_today(self)
        is_manager = self._is_manager()
        # ✅ FIX: نجيب الـ employee الخاص بالـ user الحالي
        current_employee = self.env.user.employee_id

        cleaned_vals_list = []
        for vals in vals_list:
            if not is_manager:
                # Users can only create their own record for today
                if vals.get("employee_id") and vals["employee_id"] != current_employee.id:
                    raise UserError(_("You can only create your own attendance record."))
                if vals.get("date") and vals["date"] != today:
                    raise UserError(_("You can only create attendance records for today."))

                # Prevent users from injecting check_in/check_out/state on create
                for k in ("check_in", "check_out", "state", "worked_hours"):
                    vals.pop(k, None)

                # force defaults
                vals["employee_id"] = current_employee.id
                vals["date"] = today
                vals["state"] = "new"

            cleaned_vals_list.append(vals)

        return super().create(cleaned_vals_list)

    def write(self, vals):
        # ✅ allow demo/sample XML and module install/upgrade/import/sudo/cron
        if self._bypass_guards():
            return super().write(vals)

        is_manager = self._is_manager()

        # Users cannot change employee/date/worked_hours
        if not is_manager and any(k in vals for k in ("employee_id", "date", "worked_hours")):
            raise UserError(_("You cannot change employee/date/worked hours manually."))

        # Guard state transitions
        if "state" in vals:
            if vals["state"] in ("approved", "absent"):
                self._ensure_manager()
            elif not is_manager and vals["state"] not in ("present", "late", "new"):
                raise UserError(_("Invalid status change."))

        # Users can only set check_in/check_out/state via buttons (context flag)
        if not is_manager and any(k in vals for k in ("check_in", "check_out", "state")):
            if not self.env.context.get("attendance_button"):
                raise UserError(_("Use Check In / Check Out buttons to update attendance."))

        return super().write(vals)

    # =====================
    # ONCHANGE (UI ONLY)
    # =====================
    @api.onchange("check_in")
    def _onchange_check_in(self):
        if self.check_in:
            self.state = "late" if self._is_late(self.check_in) else "present"

    # =====================
    # BUSINESS ACTIONS
    # =====================
    def action_check_in(self):
        self.ensure_one()

        # ✅ FIX: مقارنة بـ hr.employee بدل res.users
        if not self._is_manager() and self.employee_id != self.env.user.employee_id:
            raise UserError(_(
                "Permission Denied!\n\n"
                "You are trying to check in for %s, but you can only check in yourself.\n"
                "Current user: %s\n\n"
                "If you need to manage other employees' attendance, please contact your system administrator."
            ) % (self.employee_id.name, self.env.user.name))

        if not self._is_manager() and self.date != fields.Date.context_today(self):
            raise UserError(_(
                "Invalid Date!\n\n"
                "You can only check in for today.\n"
                "Record date: %s\n"
                "Today's date: %s"
            ) % (self.date, fields.Date.context_today(self)))

        if self.check_in:
            raise UserError(_("Already Checked In!\n\nYou are already checked in at %s.") % 
                          fields.Datetime.to_string(self.check_in))

        dt = fields.Datetime.now()
        new_state = "late" if self._is_late(dt) else "present"

        self.with_context(attendance_button=True).write({"check_in": dt, "state": new_state})

        # ✅ IMPROVED: Logging
        _logger.info(
            'Check-in recorded: Employee=%s, Date=%s, Time=%s, State=%s',
            self.employee_id.name,
            self.date,
            dt,
            new_state
        )

        if new_state == "late":
            # إرسال notification للموظف
            self.message_post(
                body=_("You checked in late at %s. Please try to arrive on time.") % 
                     fields.Datetime.to_string(dt),
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )
            
            # Activity للـ manager
            self.activity_schedule(
                "mail.mail_activity_data_warning",
                summary=_("Late Attendance"),
                note=_("%s checked in late at %s.") % (
                    self.employee_id.name,
                    fields.Datetime.to_string(dt)
                ),
                user_id=self.env.ref("base.user_admin").id,
            )

    def action_check_out(self):
        self.ensure_one()

        if not self.check_in:
            raise UserError(_("Cannot Check Out!\n\nYou must check in first before checking out."))

        if self.check_out:
            raise UserError(_("Already Checked Out!\n\nYou already checked out at %s.") % 
                          fields.Datetime.to_string(self.check_out))

        dt = fields.Datetime.now()

        # keep state as (present/late) and let manager approve
        self.with_context(attendance_button=True).write({"check_out": dt})

        if self.state not in ("present", "late"):
            self.with_context(attendance_button=True).write({"state": "present"})
        
        # ✅ IMPROVED: Logging
        _logger.info(
            'Check-out recorded: Employee=%s, Date=%s, Time=%s, Worked Hours=%.2f',
            self.employee_id.name,
            self.date,
            dt,
            self.worked_hours
        )
        
        # ✅ NEW: إرسال notification للموظف
        self.message_post(
            body=_("You checked out at %s. Total worked hours: %.2f") % 
                 (fields.Datetime.to_string(dt), self.worked_hours),
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )

    def action_approve(self):
        self.ensure_one()
        self._ensure_manager()

        if self.state not in ("present", "late"):
            raise UserError(_(
                "Cannot Approve!\n\n"
                "Only Present or Late attendance can be approved.\n"
                "Current status: %s"
            ) % dict(self._fields['state'].selection).get(self.state))

        # ✅ IMPROVED: Logging
        _logger.info(
            'Attendance approved: Employee=%s, Date=%s, Approved by=%s, Worked Hours=%.2f',
            self.employee_id.name,
            self.date,
            self.env.user.name,
            self.worked_hours
        )

        self.write({"state": "approved"})
        self.message_post(
            body=_("Attendance approved by %s on %s.\nWorked Hours: %.2f") % (
                self.env.user.name,
                fields.Datetime.now(),
                self.worked_hours
            ),
            message_type='notification'
        )

    # =====================
    # CRON JOBS
    # =====================
    @api.model
    def cron_mark_absent(self):
        """
        ✅ IMPROVED: Safest behavior - mark absence for yesterday (not 'today')
        Now excludes employees on approved leave
        """
        target_date = fields.Date.context_today(self) - timedelta(days=1)

        # ✅ FIX: نجيب hr.employee بدل res.users
        group = self.env.ref("employee_attendance_management.group_attendance_user")
        users = group.users.filtered(lambda u: u.active and not u.share)
        employees = users.mapped("employee_id").filtered(lambda e: e.active)

        # ✅ NEW: استبعد الموظفين في إجازة
        employees_on_leave = self.env['hr.employee']
        if self.env['ir.model'].search([('model', '=', 'hr.leave')], limit=1):
            # Check if hr.leave module is installed
            leave_obj = self.env['hr.leave']
            approved_leaves = leave_obj.search([
                ('state', '=', 'validate'),
                ('date_from', '<=', target_date),
                ('date_to', '>=', target_date),
            ])
            employees_on_leave = approved_leaves.mapped('employee_id')
            
            _logger.info(
                'Cron mark_absent: Found %d employees on leave for %s',
                len(employees_on_leave),
                target_date
            )

        existing_employee_ids = set(self.search([("date", "=", target_date)]).mapped("employee_id").ids)
        
        absent_count = 0
        for employee in employees:
            # Skip if already has record or is on leave
            if employee.id in existing_employee_ids:
                continue
            if employee in employees_on_leave:
                _logger.info(
                    'Skipping %s - on approved leave on %s',
                    employee.name,
                    target_date
                )
                continue
                
            self.sudo().create({
                "employee_id": employee.id, 
                "date": target_date, 
                "state": "absent"
            })
            absent_count += 1
        
        _logger.info(
            'Cron mark_absent completed: Marked %d employees as absent for %s',
            absent_count,
            target_date
        )

    @api.model
    def send_daily_report(self):
        """Send one summary email (yesterday) to Attendance Managers."""
        target_date = fields.Date.context_today(self) - timedelta(days=1)
        records = self.search([("date", "=", target_date)])

        managers = self.env.ref("employee_attendance_management.group_attendance_manager").users
        manager_emails = [u.email for u in managers if u.email]
        if not manager_emails:
            return

        counts = {st: 0 for st, _ in self._fields["state"].selection}
        for r in records:
            counts[r.state] = counts.get(r.state, 0) + 1

        state_label = dict(self._fields["state"].selection)

        rows = []
        for r in records:
            rows.append(
                f"<tr>"
                f"<td>{r.employee_id.name}</td>"
                f"<td>{r.date}</td>"
                f"<td>{state_label.get(r.state)}</td>"
                f"<td>{r.worked_hours:.2f}</td>"
                f"</tr>"
            )

        rows_html = "\n".join(rows) if rows else "<tr><td colspan='4'>No records</td></tr>"

        table = f"""
        <table border="1" cellpadding="6" cellspacing="0">
            <thead>
                <tr>
                    <th>Employee</th><th>Date</th><th>Status</th><th>Worked Hours</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        """

        body = f"""
        <h3>Daily Attendance Summary</h3>
        <p><b>Date:</b> {target_date}</p>
        <ul>
            <li>Present: {counts.get('present', 0)}</li>
            <li>Late: {counts.get('late', 0)}</li>
            <li>Absent: {counts.get('absent', 0)}</li>
            <li>Approved: {counts.get('approved', 0)}</li>
            <li>New: {counts.get('new', 0)}</li>
        </ul>
        {table}
        """

        mail = self.env["mail.mail"].create(
            {
                "subject": f"Daily Attendance Report - {target_date}",
                "body_html": body,
                "email_to": ",".join(manager_emails),
            }
        )
        mail.send()
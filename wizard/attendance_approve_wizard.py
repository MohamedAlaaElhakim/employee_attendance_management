from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AttendanceApproveWizard(models.TransientModel):
    _name = "attendance.approve.wizard"
    _description = "Approve Attendance Wizard"

    attendance_id = fields.Many2one(
        "employee.attendance.record",
        string="Attendance Record",
        required=True,
        readonly=True,
    )
    
    employee_name = fields.Char(
        related="attendance_id.employee_id.name",
        string="Employee",
        readonly=True,
    )
    
    date = fields.Date(
        related="attendance_id.date",
        string="Date",
        readonly=True,
    )
    
    worked_hours = fields.Float(
        related="attendance_id.worked_hours",
        string="Worked Hours",
        readonly=True,
    )

    note = fields.Text(string="Approval Note")
    
    send_email = fields.Boolean(
        string="Send Email Notification",
        default=True,
        help="Send approval notification to employee"
    )

    def action_confirm(self):
        """✅ IMPROVED: With email notification and logging"""
        self.ensure_one()

        if not self.user_has_groups("employee_attendance_management.group_attendance_manager"):
            raise UserError(_("Only Attendance Managers can approve attendance."))

        if self.attendance_id.state not in ("present", "late"):
            raise UserError(_(
                "Cannot Approve!\n\n"
                "Only Present or Late attendance can be approved.\n"
                "Current status: %s"
            ) % dict(self.attendance_id._fields['state'].selection).get(self.attendance_id.state))

        # Update note if provided
        vals = {"state": "approved"}
        if self.note:
            vals["notes"] = self.note
        
        self.attendance_id.write(vals)
        
        # ✅ Logging
        _logger.info(
            'Attendance approved via wizard: Employee=%s, Date=%s, Approved by=%s',
            self.attendance_id.employee_id.name,
            self.attendance_id.date,
            self.env.user.name
        )
        
        # ✅ Send email notification
        if self.send_email:
            template = self.env.ref(
                'employee_attendance_management.email_template_attendance_approved',
                raise_if_not_found=False
            )
            if template:
                template.send_mail(self.attendance_id.id, force_send=True)
                _logger.info('Approval email sent to %s', self.attendance_id.employee_id.name)
        
        # Post message in chatter
        message = _("Attendance approved by %s") % self.env.user.name
        if self.note:
            message += "\n\n" + _("Note: %s") % self.note
        
        self.attendance_id.message_post(
            body=message,
            message_type='notification'
        )
        
        return {'type': 'ir.actions.act_window_close'}
{
    "name": "Employee Attendance Management",
    "version": "2.0.0",
    "category": "Human Resources",
    "summary": "Comprehensive attendance tracking with check-in, break management, and approvals",
    "description": """
Employee Attendance Management System v2.0
==========================================

A professional Odoo module for managing employee attendance with advanced features.

Core Features:
--------------
* Employee check-in / check-out tracking
* Break time management with automatic deduction
* Worked hours calculation
* Late / absent / present status tracking
* Manager approval workflow with wizard
* Email notifications (late arrivals, approvals)
* Automated absence marking (cron job)
* Leave integration - excludes employees on approved leave
* Scheduled cron jobs for automation
* Professional PDF attendance reports

Analytics & Views:
-----------------
* Calendar view for visual planning
* Kanban view - mobile-friendly
* Graph view - bar charts and analysis
* Pivot view - cross-tabulation
* Monthly summary reports
* Chatter integration for communication

Advanced Features:
-----------------
* Activity tracking for late arrivals
* Comprehensive test suite (30+ tests)
* Performance optimized for large datasets
* Multi-level security (User/Manager roles)
* Detailed logging for audit trail
* Beautiful HTML email templates

Security:
--------
* Users can only manage their own attendance
* Managers have full access with approval rights
* SQL constraints prevent duplicate records
* Validation guards prevent data manipulation

Version 2.0.0 Improvements:
--------------------------
* Break time management
* Performance optimizations (batch processing)
* Enhanced email notifications
* Comprehensive test coverage
* Leave system integration
* Better error messages
* Improved mobile UI
* Full documentation (README, CHANGELOG)

    """,
    "author": "Mohamed Alaa",
    "website": "https://github.com/MohamedAlaaElakim",
    "depends": [
        "base",
        "mail",
        "hr",
        "hr_holidays",  # ✅ For leave integration
    ],
    "data": [
    "security/security.xml",
    "security/ir.model.access.csv",

    # wizards الأول
    "wizard/attendance_approve_wizard_views.xml",

    # reports قبل views عشان الـ action يبقى موجود وقت قراءة الـ view
    "reports/attendance_report.xml",
    "reports/attendance_report_template.xml",

    # بعدهم views
    "views/attendance_record_views.xml",
    "views/attendance_summary_views.xml",

    # ثم data
    "data/mail_template.xml",
    "data/attendance_cron.xml",
],
"demo": [
    "demo/attendance_demo.xml",
],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
    "images": ["static/description/banner.png"],
    "support": "contact@example.com",
}
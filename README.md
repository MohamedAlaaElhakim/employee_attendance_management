# Employee Attendance Management Module

## 📋 Overview

A comprehensive Odoo module for managing employee attendance with features including check-in/check-out tracking, break time management, approval workflows, automated absence marking, and detailed reporting.

## ✨ Features

### Core Features
- ✅ **Employee Check-in/Check-out** - Track employee arrival and departure times
- ✅ **Automatic Late Detection** - Identifies late arrivals (after 9:00 AM)
- ✅ **Break Time Management** - Track and deduct break periods from worked hours
- ✅ **Worked Hours Calculation** - Automatic calculation with break deduction
- ✅ **State Management** - New, Present, Late, Absent, Approved states
- ✅ **Multi-level Security** - User and Manager roles with appropriate permissions

### Advanced Features
- ✅ **Approval Workflow** - Manager approval with wizard interface
- ✅ **Email Notifications** - Automated emails for late arrivals and approvals
- ✅ **Activity Tracking** - Activities created for late check-ins
- ✅ **Automated Absence Marking** - Cron job marks absent employees daily
- ✅ **Leave Integration** - Excludes employees on approved leave from absence marking
- ✅ **Monthly Summary Reports** - Automated monthly attendance summaries
- ✅ **PDF Reports** - Professional attendance reports with QWeb

### Analytics & Views
- ✅ **Calendar View** - Visual calendar display of attendance
- ✅ **Kanban View** - Mobile-friendly card-based view
- ✅ **Graph View** - Bar charts for attendance analysis
- ✅ **Pivot View** - Cross-tabulation for advanced analysis
- ✅ **Chatter Integration** - Full communication history per record

## 🚀 Installation

### Requirements
- Odoo 15.0+ (tested on Odoo 15.0, 16.0, 17.0)
- Python 3.8+
- Dependencies: `base`, `mail`, `hr`, `hr_holidays`

### Installation Steps

1. **Download the module**
   ```bash
   cd /path/to/odoo/addons
   git clone <repository-url> employee_attendance_management
   ```

2. **Update Apps List**
   - Go to Apps menu in Odoo
   - Click "Update Apps List"
   - Search for "Employee Attendance Management"

3. **Install the module**
   - Click "Install" button

## 📖 Usage Guide

### For Employees

#### Daily Check-in/Check-out
1. Navigate to **Attendance → Attendance Records**
2. The system creates a new record for today automatically
3. Click **Check In** button when you arrive
4. Click **Check Out** button when you leave
5. Your worked hours are calculated automatically

#### Break Time
- During your work day, you can record breaks:
  - Set **Break Start** when you begin your break
  - Set **Break End** when you return
  - Break time is automatically deducted from worked hours

### For Managers

#### Approving Attendance
1. Go to **Attendance → Attendance Records**
2. Filter by "Present" or "Late" status
3. Open the attendance record
4. Click **Approve** button
5. In the wizard:
   - Review employee details
   - Add approval notes (optional)
   - Choose to send email notification
   - Click **Approve**

#### Viewing Reports
- **Monthly Summary**: View aggregated monthly data per employee
- **PDF Reports**: Export attendance records to PDF
- **Analytics**: Use Graph/Pivot views for insights

### For Administrators

#### Configuration
1. **User Groups**:
   - `Attendance User` - Regular employees
   - `Attendance Manager` - HR/Managers with approval rights

2. **Cron Jobs**:
   - **Mark Absent Employees**: Runs daily, marks yesterday's absences
   - **Generate Monthly Summary**: Runs monthly, creates summary reports

3. **Email Templates**:
   - Late Check-in Notification
   - Attendance Approved Notification
   - Daily Report to Managers

## 🔒 Security

### Record Rules
- **Users**: Can only view/edit their own attendance records
- **Managers**: Can view/edit all attendance records
- **Users cannot**:
  - Delete records
  - Change employee or date
  - Manually modify worked hours
  - Approve attendance (manager-only)

### Access Rights
| Group | Model | Read | Write | Create | Delete |
|-------|-------|------|-------|--------|--------|
| User | Attendance Record | ✅ | ✅ | ✅ | ❌ |
| Manager | Attendance Record | ✅ | ✅ | ✅ | ✅ |
| Manager | Attendance Summary | ✅ | ✅ | ✅ | ✅ |

## 📊 Data Model

### Main Models

#### employee.attendance.record
Main attendance tracking model with fields:
- `employee_id` - Link to hr.employee
- `date` - Attendance date
- `check_in` - Check-in datetime
- `check_out` - Check-out datetime
- `break_start` - Break start datetime
- `break_end` - Break end datetime
- `break_hours` - Computed break duration
- `worked_hours` - Computed work duration (with break deduction)
- `state` - Status (new/present/late/absent/approved)
- `notes` - Additional notes

#### employee.attendance.summary
Monthly aggregation model with fields:
- `employee_id` - Link to hr.employee
- `month` - Month number (1-12)
- `year` - Year
- `total_days` - Total attendance days
- `present_days` - Days marked present
- `late_days` - Days marked late
- `absent_days` - Days marked absent
- `approved_days` - Days approved
- `total_hours` - Sum of worked hours

## 🔧 Customization

### Changing Work Start Time
Edit the constant in `models/attendance_record.py`:
```python
WORK_START_TIME = time(9, 0)  # Change to your work start time
```

### Customizing Email Templates
Navigate to **Settings → Technical → Email Templates** and edit:
- Late Check-In Notification
- Attendance Approved Notification

### Adding Custom States
Extend the `state` selection field in `attendance_record.py`:
```python
state = fields.Selection([
    ('new', 'New'),
    ('present', 'Present'),
    ('late', 'Late'),
    ('absent', 'Absent'),
    ('approved', 'Approved'),
    ('custom_state', 'Custom State'),  # Add your state
], ...)
```

## 🧪 Testing

### Running Tests
```bash
# Run all attendance tests
odoo-bin -d your_database -i employee_attendance_management --test-tags attendance

# Run specific test file
odoo-bin -d your_database --test-file=addons/employee_attendance_management/tests/test_attendance_record.py
```

### Test Coverage
- ✅ Check-in/Check-out flow
- ✅ Late arrival detection
- ✅ Break time calculations
- ✅ Validations and constraints
- ✅ Manager approval workflow
- ✅ Security and permissions
- ✅ Cron job execution
- ✅ Monthly summary generation
- ✅ Performance tests

## 📈 Performance Optimizations

### Implemented Optimizations
1. **Batch Processing** - Monthly summaries use single query for multiple employees
2. **Computed Field Caching** - Store=True for expensive calculations
3. **Indexed Fields** - SQL constraints create automatic indexes
4. **Efficient Filtering** - Use of mapped() and filtered() for in-memory operations

### Performance Tips
- Use filters in search views instead of loading all records
- Schedule cron jobs during off-peak hours
- Archive old attendance records annually
- Use graph/pivot views with appropriate date ranges

## 🐛 Troubleshooting

### Common Issues

#### "You can only check in yourself"
- **Cause**: User trying to check in for another employee
- **Solution**: Each employee can only manage their own attendance

#### "Already checked in"
- **Cause**: Attempting to check in twice
- **Solution**: Use check-out instead, or cancel existing check-in

#### Break validation errors
- **Cause**: Break times outside work hours
- **Solution**: Ensure break times are between check-in and check-out

#### Cron not running
- **Cause**: Cron jobs disabled or incorrect schedule
- **Solution**: Check Settings → Technical → Scheduled Actions

## 🔄 Migration Guide

### From v1.0.0 to v2.0.0
1. Backup your database
2. Update the module code
3. Run upgrade:
   ```bash
   odoo-bin -d your_database -u employee_attendance_management
   ```
4. Clear browser cache
5. Test in staging environment first

## 📝 Changelog

### Version 2.0.0 (2026-02-27)
- ✅ Added break time management
- ✅ Improved performance in monthly summaries
- ✅ Added comprehensive test suite
- ✅ Integrated with hr_holidays module
- ✅ Enhanced email notifications
- ✅ Added Kanban view for mobile
- ✅ Improved error messages
- ✅ Added logging throughout
- ✅ Better security validations

### Version 1.0.0 (2024-01-01)
- Initial release
- Basic check-in/check-out functionality
- Manager approval workflow
- Daily absence marking
- Monthly summary reports

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new features
4. Ensure all tests pass
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings to all methods
- Include comments for complex logic

## 📄 License

This module is licensed under LGPL-3.

## 👥 Credits

**Author**: Mohamed Alaa  
**Website**: https://github.com/MohamedAlaaElakim  
**Email**: contact@example.com

## 📞 Support

For support, please:
1. Check this README
2. Review the [Odoo Documentation](https://www.odoo.com/documentation)
3. Open an issue on GitHub
4. Contact the module author

## 🗺️ Roadmap

### Planned Features
- [ ] Mobile app integration
- [ ] Biometric device integration
- [ ] Shift management
- [ ] Overtime calculation
- [ ] GPS location tracking
- [ ] Dashboard widgets
- [ ] Advanced analytics
- [ ] Multi-company support
- [ ] Custom work schedules per employee
- [ ] Holiday calendar integration

## 🙏 Acknowledgments

- Odoo Community Association (OCA)
- Odoo SA for the framework
- All contributors and testers

---

**Made with ❤️ for the Odoo Community**

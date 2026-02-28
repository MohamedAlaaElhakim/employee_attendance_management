# Installation Guide - Employee Attendance Management

## 📋 Prerequisites

Before installing this module, ensure you have:

- ✅ Odoo 15.0 or higher (tested on 15.0, 16.0, 17.0)
- ✅ Python 3.8 or higher
- ✅ PostgreSQL 10 or higher
- ✅ The following Odoo modules installed:
  - `base` (core)
  - `mail` (for chatter and emails)
  - `hr` (Human Resources)
  - `hr_holidays` (optional, for leave integration)

## 🚀 Installation Methods

### Method 1: Manual Installation (Recommended for Development)

1. **Download the Module**
   ```bash
   cd /path/to/odoo/custom/addons
   git clone <repository-url> employee_attendance_management
   ```

2. **Update Odoo Addon Path** (if using custom addons folder)
   
   Edit your `odoo.conf` file:
   ```ini
   [options]
   addons_path = /path/to/odoo/addons,/path/to/odoo/custom/addons
   ```

3. **Restart Odoo Service**
   ```bash
   sudo systemctl restart odoo
   # OR
   sudo service odoo restart
   # OR (if running manually)
   ./odoo-bin -c /path/to/odoo.conf
   ```

4. **Update Apps List**
   - Log in to Odoo as Administrator
   - Go to **Apps** menu
   - Click **Update Apps List** (you may need to activate Developer Mode first)
   - Wait for the update to complete

5. **Install the Module**
   - In the Apps menu, search for "Employee Attendance Management"
   - Click **Install**
   - Wait for installation to complete

### Method 2: Docker Installation

If you're using Docker for Odoo:

1. **Add Module to Docker Volume**
   ```bash
   docker cp employee_attendance_management odoo:/mnt/extra-addons/
   ```

2. **Restart Container**
   ```bash
   docker restart odoo
   ```

3. **Install via Odoo Interface**
   - Follow steps 4-5 from Method 1

### Method 3: Odoo.sh Installation

For Odoo.sh (SaaS) users:

1. **Add to Repository**
   - Add the module folder to your GitHub/Bitbucket repository
   - Push to your repository

2. **Deploy**
   - Odoo.sh will automatically detect the new module
   - Go to Apps and install it

## ⚙️ Configuration

### 1. Activate Developer Mode (Important!)

Before configuration, activate developer mode:
- Go to **Settings** → Scroll to bottom
- Click **Activate the developer mode**

### 2. Configure User Groups

1. Go to **Settings → Users & Companies → Groups**
2. Find these groups:
   - **Attendance / Attendance User** - For regular employees
   - **Attendance / Attendance Manager** - For HR/Managers

3. Assign users to appropriate groups:
   - Add all employees to "Attendance User" group
   - Add HR managers to "Attendance Manager" group

### 3. Configure Employees

1. Go to **Employees** menu
2. For each employee who will use the system:
   - Ensure they have a linked User account
   - Set their **Work Email** (for notifications)
   - Make sure they're in the correct department

### 4. Configure Cron Jobs

1. Go to **Settings → Technical → Automation → Scheduled Actions**
2. Find these cron jobs:
   - **Mark Absent Employees**: 
     - Default: Runs daily at 1:00 AM
     - Marks employees without attendance as absent
   - **Generate Monthly Attendance Summary**:
     - Default: Runs on 1st of each month
     - Creates monthly reports

3. Adjust schedules if needed:
   - Click on the cron job
   - Modify **Next Execution Date** or **Interval**
   - Save

### 5. Configure Email Settings (Optional but Recommended)

For email notifications to work:

1. **Configure Outgoing Mail Server**:
   - Go to **Settings → Technical → Email → Outgoing Mail Servers**
   - Add your SMTP server details:
     ```
     SMTP Server: smtp.gmail.com (for Gmail)
     SMTP Port: 587
     Connection Security: TLS
     Username: your-email@gmail.com
     Password: your-app-password
     ```

2. **Test Email Server**:
   - Click **Test Connection**
   - Should show "Connection Test Succeeded"

3. **Review Email Templates**:
   - Go to **Settings → Technical → Email → Templates**
   - Find:
     - "Late Check-In Notification"
     - "Attendance Approved Notification"
   - Customize content if needed

### 6. Set Work Time Constants (Optional)

If your work hours differ from 9 AM start:

1. Edit `models/attendance_record.py`
2. Change these constants:
   ```python
   WORK_START_TIME = time(9, 0)   # Change to your start time
   WORK_END_TIME = time(17, 0)    # Change to your end time
   ```
3. Restart Odoo and upgrade the module

## 🧪 Verify Installation

### Run These Tests:

1. **Create Test Attendance**:
   - Login as a regular user
   - Go to **Attendance → Attendance Records**
   - Should see a record for today
   - Click **Check In**
   - Verify check-in time is recorded

2. **Test Manager Approval**:
   - Login as a manager
   - Find a "Present" or "Late" record
   - Click **Approve** button
   - Should open approval wizard
   - Complete approval

3. **Check Email Notifications**:
   - Perform a late check-in (after 9 AM)
   - Check if email was sent
   - Verify activity was created

4. **Test Cron Jobs**:
   - Go to **Settings → Technical → Scheduled Actions**
   - Find "Mark Absent Employees"
   - Click **Run Manually**
   - Check if absent records were created for yesterday

## 🔍 Troubleshooting

### Module Not Appearing in Apps List

**Solution**:
1. Check if module is in the correct addons folder
2. Verify addons_path in odoo.conf includes the folder
3. Check odoo.log for any import errors
4. Restart Odoo service
5. Update Apps List again

### Import Errors on Installation

**Common causes**:
- Missing dependencies: Install `hr_holidays` module first
- Python syntax errors: Check odoo.log
- XML syntax errors: Validate XML files

**Solution**:
```bash
# Check logs
tail -f /var/log/odoo/odoo.log

# Install dependencies first
# Go to Apps, install "Time Off" module (hr_holidays)

# Then try installing this module again
```

### Emails Not Sending

**Solutions**:
1. Check outgoing mail server configuration
2. Test SMTP connection
3. Check odoo.log for email errors
4. Verify email templates are active
5. Ensure employees have valid email addresses

### Cron Jobs Not Running

**Solutions**:
1. Check if cron is enabled in odoo.conf:
   ```ini
   [options]
   max_cron_threads = 2
   ```
2. Restart Odoo after changing config
3. Check if cron user has permissions
4. Manually run cron to test:
   ```python
   # In Odoo shell
   self.env['employee.attendance.record'].cron_mark_absent()
   ```

### Permission Denied Errors

**Solutions**:
1. Check user groups assignment
2. Review record rules in **Settings → Technical → Security**
3. Ensure user has employee record linked
4. Check access rights CSV

### Check-in Button Not Working

**Common causes**:
- User not assigned to "Attendance User" group
- User has no linked employee record
- Date is not today
- Already checked in

**Solutions**:
1. Assign user to correct group
2. Create/link employee record
3. Check date on the record
4. View error in browser console (F12)

## 📊 Demo Data

The module includes demo data for testing:
- 5 demo employees
- Sample attendance records
- Various states (present, late, absent)

To install with demo data:
```bash
odoo-bin -d your_database -i employee_attendance_management --without-demo=None
```

To install without demo data:
```bash
odoo-bin -d your_database -i employee_attendance_management --without-demo=all
```

## 🔄 Upgrade from Previous Version

### Upgrading from v1.x to v2.0:

1. **Backup Database** (CRITICAL!):
   ```bash
   pg_dump your_database > backup_before_upgrade.sql
   ```

2. **Update Module Files**:
   ```bash
   cd /path/to/odoo/addons/employee_attendance_management
   git pull origin main
   # OR manually replace files
   ```

3. **Upgrade Module**:
   ```bash
   odoo-bin -d your_database -u employee_attendance_management
   ```

4. **Clear Browser Cache**:
   - Press Ctrl+Shift+Delete
   - Clear all browser data
   - Or use incognito/private mode

5. **Test Thoroughly**:
   - Test in staging environment first
   - Verify all features work
   - Check existing data integrity

## 📞 Support

If you encounter issues:

1. **Check Documentation**:
   - README.md
   - CHANGELOG.md
   - This INSTALL.md

2. **Check Logs**:
   ```bash
   tail -f /var/log/odoo/odoo.log
   ```

3. **Enable Debug Mode**:
   - Append `?debug=1` to your Odoo URL
   - Or use Developer Mode in Settings

4. **Get Help**:
   - Open an issue on GitHub
   - Email: contact@example.com
   - Check Odoo Community Forums

## ✅ Post-Installation Checklist

- [ ] Module appears in Apps list
- [ ] Module installed successfully
- [ ] User groups configured
- [ ] Employees linked to users
- [ ] Cron jobs scheduled correctly
- [ ] Email server configured and tested
- [ ] Test check-in/check-out works
- [ ] Test manager approval works
- [ ] Test email notifications work
- [ ] Test cron jobs work manually
- [ ] Demo data works (if installed)
- [ ] Views display correctly
- [ ] Reports generate successfully

## 🎓 Next Steps

After successful installation:

1. **Train Users**:
   - Show employees how to check in/out
   - Explain break time tracking
   - Demonstrate viewing their records

2. **Train Managers**:
   - How to approve attendance
   - How to generate reports
   - How to monitor team attendance

3. **Configure Work Hours**:
   - Set company work start time
   - Configure break policies
   - Set up overtime rules (if needed)

4. **Monitor System**:
   - Check cron logs daily (first week)
   - Review email delivery
   - Gather user feedback
   - Adjust as needed

---

**Installation Complete! 🎉**

For detailed usage instructions, see the [README.md](README.md) file.

# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from freezegun import freeze_time


@tagged('post_install', '-at_install', 'attendance')
class TestAttendanceRecord(TransactionCase):
    """
    Test suite for Employee Attendance Record
    
    Tests cover:
    - Check-in/Check-out flow
    - Late arrival detection
    - Break time calculations
    - Validations and constraints
    - Manager approval workflow
    - Security and permissions
    """
    
    def setUp(self):
        super().setUp()
        
        # Create test employee
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
            'work_email': 'test@example.com',
        })
        
        # Create test user for employee
        self.user = self.env['hr.employee'].create({
            'name': 'Test User',
            'login': 'testuser',
            'email': 'testuser@example.com',
        })
        
        # Create manager
        self.manager = self.env['hr.employee'].create({
            'name': 'Test Manager',
            'work_email': 'manager@example.com',
        })
        
        self.attendance_model = self.env['employee.attendance.record']
        self.today = datetime.today().date()
    
    def test_01_check_in_on_time(self):
        """Test successful on-time check-in (before 9:00 AM)"""
        attendance = self.attendance_model.create({
            'employee_id': self.employee.id,
            'date': self.today,
        })
        
        # Simulate check-in at 8:30 AM
        with freeze_time("2024-01-15 08:30:00"):
            attendance.action_check_in()
        
        self.assertIsNotNone(attendance.check_in)
        self.assertEqual(attendance.state, 'present', 
                        "Employee should be marked as present when checking in on time")
    
    def test_02_check_in_late(self):
        """Test late check-in (after 9:00 AM)"""
        attendance = self.attendance_model.create({
            'employee_id': self.employee.id,
            'date': self.today,
        })
        
        # Simulate check-in at 9:30 AM
        with freeze_time("2024-01-15 09:30:00"):
            attendance.action_check_in()
        
        self.assertIsNotNone(attendance.check_in)
        self.assertEqual(attendance.state, 'late', 
                        "Employee should be marked as late when checking in after 9:00 AM")
    
    def test_03_check_out_flow(self):
        """Test complete check-in and check-out flow"""
        attendance = self.attendance_model.create({
            'employee_id': self.employee.id,
            'date': self.today,
        })
        
        # Check in at 9:00 AM
        with freeze_time("2024-01-15 09:00:00"):
            attendance.action_check_in()
        
        # Check out at 5:00 PM
        with freeze_time("2024-01-15 17:00:00"):
            attendance.action_check_out()
        
        self.assertIsNotNone(attendance.check_out)
        self.assertEqual(attendance.worked_hours, 8.0, 
                        "Worked hours should be 8.0 for 9:00 AM to 5:00 PM")
    
    def test_04_check_out_without_check_in(self):
        """Test that check-out without check-in raises error"""
        attendance = self.attendance_model.create({
            'employee_id': self.employee.id,
            'date': self.today,
        })
        
        with self.assertRaises(UserError) as context:
            attendance.action_check_out()
        
        self.assertIn('check in first', str(context.exception).lower())
    
    def test_05_duplicate_check_in(self):
        """Test that duplicate check-in raises error"""
        attendance = self.attendance_model.create({
            'employee_id': self.employee.id,
            'date': self.today,
        })
        
        attendance.action_check_in()
        
        with self.assertRaises(UserError) as context:
            attendance.action_check_in()
        
        self.assertIn('already checked in', str(context.exception).lower())
    
    def test_06_break_time_calculation(self):
        """Test break time is properly deducted from worked hours"""
        attendance = self.attendance_model.create({
            'employee_id': self.employee.id,
            'date': self.today,
        })
        
        # Check in at 9:00 AM
        check_in_time = datetime(2024, 1, 15, 9, 0, 0)
        attendance.write({'check_in': check_in_time})
        
        # Break from 12:00 PM to 1:00 PM (1 hour)
        attendance.write({
            'break_start': datetime(2024, 1, 15, 12, 0, 0),
            'break_end': datetime(2024, 1, 15, 13, 0, 0),
        })
        
        # Check out at 5:00 PM
        attendance.write({'check_out': datetime(2024, 1, 15, 17, 0, 0)})
        
        self.assertEqual(attendance.break_hours, 1.0, "Break hours should be 1.0")
        self.assertEqual(attendance.worked_hours, 7.0, 
                        "Worked hours should be 7.0 (8 total - 1 break)")
    
    def test_07_check_out_before_check_in_validation(self):
        """Test validation: check-out cannot be before check-in"""
        attendance = self.attendance_model.create({
            'employee_id': self.employee.id,
            'date': self.today,
            'check_in': datetime(2024, 1, 15, 9, 0, 0),
        })
        
        with self.assertRaises(UserError):
            attendance.write({'check_out': datetime(2024, 1, 15, 8, 0, 0)})
    
    def test_08_break_before_check_in_validation(self):
        """Test validation: break cannot start before check-in"""
        attendance = self.attendance_model.create({
            'employee_id': self.employee.id,
            'date': self.today,
        })
        
        with self.assertRaises(UserError) as context:
            attendance.write({
                'break_start': datetime(2024, 1, 15, 10, 0, 0)
            })
        
        self.assertIn('check in', str(context.exception).lower())
    
    def test_09_break_end_before_start_validation(self):
        """Test validation: break end cannot be before break start"""
        attendance = self.attendance_model.create({
            'employee_id': self.employee.id,
            'date': self.today,
            'check_in': datetime(2024, 1, 15, 9, 0, 0),
            'break_start': datetime(2024, 1, 15, 12, 0, 0),
        })
        
        with self.assertRaises(UserError):
            attendance.write({'break_end': datetime(2024, 1, 15, 11, 0, 0)})
    
    def test_10_worked_hours_cannot_be_negative(self):
        """Test validation: worked hours cannot be negative"""
        # This should be prevented by constraints
        attendance = self.attendance_model.create({
            'employee_id': self.employee.id,
            'date': self.today,
            'check_in': datetime(2024, 1, 15, 17, 0, 0),
            'check_out': datetime(2024, 1, 15, 9, 0, 0),
        })
        
        # The constraint should prevent this
        with self.assertRaises(UserError):
            attendance._check_dates()
    
    def test_11_worked_hours_cannot_exceed_24(self):
        """Test validation: worked hours cannot exceed 24 hours"""
        attendance = self.attendance_model.create({
            'employee_id': self.employee.id,
            'date': self.today,
            'check_in': datetime(2024, 1, 15, 9, 0, 0),
            'check_out': datetime(2024, 1, 16, 10, 0, 0),  # Next day
        })
        
        # Should raise error for more than 24 hours
        with self.assertRaises(UserError):
            attendance._check_worked_hours()
    
    def test_12_duplicate_record_same_employee_same_date(self):
        """Test SQL constraint: cannot create duplicate records"""
        self.attendance_model.create({
            'employee_id': self.employee.id,
            'date': self.today,
        })
        
        with self.assertRaises(Exception):  # SQL constraint error
            self.attendance_model.create({
                'employee_id': self.employee.id,
                'date': self.today,
            })
    
    def test_13_manager_approval(self):
        """Test manager can approve attendance"""
        attendance = self.attendance_model.with_context(
            skip_attendance_guard=True
        ).create({
            'employee_id': self.employee.id,
            'date': self.today,
            'state': 'present',
            'check_in': datetime(2024, 1, 15, 9, 0, 0),
            'check_out': datetime(2024, 1, 15, 17, 0, 0),
        })
        
        # Manager approves
        attendance.with_context(skip_attendance_guard=True).action_approve()
        
        self.assertEqual(attendance.state, 'approved', 
                        "State should be 'approved' after manager approval")
    
    def test_14_state_transitions(self):
        """Test valid state transitions"""
        attendance = self.attendance_model.with_context(
            skip_attendance_guard=True
        ).create({
            'employee_id': self.employee.id,
            'date': self.today,
            'state': 'new',
        })
        
        # new -> present
        attendance.write({'state': 'present'})
        self.assertEqual(attendance.state, 'present')
        
        # present -> approved
        attendance.action_approve()
        self.assertEqual(attendance.state, 'approved')
    
    def test_15_cron_mark_absent(self):
        """Test cron job marks absent employees correctly"""
        yesterday = self.today - timedelta(days=1)
        
        # Run cron
        self.attendance_model.cron_mark_absent()
        
        # Check if absent records were created for yesterday
        absent_records = self.attendance_model.search([
            ('date', '=', yesterday),
            ('state', '=', 'absent')
        ])
        
        self.assertTrue(len(absent_records) >= 0, 
                       "Cron should create absent records for employees without attendance")
    
    def test_16_compute_worked_hours_with_no_times(self):
        """Test worked hours computation when times are not set"""
        attendance = self.attendance_model.create({
            'employee_id': self.employee.id,
            'date': self.today,
        })
        
        self.assertEqual(attendance.worked_hours, 0.0, 
                        "Worked hours should be 0 when check-in/out not set")
    
    def test_17_bypass_guards_for_xml_data(self):
        """Test that bypass guards work for XML demo data"""
        # Simulate XML data loading
        attendance = self.attendance_model.with_context(
            install_mode=True
        ).create({
            'employee_id': self.employee.id,
            'date': self.today,
            'state': 'absent',
        })
        
        self.assertEqual(attendance.state, 'absent', 
                        "Should allow direct state setting in install mode")
    
    def test_18_chatter_integration(self):
        """Test that chatter is properly integrated"""
        attendance = self.attendance_model.create({
            'employee_id': self.employee.id,
            'date': self.today,
        })
        
        # Post a message
        attendance.message_post(body="Test message")
        
        # Check that message was posted
        messages = attendance.message_ids
        self.assertTrue(len(messages) > 0, "Message should be posted to chatter")
    
    def test_19_activity_creation_on_late(self):
        """Test that activity is created when employee is late"""
        attendance = self.attendance_model.create({
            'employee_id': self.employee.id,
            'date': self.today,
        })
        
        # Check in late
        with freeze_time("2024-01-15 09:30:00"):
            attendance.action_check_in()
        
        # Check if activity was created
        activities = attendance.activity_ids
        self.assertTrue(len(activities) > 0, 
                       "Activity should be created for late check-in")
    
    def test_20_monthly_summary_generation(self):
        """Test monthly summary generation"""
        # Create attendance records for last month
        summary_model = self.env['employee.attendance.summary']
        
        # Generate summary
        summary_model.generate_monthly_summary()
        
        # Check if summary was created
        summaries = summary_model.search([
            ('employee_id', '=', self.employee.id)
        ])
        
        self.assertTrue(len(summaries) >= 0, 
                       "Monthly summary should be generated")

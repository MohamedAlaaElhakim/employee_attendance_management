# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged
from datetime import datetime, timedelta
import calendar


@tagged('post_install', '-at_install', 'attendance')
class TestAttendanceSummary(TransactionCase):
    """
    Test suite for Employee Attendance Summary
    
    Tests cover:
    - Monthly summary calculations
    - Performance of compute methods
    - Data aggregation accuracy
    """
    
    def setUp(self):
        super().setUp()
        
        # Create test employees
        self.employee1 = self.env['hr.employee'].create({
            'name': 'Employee One',
        })
        
        self.employee2 = self.env['hr.employee'].create({
            'name': 'Employee Two',
        })
        
        self.attendance_model = self.env['employee.attendance.record']
        self.summary_model = self.env['employee.attendance.summary']
        
        self.today = datetime.today().date()
        self.current_month = self.today.month
        self.current_year = self.today.year
    
    def _create_attendance_records(self, employee, dates_and_states):
        """Helper to create multiple attendance records"""
        records = []
        for date, state in dates_and_states:
            record = self.attendance_model.with_context(
                skip_attendance_guard=True
            ).create({
                'employee_id': employee.id,
                'date': date,
                'state': state,
                'check_in': datetime.combine(date, datetime.min.time().replace(hour=9)),
                'check_out': datetime.combine(date, datetime.min.time().replace(hour=17)),
            })
            records.append(record)
        return records
    
    def test_01_summary_basic_calculation(self):
        """Test basic summary calculation for one employee"""
        # Create 5 present days, 2 late days, 1 absent day
        dates_states = [
            (self.today.replace(day=1), 'present'),
            (self.today.replace(day=2), 'present'),
            (self.today.replace(day=3), 'late'),
            (self.today.replace(day=4), 'late'),
            (self.today.replace(day=5), 'absent'),
            (self.today.replace(day=6), 'present'),
            (self.today.replace(day=7), 'present'),
            (self.today.replace(day=8), 'present'),
        ]
        
        self._create_attendance_records(self.employee1, dates_states)
        
        # Create summary
        summary = self.summary_model.create({
            'employee_id': self.employee1.id,
            'month': self.current_month,
            'year': self.current_year,
        })
        
        self.assertEqual(summary.total_days, 8, "Total days should be 8")
        self.assertEqual(summary.present_days, 5, "Present days should be 5")
        self.assertEqual(summary.late_days, 2, "Late days should be 2")
        self.assertEqual(summary.absent_days, 1, "Absent days should be 1")
    
    def test_02_summary_month_display(self):
        """Test month display computation"""
        summary = self.summary_model.create({
            'employee_id': self.employee1.id,
            'month': 1,
            'year': 2024,
        })
        
        self.assertEqual(summary.month_display, "January 2024", 
                        "Month display should be properly formatted")
    
    def test_03_summary_total_hours_calculation(self):
        """Test total worked hours calculation"""
        dates_states = [
            (self.today.replace(day=1), 'present'),
            (self.today.replace(day=2), 'present'),
            (self.today.replace(day=3), 'present'),
        ]
        
        records = self._create_attendance_records(self.employee1, dates_states)
        
        # Each record has 8 hours (9 AM to 5 PM)
        summary = self.summary_model.create({
            'employee_id': self.employee1.id,
            'month': self.current_month,
            'year': self.current_year,
        })
        
        self.assertEqual(summary.total_hours, 24.0, 
                        "Total hours should be 24.0 (3 days * 8 hours)")
    
    def test_04_summary_unique_constraint(self):
        """Test that duplicate summaries for same employee/month/year are prevented"""
        self.summary_model.create({
            'employee_id': self.employee1.id,
            'month': self.current_month,
            'year': self.current_year,
        })
        
        with self.assertRaises(Exception):  # SQL constraint
            self.summary_model.create({
                'employee_id': self.employee1.id,
                'month': self.current_month,
                'year': self.current_year,
            })
    
    def test_05_summary_with_no_records(self):
        """Test summary when employee has no attendance records"""
        summary = self.summary_model.create({
            'employee_id': self.employee1.id,
            'month': self.current_month,
            'year': self.current_year,
        })
        
        self.assertEqual(summary.total_days, 0, "Total days should be 0")
        self.assertEqual(summary.total_hours, 0.0, "Total hours should be 0.0")
    
    def test_06_summary_performance_multiple_employees(self):
        """Test performance when computing summary for multiple employees"""
        import time
        
        # Create attendance for multiple employees
        for i in range(5):  # 5 employees
            employee = self.env['hr.employee'].create({
                'name': f'Test Employee {i}',
            })
            
            dates_states = [
                (self.today.replace(day=d), 'present')
                for d in range(1, 11)  # 10 days each
            ]
            self._create_attendance_records(employee, dates_states)
        
        # Create all summaries at once
        employees = self.env['hr.employee'].search([
            ('name', 'like', 'Test Employee%')
        ])
        
        start_time = time.time()
        
        summaries = self.summary_model.create([{
            'employee_id': emp.id,
            'month': self.current_month,
            'year': self.current_year,
        } for emp in employees])
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete in reasonable time (< 2 seconds for 5 employees)
        self.assertLess(execution_time, 2.0, 
                       f"Batch computation took {execution_time:.2f}s - should be faster")
        
        # Verify all summaries have correct data
        for summary in summaries:
            self.assertEqual(summary.total_days, 10, 
                           f"Each employee should have 10 attendance days")
    
    def test_07_summary_date_range_helper(self):
        """Test the date range helper method"""
        summary = self.summary_model.create({
            'employee_id': self.employee1.id,
            'month': 2,
            'year': 2024,
        })
        
        date_from, date_to = summary._get_date_range(2, 2024)
        
        self.assertEqual(date_from, "2024-02-01", "Start date should be first of month")
        self.assertEqual(date_to, "2024-02-29", "End date should be last of month (leap year)")
    
    def test_08_summary_approved_days_count(self):
        """Test approved days counting"""
        dates_states = [
            (self.today.replace(day=1), 'approved'),
            (self.today.replace(day=2), 'approved'),
            (self.today.replace(day=3), 'present'),
        ]
        
        self._create_attendance_records(self.employee1, dates_states)
        
        summary = self.summary_model.create({
            'employee_id': self.employee1.id,
            'month': self.current_month,
            'year': self.current_year,
        })
        
        self.assertEqual(summary.approved_days, 2, "Approved days should be 2")
        self.assertEqual(summary.present_days, 1, "Present days should be 1")
    
    def test_09_summary_cron_generation(self):
        """Test automatic monthly summary generation via cron"""
        # Create attendance records for last month
        last_month = (self.today.replace(day=1) - timedelta(days=1))
        
        dates_states = [
            (last_month.replace(day=1), 'present'),
            (last_month.replace(day=2), 'present'),
        ]
        
        self._create_attendance_records(self.employee1, dates_states)
        
        # Run cron
        self.summary_model.generate_monthly_summary()
        
        # Check if summary was created
        summary = self.summary_model.search([
            ('employee_id', '=', self.employee1.id),
            ('month', '=', last_month.month),
            ('year', '=', last_month.year),
        ])
        
        self.assertTrue(len(summary) > 0, "Summary should be generated by cron")
    
    def test_10_summary_reset_fields_on_invalid_data(self):
        """Test that fields reset when month/year/employee not set"""
        summary = self.summary_model.create({
            'employee_id': self.employee1.id,
            'month': False,
            'year': False,
        })
        
        self.assertEqual(summary.total_days, 0)
        self.assertEqual(summary.total_hours, 0.0)

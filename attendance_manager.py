import csv
import os
from datetime import datetime, timedelta
import pandas as pd
from database import DatabaseManager

class AttendanceManager:
    def __init__(self, database_manager):
        self.database_manager = database_manager
        self.attendance_data_dir = "attendance_data"
        self.ensure_attendance_directory()
    
    def ensure_attendance_directory(self):
        """Ensure attendance data directory exists"""
        if not os.path.exists(self.attendance_data_dir):
            os.makedirs(self.attendance_data_dir)
    
    def mark_attendance(self, user_id, name, status="Present", notes=""):
        """Mark attendance for a user"""
        try:
            date = datetime.now().strftime('%Y-%m-%d')
            time = datetime.now().strftime('%H:%M:%S')
            
            success = self.database_manager.mark_attendance(user_id, name, date, time, status)
            
            if success:
                # Log to CSV file as well
                self.log_attendance_to_csv(name, date, time, status, user_id, notes)
                return True
            return False
            
        except Exception as e:
            print(f"Error marking attendance: {e}")
            return False
    
    def log_attendance_to_csv(self, name, date, time, status, user_id=None, notes=""):
        """Log attendance to CSV file"""
        csv_filename = os.path.join(self.attendance_data_dir, f"attendance_{date}.csv")
        
        file_exists = os.path.exists(csv_filename)
        
        try:
            with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Name', 'Date', 'Time', 'Status', 'User ID', 'Notes']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow({
                    'Name': name,
                    'Date': date,
                    'Time': time,
                    'Status': status,
                    'User ID': user_id,
                    'Notes': notes
                })
        except Exception as e:
            print(f"Error logging to CSV: {e}")
    
    def get_today_attendance(self):
        """Get today's attendance records"""
        return self.database_manager.get_today_attendance()
    
    def get_attendance_by_date(self, date):
        """Get attendance records for a specific date"""
        return self.database_manager.get_attendance_by_date(date)
    
    def get_attendance_by_date_range(self, start_date, end_date):
        """Get attendance records between two dates"""
        return self.database_manager.get_attendance_by_date_range(start_date, end_date)
    
    def get_user_attendance_history(self, user_id, days=30):
        """Get attendance history for a specific user"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        return self.database_manager.get_attendance_by_user(user_id, start_date, end_date)
    
    def get_attendance_summary(self, start_date=None, end_date=None):
        """Get attendance summary statistics"""
        return self.database_manager.get_attendance_summary(start_date, end_date)
    
    def get_daily_attendance_stats(self, date):
        """Get daily attendance statistics"""
        return self.database_manager.get_daily_attendance_stats(date)
    
    def get_weekly_attendance(self, week_start_date=None):
        """Get weekly attendance summary"""
        if week_start_date is None:
            # Get current week start (Monday)
            today = datetime.now()
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)
            week_start_date = week_start.strftime('%Y-%m-%d')
        
        week_end_date = (datetime.strptime(week_start_date, '%Y-%m-%d') + timedelta(days=6)).strftime('%Y-%m-%d')
        
        return self.get_attendance_by_date_range(week_start_date, week_end_date)
    
    def get_monthly_attendance(self, year=None, month=None):
        """Get monthly attendance summary"""
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        # Get first and last day of the month
        start_date = f"{year}-{month:02d}-01"
        
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
        
        return self.get_attendance_by_date_range(start_date, end_date)
    
    def get_attendance_trends(self, days=30):
        """Get attendance trends for the specified number of days"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        attendance_data = self.get_attendance_by_date_range(start_date, end_date)
        
        # Process data for trend analysis
        daily_stats = {}
        
        for record in attendance_data:
            date = record[2]  # date field
            if date not in daily_stats:
                daily_stats[date] = {
                    'total': 0,
                    'present': 0,
                    'absent': 0
                }
            
            daily_stats[date]['total'] += 1
            if record[4] == 'Present':  # status field
                daily_stats[date]['present'] += 1
            else:
                daily_stats[date]['absent'] += 1
        
        # Calculate percentages
        for date in daily_stats:
            stats = daily_stats[date]
            if stats['total'] > 0:
                stats['present_percentage'] = (stats['present'] / stats['total']) * 100
                stats['absent_percentage'] = (stats['absent'] / stats['total']) * 100
            else:
                stats['present_percentage'] = 0
                stats['absent_percentage'] = 0
        
        return daily_stats
    
    def get_user_attendance_rate(self, user_id, days=30):
        """Get attendance rate for a specific user"""
        attendance_history = self.get_user_attendance_history(user_id, days)
        
        if not attendance_history:
            return 0.0
        
        total_days = len(set(record[2] for record in attendance_history))  # unique dates
        present_days = sum(1 for record in attendance_history if record[4] == 'Present')
        
        return (present_days / total_days) * 100 if total_days > 0 else 0.0
    
    def get_department_attendance(self, department, start_date=None, end_date=None):
        """Get attendance records for a specific department"""
        with self.database_manager.conn:
            cursor = self.database_manager.conn.cursor()
            
            if start_date and end_date:
                cursor.execute('''
                    SELECT a.*, u.employee_id
                    FROM attendance a
                    JOIN users u ON a.user_id = u.id
                    WHERE u.department = ? AND a.date BETWEEN ? AND ?
                    ORDER BY a.date, a.time
                ''', (department, start_date, end_date))
            else:
                cursor.execute('''
                    SELECT a.*, u.employee_id
                    FROM attendance a
                    JOIN users u ON a.user_id = u.id
                    WHERE u.department = ?
                    ORDER BY a.date DESC, a.time
                ''', (department,))
            
            return cursor.fetchall()
    
    def export_attendance_csv(self, filename, start_date=None, end_date=None, department=None):
        """Export attendance data to CSV"""
        try:
            attendance_data = self.database_manager.get_attendance_by_date_range(start_date, end_date)
            
            if department:
                filtered_data = []
                for record in attendance_data:
                    user_id = record[1]
                    user = self.database_manager.get_user_by_id(user_id)
                    if user and user[3] == department:  # user[3] is department
                        filtered_data.append(record)
                attendance_data = filtered_data
            
            self.database_manager.export_attendance_to_csv(filename, start_date, end_date)
            return True
            
        except Exception as e:
            print(f"Error exporting attendance CSV: {e}")
            return False
    
    def generate_attendance_report(self, start_date, end_date, format='dict'):
        """Generate comprehensive attendance report"""
        attendance_data = self.get_attendance_by_date_range(start_date, end_date)
        
        if not attendance_data:
            return None
        
        # Calculate various statistics
        total_records = len(attendance_data)
        unique_users = len(set(record[1] for record in attendance_data))  # user_ids
        
        present_count = sum(1 for record in attendance_data if record[4] == 'Present')
        absent_count = sum(1 for record in attendance_data if record[4] == 'Absent')
        
        # Get user-wise statistics
        user_stats = {}
        for record in attendance_data:
            user_id = record[1]
            name = record[2]
            status = record[4]
            
            if user_id not in user_stats:
                user_stats[user_id] = {
                    'name': name,
                    'total_days': 0,
                    'present_days': 0,
                    'absent_days': 0
                }
            
            user_stats[user_id]['total_days'] += 1
            if status == 'Present':
                user_stats[user_id]['present_days'] += 1
            else:
                user_stats[user_id]['absent_days'] += 1
        
        # Calculate percentages
        for user_id in user_stats:
            stats = user_stats[user_id]
            if stats['total_days'] > 0:
                stats['attendance_rate'] = (stats['present_days'] / stats['total_days']) * 100
            else:
                stats['attendance_rate'] = 0
        
        overall_attendance_rate = (present_count / total_records) * 100 if total_records > 0 else 0
        
        report = {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'total_days': (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days + 1
            },
            'overall_stats': {
                'total_records': total_records,
                'unique_users': unique_users,
                'present_count': present_count,
                'absent_count': absent_count,
                'overall_attendance_rate': overall_attendance_rate
            },
            'user_stats': user_stats,
            'daily_breakdown': self.get_attendance_trends(
                (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days
            )
        }
        
        if format == 'dataframe':
            # Convert to pandas DataFrame for easier manipulation
            df_data = []
            for user_id, stats in user_stats.items():
                df_data.append({
                    'User ID': user_id,
                    'Name': stats['name'],
                    'Total Days': stats['total_days'],
                    'Present Days': stats['present_days'],
                    'Absent Days': stats['absent_days'],
                    'Attendance Rate': f"{stats['attendance_rate']:.1f}%"
                })
            
            return pd.DataFrame(df_data)
        
        return report
    
    def get_late_arrivals(self, date, late_threshold="09:30"):
        """Get late arrivals for a specific date"""
        attendance_data = self.get_attendance_by_date(date)
        late_arrivals = []
        
        for record in attendance_data:
            name = record[1]  # name
            time = record[3]  # time
            
            if time > late_threshold:
                late_arrivals.append({
                    'name': name,
                    'time': time,
                    'minutes_late': self.calculate_late_minutes(time, late_threshold)
                })
        
        return late_arrivals
    
    def calculate_late_minutes(self, arrival_time, threshold_time):
        """Calculate minutes late"""
        arrival = datetime.strptime(arrival_time, '%H:%M:%S')
        threshold = datetime.strptime(threshold_time, '%H:%M:%S')
        
        if arrival > threshold:
            delta = arrival - threshold
            return int(delta.total_seconds() / 60)
        return 0
    
    def get_absent_users(self, date):
        """Get users who were absent on a specific date"""
        all_users = self.database_manager.get_all_users()
        attendance_data = self.get_attendance_by_date(date)
        
        # Create set of users who attended
        attended_user_ids = set(record[1] for record in attendance_data)  # user_ids
        
        # Find users who didn't attend
        absent_users = []
        for user in all_users:
            user_id = user[0]
            if user_id not in attended_user_ids:
                absent_users.append({
                    'id': user_id,
                    'name': user[1],
                    'employee_id': user[2],
                    'department': user[3]
                })
        
        return absent_users
    
    def cleanup_old_attendance_files(self, days_to_keep=365):
        """Clean up old CSV attendance files"""
        current_date = datetime.now()
        cutoff_date = current_date - timedelta(days=days_to_keep)
        
        try:
            for filename in os.listdir(self.attendance_data_dir):
                if filename.startswith('attendance_') and filename.endswith('.csv'):
                    date_str = filename[10:20]  # Extract date from filename
                    file_date = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    if file_date < cutoff_date:
                        file_path = os.path.join(self.attendance_data_dir, filename)
                        os.remove(file_path)
                        print(f"Deleted old attendance file: {filename}")
        
        except Exception as e:
            print(f"Error cleaning up attendance files: {e}")
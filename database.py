import sqlite3
import os
from datetime import datetime, timedelta
import csv

class DatabaseManager:
    def __init__(self, db_name="attendance_system.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    employee_id TEXT UNIQUE NOT NULL,
                    department TEXT,
                    face_image_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create attendance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    status TEXT DEFAULT 'Present',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Create index for faster attendance lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_attendance_user_date 
                ON attendance(user_id, date)
            ''')
            
            conn.commit()
    
    def add_user(self, name, employee_id, department, face_image_path=None):
        """Add a new user to the database"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (name, employee_id, department, face_image_path)
                    VALUES (?, ?, ?, ?)
                ''', (name, employee_id, department, face_image_path))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def get_user_by_employee_id(self, employee_id):
        """Get user by employee ID"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE employee_id = ?', (employee_id,))
            return cursor.fetchone()
    
    def get_user_by_name(self, name):
        """Get user by name"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE name = ?', (name,))
            return cursor.fetchone()
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            return cursor.fetchone()
    
    def get_all_users(self):
        """Get all users"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users ORDER BY name')
            return cursor.fetchall()
    
    def update_user(self, user_id, name=None, employee_id=None, department=None, face_image_path=None):
        """Update user information"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Build update query dynamically
            updates = []
            params = []
            
            if name:
                updates.append('name = ?')
                params.append(name)
            if employee_id:
                updates.append('employee_id = ?')
                params.append(employee_id)
            if department:
                updates.append('department = ?')
                params.append(department)
            if face_image_path:
                updates.append('face_image_path = ?')
                params.append(face_image_path)
            
            if updates:
                updates.append('updated_at = CURRENT_TIMESTAMP')
                params.append(user_id)
                
                query = f'UPDATE users SET {", ".join(updates)} WHERE id = ?'
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount > 0
        return False
    
    def delete_user(self, user_id):
        """Delete a user from database"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def mark_attendance(self, user_id, name, date=None, time=None, status='Present'):
        """Mark attendance for a user"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        if time is None:
            time = datetime.now().strftime('%H:%M:%S')
        
        # Check if attendance already marked for today
        existing_attendance = self.get_attendance_by_user_date(user_id, date)
        if existing_attendance:
            return False  # Already marked today
        
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO attendance (user_id, name, date, time, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, name, date, time, status))
                conn.commit()
                return True
        except sqlite3.Error:
            return False
    
    def get_attendance_by_user_date(self, user_id, date):
        """Get attendance record for user on specific date"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM attendance 
                WHERE user_id = ? AND date = ?
            ''', (user_id, date))
            return cursor.fetchone()
    
    def get_attendance_by_date(self, date):
        """Get all attendance records for a specific date"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, u.employee_id, u.department
                FROM attendance a
                JOIN users u ON a.user_id = u.id
                WHERE a.date = ?
                ORDER BY a.time
            ''', (date,))
            return cursor.fetchall()
    
    def get_attendance_by_date_range(self, start_date, end_date):
        """Get attendance records between two dates"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, u.employee_id, u.department
                FROM attendance a
                JOIN users u ON a.user_id = u.id
                WHERE a.date BETWEEN ? AND ?
                ORDER BY a.date, a.time
            ''', (start_date, end_date))
            return cursor.fetchall()
    
    def get_attendance_by_user(self, user_id, start_date=None, end_date=None):
        """Get attendance records for a specific user"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            if start_date and end_date:
                cursor.execute('''
                    SELECT * FROM attendance 
                    WHERE user_id = ? AND date BETWEEN ? AND ?
                    ORDER BY date, time
                ''', (user_id, start_date, end_date))
            else:
                cursor.execute('''
                    SELECT * FROM attendance 
                    WHERE user_id = ?
                    ORDER BY date DESC, time
                ''', (user_id,))
            
            return cursor.fetchall()
    
    def get_attendance_summary(self, start_date=None, end_date=None):
        """Get attendance summary statistics"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            if start_date and end_date:
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(DISTINCT user_id) as unique_users,
                        SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_count,
                        SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_count
                    FROM attendance
                    WHERE date BETWEEN ? AND ?
                ''', (start_date, end_date))
            else:
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(DISTINCT user_id) as unique_users,
                        SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_count,
                        SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_count
                    FROM attendance
                ''')
            
            return cursor.fetchone()
    
    def get_daily_attendance_stats(self, date):
        """Get daily attendance statistics"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_attendance,
                    COUNT(DISTINCT user_id) as unique_users,
                    GROUP_CONCAT(name) as attended_users
                FROM attendance
                WHERE date = ?
            ''', (date,))
            return cursor.fetchone()
    
    def export_attendance_to_csv(self, filename, start_date=None, end_date=None):
        """Export attendance data to CSV"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                if start_date and end_date:
                    cursor.execute('''
                        SELECT a.name, a.date, a.time, a.status, u.employee_id, u.department
                        FROM attendance a
                        JOIN users u ON a.user_id = u.id
                        WHERE a.date BETWEEN ? AND ?
                        ORDER BY a.date, a.time
                    ''', (start_date, end_date))
                else:
                    cursor.execute('''
                        SELECT a.name, a.date, a.time, a.status, u.employee_id, u.department
                        FROM attendance a
                        JOIN users u ON a.user_id = u.id
                        ORDER BY a.date DESC, a.time
                    ''')
                
                records = cursor.fetchall()
                
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Name', 'Date', 'Time', 'Status', 'Employee ID', 'Department'])
                    writer.writerows(records)
                
                return True
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            return False
    
    def get_user_attendance_history(self, user_id, limit=30):
        """Get recent attendance history for a user"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM attendance 
                WHERE user_id = ?
                ORDER BY date DESC, time DESC
                LIMIT ?
            ''', (user_id, limit))
            return cursor.fetchall()
    
    def get_today_attendance(self):
        """Get all attendance records for today"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.get_attendance_by_date(today)
    
    def cleanup_old_attendance(self, days_to_keep=365):
        """Clean up old attendance records"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM attendance WHERE date < ?', (cutoff_date,))
            conn.commit()
            return cursor.rowcount
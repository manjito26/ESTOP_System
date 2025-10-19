"""
ESTOP Function Record System - Main Flask Application
Mobile-friendly Flask web app for safety device testing
"""
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import logging
import os
import json
from datetime import datetime
from .utils.auth import AuthManager
from .models.database import ESTOPDatabase

# Configure logging
logging.basicConfig(
    filename='logs/app.log', 
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.secret_key = 'estop_system_secret_key_2023'
    
    # Initialize components
    auth_manager = AuthManager()
    db = ESTOPDatabase()
    
    try:
        # Initialize database tables and sample data
        db.create_tables()
        db.insert_sample_data()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    @app.route('/')
    def index():
        """Main page - redirect to login if not authenticated"""
        if 'username' not in session:
            return redirect(url_for('login'))
        
        logger.info(f"User {session['username']} accessed main page")
        machines = db.get_machines()
        return render_template('index.html', machines=machines, username=session['username'])
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login page"""
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            if auth_manager.authenticate(username, password):
                session['username'] = username
                session['privileges'] = auth_manager.get_user_privileges(username)
                logger.info(f"User {username} logged in successfully")
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password')
                logger.warning(f"Failed login attempt for {username}")
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        """Logout user"""
        username = session.get('username', 'Unknown')
        session.clear()
        logger.info(f"User {username} logged out")
        flash('You have been logged out')
        return redirect(url_for('login'))
    
    @app.route('/api/devices/<int:machine_id>')
    def get_devices(machine_id):
        """API endpoint to get devices for a machine"""
        if 'username' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        devices = db.get_safety_devices(machine_id)
        logger.info(f"Retrieved {len(devices)} devices for machine {machine_id}")
        return jsonify(devices)
    
    @app.route('/test', methods=['POST'])
    def record_test():
        """Record a safety device test"""
        if 'username' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        try:
            data = request.get_json()
            machine_id = data['machine_id']
            device_id = data['device_id']
            test_result = data['test_result']
            notes = data.get('notes', '')
            username = session['username']
            
            success = db.record_test(machine_id, device_id, username, test_result, notes)
            
            if success:
                logger.info(f"Test recorded successfully by {username}")
                return jsonify({'success': True, 'message': 'Test recorded successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to record test'}), 500
                
        except Exception as e:
            logger.error(f"Error recording test: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    @app.route('/history')
    def history():
        """View test history with search and filters"""
        if 'username' not in session:
            return redirect(url_for('login'))
        
        search_query = request.args.get('search', '')
        machine_filter = request.args.get('machine', '')
        user_filter = request.args.get('user', '')
        sort_by = request.args.get('sort', 'date')
        
        tests = db.get_device_tests(search_query, machine_filter, user_filter)
        machines = db.get_machines()
        users = auth_manager.get_all_users()
        
        # Sort tests
        if sort_by == 'age':
            tests = sorted(tests, key=lambda x: x['days_since_test'], reverse=True)
        elif sort_by == 'machine':
            tests = sorted(tests, key=lambda x: x['machine_name'])
        elif sort_by == 'device':
            tests = sorted(tests, key=lambda x: x['device_name'])
        # Default sort by date (newest first)
        
        logger.info(f"User {session['username']} viewed history page with {len(tests)} results")
        
        return render_template('history.html', 
                             tests=tests, 
                             machines=machines, 
                             users=users,
                             search_query=search_query,
                             machine_filter=machine_filter,
                             user_filter=user_filter,
                             sort_by=sort_by,
                             username=session['username'])
    
    @app.route('/debug')
    def debug():
        """Debug endpoint showing all available routes"""
        if 'username' not in session:
            return redirect(url_for('login'))
        
        logger.info(f"User {session['username']} accessed debug endpoint")
        endpoints = []
        
        for rule in app.url_map.iter_rules():
            methods = ', '.join(rule.methods - {'HEAD', 'OPTIONS'})
            endpoints.append({
                'endpoint': rule.rule,
                'methods': methods,
                'function': rule.endpoint
            })
        
        return render_template('debug.html', endpoints=endpoints, username=session['username'])
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return render_template('500.html'), 500
    
    # User Administration Routes
    @app.route('/user_admin')
    def user_admin():
        """User administration page - only for admins"""
        if 'username' not in session:
            return redirect(url_for('login'))
        
        # Check if user has admin privileges
        user_privileges = session.get('privileges', [])
        if 'admin' not in user_privileges:
            flash('Access denied. Admin privileges required.')
            return redirect(url_for('index'))
        
        logger.info(f"Admin {session['username']} accessed user administration")
        users = auth_manager.users
        return render_template('user_admin.html', users=users, username=session['username'])
    
    @app.route('/add_user', methods=['POST'])
    def add_user():
        """Add a new user - capitalize first and last names"""
        if 'username' not in session:
            return redirect(url_for('login'))
        
        # Check admin privileges
        user_privileges = session.get('privileges', [])
        if 'admin' not in user_privileges:
            flash('Access denied. Admin privileges required.')
            return redirect(url_for('user_admin'))
        
        try:
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            email = request.form.get('email', '').strip()
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            role = request.form.get('role', '')
            
            # Capitalize first letter of first and last names
            first_name = first_name.capitalize() if first_name else ''
            last_name = last_name.capitalize() if last_name else ''
            
            logger.info(f"Admin {session['username']} adding new user: {first_name} {last_name}")
            
            # Check if username already exists
            if username in auth_manager.users:
                flash('Username already exists.', 'error')
                return redirect(url_for('user_admin'))
            
            # Add user to auth manager
            new_user = {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'password': password,
                'role': role,
                'privileges': [role] if role in ['admin', 'supervisor'] else ['user'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            auth_manager.users[username] = new_user
            
            # Save users to file
            try:
                users_file = '/home/eraser/PycharmProjects/RACE/users.json'
                with open(users_file, 'w') as f:
                    json.dump(auth_manager.users, f, indent=2)
                logger.info(f"Successfully added user: {first_name} {last_name} ({username})")
                flash(f'User {first_name} {last_name} added successfully!', 'success')
            except Exception as e:
                logger.error(f"Error saving users file: {e}")
                flash('User added but could not save to file.', 'warning')
            
        except Exception as e:
            logger.error(f"Error adding user: {str(e)}")
            flash('Error adding user. Please try again.', 'error')
        
        return redirect(url_for('user_admin'))
    
    @app.route('/delete_user/<username>', methods=['DELETE'])
    def delete_user(username):
        """Delete a user - only for admins"""
        if 'username' not in session:
            return jsonify({'success': False, 'message': 'Not authenticated'})
        
        user_privileges = session.get('privileges', [])
        if 'admin' not in user_privileges:
            return jsonify({'success': False, 'message': 'Access denied. Admin privileges required.'})
        
        try:
            # Don't allow deletion of the current user
            if username == session['username']:
                return jsonify({'success': False, 'message': 'Cannot delete your own account.'})
            
            if username not in auth_manager.users:
                return jsonify({'success': False, 'message': 'User not found.'})
            
            # Get user info before deletion
            user_info = auth_manager.users[username]
            
            # Delete the user
            del auth_manager.users[username]
            
            # Save users to file
            try:
                users_file = '/home/eraser/PycharmProjects/RACE/users.json'
                with open(users_file, 'w') as f:
                    json.dump(auth_manager.users, f, indent=2)
                
                logger.info(f"Admin {session['username']} deleted user: {username}")
                return jsonify({'success': True, 'message': 'User deleted successfully.'})
            except Exception as e:
                logger.error(f"Error saving users file after deletion: {e}")
                return jsonify({'success': False, 'message': 'Error saving changes.'})
            
        except Exception as e:
            logger.error(f"Error deleting user {username}: {str(e)}")
            return jsonify({'success': False, 'message': 'Error deleting user.'})
    
    # Mock Reports System (since no database tables exist yet)
    _mock_reports = []
    _report_id_counter = 1
    
    @app.route('/reports')
    def reports():
        """View all reports"""
        if 'username' not in session:
            return redirect(url_for('login'))
        
        logger.info(f"User {session['username']} accessed reports page")
        
        # For demo purposes, use mock data
        filtered_reports = _mock_reports.copy()
        
        # Apply filters if provided
        status_filter = request.args.get('status')
        severity_filter = request.args.get('severity')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        if status_filter:
            filtered_reports = [r for r in filtered_reports if r.get('status') == status_filter]
        if severity_filter:
            filtered_reports = [r for r in filtered_reports if r.get('severity') == severity_filter]
        
        return render_template('reports.html', 
                             reports=filtered_reports,
                             current_user=type('obj', (object,), {
                                 'role': session.get('privileges', ['user'])[0]
                             })(),
                             username=session['username'])
    
    @app.route('/edit_report/<int:report_id>')
    def edit_report(report_id):
        """Edit an existing report or create new - only for supervisors and admins"""
        if 'username' not in session:
            return redirect(url_for('login'))
        
        user_privileges = session.get('privileges', [])
        if not any(priv in ['supervisor', 'admin'] for priv in user_privileges):
            flash('Access denied. Only supervisors and admins can edit reports.', 'error')
            return redirect(url_for('reports'))
        
        logger.info(f"User {session['username']} accessing edit report {report_id}")
        
        report = None
        if report_id > 0:
            report = next((r for r in _mock_reports if r.get('id') == report_id), None)
            if not report:
                flash('Report not found.', 'error')
                return redirect(url_for('reports'))
        
        users = auth_manager.users
        return render_template('edit_report.html', 
                             report=report, 
                             users=users,
                             username=session['username'])
    
    @app.route('/save_report', methods=['POST'])
    def save_report():
        """Save report changes - only for supervisors and admins"""
        if 'username' not in session:
            return redirect(url_for('login'))
        
        user_privileges = session.get('privileges', [])
        if not any(priv in ['supervisor', 'admin'] for priv in user_privileges):
            flash('Access denied. Only supervisors and admins can edit reports.', 'error')
            return redirect(url_for('reports'))
        
        logger.info(f"User {session['username']} saving report changes")
        
        try:
            global _report_id_counter
            
            report_id = request.form.get('report_id')
            incident_date = request.form.get('incident_date')
            location = request.form.get('location')
            severity = request.form.get('severity')
            status = request.form.get('status')
            reported_by = request.form.get('reported_by')
            assigned_to = request.form.get('assigned_to') if request.form.get('assigned_to') else None
            title = request.form.get('title')
            description = request.form.get('description')
            corrective_actions = request.form.get('corrective_actions')
            equipment_involved = request.form.get('equipment_involved')
            witnesses = request.form.get('witnesses')
            
            report_data = {
                'incident_date': datetime.fromisoformat(incident_date.replace('T', ' ')) if incident_date else None,
                'location': location,
                'severity': severity,
                'status': status,
                'reported_by': reported_by,
                'assigned_to': assigned_to,
                'title': title,
                'description': description,
                'corrective_actions': corrective_actions,
                'equipment_involved': equipment_involved,
                'witnesses': witnesses,
                'modified_at': datetime.now(),
                'modified_by': session['username']
            }
            
            # Add reporter and assignee names for display
            if reported_by and reported_by in auth_manager.users:
                user_data = auth_manager.users[reported_by]
                report_data['reporter_first'] = user_data.get('first_name', '')
                report_data['reporter_last'] = user_data.get('last_name', '')
            
            if assigned_to and assigned_to in auth_manager.users:
                user_data = auth_manager.users[assigned_to]
                report_data['assignee_first'] = user_data.get('first_name', '')
                report_data['assignee_last'] = user_data.get('last_name', '')
            
            if report_id:  # Update existing report
                report_id = int(report_id)
                for i, report in enumerate(_mock_reports):
                    if report.get('id') == report_id:
                        report_data['id'] = report_id
                        report_data['created_at'] = report.get('created_at')
                        report_data['created_by'] = report.get('created_by')
                        _mock_reports[i] = report_data
                        break
                
                logger.info(f"Updated report {report_id} by user {session['username']}")
                flash('Report updated successfully!', 'success')
                
            else:  # Create new report
                report_data['id'] = _report_id_counter
                report_data['created_at'] = datetime.now()
                report_data['created_by'] = session['username']
                _mock_reports.append(report_data)
                _report_id_counter += 1
                
                logger.info(f"Created new report by user {session['username']}")
                flash('Report created successfully!', 'success')
            
            return redirect(url_for('reports'))
            
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")
            flash('Error saving report. Please try again.', 'error')
            return redirect(url_for('reports'))
    
    @app.route('/view_report/<int:report_id>')
    def view_report(report_id):
        """View a specific report"""
        if 'username' not in session:
            return redirect(url_for('login'))
        
        report = next((r for r in _mock_reports if r.get('id') == report_id), None)
        if not report:
            flash('Report not found.', 'error')
            return redirect(url_for('reports'))
        
        logger.info(f"User {session['username']} viewing report {report_id}")
        return render_template('view_report.html', 
                             report=report,
                             username=session['username'])
    
    @app.route('/report_summary')
    def report_summary():
        """View report summary statistics"""
        if 'username' not in session:
            return redirect(url_for('login'))
        
        logger.info(f"User {session['username']} accessed report summary")
        
        # Calculate summary statistics
        total_reports = len(_mock_reports)
        open_reports = len([r for r in _mock_reports if r.get('status') == 'open'])
        critical_reports = len([r for r in _mock_reports if r.get('severity') == 'critical'])
        
        summary = {
            'total': total_reports,
            'open': open_reports,
            'critical': critical_reports,
            'resolved': len([r for r in _mock_reports if r.get('status') == 'resolved'])
        }
        
        return render_template('report_summary.html',
                             summary=summary,
                             reports=_mock_reports,
                             username=session['username'])
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
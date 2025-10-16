"""
ESTOP Function Record System - Main Flask Application
Mobile-friendly Flask web app for safety device testing
"""
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import logging
import os
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
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
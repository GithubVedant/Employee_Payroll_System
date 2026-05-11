# database.py — SQLite database setup and all SQL operations
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

DB_FILE = "payroll.db"

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS departments (
        id     INTEGER PRIMARY KEY AUTOINCREMENT,
        name   TEXT NOT NULL UNIQUE,
        budget REAL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS employees (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id        TEXT NOT NULL UNIQUE,
        name          TEXT NOT NULL,
        email         TEXT NOT NULL UNIQUE,
        phone         TEXT,
        department_id INTEGER REFERENCES departments(id),
        designation   TEXT NOT NULL,
        join_date     TEXT NOT NULL,
        basic_salary  REAL NOT NULL,
        hra_pct       REAL DEFAULT 40.0,
        da_pct        REAL DEFAULT 20.0,
        pf_pct        REAL DEFAULT 12.0,
        tax_pct       REAL DEFAULT 10.0,
        status        TEXT DEFAULT 'Active'
    );
    CREATE TABLE IF NOT EXISTS attendance (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER REFERENCES employees(id),
        month       TEXT NOT NULL,
        year        INTEGER NOT NULL,
        working_days INTEGER DEFAULT 26,
        present_days INTEGER DEFAULT 26,
        leaves_taken INTEGER DEFAULT 0,
        UNIQUE(employee_id, month, year)
    );
    CREATE TABLE IF NOT EXISTS payroll (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id     INTEGER REFERENCES employees(id),
        month           TEXT NOT NULL,
        year            INTEGER NOT NULL,
        basic_salary    REAL,
        hra             REAL,
        da              REAL,
        gross_salary    REAL,
        pf_deduction    REAL,
        tax_deduction   REAL,
        other_deduction REAL DEFAULT 0,
        net_salary      REAL,
        status          TEXT DEFAULT 'Pending',
        generated_on    TEXT,
        UNIQUE(employee_id, month, year)
    );
    CREATE TABLE IF NOT EXISTS users (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role     TEXT DEFAULT 'HR'
    );
    """)

    depts = [("Engineering",2000000),("Human Resources",800000),
             ("Finance",1000000),("Marketing",700000),("Operations",600000)]
    c.executemany("INSERT OR IGNORE INTO departments(name,budget) VALUES(?,?)", depts)

    pwd = hashlib.sha256("admin123".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users(username,password,role) VALUES(?,?,?)",
              ("admin", pwd, "Admin"))

    employees = [
        ("EMP001","Vedant Sharma",  "vedant@techcorp.com", "9876543210",1,"Software Engineer","2022-03-15",65000),
        ("EMP002","Priya Patel",    "priya@techcorp.com",  "9876543211",1,"Senior Developer",  "2020-06-01",95000),
        ("EMP003","Rahul Gupta",    "rahul@techcorp.com",  "9876543212",2,"HR Manager",        "2019-01-10",75000),
        ("EMP004","Sneha Joshi",    "sneha@techcorp.com",  "9876543213",3,"Accountant",        "2021-08-20",55000),
        ("EMP005","Amit Kumar",     "amit@techcorp.com",   "9876543214",4,"Marketing Lead",    "2020-11-05",70000),
        ("EMP006","Kavita Singh",   "kavita@techcorp.com", "9876543215",1,"Data Scientist",    "2023-02-14",88000),
        ("EMP007","Ravi Verma",     "ravi@techcorp.com",   "9876543216",5,"Operations Head",   "2018-05-30",82000),
        ("EMP008","Anjali Mehta",   "anjali@techcorp.com", "9876543217",2,"HR Executive",      "2022-09-01",45000),
    ]
    for emp in employees:
        c.execute("""INSERT OR IGNORE INTO employees
            (emp_id,name,email,phone,department_id,designation,join_date,basic_salary)
            VALUES(?,?,?,?,?,?,?,?)""", emp)

    conn.commit(); conn.close()

def get_all_employees():
    conn = get_conn()
    rows = conn.execute("""SELECT e.*, d.name as dept_name
        FROM employees e LEFT JOIN departments d ON e.department_id=d.id
        ORDER BY e.emp_id""").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_employee_by_id(eid):
    conn = get_conn()
    row = conn.execute("""SELECT e.*, d.name as dept_name
        FROM employees e LEFT JOIN departments d ON e.department_id=d.id
        WHERE e.emp_id=?""", (eid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def add_employee(data):
    conn = get_conn()
    conn.execute("""INSERT INTO employees
        (emp_id,name,email,phone,department_id,designation,join_date,
         basic_salary,hra_pct,da_pct,pf_pct,tax_pct,status)
        VALUES(:emp_id,:name,:email,:phone,:department_id,:designation,
               :join_date,:basic_salary,:hra_pct,:da_pct,:pf_pct,:tax_pct,:status)""", data)
    conn.commit(); conn.close()

def update_employee(emp_id, data):
    data["emp_id"] = emp_id
    conn = get_conn()
    conn.execute("""UPDATE employees SET name=:name,email=:email,phone=:phone,
        department_id=:department_id,designation=:designation,
        basic_salary=:basic_salary,hra_pct=:hra_pct,da_pct=:da_pct,
        pf_pct=:pf_pct,tax_pct=:tax_pct,status=:status
        WHERE emp_id=:emp_id""", data)
    conn.commit(); conn.close()

def delete_employee(emp_id):
    conn = get_conn()
    conn.execute("DELETE FROM employees WHERE emp_id=?", (emp_id,))
    conn.commit(); conn.close()

def get_departments():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM departments ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_attendance(employee_id, month, year, working_days, present_days):
    leaves = working_days - present_days
    conn = get_conn()
    conn.execute("""INSERT INTO attendance(employee_id,month,year,working_days,present_days,leaves_taken)
        VALUES(?,?,?,?,?,?)
        ON CONFLICT(employee_id,month,year) DO UPDATE SET
        working_days=excluded.working_days,present_days=excluded.present_days,
        leaves_taken=excluded.leaves_taken""",
        (employee_id,month,year,working_days,present_days,leaves))
    conn.commit(); conn.close()

def get_attendance(month, year):
    conn = get_conn()
    rows = conn.execute("""SELECT e.id as emp_db_id,e.emp_id,e.name,d.name as dept,
        a.working_days,a.present_days,a.leaves_taken
        FROM employees e
        LEFT JOIN attendance a ON e.id=a.employee_id AND a.month=? AND a.year=?
        LEFT JOIN departments d ON e.department_id=d.id
        WHERE e.status='Active' ORDER BY e.emp_id""", (month,year)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def calculate_payroll(month, year):
    conn = get_conn()
    emps = conn.execute("SELECT * FROM employees WHERE status='Active'").fetchall()
    for emp in emps:
        att = conn.execute("SELECT * FROM attendance WHERE employee_id=? AND month=? AND year=?",
            (emp["id"],month,year)).fetchone()
        wd = att["working_days"] if att else 26
        pd = att["present_days"] if att else 26
        ratio = pd/wd if wd > 0 else 1
        basic = round(emp["basic_salary"]*ratio, 2)
        hra   = round(basic*emp["hra_pct"]/100, 2)
        da    = round(basic*emp["da_pct"]/100, 2)
        gross = round(basic+hra+da, 2)
        pf    = round(basic*emp["pf_pct"]/100, 2)
        tax   = round(gross*emp["tax_pct"]/100, 2)
        net   = round(gross-pf-tax, 2)
        conn.execute("""INSERT INTO payroll
            (employee_id,month,year,basic_salary,hra,da,gross_salary,
             pf_deduction,tax_deduction,net_salary,status,generated_on)
            VALUES(?,?,?,?,?,?,?,?,?,?,'Generated',?)
            ON CONFLICT(employee_id,month,year) DO UPDATE SET
            basic_salary=excluded.basic_salary,hra=excluded.hra,da=excluded.da,
            gross_salary=excluded.gross_salary,pf_deduction=excluded.pf_deduction,
            tax_deduction=excluded.tax_deduction,net_salary=excluded.net_salary,
            status='Generated',generated_on=excluded.generated_on""",
            (emp["id"],month,year,basic,hra,da,gross,pf,tax,net,
             datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit(); conn.close()

def get_payroll(month, year):
    conn = get_conn()
    rows = conn.execute("""SELECT e.emp_id,e.name,d.name as dept,e.designation,
        p.basic_salary,p.hra,p.da,p.gross_salary,
        p.pf_deduction,p.tax_deduction,p.net_salary,p.status,p.generated_on
        FROM payroll p JOIN employees e ON p.employee_id=e.id
        LEFT JOIN departments d ON e.department_id=d.id
        WHERE p.month=? AND p.year=? ORDER BY e.emp_id""", (month,year)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_paid(month, year):
    conn = get_conn()
    conn.execute("UPDATE payroll SET status='Paid' WHERE month=? AND year=?",(month,year))
    conn.commit(); conn.close()

def get_dashboard_stats():
    conn = get_conn()
    s = {}
    s["total_emp"]  = conn.execute("SELECT COUNT(*) FROM employees WHERE status='Active'").fetchone()[0]
    s["total_dept"] = conn.execute("SELECT COUNT(*) FROM departments").fetchone()[0]
    now = datetime.now()
    m,y = now.strftime("%B"), now.year
    row = conn.execute("SELECT SUM(net_salary),COUNT(*) FROM payroll WHERE month=? AND year=?",
                       (m,y)).fetchone()
    s["monthly_payroll"] = row[0] or 0
    s["payroll_count"]   = row[1] or 0
    s["dept_breakdown"]  = [dict(r) for r in conn.execute("""
        SELECT d.name,COUNT(e.id) as cnt,COALESCE(SUM(e.basic_salary),0) as total
        FROM departments d LEFT JOIN employees e ON d.id=e.department_id AND e.status='Active'
        GROUP BY d.name ORDER BY d.name""").fetchall()]
    s["salary_range"] = [dict(r) for r in conn.execute("""
        SELECT designation, ROUND(AVG(basic_salary),0) as avg_sal,
               COUNT(*) as cnt FROM employees WHERE status='Active'
        GROUP BY designation ORDER BY avg_sal DESC""").fetchall()]
    conn.close()
    return s

def verify_login(username, password):
    hashed = hashlib.sha256(password.encode()).hexdigest()
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE username=? AND password=?",
                       (username,hashed)).fetchone()
    conn.close()
    return dict(row) if row else None

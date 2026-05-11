# app.py — Employee Payroll System
# Run with: streamlit run app.py

import streamlit as st
import pandas as pd
from datetime import datetime
from database import (init_db, verify_login, get_all_employees, get_employee_by_id,
    add_employee, update_employee, delete_employee, get_departments,
    save_attendance, get_attendance, calculate_payroll, get_payroll,
    mark_paid, get_dashboard_stats)

init_db()

st.set_page_config(page_title="Payroll System", page_icon="💼", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main-header { background: linear-gradient(135deg, #1A3C5E, #2E75B6);
    padding: 1.5rem 2rem; border-radius: 14px; margin-bottom: 1.5rem; color: white; }
.main-header h1 { margin: 0; font-size: 1.9rem; font-weight: 700; }
.main-header p  { margin: 0.2rem 0 0; opacity: 0.85; font-size: 0.9rem; }

.kpi-card { background: white; border-radius: 12px; padding: 1.2rem 1.5rem;
    border-left: 5px solid #2E75B6; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 1rem; }
.kpi-card h2 { margin: 0; font-size: 2rem; font-weight: 700; color: #1A3C5E; }
.kpi-card p  { margin: 0.2rem 0 0; color: #666; font-size: 0.82rem; }

.badge-active   { background:#E8F5E9; color:#2E7D32; padding:3px 10px;
    border-radius:12px; font-size:0.78rem; font-weight:600; }
.badge-inactive { background:#FFEBEE; color:#C62828; padding:3px 10px;
    border-radius:12px; font-size:0.78rem; font-weight:600; }
.badge-paid     { background:#E3F2FD; color:#1565C0; padding:3px 10px;
    border-radius:12px; font-size:0.78rem; font-weight:600; }
.badge-gen      { background:#FFF8E1; color:#F57F17; padding:3px 10px;
    border-radius:12px; font-size:0.78rem; font-weight:600; }

.section-card { background: white; border-radius: 12px; padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07); margin-bottom: 1rem; }

div[data-testid="stSidebar"] { background: #F0F4F8; }
.stButton > button { border-radius: 8px !important; font-weight: 500 !important; }
.stTextInput input, .stNumberInput input, .stSelectbox > div {
    border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ── Auth ──────────────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("""
        <div class="main-header" style="text-align:center;margin-top:3rem">
            <h1>💼 Payroll System</h1>
            <p>Employee Payroll Management</p>
        </div>""", unsafe_allow_html=True)
        with st.form("login"):
            st.markdown("### 🔐 Login")
            username = st.text_input("Username", placeholder="ID")
            password = st.text_input("Password", type="password", placeholder="Password")
            if st.form_submit_button("Login →", use_container_width=True):
                user = verify_login(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Invalid credentials! Use admin / admin123")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### 💼 Payroll System")
    st.markdown(f"👤 **{st.session_state.user['username']}** ({st.session_state.user['role']})")
    st.markdown("---")
    page = st.radio("Navigate", [
        "🏠 Dashboard",
        "👥 Employees",
        "📅 Attendance",
        "💰 Payroll",
        "📊 Reports",
    ], label_visibility="collapsed")
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

st.markdown("""
<div class="main-header">
    <h1>💼 Employee Payroll Management System</h1>
    <p>Manage employees, attendance, salary calculation and payroll processing</p>
</div>""", unsafe_allow_html=True)

MONTHS = ["January","February","March","April","May","June",
          "July","August","September","October","November","December"]

# ══════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════
if page == "🏠 Dashboard":
    stats = get_dashboard_stats()
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="kpi-card"><h2>{stats["total_emp"]}</h2><p>👥 Active Employees</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-card" style="border-left-color:#1A7A4A"><h2>{stats["total_dept"]}</h2><p>🏢 Departments</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi-card" style="border-left-color:#B06000"><h2>₹{stats["monthly_payroll"]:,.0f}</h2><p>💰 This Month Payroll</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="kpi-card" style="border-left-color:#6B2FA0"><h2>{stats["payroll_count"]}</h2><p>📋 Payslips Generated</p></div>', unsafe_allow_html=True)

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### 🏢 Department Headcount")
        if stats["dept_breakdown"]:
            df = pd.DataFrame(stats["dept_breakdown"])
            df.columns = ["Department","Employees","Total Basic (₹)"]
            df["Total Basic (₹)"] = df["Total Basic (₹)"].apply(lambda x: f"₹{x:,.0f}")
            st.dataframe(df, use_container_width=True, hide_index=True)

    with col_b:
        st.markdown("### 💼 Avg Salary by Role")
        if stats["salary_range"]:
            df2 = pd.DataFrame(stats["salary_range"])
            df2.columns = ["Designation","Avg Basic (₹)","Count"]
            df2["Avg Basic (₹)"] = df2["Avg Basic (₹)"].apply(lambda x: f"₹{x:,.0f}")
            st.dataframe(df2, use_container_width=True, hide_index=True)

    st.markdown("### 👥 All Employees")
    emps = get_all_employees()
    if emps:
        df3 = pd.DataFrame(emps)[["emp_id","name","dept_name","designation","basic_salary","status"]]
        df3.columns = ["Emp ID","Name","Department","Designation","Basic Salary (₹)","Status"]
        df3["Basic Salary (₹)"] = df3["Basic Salary (₹)"].apply(lambda x: f"₹{x:,.0f}")
        st.dataframe(df3, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
# EMPLOYEES
# ══════════════════════════════════════════════════════════════
elif page == "👥 Employees":
    st.markdown("## 👥 Employee Management")
    tab1, tab2, tab3 = st.tabs(["📋 All Employees", "➕ Add Employee", "✏️ Edit / Delete"])

    with tab1:
        emps = get_all_employees()
        if emps:
            df = pd.DataFrame(emps)[["emp_id","name","dept_name","designation",
                                      "basic_salary","join_date","status"]]
            df.columns = ["Emp ID","Name","Department","Designation",
                          "Basic Salary","Join Date","Status"]
            df["Basic Salary"] = df["Basic Salary"].apply(lambda x: f"₹{x:,.0f}")
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = pd.DataFrame(emps).to_csv(index=False)
            st.download_button("⬇ Export CSV", csv, "employees.csv", use_container_width=True)
        else:
            st.info("No employees found.")

    with tab2:
        depts = get_departments()
        dept_map = {d["name"]: d["id"] for d in depts}
        with st.form("add_emp"):
            st.markdown("### Add New Employee")
            c1,c2 = st.columns(2)
            with c1:
                emp_id   = st.text_input("Employee ID *", placeholder="EMP009")
                name     = st.text_input("Full Name *")
                email    = st.text_input("Email *")
                phone    = st.text_input("Phone")
                dept     = st.selectbox("Department", list(dept_map.keys()))
            with c2:
                desig    = st.text_input("Designation *")
                join_date= st.date_input("Join Date")
                basic    = st.number_input("Basic Salary (₹) *", min_value=10000, value=50000, step=1000)
                hra_pct  = st.number_input("HRA %", value=40.0, step=1.0)
                da_pct   = st.number_input("DA %", value=20.0, step=1.0)
            c3,c4 = st.columns(2)
            with c3:
                pf_pct   = st.number_input("PF %", value=12.0, step=0.5)
            with c4:
                tax_pct  = st.number_input("Tax %", value=10.0, step=0.5)

            if st.form_submit_button("✅ Add Employee", use_container_width=True):
                if emp_id and name and email and desig:
                    try:
                        add_employee({
                            "emp_id": emp_id, "name": name, "email": email,
                            "phone": phone, "department_id": dept_map[dept],
                            "designation": desig, "join_date": str(join_date),
                            "basic_salary": basic, "hra_pct": hra_pct,
                            "da_pct": da_pct, "pf_pct": pf_pct,
                            "tax_pct": tax_pct, "status": "Active"
                        })
                        st.success(f"✅ Employee {name} added successfully!")
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Please fill all required fields.")

    with tab3:
        emps = get_all_employees()
        emp_ids = [e["emp_id"] for e in emps]
        sel = st.selectbox("Select Employee", emp_ids)
        if sel:
            emp = get_employee_by_id(sel)
            depts = get_departments()
            dept_map = {d["name"]: d["id"] for d in depts}
            dept_names = list(dept_map.keys())
            curr_dept = next((d["name"] for d in depts if d["id"]==emp["department_id"]), dept_names[0])

            with st.form("edit_emp"):
                st.markdown(f"### Edit: {emp['name']}")
                c1,c2 = st.columns(2)
                with c1:
                    name  = st.text_input("Name", value=emp["name"])
                    email = st.text_input("Email", value=emp["email"])
                    phone = st.text_input("Phone", value=emp["phone"] or "")
                    dept  = st.selectbox("Department", dept_names, index=dept_names.index(curr_dept))
                    desig = st.text_input("Designation", value=emp["designation"])
                with c2:
                    basic   = st.number_input("Basic Salary", value=float(emp["basic_salary"]), step=1000.0)
                    hra_pct = st.number_input("HRA %", value=float(emp["hra_pct"]))
                    da_pct  = st.number_input("DA %", value=float(emp["da_pct"]))
                    pf_pct  = st.number_input("PF %", value=float(emp["pf_pct"]))
                    tax_pct = st.number_input("Tax %", value=float(emp["tax_pct"]))
                    status  = st.selectbox("Status", ["Active","Inactive"],
                                          index=0 if emp["status"]=="Active" else 1)

                col_u, col_d = st.columns(2)
                with col_u:
                    if st.form_submit_button("💾 Update", use_container_width=True):
                        update_employee(sel, {
                            "name":name,"email":email,"phone":phone,
                            "department_id":dept_map[dept],"designation":desig,
                            "basic_salary":basic,"hra_pct":hra_pct,"da_pct":da_pct,
                            "pf_pct":pf_pct,"tax_pct":tax_pct,"status":status
                        })
                        st.success("✅ Employee updated!")
                with col_d:
                    if st.form_submit_button("🗑 Delete", use_container_width=True):
                        delete_employee(sel)
                        st.success("🗑 Employee deleted!")
                        st.rerun()

# ══════════════════════════════════════════════════════════════
# ATTENDANCE
# ══════════════════════════════════════════════════════════════
elif page == "📅 Attendance":
    st.markdown("## 📅 Attendance Management")
    col1, col2 = st.columns(2)
    with col1:
        sel_month = st.selectbox("Month", MONTHS, index=datetime.now().month-1)
    with col2:
        sel_year = st.number_input("Year", value=datetime.now().year, min_value=2020, max_value=2030)

    records = get_attendance(sel_month, sel_year)
    if not records:
        st.info("No employees found.")
    else:
        st.markdown(f"### Attendance for {sel_month} {sel_year}")
        st.caption("Edit present days below and click Save All Attendance")

        with st.form("attendance_form"):
            data_rows = []
            for r in records:
                c1,c2,c3,c4 = st.columns([3,2,2,2])
                with c1: st.markdown(f"**{r['emp_id']}** — {r['name']}")
                with c2:
                    wd = st.number_input("Working Days", value=r["working_days"] or 26,
                        min_value=1, max_value=31, key=f"wd_{r['emp_db_id']}")
                with c3:
                    pd_val = st.number_input("Present Days", value=r["present_days"] or 26,
                        min_value=0, max_value=31, key=f"pd_{r['emp_db_id']}")
                with c4:
                    st.markdown(f"Leaves: **{wd - pd_val}**")
                data_rows.append((r["emp_db_id"], wd, pd_val))

            if st.form_submit_button("💾 Save All Attendance", use_container_width=True):
                for emp_db_id, wd, pd_val in data_rows:
                    save_attendance(emp_db_id, sel_month, sel_year, wd, pd_val)
                st.success(f"✅ Attendance saved for {sel_month} {sel_year}!")

# ══════════════════════════════════════════════════════════════
# PAYROLL
# ══════════════════════════════════════════════════════════════
elif page == "💰 Payroll":
    st.markdown("## 💰 Payroll Processing")
    col1, col2 = st.columns(2)
    with col1:
        sel_month = st.selectbox("Month", MONTHS, index=datetime.now().month-1)
    with col2:
        sel_year = st.number_input("Year", value=datetime.now().year,
                                   min_value=2020, max_value=2030)

    col_gen, col_pay = st.columns(2)
    with col_gen:
        if st.button("⚙️ Generate Payroll", use_container_width=True, type="primary"):
            with st.spinner("Calculating salaries..."):
                calculate_payroll(sel_month, sel_year)
            st.success(f"✅ Payroll generated for {sel_month} {sel_year}!")
            st.rerun()
    with col_pay:
        if st.button("✅ Mark All as Paid", use_container_width=True):
            mark_paid(sel_month, sel_year)
            st.success("✅ All payslips marked as Paid!")
            st.rerun()

    records = get_payroll(sel_month, sel_year)
    if records:
        st.markdown(f"### 📋 Payroll — {sel_month} {sel_year}")
        df = pd.DataFrame(records)

        # Format currency columns
        for col in ["basic_salary","hra","da","gross_salary","pf_deduction","tax_deduction","net_salary"]:
            df[col] = df[col].apply(lambda x: f"₹{x:,.0f}" if x else "₹0")

        df.columns = ["Emp ID","Name","Dept","Designation","Basic","HRA","DA",
                      "Gross","PF","Tax","Net Salary","Status","Generated"]
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Summary
        raw = get_payroll(sel_month, sel_year)
        total_gross = sum(r["gross_salary"] for r in raw)
        total_net   = sum(r["net_salary"] for r in raw)
        total_pf    = sum(r["pf_deduction"] for r in raw)
        total_tax   = sum(r["tax_deduction"] for r in raw)

        st.markdown("### 💹 Payroll Summary")
        s1,s2,s3,s4 = st.columns(4)
        with s1: st.metric("Total Gross", f"₹{total_gross:,.0f}")
        with s2: st.metric("Total PF",    f"₹{total_pf:,.0f}")
        with s3: st.metric("Total Tax",   f"₹{total_tax:,.0f}")
        with s4: st.metric("Total Net",   f"₹{total_net:,.0f}")

        csv = pd.DataFrame(raw).to_csv(index=False)
        st.download_button("⬇ Download Payroll CSV", csv,
                           f"payroll_{sel_month}_{sel_year}.csv", use_container_width=True)
    else:
        st.info(f"No payroll generated for {sel_month} {sel_year}. Click 'Generate Payroll' above.")

# ══════════════════════════════════════════════════════════════
# REPORTS
# ══════════════════════════════════════════════════════════════
elif page == "📊 Reports":
    st.markdown("## 📊 Reports & Analytics")

    tab1, tab2 = st.tabs(["👥 Employee Report", "💰 Payroll Report"])

    with tab1:
        st.markdown("### Employee Database Report")
        emps = get_all_employees()
        if emps:
            df = pd.DataFrame(emps)
            active   = df[df["status"]=="Active"]
            inactive = df[df["status"]=="Inactive"]

            c1,c2,c3 = st.columns(3)
            with c1: st.metric("Total Employees", len(df))
            with c2: st.metric("Active",   len(active))
            with c3: st.metric("Inactive", len(inactive))

            st.markdown("#### By Department")
            dept_grp = active.groupby("dept_name").agg(
                Count=("emp_id","count"),
                Avg_Basic=("basic_salary","mean"),
                Total_Basic=("basic_salary","sum")
            ).reset_index()
            dept_grp.columns = ["Department","Count","Avg Basic (₹)","Total Basic (₹)"]
            dept_grp["Avg Basic (₹)"]   = dept_grp["Avg Basic (₹)"].apply(lambda x: f"₹{x:,.0f}")
            dept_grp["Total Basic (₹)"] = dept_grp["Total Basic (₹)"].apply(lambda x: f"₹{x:,.0f}")
            st.dataframe(dept_grp, use_container_width=True, hide_index=True)

            st.markdown("#### Full Employee List")
            disp = df[["emp_id","name","dept_name","designation","basic_salary","join_date","status"]].copy()
            disp.columns = ["Emp ID","Name","Dept","Designation","Basic (₹)","Join Date","Status"]
            disp["Basic (₹)"] = disp["Basic (₹)"].apply(lambda x: f"₹{x:,.0f}")
            st.dataframe(disp, use_container_width=True, hide_index=True)

            csv = df.to_csv(index=False)
            st.download_button("⬇ Download Full Report", csv, "employee_report.csv", use_container_width=True)

    with tab2:
        st.markdown("### Payroll Report")
        col1,col2 = st.columns(2)
        with col1: sel_month = st.selectbox("Month", MONTHS, index=datetime.now().month-1, key="rep_m")
        with col2: sel_year  = st.number_input("Year", value=datetime.now().year, key="rep_y")

        records = get_payroll(sel_month, sel_year)
        if records:
            df = pd.DataFrame(records)
            st.markdown(f"#### {sel_month} {sel_year} — {len(df)} employees")
            c1,c2,c3 = st.columns(3)
            with c1: st.metric("Total Gross", f"₹{df['gross_salary'].sum():,.0f}")
            with c2: st.metric("Total Deductions", f"₹{(df['pf_deduction']+df['tax_deduction']).sum():,.0f}")
            with c3: st.metric("Total Net Paid", f"₹{df['net_salary'].sum():,.0f}")

            disp = df[["emp_id","name","dept","gross_salary","pf_deduction","tax_deduction","net_salary","status"]].copy()
            for col in ["gross_salary","pf_deduction","tax_deduction","net_salary"]:
                disp[col] = disp[col].apply(lambda x: f"₹{x:,.0f}")
            disp.columns = ["Emp ID","Name","Dept","Gross","PF","Tax","Net","Status"]
            st.dataframe(disp, use_container_width=True, hide_index=True)

            csv = df.to_csv(index=False)
            st.download_button("⬇ Download Payroll Report", csv,
                               f"payroll_report_{sel_month}_{sel_year}.csv", use_container_width=True)
        else:
            st.info(f"No payroll data for {sel_month} {sel_year}.")

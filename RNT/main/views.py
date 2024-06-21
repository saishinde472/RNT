from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection, IntegrityError
from django.contrib.auth.hashers import make_password, check_password



def registration(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        username = request.POST['username']
        phone = request.POST['phone']
        department_id = request.POST['department']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        print(department_id)
        
        if password == confirm_password:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM emp WHERE username = %s", [username])
                if cursor.fetchone()[0] > 0:
                    messages.error(request, 'Username already exists')
                else:
                    cursor.execute("SELECT COUNT(*) FROM emp WHERE email = %s", [email])
                    if cursor.fetchone()[0] > 0:
                        messages.error(request, 'Email already exists')
                    else:
                        hashed_password = make_password(password)
                        cursor.execute("""
                            INSERT INTO emp (name, email, username, phone, department_id, password)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, [name, email, username, phone, department_id, hashed_password])
                        
                        messages.success(request, 'Your account has been created successfully')
                        return redirect('login')
        else:
            messages.error(request, 'Passwords do not match')
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name FROM departments ORDER BY name")
        departments = cursor.fetchall()
    print(departments)
    return render(request, 'registration.html', {'departments': departments})

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM emp WHERE username = %s", [username])
            user = cursor.fetchone()

            if user is not None:
                stored_password = user[2]
                if check_password(password, stored_password):
                    request.session['username'] = username 
                    # messages.success(request, 'You have been logged in successfully.')
                    return redirect('emp')
                else:
                    messages.error(request, 'Invalid password.')
            else:
                messages.error(request, 'Username not Found, Please Register')
                return redirect('registration')
    return render(request, 'login.html')


def emp(request):
    employees = []
    with connection.cursor() as cursor:
        cursor.execute("""SELECT emp.id, emp.name, emp.email, emp.phone, departments.name AS department
FROM emp
INNER JOIN departments ON emp.department_id = departments.id order by id;""")
        rows = cursor.fetchall()

        for row in rows:
            employee = {
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'phone': row[3],
                'department': row[4]
            }
            employees.append(employee)

    context = {
        'employees': employees
    }

    return render(request, 'emp.html', context)
def update_emp(request, employee_id):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        phone = request.POST['phone']
        department_id = request.POST['department']  
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE emp
                SET name = %s, email = %s, phone = %s, department_id = %s
                WHERE id = %s
            """, [name, email, phone, department_id, employee_id])

            messages.success(request, 'Employee details updated successfully')
            return redirect('emp') 
    else:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, email, phone, department_id
                FROM emp
                WHERE id = %s
            """, [employee_id])
            employee = cursor.fetchone() 
            if not employee:
                return HttpResponse('Employee not found', status=404)
            cursor.execute("SELECT id, name FROM departments")
            departments = cursor.fetchall()

        employee_data = {
            'id': employee[0],
            'name': employee[1],
            'email': employee[2],
            'phone': employee[3],
            'department_id': employee[4],
        }

        return render(request, 'update.html', {'employee': employee_data, 'departments': departments})


def delete_emp(request, employee_id):
    with connection.cursor() as cursor:
        try:
            cursor.execute("DELETE FROM emp WHERE id = %s", [employee_id])
            connection.commit()
            return redirect('emp')
        except IntegrityError as e:
            print(f"Error deleting employee: {e}")
            return redirect('emp')
        
def add_department(request):
    if request.method == 'POST':
        name = request.POST['name']
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM departments WHERE name = %s", [name])
            count = cursor.fetchone()[0]
            
            if count > 0:
                messages.error(request, 'Department already exists')
            else:
                cursor.execute("INSERT INTO departments (name) VALUES (%s)", [name])
                messages.success(request, 'Department added successfully')
                return redirect('add_department')
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name FROM departments order by id")
        departments = cursor.fetchall()

    return render(request, 'add_department.html', {'departments': departments})

def search_employees(request):
    search_name = request.GET.get('name', '')
    department_id = request.GET.get('department', '')

    employees = []
    selected_department_name = ''

    query = """
        SELECT emp.id, emp.name, emp.email, emp.phone, dep.name AS department_name
        FROM emp
        JOIN departments dep ON emp.department_id = dep.id
        WHERE (%s = '' OR emp.name LIKE %s)
          AND (%s = '' OR emp.department_id = %s)
    """
    params = [search_name, '%' + search_name + '%', department_id, department_id]

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        employees = cursor.fetchall()
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name FROM departments")
        departments = cursor.fetchall()

    return render(request, 'search.html', {
        'departments': departments,
        'employees': employees,
        'search_name': search_name,
        'selected_department_id': department_id
    })
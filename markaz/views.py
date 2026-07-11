from django.shortcuts import render, redirect, get_object_or_404
from .models import Group, Student, Attendance, Payment
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q

from django.shortcuts import render, get_object_or_404, redirect
from .models import Student, Teacher, Group, Attendance, Payment
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.contrib import messages
from django.core.exceptions import PermissionDenied # Taqiqlangan kirish uchun
from django.contrib.auth.decorators import login_required



from datetime import date

WEEKDAY_CODES = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
UZ_DAY_LABELS = {
    'mon': 'Dush', 'tue': 'Sesh', 'wed': 'Chor', 'thu': 'Pay',
    'fri': 'Jum', 'sat': 'Shan', 'sun': 'Yak',
}
WEEKDAYS = [
    ('mon', 'Dushanba'),
    ('tue', 'Seshanba'),
    ('wed', 'Chorshanba'),
    ('thu', 'Payshanba'),
    ('fri', 'Juma'),
    ('sat', 'Shanba'),
    ('sun', 'Yakshanba'),
]


@login_required(login_url='login')
def dashboard(request):

    today = timezone.now().date()
    five_days_later = today + timedelta(days=5)

    chronic_absent_students = []
    all_students = Student.objects.all()

    for student in all_students:
        last_3 = Attendance.objects.filter(student=student).order_by('-date')[:3]
        if last_3.count() == 3 and all(not att.is_present for att in last_3):
            chronic_absent_students.append(student)

    absent_records = Attendance.objects.filter(date=today, is_present=False)

    absent_unexcused = absent_records.filter(reason_type='sababsiz')
    absent_excused = absent_records.filter(reason_type='sababli')
    present_today = Attendance.objects.filter(date=today, is_present=True)

    warning_students = Student.objects.filter(
        pay_until__lte=five_days_later,
        pay_until__gte=today
    )

    debtors_count = Student.objects.filter(pay_until__lt=today).count()

    context = {
        'students_count': all_students.count(),
        'teachers_count': Teacher.objects.count(),
        'groups_count': Group.objects.count(),

        'absent_unexcused': absent_unexcused,
        'absent_excused': absent_excused,
        'present_today': present_today,
        'chronic_absent_students': chronic_absent_students,

        'warning_students': warning_students,
        'debtors_count': debtors_count,
        'today': today,
    }

    return render(request, 'dashboard.html', context)

@login_required
def group_attendance_view(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    students = group.students.all()
    
    if request.method == "POST":
        for student in students:
            # Checkbox holati
            status = request.POST.get(f'attendance_{student.id}') == 'on'
            # Sabab va Izoh
            reason = request.POST.get(f'reason_{student.id}')
            comment = request.POST.get(f'comment_{student.id}', "")

            # Davomatni saqlash yoki yangilash
            Attendance.objects.update_or_create(
                student=student, 
                group=group, 
                date=timezone.now().date(),
                defaults={
                    'is_present': status,
                    'reason_type': reason if not status else None,
                    'comment': comment if not status else ""
                }
            )
            
            # SMS yuborish (faqat sababsiz bo'lsa yuborishni sozlasa ham bo'ladi)
            if not status and reason == 'sababsiz':
                send_absent_sms(student.phone, student.full_name)
                
        return redirect('dashboard')

    # 3 marta dars qoldirganlarni dashboardda chiqarish uchun mantiqni 
    # alohida dashboard viewda yozish tavsiya etiladi.
    return render(request, 'attendance.html', {'group': group, 'students': students})

def send_absent_sms(phone, name):
    # Bu yerda SMS yuborish kodi bo'ladi
    print(f"SMS: {name} darsga kelmadi. Tel: {phone}")
from django.utils import timezone
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from .models import Student, Payment

from django.contrib import messages

def student_payment(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    group_price = student.group.price

    if request.method == "POST":
        try:
            amount = int(float(request.POST.get('amount')))
        except (ValueError, TypeError):
            amount = 0

        payment_type = request.POST.get('payment_type')
        custom_date = request.POST.get('pay_until')
        receipt_file = request.FILES.get('receipt')   # <-- YANGI QATOR

        # 1. To'lovni saqlash
        Payment.objects.create(
            student=student,
            amount=amount,
            payment_type=payment_type,
            receipt_image=receipt_file,                # <-- YANGI QATOR
        )

        # 2. Eskini unutish va yangi balansni o'rnatish
        student.balance = amount

        # 3. Xabarnoma va Muddat mantiqi
        if amount < group_price:
            difference = group_price - amount
            messages.warning(request, f"Siz {amount} so'm to'lov qildingiz. To'liq kurs uchun yana {difference} so'm to'lashingiz kerak.")
        else:
            messages.success(request, f"To'lov muvaffaqiyatli qabul qilindi: {amount} so'm.")

        # 4. Sana mantiqi
        if custom_date:
            student.pay_until = custom_date
        elif amount >= group_price:
            student.pay_until = timezone.now().date() + timedelta(days=30)

        student.save()
        return redirect('student_list')

    return render(request, 'add_payment.html', {'student': student})



# 2. O'quvchilar ro'yxati
@login_required
def student_list(request):
    students = Student.objects.all()
    return render(request, 'students.html', {'students': students})

# 3. Ustozlar ro'yxati
@login_required
def teacher_list(request):
    teachers = Teacher.objects.all()
    return render(request, 'teachers.html', {'teachers': teachers})

# 4. Guruhlar ro'yxati
@login_required
def group_list(request):
    groups = Group.objects.all()
    return render(request, 'groups.html', {'groups': groups})

# 5. Davomat hisoboti (Bugun kim keldi, kim kelmadi)
# @login_required
# def attendance_report(request):
#     today = timezone.now().date()
#     absent = Attendance.objects.filter(date=today, is_present=False)
#     present = Attendance.objects.filter(date=today, is_present=True)
#     return render(request, 'attendance_report.html', {
#         'absent': absent, 
#         'present': present, 
#         'today': today
#     })


from datetime import timedelta
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

EDIT_WINDOW_HOURS = 1  # tahrirlash uchun berilgan muddat



from datetime import datetime

@login_required
def attendance_report(request):
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    now = timezone.now()

    records = (
        Attendance.objects
        .filter(date=selected_date)
        .select_related('student', 'group')
        .order_by('student__full_name')
    )

    absent = []
    present = []
    for a in records:
        a.is_editable = bool(a.created_at) and (now - a.created_at) <= timedelta(hours=EDIT_WINDOW_HOURS)
        if a.is_present:
            present.append(a)
        else:
            absent.append(a)

    return render(request, 'attendance_report.html', {
        'selected_date': selected_date,
        'absent': absent,
        'present': present,
        'prev_date': selected_date - timedelta(days=1),
        'next_date': selected_date + timedelta(days=1),
        'today': timezone.now().date(),
    })


@login_required
def attendance_edit(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)

    # 12 soatdan o'tgan bo'lsa — bloklaymiz
    if timezone.now() - attendance.created_at > timedelta(hours=EDIT_WINDOW_HOURS):
        messages.error(request, "❌ Bu yozuvni tahrirlash muddati tugagan (12 soat). Endi o'zgartirib bo'lmaydi.")
        return redirect('attendance_report')

    if request.method == 'POST':
        attendance.is_present = request.POST.get('is_present') == 'on'
        attendance.comment = request.POST.get('comment', '')
        attendance.save()
        messages.success(request, "✅ Davomat muvaffaqiyatli yangilandi.")
        return redirect('attendance_report')

    return render(request, 'attendance_edit.html', {'attendance': attendance})



from django.shortcuts import render, get_object_or_404
from .models import Student, Payment, Attendance
@login_required
def student_detail(request, student_id):
    # O'quvchini ID bo'yicha topamiz, agar yo'q bo'lsa 404 xatolik beradi
    student = get_object_or_404(Student, id=student_id)
    
    # O'quvchining barcha to'lovlarini eng oxirgisidan boshlab olamiz
    payments = student.payments.all().order_by('-date')
    
    # O'quvchining davomat tarixini olamiz
    attendances = Attendance.objects.filter(student=student).order_by('-date')
    
    context = {
        'student': student,
        'payments': payments,
        'attendances': attendances,
    }
    
    return render(request, 'student_detail.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from .forms import StudentForm, TeacherForm, GroupForm, SimpleTeacherForm
from .models import Student, Teacher, Group

# --- O'QUVCHILAR UCHUN ---
@login_required
def student_create(request):
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('student_list')
    else:
        form = StudentForm()
    return render(request, 'form_template.html', {'form': form, 'title': "Yangi o'quvchi qo'shish"})
@login_required
def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('student_list')
    else:
        form = StudentForm(instance=student)
    return render(request, 'form_template.html', {'form': form, 'title': "O'quvchini tahrirlash"})
@login_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        student.delete()
        return redirect('student_list')
    return render(request, 'confirm_delete.html', {'obj': student})

# --- GURUHLAR UCHUN ---
# @login_required
# def group_create(request):
#     if request.method == "POST":
#         form = GroupForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('group_list')
#     form = GroupForm()
#     return render(request, 'form_template.html', {'form': form, 'title': "Yangi guruh ochish"})


@login_required
def group_create(request):
    teachers = Teacher.objects.all()

    if request.method == "POST":
        name = request.POST.get('name')
        teacher_id = request.POST.get('teacher')
        price = request.POST.get('price') or 0
        selected_days = request.POST.getlist('days')
        start_time = request.POST.get('start_time') or None
        end_time = request.POST.get('end_time') or None

        Group.objects.create(
            name=name,
            teacher_id=teacher_id or None,
            price=price,
            days=','.join(selected_days),
            start_time=start_time,
            end_time=end_time,
        )
        messages.success(request, "✅ Guruh muvaffaqiyatli yaratildi.")
        return redirect('group_list')

    return render(request, 'group_form.html', {
        'teachers': teachers,
        'weekdays': WEEKDAYS,
        'title': "Yangi guruh ochish",
    })









@login_required
def schedule_view(request):
    groups = Group.objects.select_related('teacher').all().order_by('name')
    today = timezone.now().date()

    show_full_range = request.GET.get('range') == 'full'

    try:
        week_offset = int(request.GET.get('week', 0))
    except (ValueError, TypeError):
        week_offset = 0

    if show_full_range:
        # 1 oy oldin — 1 oy keyin
        start_date = today - timedelta(days=30)
        end_date = today + timedelta(days=30)
    else:
        # faqat bitta hafta (Dushanbadan boshlab), week_offset bilan siljiydi
        current_monday = today - timedelta(days=today.weekday())
        week_start = current_monday + timedelta(weeks=week_offset)
        start_date = week_start
        end_date = week_start + timedelta(days=6)

    # Haftalarga bo'lib chiqamiz (har doim Dushanbadan boshlanadi)
    weeks = []
    cursor = start_date - timedelta(days=start_date.weekday())
    while cursor <= end_date:
        week_days = []
        for i in range(7):
            d = cursor + timedelta(days=i)
            code = WEEKDAY_CODES[d.weekday()]
            week_days.append({
                'date': d,
                'code': code,
                'label': UZ_DAY_LABELS[code],
                'is_today': d == today,
            })
        weeks.append(week_days)
        cursor += timedelta(days=7)

    return render(request, 'schedule.html', {
        'groups': groups,
        'weeks': weeks,
        'show_full_range': show_full_range,
        'week_offset': week_offset,
        'today': today,
    })


@login_required
def schedule_edit(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    if request.method == 'POST':
        selected_days = request.POST.getlist('days')
        group.days = ','.join(selected_days)
        group.start_time = request.POST.get('start_time') or None
        group.end_time = request.POST.get('end_time') or None
        group.save()
        messages.success(request, "✅ Dars jadvali yangilandi.")
        return redirect('schedule_view')

    return render(request, 'schedule_edit.html', {
        'group': group,
        'weekdays': WEEKDAYS,
        'selected_days': group.get_days_list(),
    })





# Ustozlar ro'yxati
@login_required
def teacher_list(request):
    teachers = Teacher.objects.all()
    return render(request, 'teachers.html', {'teachers': teachers})

# Ustoz qo'shish
@login_required
def teacher_create(request):
    form = TeacherForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('teacher_list')
    return render(request, 'form_template.html', {'form': form, 'title': "Yangi ustoz"})

# Ustozni tahrirlash
@login_required
def teacher_update(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    form = TeacherForm(request.POST or None, instance=teacher)
    if form.is_valid():
        form.save()
        return redirect('teacher_list')
    return render(request, 'form_template.html', {'form': form, 'title': "Ustoz ma'lumotlarini tahrirlash"})

# Ustozni o'chirish
@login_required
def teacher_delete(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == "POST":
        teacher.delete()
        return redirect('teacher_list')
    return render(request, 'confirm_delete.html', {'obj': teacher})





@login_required
def move_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    groups = Group.objects.exclude(id=student.group.id) # Hozirgi guruhidan boshqa hamma guruhlar

    if request.method == "POST":
        new_group_id = request.POST.get('new_group')
        new_group = get_object_or_404(Group, id=new_group_id)
        
        # O'quvchini yangi guruhga biriktirish
        student.group = new_group
        student.save()
        
        return redirect('student_detail', student_id=student.id)

    return render(request, 'move_student.html', {
        'student': student,
        'groups': groups
    })

@login_required
def change_group_teacher(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    teachers = Teacher.objects.all()

    if request.method == "POST":
        new_teacher_id = request.POST.get('new_teacher')
        new_teacher = get_object_or_404(Teacher, id=new_teacher_id)
        
        group.teacher = new_teacher
        group.save()
        
        return redirect('group_list')

    return render(request, 'change_teacher.html', {
        'group': group,
        'teachers': teachers
    })
@login_required
def teacher_create_simple(request):
    if request.method == "POST":
        form = SimpleTeacherForm(request.POST)
        if form.is_valid():
            # 1. User yaratish
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name']
            )
            # 2. Teacher profilini yaratish
            teacher = Teacher.objects.create(
                user=user,
                phone=form.cleaned_data['phone']
            )
            
            # 3. Guruhga ustozni biriktirish (Ixtiyoriy qism)
            group = form.cleaned_data.get('group') # get ishlatish xavfsizroq
            if group is not None:  # Agar guruh tanlangan bo'lsagina ishlaydi
                group.teacher = teacher
                group.save()
            
            return redirect('teacher_list')
    else:
        form = SimpleTeacherForm()
    
    return render(request, 'teacher_add_custom.html', {'form': form})

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login

def custom_login(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(username=u, password=p)
        
        if user is not None:
            auth_login(request, user)
            
            # KIMLIGINI TEKSHIRISH
            if user.is_superuser:
                # Admin bo'lsa - Dashboardga
                return redirect('dashboard')
            else:
                # Ustoz (oddiy user) bo'lsa - Tashqi saytga
                return redirect('https://kun.uz')
        else:
            return render(request, 'login.html', {'error': 'Login yoki parol xato!'})
            
    return render(request, 'login.html')


from django.contrib.auth import logout as auth_logout

def logout_view(request):
    if request.method == 'POST':
        auth_logout(request) # Tizimdan chiqarish
        return redirect('login') # Chiqib ketgandan keyin login sahifasiga qaytarish
    
    # Agar kimdir URL orqali (GET) kirmoqchi bo'lsa, uni ham login sahifasiga haydaymiz
    return redirect('login')





from .models import Student, Payment, Expense
from datetime import timedelta
from django.db.models import Sum
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect





from datetime import datetime
import calendar

@login_required
def financial_report(request):
    today = timezone.now().date()

    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    if start_str and end_str:
        try:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = today.replace(day=1)
            end_date = today
    else:
        # standart: joriy oy boshidan bugungacha
        start_date = today.replace(day=1)
        end_date = today

    payments = (
        Payment.objects
        .filter(date__date__gte=start_date, date__date__lte=end_date)
        .select_related('student', 'student__group')
        .order_by('-date')
    )
    expenses = (
        Expense.objects
        .filter(date__gte=start_date, date__lte=end_date)
        .order_by('-date')
    )

    total_income = payments.aggregate(total=Sum('amount'))['total'] or 0
    total_expense = expenses.aggregate(total=Sum('amount'))['total'] or 0
    net_profit = total_income - total_expense

    # Tezkor tugmalar uchun oldindan hisoblangan sanalar
    this_month_start = today.replace(day=1)

    last_month_end = this_month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    return render(request, 'financial_report.html', {
        'payments': payments,
        'expenses': expenses,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_profit': net_profit,
        'start_date': start_date,
        'end_date': end_date,
        'today': today,
        'this_month_start': this_month_start,
        'last_month_start': last_month_start,
        'last_month_end': last_month_end,
    })

@login_required
def add_expense(request):
    if request.method == 'POST':
        Expense.objects.create(
            title=request.POST.get('title'),
            expense_type=request.POST.get('expense_type'),
            amount=request.POST.get('amount'),
            date=request.POST.get('date') or timezone.now().date(),
            comment=request.POST.get('comment', ''),
        )
        messages.success(request, "✅ Xarajat muvaffaqiyatli qo'shildi.")
        return redirect('financial_report')

    return render(request, 'add_expense.html')




from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

def delete_group(request, pk):
    group = get_object_or_404(Group, pk=pk)

    if request.method == "POST":
        group.delete()
        messages.success(request, "Guruh muvaffaqiyatli o'chirildi.")

    return redirect("group_list")
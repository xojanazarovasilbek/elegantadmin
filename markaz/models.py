from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
# 1. Ustozlar
class Teacher(models.Model):
    name = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE , null=True, blank=True)
    phone = models.CharField(max_length=13)
    
    def __str__(self):
        return self.user.get_full_name()or self.user.username

# 2. Guruhlar
class Group(models.Model):
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # YANGI MAYDONLAR
    start_time = models.TimeField(null=True, blank=True, verbose_name="Boshlanish vaqti")
    end_time = models.TimeField(null=True, blank=True, verbose_name="Tugash vaqti")
    days = models.CharField(
        max_length=50, blank=True, default='',
        verbose_name="Dars kunlari",
        help_text="mon,wed,fri kabi vergul bilan ajratilgan kunlar"
    )

    def get_days_list(self):
        return [d.strip() for d in self.days.split(',') if d.strip()]

    def __str__(self):
        return self.name

# 3. O'quvchilar
class Student(models.Model):
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=13)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='students')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return self.full_name
    
    pay_until = models.DateField(null=True, blank=True, verbose_name="To'lov muddati")

    @property
    def days_left(self):
        if self.pay_until:
            import datetime
            delta = self.pay_until - datetime.date.today()
            return delta.days
        return None

# 4. Davomat (SMS mantiqi bilan)
class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    date = models.DateField()
    is_present = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    # SHU IKKI QATORNI QO'SHING
    reason_type = models.CharField(
        max_length=20, 
        choices=[('sababli', 'Sababli'), ('sababsiz', 'Sababsiz')], 
        null=True, 
        blank=True
    )
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.full_name} - {self.date}"

# 5. To'lovlar (Naqd/Click va Chek rasmi)
class Payment(models.Model):
    PAYMENT_TYPES = (
        ('cash', 'Naqd'),
        ('click', 'Click / Payme'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPES)
    receipt_image = models.ImageField(upload_to='receipts/', null=True, blank=True) # Chek rasmi
    date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # To'lov qilinganda o'quvchi balansini avtomat oshirish
        self.student.balance += Decimal(self.amount)
        self.student.save()
        super().save(*args, **kwargs)




class Expense(models.Model):
    EXPENSE_TYPES = [
        ('salary', "Ustozlarga maosh"),
        ('rent', "Ijara"),
        ('utility', "Kommunal (svet/gaz/suv)"),
        ('repair', "Ta'mirlash"),
        ('other', "Boshqa"),
    ]
    title = models.CharField(max_length=255, verbose_name="Nomi")
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPES, default='other', verbose_name="Turi")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Summa")
    date = models.DateField(default=timezone.now, verbose_name="Sana")
    comment = models.TextField(blank=True, null=True, verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.title} - {self.amount} so'm"
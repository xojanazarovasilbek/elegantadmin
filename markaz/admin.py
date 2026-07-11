from django.contrib import admin
from django.utils.html import format_html
from .models import Teacher, Group, Student, Attendance, Payment

# 1. Ustozlar uchun admin
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name','user', 'phone')
    search_fields = ('user__first_name', 'user__last_name', 'phone')

# 2. Guruhlar uchun admin
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'price')
    list_filter = ('teacher',)
    search_fields = ('name',)

# 3. O'quvchilar uchun admin
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'group', 'phone', 'balance_status')
    list_filter = ('group',)
    search_fields = ('full_name', 'phone')

    # Balans manfiy bo'lsa qizil rangda ko'rsatish
    def balance_status(self, obj):
        color = 'green' if obj.balance >= 0 else 'red'
        return format_html('<b style="color: {};">{} so\'m</b>', color, obj.balance)
    balance_status.short_description = "Balans"

# 4. Davomat uchun admin
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'group', 'date', 'is_present')
    list_filter = ('date', 'is_present', 'group')
    date_hierarchy = 'date' # Sanalar bo'yicha navigatsiya

# 5. To'lovlar uchun admin (Rasm ko'rinishi bilan)
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'payment_type', 'date', 'show_receipt')
    list_filter = ('payment_type', 'date')
    readonly_fields = ('show_receipt_large',) # Rasmni tahrirlab bo'lmaydigan qilish

    # Kichik rasmcha (listda ko'rinishi)
    def show_receipt(self, obj):
        if obj.receipt_image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.receipt_image.url)
        return "Rasm yo'q"
    show_receipt.short_description = "Chek"

    # Katta rasm (ichiga kirganda ko'rinishi)
    def show_receipt_large(self, obj):
        if obj.receipt_image:
            return format_html('<a href="{0}" target="_blank"><img src="{0}" width="300" /></a>', obj.receipt_image.url)
        return "Rasm yuklanmagan"
    show_receipt_large.short_description = "Chek nusxasi"




from .models import Expense

admin.site.register(Expense)
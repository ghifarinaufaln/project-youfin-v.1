from django.contrib import admin
from .models import Profile, Category, Budget, Transaction

# Register your models here.
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'address', 'birth_date', 'gender']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'description', 'category_type']

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'month', 'year', 'amount']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'amount', 'transaction_date', 'description', 'transaction_type']
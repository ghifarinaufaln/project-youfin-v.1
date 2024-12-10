from django import forms
from .models import Transaction, Budget, Category

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['category', 'amount', 'transaction_date', 'description', 'transaction_type']
        widgets = {
            'transaction_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Jumlah transaksi harus lebih besar dari 0.")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        transaction_type = cleaned_data.get('transaction_type')
        
        # Validasi kesesuaian kategori dengan tipe transaksi
        if category and transaction_type:
            if category.category_type != transaction_type:
                raise forms.ValidationError("Kategori tidak sesuai dengan tipe transaksi.")
        
        return cleaned_data

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'amount', 'month', 'year']

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Jumlah anggaran harus lebih besar dari 0.")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        
        # Pastikan kategori adalah kategori pengeluaran
        if category and category.category_type != 'expense':
            raise forms.ValidationError("Anggaran hanya dapat dibuat untuk kategori pengeluaran.")
        
        return cleaned_data

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'category_type']

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Nama kategori tidak boleh kosong.")
        return name
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('L', 'Laki-laki'), ('P', 'Perempuan')], blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    def __str__(self):
        return self.user.username

    @property
    def is_complete(self):
        """
        Properti untuk mengecek apakah semua data profil terisi dengan lengkap.
        Memeriksa: nomor telepon, alamat, tanggal lahir, jenis kelamin, dan foto profil.
        """
        return all([
            self.phone_number, 
            self.address, 
            self.birth_date, 
            self.gender, 
            self.profile_picture
        ])

    def delete_profile_picture(self):
        """
        Fungsi untuk menghapus foto profil dari server dan mengatur ulang field profile_picture menjadi None.
        """
        if self.profile_picture:
            self.profile_picture.delete(save=False)  # Menghapus file dari media folder
            self.profile_picture = None  # Set field profile_picture ke None
            self.save()  # Menyimpan perubahan ke database

class Category(models.Model):
    """
    Kategori untuk transaksi dan anggaran
    Tipe: Pemasukan (income) atau Pengeluaran (expense)
    """
    CATEGORY_TYPES = [
        ('income', 'Pemasukan'),
        ('expense', 'Pengeluaran')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category_type = models.CharField(max_length=10, choices=CATEGORY_TYPES)
    
    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"

class Budget(models.Model):
    """
    Model untuk perencanaan anggaran bulanan
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, limit_choices_to={'category_type': 'expense'})
    month = models.IntegerField()  # 1-12
    year = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    class Meta:
        unique_together = ('user', 'category', 'month', 'year')
    
    def __str__(self):
        return f"{self.category.name} Budget - {self.month}/{self.year}"
    
    def get_total_spent(self):
        """
        Menghitung total pengeluaran dalam kategori dan bulan ini
        """
        start_date = timezone.datetime(self.year, self.month, 1)
        if self.month == 12:
            end_date = timezone.datetime(self.year + 1, 1, 1)
        else:
            end_date = timezone.datetime(self.year, self.month + 1, 1)
        
        return Transaction.objects.filter(
            user=self.user,
            category=self.category,
            transaction_date__gte=start_date,
            transaction_date__lt=end_date,
            transaction_type='expense'
        ).aggregate(total=models.Sum('amount'))['total'] or 0

    def get_remaining_budget(self):
        """
        Menghitung sisa anggaran
        """
        return max(self.amount - self.get_total_spent(), 0)

class Transaction(models.Model):
    """
    Model untuk mencatat transaksi keuangan
    """
    TRANSACTION_TYPES = [
        ('income', 'Pemasukan'),
        ('expense', 'Pengeluaran')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    transaction_date = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    
    def __str__(self):
        return f"{self.transaction_type.capitalize()} - {self.category.name} - {self.amount}"
    
    class Meta:
        ordering = ['-transaction_date']
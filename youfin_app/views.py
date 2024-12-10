from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .decorators import unauthenticated_user

from .models import Profile
from django.contrib.auth import update_session_auth_hash
from django.db.models import Sum
from django.utils import timezone
from .models import Transaction, Category, Budget
from django.utils.timezone import now

# Create your views here.
# views front-end
@unauthenticated_user
def index(request):
    return render(request, 'index.html')

@unauthenticated_user
def login_user(request):
    if request.method == 'POST':
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')

        # Inisialisasi context untuk mengembalikan data form
        context = {
            'form_data': {
                'username': username_or_email,
            }
        }

        # Cari user berdasarkan username atau email
        user = User.objects.filter(email=username_or_email).first() or User.objects.filter(username=username_or_email).first()

        if user:
            # Cek apakah pengguna adalah superuser
            if user.is_superuser:
                messages.error(request, "Akses ditolak! Superuser (Admin) tidak dapat login ke website aplikasi.")
                return render(request, 'login/index.html')

            # Autentikasi pengguna
            user = authenticate(username=user.username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    if user.last_name == "-":
                        messages.success(request, f"Login berhasil! Selamat datang, {user.first_name}, di YouFin.")
                    else:
                        messages.success(request, f"Login berhasil! Selamat datang, {user.first_name} {user.last_name}, di YouFin.")
                    return redirect('youfin_app:dashboard')
                else:
                    messages.error(request, "Akun Anda tidak aktif.")
            else:
                messages.error(request, "Password salah!")
        else:
            messages.error(request, "Username atau email tidak ditemukan!")

        return render(request, 'login/index.html', context)

    return render(request, 'login/index.html', {'form_data': {}})

# user logout
@login_required
def logout_user(request):
    logout(request)
    # messages.success(request, "Anda telah berhasil logout.")
    return HttpResponseRedirect(reverse('login'))

@unauthenticated_user
def registration_user(request):
    if request.method == "POST":
        firstname = request.POST.get('firstname')  
        lastname = request.POST.get('lastname') 
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('konfirmasiPassword')

        # Menyusun context untuk mengirimkan data ke template jika terjadi kesalahan
        context = {
            'form_data': {
                'firstname': firstname,
                'lastname': lastname,
                'username': username,
                'email': email,
            }
        }

        # Validasi jika ada field yang kosong
        if not firstname:
            messages.error(request, "Nama depan tidak boleh kosong!")
        if not lastname:
            messages.error(request, "Nama belakang tidak boleh kosong!")
        if not username:
            messages.error(request, "Username tidak boleh kosong!")
        if not email:
            messages.error(request, "Email tidak boleh kosong!")
        if not password:
            messages.error(request, "Password tidak boleh kosong!")
        if not confirm_password:
            messages.error(request, "Konfirmasi password tidak boleh kosong!")

        # Validasi jika nama depan tidak diawali dengan huruf besar pada setiap kata
        if firstname and not all(word.istitle() for word in firstname.split()):
            messages.error(request, "Nama depan harus diawali dengan huruf besar pada setiap kata!")

        # Validasi nama belakang jika tidak berisi simbol "-" dan tidak diawali huruf besar
        if lastname != "-" and lastname and not all(word.istitle() for word in lastname.split()):
            messages.error(request, "Nama belakang harus diawali dengan huruf besar pada setiap kata!")

        # Jika ada error, kembalikan ke halaman registrasi dengan pesan error
        if not username or not email or not password or not confirm_password or not firstname or not lastname:
            return render(request, 'sign_up/index.html', context)

        # Validasi password dan konfirmasi password tidak cocok
        if password != confirm_password:
            messages.error(request, "Password dan konfirmasi password tidak cocok!")
            return render(request, 'sign_up/index.html', context)

        # Validasi username sudah terdaftar
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username sudah digunakan!")
            return render(request, 'sign_up/index.html', context)

        # Validasi email sudah terdaftar
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email sudah terdaftar!")
            return render(request, 'sign_up/index.html', context)

        # Validasi password sesuai dengan aturan di AUTH_PASSWORD_VALIDATORS
        try:
            validate_password(password)  # Validasi dengan aturan Django
        except ValidationError as e:
            for error in e.messages:
                # Menambahkan pesan error kustom untuk password
                if "This password is too short" in error:
                    messages.error(request, "Password harus terdiri dari minimal 8 karakter!")
                elif "This password is too common" in error:
                    messages.error(request, "Password terlalu umum, coba gunakan kombinasi yang lebih kuat!")
                elif "This password is entirely numeric" in error:
                    messages.error(request, "Password tidak boleh hanya terdiri dari angka!")
                else:
                    messages.error(request, error)  # Pesan lainnya dari validasi default
            return render(request, 'sign_up/index.html', context)

        # Menangani nama belakang hanya tanda "-", itu berarti user hanya memiliki 1 kata didalam namanya
        if lastname == "-":
            lastname = "-"  

        # Membuat user baru dan mengenkripsi password
        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = firstname  # Menyimpan nama depan
        user.last_name = lastname    # Menyimpan nama belakang
        user.save()

        messages.success(request, "Registrasi berhasil! Silakan login.")
        return redirect('login')

    # Menampilkan halaman registrasi awal dengan context kosong
    return render(request, 'sign_up/index.html', {'form_data': {}})


# views back-end
@login_required
def dashboard(request):
    return render(request, 'page/dashboard/index.html')

@login_required
def transaksi(request):
    """
    Halaman untuk mengelola dan melihat transaksi
    """
    # Filter transaksi berdasarkan pengguna yang sedang login
    transactions = Transaction.objects.filter(user=request.user)
    
    # Hitung total pemasukan dan pengeluaran
    income_total = transactions.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0
    expense_total = transactions.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0
    
    # Persiapkan context untuk template
    context = {
        'transactions': transactions,
        'income_total': income_total,
        'expense_total': expense_total,
        'net_balance': income_total - expense_total,
        'categories': Category.objects.filter(user=request.user)
    }
    
    return render(request, 'page/transaksi/index.html', context)

@login_required
def add_transaction(request):
    """
    Tambah transaksi baru
    """
    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            amount = request.POST.get('amount')
            transaction_type = request.POST.get('transaction_type')
            description = request.POST.get('description')
            transaction_date = request.POST.get('transaction_date')
            
            # Validasi input
            if not all([category_id, amount, transaction_type]):
                messages.error(request, "Harap lengkapi semua field yang diperlukan!")
                return redirect('youfin_app:add_transaction')
            
            category = get_object_or_404(Category, id=category_id, user=request.user)
            
            Transaction.objects.create(
                user=request.user,
                category=category,
                amount=amount,
                transaction_type=transaction_type,
                description=description,
                transaction_date=transaction_date or timezone.now()
            )
            
            messages.success(request, "Transaksi berhasil ditambahkan!")
            return redirect('youfin_app:transaksi')
        
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    # Untuk GET request, tampilkan form
    categories = Category.objects.filter(user=request.user)
    return render(request, 'page/transaksi/add_transaction.html', {'categories': categories})

@login_required
def edit_transaction(request, transaction_id):
    """
    Edit an existing transaction
    """
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            amount = request.POST.get('amount')
            transaction_type = request.POST.get('transaction_type')
            description = request.POST.get('description')
            transaction_date = request.POST.get('transaction_date')
            
            # Validasi input
            if not all([category_id, amount, transaction_type]):
                messages.error(request, "Harap lengkapi semua field yang diperlukan!")
                return redirect('youfin_app:edit_transaction', transaction_id=transaction_id)
            
            category = get_object_or_404(Category, id=category_id, user=request.user)
            
            # Update transaksi
            transaction.category = category
            transaction.amount = amount
            transaction.transaction_type = transaction_type
            transaction.description = description
            transaction.transaction_date = transaction_date or timezone.now()
            transaction.save()
            
            messages.success(request, "Transaksi berhasil diperbarui!")
            return redirect('youfin_app:manage_transactions')
        
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    # Untuk GET request, tampilkan form edit
    categories = Category.objects.filter(user=request.user)
    context = {
        'transaction': transaction,
        'categories': categories
    }
    return render(request, 'page/transaksi/edit_transaction.html', context)

@login_required
def delete_transaction(request, transaction_id):
    """
    Hapus transaksi
    """
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)
    
    try:
        transaction.delete()
        messages.success(request, "Transaksi berhasil dihapus!")
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan saat menghapus transaksi: {str(e)}")
    
    return redirect('youfin_app:manage_transactions')

@login_required
def manage_budgets(request):
    """
    Halaman untuk mengelola anggaran
    """
    current_year = timezone.now().year
    current_month = timezone.now().month
    
    # Ambil atau buat budget untuk bulan ini
    budgets = Budget.objects.filter(
        user=request.user, 
        year=current_year, 
        month=current_month
    )
    
    context = {
        'budgets': [
            {
                'budget': budget, 
                'total_spent': budget.get_total_spent(),
                'remaining': budget.get_remaining_budget()
            } for budget in budgets
        ],
        'categories': Category.objects.filter(user=request.user, category_type='expense')
    }
    
    return render(request, 'page/anggaran/index.html', context)

@login_required
def add_budget(request):
    """
    Tambah anggaran baru
    """
    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            amount = request.POST.get('amount')
            month = request.POST.get('month')
            year = request.POST.get('year')
            
            # Validasi input
            if not all([category_id, amount, month, year]):
                messages.error(request, "Harap lengkapi semua field yang diperlukan!")
                return redirect('youfin_app:add_budget')
            
            category = get_object_or_404(Category, id=category_id, user=request.user)
            
            Budget.objects.create(
                user=request.user,
                category=category,
                amount=amount,
                month=month,
                year=year
            )
            
            messages.success(request, "Anggaran berhasil ditambahkan!")
            return redirect('youfin_app:manage_budgets')
        
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    # Untuk GET request, tampilkan form
    categories = Category.objects.filter(user=request.user, category_type='expense')
    return render(request, 'page/anggaran/add_budget.html', {'categories': categories})

@login_required
def edit_budget(request, budget_id):
    """
    Edit anggaran yang sudah ada
    """
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    
    if request.method == 'POST':
        try:
            category_id = request.POST.get('category')
            amount = request.POST.get('amount')
            month = request.POST.get('month')
            year = request.POST.get('year')
            
            # Validasi input
            if not all([category_id, amount, month, year]):
                messages.error(request, "Harap lengkapi semua field yang diperlukan!")
                return redirect('youfin_app:edit_budget', budget_id=budget_id)
            
            category = get_object_or_404(Category, id=category_id, user=request.user)
            
            # Update budget
            budget.category = category
            budget.amount = amount
            budget.month = month
            budget.year = year
            budget.save()
            
            messages.success(request, "Anggaran berhasil diperbarui!")
            return redirect('youfin_app:manage_budgets')
        
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    # Untuk GET request, tampilkan form edit
    categories = Category.objects.filter(user=request.user, category_type='expense')
    context = {
        'budget': budget,
        'categories': categories
    }
    return render(request, 'page/anggaran/edit_budget.html', context)

@login_required
def delete_budget(request, budget_id):
    """
    Hapus anggaran
    """
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    
    try:
        budget.delete()
        messages.success(request, "Anggaran berhasil dihapus!")
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan saat menghapus anggaran: {str(e)}")
    
    return redirect('youfin_app:manage_budgets')

@login_required
def manage_categories(request):
    """
    Halaman untuk mengelola kategori
    """
    categories = Category.objects.filter(user=request.user)
    return render(request, 'page/kategori/index.html', {'categories': categories})

@login_required
def add_category(request):
    """
    Tambah kategori baru
    """
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            category_type = request.POST.get('category_type')
            description = request.POST.get('description', '')  # Optional description
            
            # Validasi input
            if not name or not category_type:
                messages.error(request, "Harap lengkapi nama dan tipe kategori!")
                return redirect('youfin_app:add_category')
            
            Category.objects.create(
                user=request.user,
                name=name,
                category_type=category_type,
                description=description
            )
            
            messages.success(request, "Kategori berhasil ditambahkan!")
            return redirect('youfin_app:manage_categories')
        
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    return render(request, 'page/kategori/add_category.html')

@login_required
def edit_category(request, category_id):
    """
    Edit kategori yang sudah ada
    """
    category = get_object_or_404(Category, id=category_id, user=request.user)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            category_type = request.POST.get('category_type')
            description = request.POST.get('description', '')  # Optional description
            
            # Validasi input
            if not name or not category_type:
                messages.error(request, "Harap lengkapi nama dan tipe kategori!")
                return redirect('youfin_app:edit_category', category_id=category_id)
            
            # Update kategori
            category.name = name
            category.category_type = category_type
            category.description = description
            category.save()
            
            messages.success(request, "Kategori berhasil diperbarui!")
            return redirect('youfin_app:manage_categories')
        
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    # Untuk GET request, tampilkan form edit
    context = {
        'category': category
    }
    return render(request, 'page/kategori/edit_category.html', context)

@login_required
def delete_category(request, category_id):
    """
    Hapus kategori
    """
    category = get_object_or_404(Category, id=category_id, user=request.user)
    
    try:
        # Periksa apakah kategori sudah pernah digunakan di transaksi atau anggaran
        if Transaction.objects.filter(category=category).exists() or Budget.objects.filter(category=category).exists():
            messages.error(request, "Kategori tidak dapat dihapus karena sudah digunakan dalam transaksi atau anggaran!")
            return redirect('youfin_app:manage_categories')
        
        category.delete()
        messages.success(request, "Kategori berhasil dihapus!")
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan saat menghapus kategori: {str(e)}")
    
    return redirect('youfin_app:manage_categories')

# @login_required
# def anggaran(request):
#     return render(request, 'page/anggaran/index.html')

# @login_required
# def transaksi(request):
#     return render(request, 'page/transaksi/index.html')

@login_required
def tips(request):
    return render(request, 'page/tips/index.html')

# pengaturan profile pengguna
@login_required
def pengaturan(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'page/pengaturan/index.html', {'profile': profile, 'user_status': 'premium' if request.user.groups.filter(name='Premium').exists() else 'standar'})

# Tambahkan fungsi validasi untuk memeriksa ekstensi gambar
def is_valid_image(file):
    # Daftar ekstensi gambar yang diperbolehkan
    allowed_extensions = ['.jpg', '.jpeg', '.png']
    # Periksa apakah file memiliki ekstensi yang valid
    if any(file.name.endswith(ext) for ext in allowed_extensions):
        return True
    return False

@login_required
def edit_pengaturan(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Ambil data dari form
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        birth_date = request.POST.get('birth_date')
        gender = request.POST.get('gender')
        profile_picture = request.FILES.get('profile_picture')

        # Validasi jika ada field yang kosong
        if not first_name:
            messages.error(request, "Nama depan tidak boleh kosong!")
        if not last_name:
            messages.error(request, "Nama belakang tidak boleh kosong!")
        if not username:
            messages.error(request, "Username tidak boleh kosong!")
        if not email:
            messages.error(request, "Email tidak boleh kosong!")
        if not phone_number:
            messages.error(request, "Nomor telepon tidak boleh kosong!")
        if not address:
            messages.error(request, "Alamat tidak boleh kosong!")
        if not birth_date:
            messages.error(request, "Tanggal lahir tidak boleh kosong!")
        if not gender:
            messages.error(request, "Jenis kelamin tidak boleh kosong!")
        # Validasi gender
        elif gender not in ['L', 'P']:
            messages.error(request, "Jenis kelamin tidak valid!")

        # Validasi jika nama depan tidak diawali dengan huruf besar pada setiap kata
        if first_name and not all(word.istitle() for word in first_name.split()):
            messages.error(request, "Nama depan harus diawali dengan huruf besar pada setiap kata!")

        # Validasi nama belakang jika tidak berisi simbol "-" dan tidak diawali huruf besar
        if last_name != "-" and last_name and not all(word.istitle() for word in last_name.split()):
            messages.error(request, "Nama belakang harus diawali dengan huruf besar pada setiap kata!")

        # Validasi username sudah terdaftar oleh user lain
        if User.objects.filter(username=username).exclude(pk=request.user.pk).exists():
            messages.error(request, "Username sudah digunakan oleh pengguna lain!")

        # Validasi email sudah terdaftar oleh user lain
        if User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
            messages.error(request, "Email sudah digunakan oleh pengguna lain!")

        # Validasi format nomor telepon (opsional, contoh validasi panjang minimal)
        if phone_number and not phone_number.isdigit():
            messages.error(request, "Nomor telepon harus berupa angka!")
        elif phone_number and len(phone_number) < 10:
            messages.error(request, "Nomor telepon harus terdiri dari minimal 10 digit!")

        # Validasi dan set tanggal lahir
        if birth_date:
            try:
                profile.birth_date = birth_date
            except ValueError:
                messages.error(request, "Tanggal lahir tidak valid.")

        # Validasi format gambar jika ada yang diunggah
        if profile_picture and not is_valid_image(profile_picture):
            messages.error(request, "Format gambar tidak valid. Harap unggah gambar dengan ekstensi .jpg, .jpeg, atau .png!")

        # Jika ada error, kembali ke halaman edit pengaturan
        if messages.get_messages(request):
            return render(request, 'page/pengaturan/edit.html', {'profile': profile})

        # Update User fields
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.username = username
        request.user.email = email
        request.user.save()

        # Update Profile fields
        profile.phone_number = phone_number
        profile.address = address
        profile.gender = gender

        # Hapus foto profil jika checkbox 'clear_picture' dicentang
        if 'clear_picture' in request.POST:
            profile.delete_profile_picture()

        # Ganti foto profil jika user mengunggah yang baru
        elif profile_picture:
            # Hapus foto profil lama dari path dan database
            if profile.profile_picture:
                profile.profile_picture.delete(save=False)
            profile.profile_picture = profile_picture

        # Simpan perubahan pada profil
        profile.save()
        messages.success(request, "Data profil berhasil diperbarui!")
        return redirect('youfin_app:pengaturan')

    return render(request, 'page/pengaturan/edit.html', {'profile': profile})

@login_required
def ubah_password(request):
    if request.method == 'POST':
        # Ambil input dari form
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Validasi inputan kosong
        if not current_password:
            messages.error(request, "Password lama tidak boleh kosong!")
        if not new_password:
            messages.error(request, "Password baru tidak boleh kosong!")
        if not confirm_password:
            messages.error(request, "Konfirmasi password baru tidak boleh kosong!")

        # Periksa apakah password baru sama dengan konfirmasinya
        if new_password and confirm_password and new_password != confirm_password:
            messages.error(request, "Password baru dan konfirmasi tidak cocok!")

        # Periksa validitas password lama
        if current_password and not request.user.check_password(current_password):
            messages.error(request, "Password lama yang dimasukkan salah!")

        # Jika ada error, tampilkan halaman kembali tanpa mengubah password
        if messages.get_messages(request):
            return redirect('youfin_app:edit_pengaturan')

        # Jika semua validasi lulus, lanjutkan untuk ubah password
        try:
            request.user.set_password(new_password)
            request.user.save()

            # Memastikan sesi tetap aktif setelah mengubah password
            update_session_auth_hash(request, request.user)

            messages.success(request, "Password berhasil diperbarui! Silahkan logout dan login kembali menggunakan password baru Anda.")
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan saat mengubah password: {str(e)}")

        return redirect('youfin_app:edit_pengaturan')

    # Jika bukan POST, langsung kembali ke halaman edit_pengaturan
    return redirect('youfin_app:edit_pengaturan')



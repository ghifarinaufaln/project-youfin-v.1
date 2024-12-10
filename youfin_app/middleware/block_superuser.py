from django.shortcuts import redirect
from django.contrib import messages

class BlockSuperuserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Cek apakah pengguna yang login adalah superuser
        if request.user.is_authenticated and request.user.is_superuser:
            # Blokir akses ke aplikasi (kecuali admin Django)
            if not request.path.startswith('/admin/'):
                # Logout pengguna
                from django.contrib.auth import logout
                logout(request)
                # Tambahkan pesan error
                messages.error(request, "Superuser (Admin) tidak diizinkan mengakses website aplikasi.")
                return redirect('login')  # Ubah ke URL login Anda
        return self.get_response(request)

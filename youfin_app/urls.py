from django.urls import path
from . import views

app_name = "youfin_app"

urlpatterns = [
    # urls & views bag.back-end
    path('dashboard/', views.dashboard, name='dashboard'),
    # path('anggaran/', views.anggaran, name='anggaran'),
    # path('transaksi/', views.transaksi, name='transaksi'),
    # path('notifikasi/', views.notifikasi, name='notifikasi'),
    # path('premium/', views.premium, name='premium'),
    # path('konsultasi/', views.konsultasi, name='konsultasi'),
    path('tips/', views.tips, name='tips'),
    path('pengaturan/', views.pengaturan, name='pengaturan'),
    path('pengaturan/edit/', views.edit_pengaturan, name='edit_pengaturan'),
    path('pengaturan/edit/password', views.ubah_password, name='ubah_password'),

    # Transaksi URLs
    path('transaksi/', views.transaksi, name='transaksi'),
    path('transaksi/tambah/', views.add_transaction, name='add_transaction'),
    path('transaksi/edit/<int:transaction_id>/', views.edit_transaction, name='edit_transaction'),
    path('transaksi/hapus/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
    
    # Anggaran URLs
    path('anggaran/', views.manage_budgets, name='manage_budgets'),
    path('anggaran/tambah/', views.add_budget, name='add_budget'),
    path('anggaran/edit/<int:budget_id>/', views.edit_budget, name='edit_budget'),
    path('anggaran/hapus/<int:budget_id>/', views.delete_budget, name='delete_budget'),
    
    # Kategori URLs
    path('kategori/', views.manage_categories, name='manage_categories'),
    path('kategori/tambah/', views.add_category, name='add_category'),
    path('kategori/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('kategori/hapus/<int:category_id>/', views.delete_category, name='delete_category'),
]
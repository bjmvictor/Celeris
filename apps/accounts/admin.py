from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Empresa, User, UsuarioEmpresa


class UsuarioEmpresaInline(admin.TabularInline):
    model = UsuarioEmpresa
    extra = 1


@admin.register(User)
class CelerisUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Celeris", {"fields": ("full_name", "is_coordinator", "must_change_password")}),
    )
    list_display = ("username", "email", "full_name", "is_staff", "is_coordinator", "is_active")
    inlines = (UsuarioEmpresaInline,)


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("cd_empresa", "nm_empresa", "nr_cnpj", "sn_ativo")
    search_fields = ("nm_empresa", "nr_cnpj", "ds_razao_social")


@admin.register(UsuarioEmpresa)
class UsuarioEmpresaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "empresa", "sn_padrao", "sn_ativo")
    list_filter = ("empresa", "sn_ativo", "sn_padrao")
    autocomplete_fields = ("usuario", "empresa")

from django.contrib import admin

from .models import ReportQuery, ReportQueryVersion


@admin.register(ReportQuery)
class ReportQueryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "module", "destination", "active", "show_in_menu")
    list_filter = ("module", "active", "show_in_menu")
    search_fields = ("code", "name", "menu_name", "sql")


@admin.register(ReportQueryVersion)
class ReportQueryVersionAdmin(admin.ModelAdmin):
    list_display = ("report", "created_by", "created_at")
    search_fields = ("report__code", "report__name")

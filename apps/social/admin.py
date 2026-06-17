from django.contrib import admin

from .models import SocialAttendance, SocialPeriod


@admin.register(SocialPeriod)
class SocialPeriodAdmin(admin.ModelAdmin):
    list_display = ("month", "year", "active")
    list_filter = ("year", "active")


@admin.register(SocialAttendance)
class SocialAttendanceAdmin(admin.ModelAdmin):
    list_display = ("patient_name", "attendance_code", "sector", "period", "user", "active")
    list_filter = ("period", "sector", "active")
    search_fields = ("patient_name", "attendance_code", "sector")

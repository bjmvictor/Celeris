from django.contrib import admin

from .models import IconeSistema, Module, ScreenDefinition, ScreenField, UserModule


@admin.register(IconeSistema)
class IconeSistemaAdmin(admin.ModelAdmin):
    list_display = ("cd_icone", "nm_icone", "sn_ativo")
    list_filter = ("sn_ativo",)
    search_fields = ("cd_icone", "nm_icone")


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "icon", "order", "active", "is_system")
    list_filter = ("active", "is_system")
    search_fields = ("code", "title")


@admin.register(UserModule)
class UserModuleAdmin(admin.ModelAdmin):
    list_display = ("user", "module")
    autocomplete_fields = ("user", "module")


class ScreenFieldInline(admin.TabularInline):
    model = ScreenField
    extra = 1
    fields = (
        "order",
        "label",
        "table_name",
        "field_name",
        "field_type",
        "required",
        "consultable",
        "editable",
        "primary_key",
        "visible",
    )


@admin.register(ScreenDefinition)
class ScreenDefinitionAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "parent", "screen_type", "access_key", "allow_query", "allow_insert", "allow_update", "allow_delete", "active", "order")
    list_filter = ("module", "screen_type", "active")
    search_fields = ("title", "slug", "parent_label", "table_name")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("module", "parent")
    inlines = (ScreenFieldInline,)


@admin.register(ScreenField)
class ScreenFieldAdmin(admin.ModelAdmin):
    list_display = ("label", "screen", "field_name", "field_type", "required", "consultable", "editable", "primary_key", "visible")
    list_filter = ("field_type", "required", "consultable", "editable", "primary_key", "visible")
    search_fields = ("label", "field_name", "table_name", "screen__title")
    autocomplete_fields = ("screen",)

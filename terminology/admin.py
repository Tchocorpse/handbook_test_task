from django.contrib import admin

from terminology.models import Handbook, HandbookVersion, HandbookElement


class HandbookElementAdmin(admin.ModelAdmin):
    model = HandbookElement
    list_display = ('element_code', 'element_value', 'list_handbooks', )


class HandbookVersionAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('version', 'handbook_identifier', 'starting_date')
        }),
    )
    readonly_fields = ('created',)
    model = HandbookVersion
    list_display = ('version', 'handbook_identifier', 'starting_date', 'created', )


class HandbookAdmin(admin.ModelAdmin):
    model = Handbook
    list_display = ('name', 'short_name', 'description', )


admin.site.register(HandbookElement, HandbookElementAdmin)
admin.site.register(HandbookVersion, HandbookVersionAdmin)
admin.site.register(Handbook, HandbookAdmin)

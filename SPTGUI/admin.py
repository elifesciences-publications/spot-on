from django.contrib import admin

from .models import Analysis, Dataset, Download


class AnalysisAdmin(admin.ModelAdmin):
    list_display = ('url_basename', 'pub_date', 'acc_date', 'mod_date')

# Register your models here.
admin.site.register(Analysis, AnalysisAdmin)
admin.site.register(Dataset)
admin.site.register(Download)

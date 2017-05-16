from django.contrib import admin
from django.conf.urls import url
from django.utils.html import format_html
from django.core.urlresolvers import reverse
from django.template import loader
from django.http import HttpResponse
from django.shortcuts import redirect
from .models import Analysis, Dataset, Download


class AnalysisAdmin(admin.ModelAdmin):
    list_display = ('url_basename', 'pub_date', 'acc_date', 'mod_date', 'analysis_actions')
    readonly_fields = ('analysis_actions',)
    def get_urls(self):
        urls = super(AnalysisAdmin, self).get_urls()
        custom_urls = [
            # url(
            #     r'^(?P<account_id>.+)/deposit/$',
            #     self.admin_site.admin_view(self.run_tests),
            #     name='account-deposit',
            # ),
            url(
                r'^(?P<analysis_id>.+)/test/$',
                self.admin_site.admin_view(self.run_tests),
                name='analysis-test',
            ),
        ]
        return custom_urls + urls
    
    def analysis_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">Run tests</a>&nbsp;',
            #'<a class="button" href="{}">Withdraw</a>',
            #reverse('admin:account-deposit', args=[obj.pk]),
            reverse('admin:analysis-test', args=[obj.pk]),
        )
    def run_tests(self, request, analysis_id, *args, **kwargs):
        ana = Analysis.objects.get(id=analysis_id)
        template = loader.get_template('SPTGUI/analysis.html')
        #context = {'url_basename': ana.url_basename,
        #           'run_tests': True,
        #           'version': 'not initialized',
        #           'versionbackend': 'not initialized'}
        #return HttpResponse(template.render(context, request))
        return redirect('SPTGUI:analysis_dbg', url_basename=ana.url_basename)
    
    analysis_actions.short_description = 'Tests'
    analysis_actions.allow_tags = True

# Register your models here.
admin.site.register(Analysis, AnalysisAdmin)
admin.site.register(Dataset)
admin.site.register(Download)

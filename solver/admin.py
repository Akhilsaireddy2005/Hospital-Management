from django.contrib import admin
from .models import LPProblem, TransportationProblem

@admin.register(LPProblem)
class LPProblemAdmin(admin.ModelAdmin):
    list_display = ('name', 'objective_type', 'num_variables', 'num_constraints', 'is_solved', 'created_at')
    list_filter = ('objective_type', 'is_solved', 'created_at')
    search_fields = ('name',)

@admin.register(TransportationProblem)
class TransportationProblemAdmin(admin.ModelAdmin):
    list_display = ('name', 'num_sources', 'num_destinations', 'method_used', 'total_cost', 'is_solved', 'created_at')
    list_filter = ('method_used', 'is_solved', 'created_at')
    search_fields = ('name',)

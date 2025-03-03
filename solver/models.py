from django.db import models
import json

class LPProblem(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    objective_type = models.CharField(max_length=3, choices=[('MAX', 'Maximize'), ('MIN', 'Minimize')])
    objective_function = models.JSONField(help_text="Coefficients of objective function")
    constraints_lhs = models.JSONField(help_text="Left-hand side coefficients of constraints")
    constraints_rhs = models.JSONField(help_text="Right-hand side values of constraints")
    constraints_signs = models.JSONField(help_text="Signs of constraints (≤, ≥, =)")
    num_variables = models.IntegerField()
    num_constraints = models.IntegerField()
    solution = models.JSONField(null=True, blank=True)
    is_solved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {'Maximization' if self.objective_type == 'MAX' else 'Minimization'}"

    class Meta:
        verbose_name = "Linear Programming Problem"
        verbose_name_plural = "Linear Programming Problems"

class TransportationProblem(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    supply = models.JSONField(help_text="Supply values from sources")
    demand = models.JSONField(help_text="Demand values at destinations")
    cost_matrix = models.JSONField(help_text="Transportation costs matrix")
    num_sources = models.IntegerField()
    num_destinations = models.IntegerField()
    solution = models.JSONField(null=True, blank=True)
    total_cost = models.FloatField(null=True, blank=True)
    is_solved = models.BooleanField(default=False)
    method_used = models.CharField(
        max_length=10,
        choices=[
            ('NWCR', 'Northwest Corner Rule'),
            ('LCM', 'Least Cost Method'),
            ('VAM', "Vogel's Approximation")
        ],
        default='NWCR'
    )

    def __str__(self):
        return f"{self.name} - {self.num_sources}x{self.num_destinations} Transportation Problem"

    class Meta:
        verbose_name = "Transportation Problem"
        verbose_name_plural = "Transportation Problems"
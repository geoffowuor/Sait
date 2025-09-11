from django.db import models, transaction
from django.contrib.auth.models import User
from django.db.models import F


#site model,table in db

class Site(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sites',null=True, blank=True)
    
    def __str__(self):
        return self.name

class Asset(models.Model):
    asset_types = [
        ('equipment', 'Equipment'),
        ('material', 'Material'),
    ]
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='assets')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100, choices=asset_types, default='equipment')
    units = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=50, blank=True, null=True)  # for equipment
    quantity_in_stock = models.IntegerField(default=0)  # for material
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    maintenance_date = models.DateField(blank=True, null=True)
    assignment_date = models.DateField()
    discription = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assets',null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(quantity_in_stock__gte=0), name='asset_qty_non_negative')
        ]
    
    def __str__(self):
        return self.name

class Human_resource(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='human_resources')
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='human_resources',null=True, blank=True)
    
    def __str__(self):
        return self.name


class chat(models.Model):
    query = models.TextField()
    response = models.TextField()


class AssetTransaction(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    issued_to = models.CharField(max_length=255)  
    quantity_issued = models.PositiveIntegerField()
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk is None:  
            if self.quantity_issued > self.asset.quantity_in_stock:
                raise ValueError("Not enough stock available")
            self.asset.quantity_in_stock -= self.quantity_issued
            self.asset.save()
        super().save(*args, **kwargs)
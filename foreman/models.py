from django.db import models


#site model,table in db

class Site(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    
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
    serial_number = models.CharField(max_length=100, blank=True, null=True)  # equipment
    quantity_in_stock = models.IntegerField(default=0)  # material
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    maintenance_date = models.DateField(blank=True, null=True)
    assignment_date = models.DateField()
    discription = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Human_resource(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='human_resources')
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.name


class chat(models.Model):
    query = models.TextField()
    response = models.TextField()
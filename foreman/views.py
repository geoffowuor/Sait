from django.shortcuts import render, redirect, get_object_or_404
import os
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import AIAssistantForm
import google.generativeai as genai
import json
from django.conf import settings
from .models import Site,Asset, Human_resource
from .forms import SiteForm, HumanResourceForm,AssetForm
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q, F
from django.utils import timezone

def home(request):
    return render(request, "index.html")

#auth view
# Register view
def register(request):
    if request.method == 'POST':
        name = request.POST['name']
        username = request.POST['username']
        contact = request.POST['contact']
        password = request.POST['password']
        password_confirm = request.POST['password_confirm']
        
        if password == password_confirm:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists')
            elif User.objects.filter(email=contact).exists():
                messages.error(request, 'Email already exists')
            else:
                user = User.objects.create_user(
                    username=username,
                    email=contact,
                    password=password
                )
                # Store the full name
                user.first_name = name  # You could split the name into first_name and last_name if needed
                user.save()
                
                messages.success(request, 'Account created successfully!')
                return redirect('login')
        else:
            messages.error(request, 'Passwords do not match')
    
    return render(request, 'accounts/register.html')

# Login view
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirect to a dashboard
        else:
            messages.error(request, 'Invalid username or password!')
    return render(request, 'accounts/login.html')


@login_required
def dashboard(request):
    sites= Site.objects.filter(owner=request.user)
    assets = Asset.objects.filter(owner=request.user)
    human_resources = Human_resource.objects.filter(owner=request.user)
    return render(request, "dashboard.html", {"sites": sites,
                                              "assets": assets,
                                              "human_resources": human_resources})

def ai_assistant(request):
    if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        try:
            data = json.loads(request.body)
            query = data.get("query", "").strip()
            
            if not query:
                return JsonResponse({"response": "Please ask a valid question."})
            
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
                
                
                model = genai.GenerativeModel('gemini-2.0-flash')
                
                plain_text_query = (
                    f"You are a construction site manager and expert assitant,you know everything about construction sites,your name is Foreman. Only answer things related to construction  and project management.You were made and trained by Geoffrey "
                    f"Please respond in plain text only. Do not use any markdown, symbols like *, or HTML tags. and please list where necessary,don't just use blocked paragraph and please also paragraph your work clead typography and be very polite"
                    f"Just write polite, easy-to-read and proffesional response with no formatting. Question: {query}"
                )

                response = model.generate_content(plain_text_query)
                
                return JsonResponse({"response": response.text}, safe=False)
            except Exception as e:
                return JsonResponse({"response": f"An error occurred: {str(e)}"})
        except json.JSONDecodeError:
            return JsonResponse({"response": "Invalid JSON data."}, status=400)
    
    return render(request, '#.html')

@login_required
def site_list(request):
    sites = Site.objects.filter(owner=request.user)
    return render(request, 'site_list.html', {'sites': sites})

@login_required
def site_create(request):
    if request.method == 'POST':
        form = SiteForm(request.POST)   
        if form.is_valid():
            site = form.save(commit=False)
            site.owner = request.user
            site.save()
            return redirect('site_list')
    else:
        form = SiteForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Add New Site',
        'button_text': 'Create Site'
    }
    return render(request, 'site_form.html', context)

@login_required
def site_update(request, pk):
    site = get_object_or_404(Site, pk=pk)
    
    if request.method == 'POST':
        form = SiteForm(request.POST, instance=site)
        if form.is_valid():
            site.owner = request.user
            site.save()
            return redirect('site_list')
    else:
        form = SiteForm(instance=site)
    
    context = {
        'form': form,
        'title': 'Edit Site',
        'button_text': 'Update Site'
    }
    return render(request, 'site_form.html', context)
@login_required
def site_delete(request, pk):
    site = get_object_or_404(Site, pk=pk)
    
    if request.method == 'POST':
        site.delete()
        return redirect('site_list')

    return render(request, 'site_confirm_delete.html', {'object': site})


@login_required
def site_detail(request, pk):
    site = get_object_or_404(Site, pk=pk)
    assets = Asset.objects.filter(site=site)
    human_resources = Human_resource.objects.filter(site=site)
    context = { 
        'site': site,
        'assets': assets,
        'human_resources': human_resources
    }
    return render(request, 'site_detail.html', context)


'''Human Resource Views'''
@login_required
def human_resource_list(request):
    # Get all human resources
    human_resources_list = Human_resource.objects.filter(owner=request.user)
    # Get all sites for the filter dropdown
    sites = Site.objects.filter(owner=request.user)
    # Get unique roles for the filter dropdown
    roles = Human_resource.objects.values_list('role', flat=True).distinct()
    # Apply filters if provided
    site_filter = request.GET.get('site')
    role_filter = request.GET.get('role')
    search_query = request.GET.get('search')
    
    if site_filter:
        human_resources_list = human_resources_list.filter(site_id=site_filter)
    
    if role_filter:
        human_resources_list = human_resources_list.filter(role=role_filter)
    
    if search_query:
        human_resources_list = human_resources_list.filter(name__icontains=search_query)
    
    # Pagination
    paginator = Paginator(human_resources_list, 10)  # Show 10 records per page
    page_number = request.GET.get('page')
    human_resources = paginator.get_page(page_number)
    
    context = {
        'human_resources': human_resources,
        'sites': sites,
        'roles': roles,
    }
    
    return render(request, 'human_resource_list.html', context)
@login_required
def add_human_resource(request):
    if request.method == 'POST':
        form = HumanResourceForm(request.POST)
        if form.is_valid():
            human_resource = form.save(commit=False) 
            human_resource.owner = request.user
            human_resource.save()
            return redirect('human_resource_list')
    else:
        form = HumanResourceForm(user=request.user)
    
    return render(request, 'human_resource_form.html', {'form': form, 'action': 'Add'})

def edit_human_resource(request, pk):
    human_resource = get_object_or_404(Human_resource, pk=pk)
    
    if request.method == 'POST':
        form = HumanResourceForm(request.POST, instance=human_resource)
        if form.is_valid():
            human_resource= form.save(commit=False) 
            human_resource.owner = request.user
            human_resource.user = request.user
            human_resource.save()
            return redirect('human_resource_list')
    else:
        form = HumanResourceForm(instance=human_resource)
    
    return render(request, 'human_resource_form.html', {'form': form, 'action': 'Edit'})

def delete_human_resource(request, pk):
    human_resource = get_object_or_404(Human_resource, pk=pk)
    human_resource.delete()
    return redirect('human_resource_list')




def asset_list(request):
    sites = Site.objects.filter(owner=request.user)
    asset_types = Asset.asset_types
    assets_queryset = Asset.objects.select_related('site').all()
    # Apply filters
    site_id = request.GET.get('site', '')
    asset_type = request.GET.get('type', '')
    search = request.GET.get('search', '')
    
    if site_id:
        assets_queryset = assets_queryset.filter(site_id=site_id)
    
    if asset_type:
        assets_queryset = assets_queryset.filter(type=asset_type)
    
    if search:
        assets_queryset = assets_queryset.filter(
            Q(name__icontains=search) | 
            Q(serial_number__icontains=search) |
            Q(discription__icontains=search)
        )
    
    total_assets = assets_queryset.count()
    equipment_count = assets_queryset.filter(type='equipment').count()
    material_count = assets_queryset.filter(type='material').count()
    
    # Calculate total value
    equipment_value = assets_queryset.filter(type='equipment').aggregate(
        value=Sum('cost_per_unit'))['value'] or 0
    
    material_value = assets_queryset.filter(type='material').aggregate(
        value=Sum(F('cost_per_unit') * F('quantity_in_stock')))['value'] or 0
    
    total_value = equipment_value + material_value
    
    # Get maintenance alerts
    today = timezone.now().date()
    next_month = today + timezone.timedelta(days=30)
    maintenance_due_assets = assets_queryset.filter(
        maintenance_date__isnull=False,
        maintenance_date__lte=next_month
    ).order_by('maintenance_date')
    
    # Pagination
    paginator = Paginator(assets_queryset, 10)
    page_number = request.GET.get('page')
    assets = paginator.get_page(page_number)
    
    context = {
        'assets': assets,
        'sites': sites,
        'asset_types': asset_types,
        'total_assets': total_assets,
        'equipment_count': equipment_count,
        'material_count': material_count,
        'total_value': total_value,
        'maintenance_due_assets': maintenance_due_assets,
        'today': today,
    }
    
    return render(request, 'asset_management.html', context)

def asset_detail(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    return render(request, 'asset_detail.html', {'asset': asset})

def asset_create(request):
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False) 
            asset.owner = request.user
            asset = form.save()
            messages.success(request, f'Asset "{asset.name}" created successfully!')
            return redirect('asset_management')
    else:
        form = AssetForm(user=request.user)
    
    return render(request, 'asset_form.html', {
        'form': form,
        'title': 'Add New Asset',
    })

def asset_update(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            asset = form.save(commit=False) 
            asset.user = request.user
            asset = form.save()
            messages.success(request, f'Asset "{asset.name}" updated successfully!')
            return redirect('asset_management')
    else:
        form = AssetForm(instance=asset)
    
    return render(request, 'asset_form.html', {
        'form': form,
        'asset': asset,
        'title': f'Edit Asset: {asset.name}', 
    })

def asset_delete(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    
    if request.method == 'POST':
        asset_name = asset.name
        asset.delete()
        messages.success(request, f'Asset "{asset_name}" deleted successfully!')
        return redirect('asset_management')
    
    return render(request, 'asset_confirm_delete.html', {'asset': asset})

def asset_maintenance(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    
    if request.method == 'POST':
        new_date = request.POST.get('maintenance_date')
        if new_date:
            try:
                asset.maintenance_date = new_date
                asset.save()
                messages.success(request, f'Maintenance scheduled for {asset.name}')
                return redirect('asset_management')
            except ValueError:
                messages.error(request, 'Invalid date format')
    
    suggested_date = (timezone.now() + timezone.timedelta(days=14)).date()
    
    return render(request, 'asset_maintenance.html', {
        'asset': asset,
        'suggested_date': suggested_date,
    })

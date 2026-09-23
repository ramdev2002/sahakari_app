from .models import Branch, Department, Organization


def get_active_organizations():
    return Organization.objects.filter(status='active').order_by('name')


def get_active_branches():
    return Branch.objects.select_related('organization').filter(status='active').order_by('code')


def get_branch_by_id(branch_id):
    return Branch.objects.filter(pk=branch_id).first()


def get_departments_of_branch(branch):
    return Department.objects.filter(branch=branch, status='active').order_by('code')


def get_or_create_default_organization(name='Sahakari Cooperative'):
    """Idempotent default tenant used by tests and bootstrap flows."""
    org, _ = Organization.objects.get_or_create(code='DEFAULT', defaults={'name': name})
    return org

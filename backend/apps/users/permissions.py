from rest_framework.permissions import BasePermission



# Only System Administrators
class IsAdmin(BasePermission):
   
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsAdminOrBranchManager(BasePermission):
    def has_permission(self, request, view):
        
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user.is_authenticated and request.user.role in ['admin', 'branch_manager', 'collections_officer', 'finance_staff', 'risk_analyst', 'compliance_officer']
        return request.user.is_authenticated and request.user.role in ['admin', 'branch_manager']


class IsLoanOfficer(BasePermission):
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user.is_authenticated and request.user.role in ['admin', 'loan_officer', 'branch_manager', 'risk_analyst', 'finance_staff', 'credit_committee', 'collections_officer', 'compliance_officer']
        return request.user.is_authenticated and request.user.role in ['admin', 'loan_officer', 'branch_manager']


class IsRiskAnalyst(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'risk_analyst', 'branch_manager']


class IsBranchManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'branch_manager']


class IsCreditCommittee(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'credit_committee', 'branch_manager']


class IsCollectionsOfficer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'collections_officer', 'branch_manager']


class IsComplianceOfficer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'compliance_officer', 'branch_manager']


class IsFinanceStaff(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'finance_staff', 'branch_manager']
from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreaionForm, UserChangeForm as BaseUserChangeForm
from .models import User, Branch

class UserCreationForm(BaseUserCreaionForm):
  print('I am in user creation form')
  class Meta:
    model = User
    fields = ('email', 'mobile', 'username', 'first_name', 'last_name', 'company', 'branch')
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['branch'].queryset = Branch.objects.none()
    
    if 'company' in self.data:
      try:
        company_id = int(self.data.get('company'))
        self.fields['branch'].queryset = Branch.objects.filter(company_id=company_id)
        print('company id is', company_id)
        print('branch queryset is', self.fields['branch'].queryset)
      except (ValueError, TypeError):
        pass 
    
    elif self.instance.pk and self.instance.company:
      self.fields['branch'].queryset = Branch.objects.filter(company=self.instance.company)
        
  
class UserChangeForm(BaseUserChangeForm):
  class Meta:
    model = User
    fields = ('email', 'mobile', 'username', 'first_name', 'last_name', 'company', 'branch')

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['branch'].queryset = Branch.objects.none()

    # If a company is selected, filter branches by company
    if 'company' in self.data:
      try:
        company_id = int(self.data.get('company'))
        self.fields['branch'].queryset = Branch.objects.filter(company_id=company_id)
      except (ValueError, TypeError):
        pass
    # If this is an instance example: editing an existing user
    elif self.instance.pk and self.instance.company:
      self.fields['branch'].queryset = Branch.objects.filter(company=self.instance.company)
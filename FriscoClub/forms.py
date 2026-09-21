from django import forms
from django.contrib.auth import get_user_model
from .models import Produits, PasswordResetCode


class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produits
        fields = ['nom', 'Cathegories', 'Genres', 'Prix_vente', 'is_available', 'image']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'Cathegories': forms.Select(attrs={'class': 'form-select'}),
            'Genres': forms.Select(attrs={'class': 'form-select'}),
            'Prix_vente': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class TeamMemberForm(forms.Form):
    username = forms.CharField(max_length=150, label='Nom d’utilisateur', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email', required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Mot de passe', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirm = forms.CharField(label='Confirmer le mot de passe', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(choices=[('Caissiers', 'Caissier'), ('Serveurs', 'Serveur'), ('Fournisseurs', 'Fournisseur')], label='Rôle', widget=forms.Select(attrs={'class': 'form-select'}))
    phone = forms.CharField(max_length=20, required=False, label='Téléphone', widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Les mots de passe ne correspondent pas.')

        username = cleaned_data.get('username')
        if username:
            User = get_user_model()
            if User.objects.filter(username__iexact=username).exists():
                raise forms.ValidationError('Ce nom d’utilisateur est déjà utilisé.')

        return cleaned_data

    def save(self):
        User = get_user_model()
        return User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            role=self.cleaned_data['role'],
            phone=self.cleaned_data['phone'] or '',
        )


class PasswordResetForm(forms.Form):
    username = forms.CharField(label='Nom d’utilisateur', widget=forms.TextInput(attrs={'class': 'form-control'}))
    new_password = forms.CharField(label='Nouveau mot de passe', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password_confirm = forms.CharField(label='Confirmer le nouveau mot de passe', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('new_password')
        password_confirm = cleaned_data.get('new_password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Les mots de passe ne correspondent pas.')

        return cleaned_data

    def save(self):
        User = get_user_model()
        user = User.objects.filter(username__iexact=self.cleaned_data['username']).first()
        if not user:
            raise forms.ValidationError('Aucun utilisateur trouvé avec ce nom.')

        user.set_password(self.cleaned_data['new_password'])
        user.save()
        return user


class ForgotPasswordForm(forms.Form):
    username = forms.CharField(label='Nom d’utilisateur', widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean_username(self):
        username = self.cleaned_data.get('username')
        User = get_user_model()
        user = User.objects.filter(username__iexact=username).first()
        if not user:
            raise forms.ValidationError('Aucun compte trouvé pour ce nom d’utilisateur.')
        if not user.email:
            raise forms.ValidationError('Aucun email n’est associé à ce compte.')
        return username


class VerifyResetCodeForm(forms.Form):
    username = forms.CharField(label='Nom d’utilisateur', widget=forms.TextInput(attrs={'class': 'form-control'}))
    code = forms.CharField(label='Code de vérification', widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        code = cleaned_data.get('code')
        if username and code:
            User = get_user_model()
            user = User.objects.filter(username__iexact=username).first()
            if not user:
                raise forms.ValidationError('Utilisateur introuvable.')
            reset_code = PasswordResetCode.objects.filter(user=user, code=code).order_by('-created_at').first()
            if not reset_code or not reset_code.is_valid():
                raise forms.ValidationError('Code invalide ou expiré.')
            cleaned_data['user'] = user
            cleaned_data['reset_code'] = reset_code
        return cleaned_data


class NewPasswordForm(forms.Form):
    username = forms.CharField(widget=forms.HiddenInput())
    password = forms.CharField(label='Nouveau mot de passe', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirm = forms.CharField(label='Confirmer le mot de passe', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Les mots de passe ne correspondent pas.')
        return cleaned_data

    def save(self):
        User = get_user_model()
        user = User.objects.filter(username__iexact=self.cleaned_data['username']).first()
        if not user:
            raise forms.ValidationError('Utilisateur introuvable.')
        user.set_password(self.cleaned_data['password'])
        user.save()
        PasswordResetCode.objects.filter(user=user).update(used=True)
        return user
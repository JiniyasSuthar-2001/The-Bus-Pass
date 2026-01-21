from django.test import TestCase, Client
from django.urls import reverse
from .models import CustomUser

class LoginSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_pass = "password123"
        
        # Create standard user
        self.user = CustomUser.objects.create_user(
            username='regularUser', 
            email='user@test.com', 
            password=self.user_pass,
            role='USER'
        )
        
        # Create admin user
        self.admin = CustomUser.objects.create_user(
            username='adminUser', 
            email='admin@test.com', 
            password=self.user_pass,
            role='ADMIN'
        )
        # Create conductor user
        self.conductor = CustomUser.objects.create_user(
            username='conductorUser', 
            email='conductor@test.com', 
            password=self.user_pass,
            role='CONDUCTOR'
        )

    def test_user_login_success(self):
        """Standard user should be able to login via /login/"""
        response = self.client.post(reverse('login'), {
            'username': 'regularUser',
            'password': self.user_pass
        }, follow=True)
        
        # Should eventually land on user_dashboard
        self.assertTemplateUsed(response, 'user_dashboard.html')
        # Or check final URL
        self.assertTrue(response.redirect_chain)
        # Check if logged in
        self.assertIn('_auth_user_id', self.client.session)

    def test_admin_login_restriction(self):
        """Admin should NOT be able to login via /login/ and should see error"""
        response = self.client.post(reverse('login'), {
            'username': 'adminUser',
            'password': self.user_pass
        }, follow=True)
        
        # Should end up back at login page (200 OK)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # Check verified they are NOT logged in
        self.assertNotIn('_auth_user_id', self.client.session)
        
        # Check error message
        messages = list(response.context['messages'])
        self.assertTrue(any("Admins and Conductors" in str(m) for m in messages))

    def test_conductor_login_restriction(self):
        """Conductor should NOT be able to login via /login/"""
        response = self.client.post(reverse('login'), {
            'username': 'conductorUser',
            'password': self.user_pass
        }, follow=True)
        
        self.assertTemplateUsed(response, 'registration/login.html')
        self.assertNotIn('_auth_user_id', self.client.session)

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import UserProfile, UserRole, PatientProfile, ClinicianProfile


class LoginTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create test users
        self.patient_user = User.objects.create_user(
            username='testpatient',
            email='patient@test.com',
            password='testpass123'
        )
        self.patient_profile = UserProfile.objects.create(user=self.patient_user, role=UserRole.PATIENT)
        PatientProfile.objects.create(user_profile=self.patient_profile)

        self.clinician_user = User.objects.create_user(
            username='testclinician',
            email='clinician@test.com',
            password='testpass123'
        )
        self.clinician_profile = UserProfile.objects.create(user=self.clinician_user, role=UserRole.CLINICIAN)
        ClinicianProfile.objects.create(user_profile=self.clinician_profile)

        self.admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123'
        )
        self.admin_profile = UserProfile.objects.create(user=self.admin_user, role=UserRole.ADMIN)
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save()

        # Create demo users for demo_login tests
        self.demo_patient = User.objects.create_user(
            username='patient@demo.com',
            email='patient@demo.com',
            password='demo123'
        )
        self.demo_patient_profile = UserProfile.objects.create(user=self.demo_patient, role=UserRole.PATIENT)
        PatientProfile.objects.create(user_profile=self.demo_patient_profile)

        self.demo_clinician = User.objects.create_user(
            username='clinician@demo.com',
            email='clinician@demo.com',
            password='demo123'
        )
        self.demo_clinician_profile = UserProfile.objects.create(user=self.demo_clinician, role=UserRole.CLINICIAN)
        ClinicianProfile.objects.create(user_profile=self.demo_clinician_profile)

        self.demo_admin = User.objects.create_user(
            username='admin@demo.com',
            email='admin@demo.com',
            password='demo123'
        )
        self.demo_admin_profile = UserProfile.objects.create(user=self.demo_admin, role=UserRole.ADMIN)
        self.demo_admin.is_staff = True
        self.demo_admin.is_superuser = True
        self.demo_admin.save()

    def test_login_page_get(self):
        """Test that login page loads correctly"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/login.html')

    def test_successful_patient_login(self):
        """Test successful login for patient user"""
        response = self.client.post(reverse('login'), {
            'username': 'testpatient',
            'password': 'testpass123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain[-1][0], reverse('dashboard_patient'))

    def test_successful_clinician_login(self):
        """Test successful login for clinician user"""
        response = self.client.post(reverse('login'), {
            'username': 'testclinician',
            'password': 'testpass123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain[-1][0], reverse('dashboard_clinician'))

    def test_successful_admin_login(self):
        """Test successful login for admin user"""
        response = self.client.post(reverse('login'), {
            'username': 'testadmin',
            'password': 'testpass123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain[-1][0], reverse('dashboard_admin'))

    def test_failed_login_wrong_password(self):
        """Test login with wrong password"""
        response = self.client.post(reverse('login'), {
            'username': 'testpatient',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)  # Stay on login page
        self.assertTemplateUsed(response, 'auth/login.html')
        self.assertContains(response, 'Please enter a correct username and password')

    def test_failed_login_nonexistent_user(self):
        """Test login with nonexistent user"""
        response = self.client.post(reverse('login'), {
            'username': 'nonexistent',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/login.html')
        self.assertContains(response, 'Please enter a correct username and password')

    def test_login_redirect_authenticated_user(self):
        """Test that authenticated users are redirected from login page"""
        self.client.login(username='testpatient', password='testpass123')
        response = self.client.get(reverse('login'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain[-1][0], reverse('dashboard_patient'))

    @override_settings(DEBUG=True)
    def test_demo_login_patient(self):
        """Test demo login for patient"""
        response = self.client.post(reverse('demo_login', args=['patient']))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

    @override_settings(DEBUG=True)
    def test_demo_login_clinician(self):
        """Test demo login for clinician"""
        response = self.client.post(reverse('demo_login', args=['clinician']))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

    @override_settings(DEBUG=True)
    def test_demo_login_admin(self):
        """Test demo login for admin"""
        response = self.client.post(reverse('demo_login', args=['admin']))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

    def test_demo_login_invalid_role(self):
        """Test demo login with invalid role"""
        response = self.client.post(reverse('demo_login', args=['invalid']))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))

    def test_logout(self):
        """Test logout functionality"""
        self.client.login(username='testpatient', password='testpass123')
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))

from django.urls import path
from .views import RegisterView, LoginView, LogoutView, PlagDataView , UserDashboardView
urlpatterns = [
    path('register', RegisterView.as_view()),
    path('login', LoginView.as_view()),
    path('logout', LogoutView.as_view()),
    path("PlagiarismCheck/", PlagDataView.as_view(), name ="plagiarism" ),
    path('dashboard',UserDashboardView.as_view(), name='dashboard')
]
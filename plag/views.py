from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework import permissions , status
from rest_framework.exceptions import AuthenticationFailed
from .serializers import UserSerializer , PlagCheckSerializer, PlagDataSerializer, UsageStatSerializer
from .models import User,PlagCheck,UsageStat , PlagData
import jwt, datetime
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncMonth
from .utils import search_and_similarity


class RegisterView(APIView):
    """
    Handles user registration by accepting user data, validating it, 
    and saving the user to the database.
    """
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LoginView(APIView):
    """
    Handles user login by validating the credentials, 
    creating a JWT token, and saving a check-in time for the user.
    """
    def post(self, request):
        email = request.data['email']
        password = request.data['password']

        user = User.objects.filter(email=email).first()

        if user is None:
            raise AuthenticationFailed('User not found!')

        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect password!')
        
        UsageStat.objects.create(user=user, check_in=timezone.now())

        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            'iat': datetime.datetime.utcnow()
        }

        token = jwt.encode(payload, 'secret', algorithm='HS256')

        response = Response()

        response.set_cookie(key='jwt', value=token, httponly=True)
        response.data = {
            'jwt': token
        }
        return response


class UserView(APIView):
    """
    Retrieves the authenticated user's data using the JWT token.
    """
    def get(self, request):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Unauthenticated!')

        try:
            payload = jwt.decode(token, 'secret', algorithm=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Unauthenticated!')

        user = User.objects.filter(id=payload['id']).first()
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    
class UserDashboardView(APIView):
    """
    Retrieves various details for the authenticated user's dashboard, 
    including usage statistics, the latest plagiarism check, and plagiarism data.
    """

    def get(self, request):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Unauthenticated!')

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Unauthenticated!')

        user = User.objects.filter(id=payload['id']).first()
        if not user:
            raise AuthenticationFailed('User not found!')

        # User details
        user_data = UserSerializer(user).data

        # Retrieve usage statistics for the user
        usage_stats = UsageStat.objects.filter(user=user).order_by('-check_in')
        usage_stats_data = UsageStatSerializer(usage_stats, many=True).data

        # Retrieve the latest plagiarism check for the user
        latest_plag_check = PlagCheck.objects.filter(user=user).order_by('-date_uploaded').first()
        latest_plag_check_data = PlagCheckSerializer(latest_plag_check).data if latest_plag_check else None

        # Retrieve plagiarism data for the user
        plag_data = PlagData.objects.filter(user_id=user).order_by('-created_at')
        plag_data_serialized = PlagDataSerializer(plag_data, many=True).data

        return Response({
            'usage_statistics': usage_stats_data,
            'latest_plagiarism_check': latest_plag_check_data,
            'plagiarism_data': plag_data_serialized,
        })

class LogoutView(APIView):
    """
    Handles user logout by deleting the JWT token and updating the 
    check-out time for the most recent usage statistic.
    """
    def post(self, request):
        
        response = Response()
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Unauthenticated!')

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Unauthenticated!')

        user = User.objects.filter(id=payload['id']).first()

        latest_usage = UsageStat.objects.filter(user=user).order_by('-check_in').first()
        if latest_usage:
            latest_usage.check_out = timezone.now()
            latest_usage.save()
       

        # UsageStat.objects.update(user=user, check_out=timezone.now())
        response.delete_cookie('jwt')
        response.data = {
            'message': 'success'
        }

        return response
    
class PlagDataView(APIView):
    """
    Handles plagiarism data submission by accepting user text, 
    checking for plagiarism, and returning a report.
    """  
    permission_classes= [permissions.AllowAny]
    def post(self,request: any , format: any = None) -> any :
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Unauthenticated!')

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Unauthenticated!')

        user = User.objects.filter(id=payload['id']).first()
        if not user:
            raise AuthenticationFailed('User not found!')

        # User details
        user_data = UserSerializer(user).data
        print(request.data['text'])
        request.data['user_id'] = user
        serializer = PlagDataSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        report = search_and_similarity(request.data['text'], user)
        del report['corpus_data']
        return Response(report, status=status.HTTP_200_OK)
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from Login_Portal import settings
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes,force_str
from . tokens import generate_token
from django.core.mail import EmailMessage, send_mail

# Create your views here.
def home(request):
    return render(request,"auth/index.html")

def signup(request):
    
    #getting data from post method
    if request.method == "POST":
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        if User.objects.filter(username=username):
            messages.error(request, " Username already exist, Try other username ")
            return redirect('home')

        if User.objects.filter(email=email):
            messages.error(request, " Email already taken ")
            return redirect('home')

        if len(username)>10:
            messages.error(request, " Username must be under 10 characters ")

        if pass1 != pass2:
            messages.error(request, " Password didn't matched ")

        if not username.isalpha():
            messages.error(request, " Username must be alphanumeric. ")
            return redirect('home')

        #creating user object 
        myuser = User.objects.create_user(username , email , pass1)
        myuser.first_name = fname
        myuser.last_name = lname 

        #makng user in active so that we can make it active through conformation mail
        myuser.is_active = False

        #saving user in database 
        myuser.save()
        messages.success(request, "YOUR ACCOUNT HAS BEEN CREATED SUCESSFULLY. WE HAVE SENT CONFIRMATION EMAIL.PLEASE CONFIRM YOUR E-MAIL IN ORDER TO ACTIVATE YOUR ACCOUNT ")

        #Welcome EMail
        subject = "Welcome to Ashutosh Login Portal!!"
        message = "Hello "+ myuser.first_name +" !! \n" + " Welcome to the portal \n Thank you for visiting our site \n We have sent you a confirmation e-mail. Please confirm to the mail in order to activate  your account. \n Thanking You Ashutosh Kumar Maurya "
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject ,message, from_email, to_list, fail_silently=True)

        #Email address confirmation mail
        current_site = get_current_site(request)
        email_subject = "Confirm your email at Ashutosh's Portal !!"
        message2 = render_to_string('email_confirmation.html',{
            'name': myuser.first_name,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token':generate_token.make_token(myuser)
        })
        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],
        )
        email.fail_silently = True
        email.send()

        #redirecting after user creation to sign in
        return redirect('signin')

    return render(request,"auth/signup.html")

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']

        user = authenticate(username = username, password = pass1)

        if user is not None :
            login(request, user)
            fname=user.first_name
            return render(request, "auth/index.html", {'fname':fname})

        else :
            messages.error(request, "Invalid username or Password ")
            return redirect('home')

    return render(request,"auth/signin.html")

def signout(request):
    logout(request)
    messages.success(request, "Logged Out Sucessfully")
    return redirect('home')

def activate(request, uidb64, token):
    try:
        uid=force_str(urlsafe_base64_decode(uidb64))
        myuser= User.object.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser=None

    if myuser is not None and generate_token.check_token(myuser, token):
        myuser.is_active = True
        myuser.save()
        login(request, myuser)
        return redirect('home')

    else:
        return render(request, 'activation_failed.html')

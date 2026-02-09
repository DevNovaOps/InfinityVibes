from django.db import IntegrityError
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib.auth.hashers import check_password
from .models import User, VendorProfile,VendorDis
from .forms import LoginForm, UserSignupForm, VendorProfileForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from .utils import get_image_embedding
from django.conf import settings
import google.generativeai as genai
import os
import tempfile
import json

def home(request):
    return render(request, 'event/home.html')

def about(request):
    return render(request, 'event/about.html')

def terms(request):
    return render(request, 'event/terms.html')

# your_app/views.py
def signup(request):
    if request.session.get('user_id'):
        messages.info(request, 'You are already logged in.')
        # Redirect vendors to vendor.html, others to home
        if request.session.get('user_type') == 'vendor':
            return redirect('vendor')
        return redirect('home')

    # On a POST request, decide which form was submitted
    if request.method == 'POST':
        # Determine if it's a login or signup attempt
        if 'login' in request.POST:
            login_form = LoginForm(request.POST)
            signup_form = UserSignupForm()
            vendor_form = VendorProfileForm()
            show_signup = False # Show the login form

            if login_form.is_valid():
                email = login_form.cleaned_data['email']
                password = login_form.cleaned_data['password']
                try:
                    user = User.objects.get(email=email)
                    if check_password(password, user.password):
                        request.session['user_id'] = user.id
                        request.session['user_name'] = user.first_name
                        request.session['user_type'] = user.user_type
                        messages.success(request, f"Welcome back, {user.first_name}!")
                        # Redirect vendors to vendor.html, others to home
                        if user.user_type == 'vendor':
                            return redirect('vendor')
                        return redirect('home')
                    else:
                        login_form.add_error(None, 'Invalid email or password.')
                except User.DoesNotExist:
                    login_form.add_error(None, 'Invalid email or password.')
        
        elif 'signup' in request.POST:
            login_form = LoginForm()
            signup_form = UserSignupForm(request.POST)
            vendor_form = VendorProfileForm(request.POST)
            show_signup = True # Show the signup form

            user_type = request.POST.get('user_type')

            # The validation logic is now beautifully simple
            is_signup_valid = signup_form.is_valid()
            is_vendor_valid = vendor_form.is_valid() if user_type == 'vendor' else True

            if is_signup_valid and is_vendor_valid:
                try:
                    # The form's save() method now handles hashing!
                    user = signup_form.save()

                    if user_type == 'vendor':
                        vendor_profile = vendor_form.save(commit=False)
                        vendor_profile.user = user
                        vendor_profile.save()

                    send_mail(
                        'Welcome to EventHub 🎉',
                        f'Dear {user.first_name},\n\nThanks for signing up! 🚀',
                        'noreply@eventhub.com', [user.email],
                        fail_silently=True
                    )
                    messages.success(request, "Account created! Please log in.")
                    return redirect('signup')
                
                except IntegrityError:
                    # This is now less likely to happen since forms have email validation
                    # but is good to keep as a fallback.
                    signup_form.add_error('email', 'This email is already registered.')

    # On a GET request or if forms are invalid
    else:
        login_form = LoginForm()
        signup_form = UserSignupForm()
        vendor_form = VendorProfileForm()
        show_signup = False # Default to showing the login form

    context = {
        'login_form': login_form,
        'signup_form': signup_form,
        'vendor_form': vendor_form,
        'show_signup': show_signup,
    }
    return render(request, 'event/signup.html', context)

def logout(request):
    request.session.flush()
    messages.success(request, "Logged out successfully.")
    return redirect('home')

def vendor(request):
    if 'user_id' not in request.session:
        messages.error(request, "You must be logged in to view this page.")
        return redirect('signup')

    if request.session.get('user_type') != 'vendor':
        messages.error(request, "This page is for vendors only.")
        return redirect('home')

    try:
        vendor_profile = VendorProfile.objects.select_related('user').get(user__id=request.session['user_id'])
        portfolio_items = VendorDis.objects.filter(vendor=vendor_profile).select_related('event')
        for item in portfolio_items:
            if item.tags:
                item.tags_list = [tag.strip() for tag in item.tags.split(',')]
            else:
                item.tags_list = []

    except VendorProfile.DoesNotExist:
        messages.error(request, "Could not find a vendor profile for your account.")
        return redirect('logout')

    context = {
        'vendor': vendor_profile,
        'portfolio': portfolio_items
    }
    return render(request, 'event/vendor.html', context)

genai.configure(api_key=settings.GOOGLE_API_KEY)


@csrf_exempt
def generate_tags_and_upload(request):
    if 'user_id' not in request.session:
        return JsonResponse({'success': False, 'error': 'User not authenticated.'}, status=401)
    
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            user_id = request.session['user_id']
            vendor_profile = VendorProfile.objects.get(user__id=user_id)
            image_file = request.FILES['image']
            image_parts = [{"mime_type": image_file.content_type, "data": image_file.read()}]
            prompt = """
            Analyze this image from an event. Provide a comma-separated list of 5-7 relevant tags 
            for a vendor portfolio. Tags should describe the event type, key elements, and ambiance.
            Examples: Wedding, Outdoor, Floral; Conference, Corporate, Presentation; Concert, Lights, Crowd.
            """

            # 3. Call Gemini API
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            response = model.generate_content([prompt, *image_parts])

            # 4. Clean up the response into tags
            generated_tags = [tag.strip() for tag in response.text.split(',') if tag.strip()]

            # 5. Save to DB
            image_file.seek(0)
            tags_str = ','.join(generated_tags)
            new_portfolio_item = VendorDis.objects.create(
                vendor=vendor_profile,
                image=image_file,
                tags=tags_str
            )

            # 6. Return response
            return JsonResponse({
                'success': True,
                'image_url': new_portfolio_item.image.url,
                'tags': generated_tags,
            })

        except VendorProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Vendor profile not found.'}, status=404)
        except Exception as e:
            print(f"An error occurred: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


def safe_embedding(array):
    """
    Convert list to numpy array and check for NaN/empty.
    Returns None if invalid.
    """
    if array is None:
        return None
    arr = np.array(array, dtype=np.float32)
    if arr.size == 0 or np.any(np.isnan(arr)):
        return None
    return arr


def image_search(request):
    print("📩 Image search called:", request.method, request.FILES)

    if request.method == "POST" and "image" in request.FILES:
        uploaded_image = request.FILES["image"]
        print("📂 Uploaded image:", uploaded_image)

        temp_path = None
        try:
            # Save uploaded image to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                for chunk in uploaded_image.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name

            # Generate embedding for uploaded image
            query_embedding = get_image_embedding(temp_path)
            query_embedding = safe_embedding(query_embedding)

            if query_embedding is None:
                return JsonResponse({"success": False, "error": "Query embedding invalid"})

            print("✅ Query embedding shape:", query_embedding.shape)

            results = []
            vendors = VendorDis.objects.exclude(embedding=None)

            for vendor in vendors:
                vendor_embedding = safe_embedding(vendor.embedding)
                if vendor_embedding is None:
                    print(f"⚠️ Skipping vendor {vendor.vendor.business_name}, invalid embedding")
                    continue

                try:
                    similarity = cosine_similarity(
                        query_embedding.reshape(1, -1),
                        vendor_embedding.reshape(1, -1)
                    )[0][0]
                except Exception as e:
                    print(f"❌ Similarity error for {vendor.vendor.business_name}: {e}")
                    continue

                results.append({
                    "image_url": vendor.image.url,
                    "vendor": vendor.vendor.business_name,
                    "similarity": float(similarity),
                    "tags": vendor.tags.split(",") if vendor.tags else [],
                    "vendor_url": f"/vendor/{vendor.vendor.pk}/",
                })

            results = sorted(results, key=lambda x: x["similarity"], reverse=True)

            return JsonResponse({"success": True, "results": results[:5]})

        except Exception as e:
            print("❌ Error in image_search:", str(e))
            return JsonResponse({"success": False, "error": str(e)})

        finally:
            # ✅ Always clean up temp file
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    return JsonResponse({"success": False, "results": []})
@csrf_exempt

def text_search(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            query = data.get("query", "").strip()
            if not query:
                return JsonResponse({"success": False, "error": "Empty query"})

            query_embedding = get_text_embedding(query)
            query_embedding = safe_embedding(query_embedding)

            if query_embedding is None:
                return JsonResponse({"success": False, "error": "Query embedding invalid"})

            results = []
            vendors = VendorDis.objects.exclude(embedding=None)

            # keywords we want to boost for wedding-related queries
            wedding_keywords = ["wedding", "bride", "groom", "mandap", "ceremony", "decor"]

            for vendor in vendors:
                vendor_embedding = safe_embedding(vendor.embedding)
                if vendor_embedding is None:
                    continue

                similarity = cosine_similarity(
                    query_embedding.reshape(1, -1),
                    vendor_embedding.reshape(1, -1)
                )[0][0]

                # ✅ keyword boosting
                description_text = (vendor.tags or "").lower()
                if any(kw in description_text for kw in wedding_keywords):
                    similarity += 0.15  # boost score if vendor is wedding-related

                results.append({
                    "image_url": vendor.image.url,
                    "vendor": vendor.vendor.business_name,
                    "similarity": float(similarity),
                    "tags": vendor.tags.split(",") if vendor.tags else [],
                    "vendor_url": f"/vendor/{vendor.vendor.pk}/",
                })

            # sort results after boosting
            results = sorted(results, key=lambda x: x["similarity"], reverse=True)
            return JsonResponse({"success": True, "results": results[:5]})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})

def get_text_embedding(query: str):
    try:
        embedding_response = genai.embed_content(
            model="models/text-embedding-004", 
            content=query,
            task_type="retrieval_query"        
        )
        return embedding_response["embedding"]
    except Exception as e:
        print("❌ Error in get_text_embedding:", str(e))
        return None
    


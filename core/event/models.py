from django.db import models
class User(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    password = models.CharField(max_length=128)
    USER_TYPE_CHOICES = (
        ("consumer", "Consumer"),
        ("vendor", "Vendor"),
    )

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default="consumer")
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class VendorProfile(models.Model):
    SERVICE_CHOICES = [
        ('decoration', 'Event Decoration'), ('catering', 'Catering Services'),
        ('photography', 'Photography & Videography'), ('venue', 'Venue Management'),
        ('entertainment', 'Entertainment'), ('planning', 'Event Planning'),
        ('lighting', 'Lighting & Audio'), ('transport', 'Transportation'),
        ('other', 'Other Services')
    ]
    EXPERIENCE_CHOICES = [
        ('1', '1 years'), ('2', '2 years'),
        ('6', '6 years'), ('10+', '10+ years')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    business_name = models.CharField(max_length=255)
    service_category = models.CharField(max_length=100, choices=SERVICE_CHOICES)
   
    experience = models.CharField(max_length=10, choices=EXPERIENCE_CHOICES)
    business_description = models.TextField()

    def __str__(self):
        return self.business_name

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=200)

    def __str__(self):
        return self.title

class VendorService(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE)
    service_type = models.CharField(max_length=100, choices=VendorProfile.SERVICE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.service_type} for {self.event.title} by {self.vendor.business_name}"
    
class VendorDis(models.Model):
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to='vendor_images/')
    tags = models.JSONField(default=list, blank=True) 
    profile_photo=models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    embedding = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        return f"{self.vendor.business_name} - {self.id}"
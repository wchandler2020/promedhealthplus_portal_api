from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.conf import settings
from django.utils import timezone
from sales_rep.models import SalesRep
from phonenumber_field.modelfields import PhoneNumberField
import random

COUNTRY_CODE_CHOICES = (
    ('+93', 'Afghanistan'),
    ('+355', 'Albania'),
    ('+213', 'Algeria'),
    ('+1', 'American Samoa'),
    ('+376', 'Andorra'),
    ('+244', 'Angola'),
    ('+1', 'Anguilla'),
    ('+1', 'Antigua and Barbuda'),
    ('+54', 'Argentina'),
    ('+374', 'Armenia'),
    ('+297', 'Aruba'),
    ('+247', 'Ascension Island'),
    ('+61', 'Australia'),
    ('+672', 'Australian External Territories'),
    ('+43', 'Austria'),
    ('+994', 'Azerbaijan'),
    ('+1', 'Bahamas'),
    ('+973', 'Bahrain'),
    ('+880', 'Bangladesh'),
    ('+1', 'Barbados'),
    ('+375', 'Belarus'),
    ('+32', 'Belgium'),
    ('+501', 'Belize'),
    ('+229', 'Benin'),
    ('+1', 'Bermuda'),
    ('+975', 'Bhutan'),
    ('+591', 'Bolivia'),
    ('+387', 'Bosnia and Herzegovina'),
    ('+267', 'Botswana'),
    ('+55', 'Brazil'),
    ('+1', 'British Virgin Islands'),
    ('+673', 'Brunei'),
    ('+359', 'Bulgaria'),
    ('+226', 'Burkina Faso'),
    ('+257', 'Burundi'),
    ('+855', 'Cambodia'),
    ('+237', 'Cameroon'),
    ('+1', 'Canada'),
    ('+238', 'Cape Verde'),
    ('+1', 'Cayman Islands'),
    ('+236', 'Central African Republic'),
    ('+235', 'Chad'),
    ('+56', 'Chile'),
    ('+86', 'China'),
    ('+61', 'Christmas Island'),
    ('+61', 'Cocos (Keeling) Islands'),
    ('+57', 'Colombia'),
    ('+269', 'Comoros'),
    ('+242', 'Congo'),
    ('+243', 'Congo (Dem. Rep.)'),
    ('+682', 'Cook Islands'),
    ('+506', 'Costa Rica'),
    ('+225', 'Cote d\'Ivoire'),
    ('+385', 'Croatia'),
    ('+53', 'Cuba'),
    ('+599', 'Curaçao'),
    ('+357', 'Cyprus'),
    ('+420', 'Czech Republic'),
    ('+45', 'Denmark'),
    ('+253', 'Djibouti'),
    ('+1', 'Dominica'),
    ('+1', 'Dominican Republic'),
    ('+593', 'Ecuador'),
    ('+20', 'Egypt'),
    ('+503', 'El Salvador'),
    ('+240', 'Equatorial Guinea'),
    ('+291', 'Eritrea'),
    ('+372', 'Estonia'),
    ('+251', 'Ethiopia'),
    ('+500', 'Falkland Islands'),
    ('+298', 'Faroe Islands'),
    ('+679', 'Fiji'),
    ('+358', 'Finland'),
    ('+33', 'France'),
    ('+594', 'French Guiana'),
    ('+689', 'French Polynesia'),
    ('+241', 'Gabon'),
    ('+220', 'Gambia'),
    ('+995', 'Georgia'),
    ('+49', 'Germany'),
    ('+233', 'Ghana'),
    ('+350', 'Gibraltar'),
    ('+30', 'Greece'),
    ('+299', 'Greenland'),
    ('+1', 'Grenada'),
    ('+590', 'Guadeloupe'),
    ('+1', 'Guam'),
    ('+502', 'Guatemala'),
    ('+224', 'Guinea'),
    ('+245', 'Guinea-Bissau'),
    ('+592', 'Guyana'),
    ('+509', 'Haiti'),
    ('+504', 'Honduras'),
    ('+852', 'Hong Kong'),
    ('+36', 'Hungary'),
    ('+354', 'Iceland'),
    ('+91', 'India'),
    ('+62', 'Indonesia'),
    ('+98', 'Iran'),
    ('+964', 'Iraq'),
    ('+353', 'Ireland'),
    ('+972', 'Israel'),
    ('+39', 'Italy'),
    ('+1', 'Jamaica'),
    ('+81', 'Japan'),
    ('+962', 'Jordan'),
    ('+7', 'Kazakhstan'),
    ('+254', 'Kenya'),
    ('+686', 'Kiribati'),
    ('+383', 'Kosovo'),
    ('+965', 'Kuwait'),
    ('+996', 'Kyrgyzstan'),
    ('+856', 'Laos'),
    ('+371', 'Latvia'),
    ('+961', 'Lebanon'),
    ('+266', 'Lesotho'),
    ('+231', 'Liberia'),
    ('+218', 'Libya'),
    ('+423', 'Liechtenstein'),
    ('+370', 'Lithuania'),
    ('+352', 'Luxembourg'),
    ('+853', 'Macau'),
    ('+389', 'Macedonia'),
    ('+261', 'Madagascar'),
    ('+265', 'Malawi'),
    ('+60', 'Malaysia'),
    ('+960', 'Maldives'),
    ('+223', 'Mali'),
    ('+356', 'Malta'),
    ('+692', 'Marshall Islands'),
    ('+596', 'Martinique'),
    ('+222', 'Mauritania'),
    ('+230', 'Mauritius'),
    ('+262', 'Mayotte'),
    ('+52', 'Mexico'),
    ('+691', 'Micronesia'),
    ('+373', 'Moldova'),
    ('+377', 'Monaco'),
    ('+976', 'Mongolia'),
    ('+382', 'Montenegro'),
    ('+1', 'Montserrat'),
    ('+212', 'Morocco'),
    ('+258', 'Mozambique'),
    ('+95', 'Myanmar'),
    ('+264', 'Namibia'),
    ('+674', 'Nauru'),
    ('+977', 'Nepal'),
    ('+31', 'Netherlands'),
    ('+599', 'Netherlands Antilles'),
    ('+687', 'New Caledonia'),
    ('+64', 'New Zealand'),
    ('+505', 'Nicaragua'),
    ('+227', 'Niger'),
    ('+234', 'Nigeria'),
    ('+683', 'Niue'),
    ('+672', 'Norfolk Island'),
    ('+850', 'North Korea'),
    ('+1', 'Northern Mariana Islands'),
    ('+47', 'Norway'),
    ('+968', 'Oman'),
    ('+92', 'Pakistan'),
    ('+680', 'Palau'),
    ('+970', 'Palestine'),
    ('+507', 'Panama'),
    ('+675', 'Papua New Guinea'),
    ('+595', 'Paraguay'),
    ('+51', 'Peru'),
    ('+63', 'Philippines'),
    ('+48', 'Poland'),
    ('+351', 'Portugal'),
    ('+1', 'Puerto Rico'),
    ('+974', 'Qatar'),
    ('+262', 'Reunion'),
    ('+40', 'Romania'),
    ('+7', 'Russia'),
    ('+250', 'Rwanda'),
    ('+590', 'Saint Barthelemy'),
    ('+290', 'Saint Helena'),
    ('+1', 'Saint Kitts and Nevis'),
    ('+1', 'Saint Lucia'),
    ('+590', 'Saint Martin'),
    ('+508', 'Saint Pierre and Miquelon'),
    ('+1', 'Saint Vincent and the Grenadines'),
    ('+685', 'Samoa'),
    ('+378', 'San Marino'),
    ('+239', 'Sao Tome and Principe'),
    ('+966', 'Saudi Arabia'),
    ('+221', 'Senegal'),
    ('+381', 'Serbia'),
    ('+248', 'Seychelles'),
    ('+232', 'Sierra Leone'),
    ('+65', 'Singapore'),
    ('+1', 'Sint Maarten'),
    ('+421', 'Slovakia'),
    ('+386', 'Slovenia'),
    ('+677', 'Solomon Islands'),
    ('+252', 'Somalia'),
    ('+27', 'South Africa'),
    ('+82', 'South Korea'),
    ('+211', 'South Sudan'),
    ('+34', 'Spain'),
    ('+94', 'Sri Lanka'),
    ('+249', 'Sudan'),
    ('+597', 'Suriname'),
    ('+47', 'Svalbard and Jan Mayen'),
    ('+268', 'Swaziland'),
    ('+46', 'Sweden'),
    ('+41', 'Switzerland'),
    ('+963', 'Syria'),
    ('+886', 'Taiwan'),
    ('+992', 'Tajikistan'),
    ('+255', 'Tanzania'),
    ('+66', 'Thailand'),
    ('+670', 'Timor-Leste'),
    ('+228', 'Togo'),
    ('+690', 'Tokelau'),
    ('+676', 'Tonga'),
    ('+1', 'Trinidad and Tobago'),
    ('+216', 'Tunisia'),
    ('+90', 'Turkey'),
    ('+993', 'Turkmenistan'),
    ('+1', 'Turks and Caicos Islands'),
    ('+688', 'Tuvalu'),
    ('+256', 'Uganda'),
    ('+380', 'Ukraine'),
    ('+971', 'United Arab Emirates'),
    ('+44', 'United Kingdom'),
    ('+1', 'United States'),
    ('+598', 'Uruguay'),
    ('+998', 'Uzbekistan'),
    ('+678', 'Vanuatu'),
    ('+39', 'Vatican City'),
    ('+58', 'Venezuela'),
    ('+84', 'Vietnam'),
    ('+1', 'Virgin Islands, U.S.'),
    ('+681', 'Wallis and Futuna'),
    ('+212', 'Western Sahara'),
    ('+967', 'Yemen'),
    ('+260', 'Zambia'),
    ('+263', 'Zimbabwe'),
)

verification_methods = (
    ('email', 'Email'), ('sms', 'SMS')
)

ROLES = (
    ('Primary Care Provider', 'Primary Care Provider'),
    ('Nurse', 'Nurse'),
    ('Administrator', 'Administrator'),
    ('Medical Supply Technician', 'Medical Supply Technician'),
)

def generate_code():
    return str(random.randint(100000, 999999))

class User(AbstractUser):
    username = models.CharField(unique=True, max_length=255)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = PhoneNumberField(null=True, blank=True)
    country_code = models.CharField(
        max_length=5, 
        choices=COUNTRY_CODE_CHOICES, 
        default='+1', # Set a default country code
        help_text="Default country code is +1 (US)."
    )
    otp = models.CharField(max_length=100, null=True, blank=True)
    refresh_token = models.CharField(max_length=1000, null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self) -> str:
        return f'{self.email} | {self.date_joined}'

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email.split('@')[0] if '@' in self.email else self.email
        if not self.full_name:
            self.full_name = f"{self.first_name} {self.last_name}".strip() or self.username
        super().save(*args, **kwargs)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    sales_rep = models.ForeignKey(SalesRep, on_delete=models.SET_NULL, null=True, blank=True, related_name="providers")
    image = models.FileField(upload_to='images', default=f'{settings.MEDIA_URL}images/default_user.jpg', null=True, blank=True)
    role = models.CharField(max_length=200, choices=ROLES, null=True, blank=True)
    facility = models.CharField(max_length=200, null=True, blank=True)
    facility_phone_number = models.CharField(max_length=20, null=True, blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True) 
    country = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    bio = models.TextField(blank=True,null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        if str(self.full_name):
            return str(self.full_name)
        else:
            return str(self.user.username)

    def save(self, *args, **kwargs):
        if self.full_name == None or self.full_name == '':
            self.full_name = self.user.username
        super(Profile, self).save(*args, **kwargs)


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

def post_save_profile(sender, instance, **kwargs):
    instance.profile.save()

post_save.connect(create_user_profile, sender=User)
post_save.connect(post_save_profile, sender=User)

class Verification_Code(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    method = models.CharField(max_length=10, choices=verification_methods)
    created_at = models.DateTimeField(default=timezone.now)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    
    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=10)

        



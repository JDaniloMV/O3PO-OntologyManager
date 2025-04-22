from django.db import models
from django.contrib.postgres.fields import ArrayField
from rest_framework import generics, serializers

class Product(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return self.name

class ProductInterest(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='interesses')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interesse em {self.product.name} por {self.name}"

class HomeBanner(models.Model):
    headline = models.CharField(max_length=200)
    subtext = models.TextField(blank=True)
    cta_text = models.CharField(max_length=50, default="Saiba Mais")
    is_active = models.BooleanField(default=True)

class FeaturedProduct(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    description = models.TextField()
    highlight = models.CharField(max_length=100)

class AboutSection(models.Model):
    mission = models.TextField(verbose_name="Missão")
    vision = models.TextField(verbose_name="Visão")
    values = models.TextField(verbose_name="Valores")
    history = models.TextField(verbose_name="História", blank=True)
    team = models.TextField(verbose_name="Equipe", blank=True)
    diferentials = models.TextField(verbose_name="Diferenciais", blank=True)
    partners = models.TextField(verbose_name="Parceiros", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Seção Sobre - Atualizada em " + self.updated_at.strftime("%d/%m/%Y")

class Testimonial(models.Model):
    client_name = models.CharField(max_length=100)
    client_image = models.ImageField(upload_to='testimonials/')
    quote = models.TextField()
    date = models.DateField(auto_now_add=True)

class ProductCTA(models.Model):
    title = models.CharField(max_length=100)
    products = models.ManyToManyField('Product')

class TeamMember(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nome")
    position = models.CharField(max_length=100, verbose_name="Cargo")
    specialty = models.CharField(max_length=100, verbose_name="Especialidade")
    image = models.ImageField(upload_to='team/', verbose_name="Foto")
    linkedin = models.URLField(blank=True, verbose_name="LinkedIn")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordem de Exibição")

    class Meta:
        ordering = ['order']
        verbose_name = "Membro da Equipe"
        verbose_name_plural = "Membros da Equipe"

    def __str__(self):
        return f"{self.name} - {self.position}"


class Post(models.Model):
    CATEGORIAS = [
        ("Biomecânica da Corrida", "Biomecânica da Corrida"),
        ("Dicas de Treinamento", "Dicas de Treinamento"),
        ("Estudos e Pesquisas", "Estudos e Pesquisas"),
        ("Notícias sobre Produtos", "Notícias sobre Produtos"),
        ("Vídeos", "Vídeos"),
    ]

    title = models.CharField(max_length=200)
    summary = models.TextField()
    content = models.TextField()
    date = models.DateField(auto_now_add=True)
    slug = models.SlugField(unique=True)
    category = models.CharField(max_length=50, choices=CATEGORIAS)
    video_url = models.URLField(blank=True, null=True)  

    def __str__(self):
        return self.title

class ContactPageInfo(models.Model):
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255, blank=True, null=True)
    google_maps_embed_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Informações de Contato"
    
class SocialLink(models.Model):
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('youtube', 'YouTube'),
    ]

    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    url = models.URLField()
    icon_class = models.CharField(max_length=100, help_text="Classe do ícone (ex: 'fa-brands fa-instagram')")

    def __str__(self):
        return self.platform

class ContactInfo(models.Model):
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)
    map_embed_url = models.URLField("Google Maps Embed URL", blank=True, null=True)

    def __str__(self):
        return "Informações de Contato"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mensagem de {self.name} ({self.email})"

class PrivacyPolicy(models.Model):
    data_protection = models.TextField("Proteção de Dados")
    refund_policy = models.TextField("Política de Cancelamento e Reembolso")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Política de Privacidade"
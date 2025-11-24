from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Colaborador

@receiver(post_save, sender=User)
def crear_perfil_colaborador(sender, instance, created, **kwargs):
    """
    Esta función se ejecuta automáticamente CADA VEZ que un User se guarda.
    """
    if created:
        rol_asignado = 'estilista' 

        if instance.is_superuser:
            rol_asignado = 'admin'
        Colaborador.objects.create(user=instance, rol=rol_asignado)

@receiver(post_save, sender=User)
def guardar_perfil_colaborador(sender, instance, **kwargs):
    try:
        instance.colaborador.save()
    except Colaborador.DoesNotExist:
        Colaborador.objects.create(user=instance, rol='estilista')
#----- Evolution for reviews
from django_evolution.mutations import *
from django.db import models

MUTATIONS = [
    AddField('ReviewRequest', 'revision', models.CharField, max_length=42, null=True)
]
#----------------------

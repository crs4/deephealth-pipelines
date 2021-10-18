#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from django.contrib.auth.models import Group, User

username = os.environ["PROMORT_USER"]
password = os.environ["PROMORT_PASSWORD"]
user = User.objects.get_or_create(username=username)[0]
user.set_password(password)
user.save()

rois_manager_group = Group.objects.get(name="ROIS_MANAGERS")
rois_manager_group.user_set.add(user)

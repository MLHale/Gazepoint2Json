# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import *

# Import models
from django.db import models
from django.contrib.auth.models import *
from api.models import *

#REST API
from rest_framework import viewsets, filters
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework.permissions import *
from rest_framework.decorators import *
from rest_framework.authentication import *

#Gazepoint stuff
import os
import time

from GazepointAnalysis import Gazepoint2JSON

import threading


def sendData(username,password,api_endpoint):
	t = threading.currentThread()
	tracker = Gazepoint2JSON(debug=True, api_endpoint=api_endpoint, api_user=username, api_password=password)

	# Calibrate the tracker.
	# tracker.calibrate()

	# Start recording data.
	tracker.start_recording()
	tracker.log("START=%d" % (round(time.time()*1000)))

	# Collect data for a bit.
	i=0
	while getattr(t, "do_run", True):
		tracker.log("STEP %d: %d" % (i+1, round(time.time()*1000)))
		print 'on: ' + str(i)
		time.sleep(1.0)

	# Stop recording.
	tracker.log("STOP=%d" % (round(time.time()*1000)))
	tracker.stop_recording()
	tracker.close()

class Session(APIView):
	permission_classes = (AllowAny,)

	def post(self, request, *args, **kwargs):
		# Gather login credentials
		username = request.POST.get('username')
		password = request.POST.get('password')
		cybertrustpath = request.POST.get('cybertrustpath')

		data = {
			'msg': '',
		}
		print request.POST
		# check to see if they are already stored
		session = EyeTrackerSession.objects.all()
		try:
			# add type checking
			if session.first():
				session = session.first()
				session.username = username
				session.password = password
				session.cybertrustpath = cybertrustpath
				session.save()
			else:
				print 'Creating session'
				session = EyeTrackerSession(username=username,password=password,cybertrustpath=cybertrustpath)
				session.save()

			#start gazepoint capture
			t = threading.Thread(target=sendData, args=(username,password,cybertrustpath))
			t.start()
			# time.sleep(5)
			# t.do_run = False
			# t.join()
			data['msg'] = 'gazepoint started'


		except Exception as e:
			data['msg'] = str(e)

		return Response(data)

	def delete(self, request, *args, **kwargs):
		session = EyeTrackerSession.objects.all().first()
		session.username = ''
		session.password = ''
		session.cybertrustpath = ''
		session.save()
		return Response(status=status.HTTP_204_NO_CONTENT)

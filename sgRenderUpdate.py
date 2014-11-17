import subprocess
import os
import maya.cmds as mc
import maya.mel as mm

from functools import partial

from tools import mayaTools
reload(mayaTools)

from tools import fileUtils
reload(fileUtils)

from miscs import cameraDomeGenerator as camGen
reload(camGen)

from sg import utils as sgUtils
reload(sgUtils)

class MyApp() : 
	def __init__(self) : 


		self.ui = 'sgRenderUpdate'
		self.renderPath = str()


	def mayaUI(self) : 
		
		if mc.window(self.ui, exists = True) : 
			mc.deleteUI(self.ui)
			
		mc.window(self.ui, t = '2D Tool v.1.2')
		mc.columnLayout(adj = 1,rs = 4)

		mc.text(l = 'projName')
		mc.textField('%s_projTX' % self.ui, tx = 'Lego_City2D')
		mc.text(l = 'episodeName')
		mc.textField('%s_episodeTX' % self.ui, tx = 'cty2D_EP02_Demolition')
		mc.text(l = 'sequenceName')
		mc.textField('%s_sequenceTX' % self.ui, tx = 'q0010')
		mc.text(l = 'shotName')
		mc.textField('%s_shotTX' % self.ui)
		mc.text(l = 'Task Name')
		mc.textField('%s_taskNameTX' % self.ui)
		mc.text(l = 'Path')
		mc.textField('%s_pathTX' % self.ui, cc = partial(self.autoFill))
		mc.text(l = 'disply')
		mc.textField('%s_displayTX' % self.ui)

		mc.button(l = 'Set Shotgun', h = 30, c = partial(self.updateShotgunCmd))

		mc.text('%s_statusLabel' % self.ui, l = '')

		mc.showWindow()

		mc.window(self.ui, e = True, wh = [400, 400])


	def updateShotgunCmd(self, arg = None) : 

		projName = mc.textField('%s_projTX' % self.ui, q = True, tx = True)
		episode = mc.textField('%s_episodeTX' % self.ui, q = True, tx = True)
		sequenceName = mc.textField('%s_sequenceTX' % self.ui, q = True, tx = True)
		shotName = mc.textField('%s_shotTX' % self.ui, q = True, tx = True)
		taskName = mc.textField('%s_taskNameTX' % self.ui, q = True, tx = True)
		path = mc.textField('%s_pathTX' % self.ui, q = True, tx = True).replace('\\', '\\\\')
		displayName = mc.textField('%s_displayTX' % self.ui, q = True, tx = True)
		pipeline = 'Render'
		
		result = sgUtils.createShotTask(projName, episode, sequenceName, shotName, pipeline, taskName)

		data = {'sg_hero_2': {'local_path': path, 'name': displayName}}
		result = sgUtils.sg.update('Task', result['id'], data)

		if result : 
			mc.text('%s_statusLabel' % self.ui, e = True, l = 'Success', bgc = [0, 1, 0])

	def autoFill(self, arg = None) : 
		
		path = mc.textField('%s_pathTX' % self.ui, q = True, tx = True).replace('\\', '/')
		

		# P:\Lego_City2D\asset\3D\vehicle\construction\cty_carBulldozer_60074\images\library\default\h330_n000_cam1
		print path
		eles = path.split('/')

		taskName = eles[6]
		displayName = eles[-1].replace('_cam', '')

		taskName = mc.textField('%s_taskNameTX' % self.ui, e = True, tx = taskName)
		display = mc.textField('%s_displayTX' % self.ui, e = True, tx = displayName)
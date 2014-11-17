import subprocess
import os
import maya.cmds as mc

from functools import partial

from tools import mayaTools
reload(mayaTools)

from tools import fileUtils
reload(fileUtils)

class minifig2D() : 
	def __init__(self) : 

		self.group = ['armGeoRGT_grp', 'armGeoLFT_grp', 'legGeo_grp', 'headGeo_grp', 'handGeoLFT_grp', 'handGeoRGT_grp', 'bodyGeo_grp', 'eyeGuideGeo_grp']
		self.renderLayerGrp = {'body': ['bodyGeo_grp', 'legGeo_grp'], 
						'LFT_arm': ['armGeoLFT_grp', 'handGeoLFT_grp'], 
						'RGT_arm': ['armGeoRGT_grp', 'handGeoRGT_grp'],
						'LFT_hand': ['handGeoLFT_grp', 'wristPlyZroLFT_grp'], 
						'RGT_hand': ['handGeoRGT_grp', 'wristPlyZroRGT_grp'], 
						'LFT_leg': ['legGeoLFT_grp', 'pelvis_ply'], 
						'RGT_leg': ['legGeoRGT_grp'], 
						'head': ['headGeo_grp']}


		self.ui = 'export2DTool'

		self.renderCameraName = 'renderCamera'
		self.currentCamera = str()
		self.renderCamera = []
		self.fileInfo = dict()

	def mayaUI(self) : 
		
		if mc.window(self.ui, exists = True) : 
			mc.deleteUI(self.ui)
			
		mc.window(self.ui, t = '2D Tool v.1.0')
		mc.columnLayout(adj = 1,rs = 3)

		mc.text(l = 'Project')
		mc.textField('%s_projectTX' % self.ui)

		mc.text(l = '2D Render Tool')
		mc.button(l = 'Make 2D Camera', h = 30, bgc = [0.4, 0.9, 0.4], c = partial(self.makeCamera))

		mc.frameLayout(borderStyle = 'etchedIn', lv = False)
		mc.rowColumnLayout(nc = 3, cw = ([1, 100], [2, 150], [3, 40]))

		mc.text(l = 'Current Camera : ', al = 'right')
		mc.textField('%s_crrCameraTX' % self.ui)
		mc.button(l = 'Get', bgc = [0.9, 0.9, 0.9], c = partial(self.setUI, 'getCurrentCamera'))

		mc.text(l = '2D Camera : ', al = 'right')
		mc.textField('%s_cameraTX' % self.ui)
		mc.button(l = 'Get', bgc = [0.9, 0.9, 0.9], c = partial(self.setUI, 'get2DCamera'))

		mc.text(l = 'Frame : ', al = 'right')
		mc.textField('%s_frameTX' % self.ui, tx = '1')
		mc.button(l = 'Get', bgc = [0.9, 0.9, 0.9], c = partial(self.setUI, 'getCurrentTime'))

		mc.setParent('..')
		mc.setParent('..')

		mc.button(l = '3D cam <--- Switch ---> 2D cam', h = 30, bgc = [0.8, 0.8, 0.3], c = partial(self.switchCamera))

		mc.text(l = 'Render List')
		mc.textScrollList('%s_TSL' % self.ui, numberOfRows = 8, allowMultiSelection = True)


		mc.checkBox(l = 'Prop')

		mc.frameLayout(borderStyle = 'etchedIn', lv = False)
		mc.rowColumnLayout(nc = 2, cw = ([1, 150], [2, 150]))

		mc.button(l = 'Export to List', h = 30, bgc = [0.4, 0.6, 0.9], c = partial(self.doCreateRenderLayer))
		mc.button(l = 'Run Batch', h = 30, bgc = [0.4, 0.9, 0.4], c = partial(self.runBatch))
		mc.button(l = 'Open bat file', h = 30, bgc = [1, 1, 1], c = partial(self.openInExplorer, 'bat file'))
		mc.button(l = 'Open output', h = 30, bgc = [1, 1, 1], c = partial(self.openInExplorer, 'output'))

		mc.setParent('..')
		mc.setParent('..')

		mc.showWindow()
		mc.window(self.ui, e = True, wh = [300, 495])

		self.readProject()
		self.checkCamera()
		self.listBatFile()



	def doCreateRenderLayer(self, arg = None) : 
		camera = mc.textField('%s_cameraTX' % self.ui, q = True, tx = True)
		frame = mc.textField('%s_frameTX' % self.ui, q = True, tx = True)
		rigGrp = mc.ls(sl = True)

		mc.currentTime(frame)

		if rigGrp and camera and frame : 
			self.createRenderLayerCmd(rigGrp[0], camera, frame)
			self.listBatFile()
			# self.removeCamera()

		else : 
			if not rigGrp : 
				print 'Select object'

			if not camera : 
				print 'No render camera'

			if not frame : 
				print 'Please set frame'



	def createRenderLayerCmd(self, rigGrp, camera, frame) : 

		layers = []

		namespace = mayaTools.getNamespace(rigGrp)
		# rigGrp = '%s:Rig_Grp' % (namespace)
		# camera = obj[1]

		# set render setting
		self.setRenderSetting()

		# set prefix
		mc.setAttr('defaultRenderGlobals.imageFilePrefix', '%s_<RenderLayer>' % namespace, type = "string")

		result = self.makeRenderLayer(namespace, 'body')
		layers.append(result)
		result = self.makeRenderLayer(namespace, 'LFT_arm')
		layers.append(result)
		result = self.makeRenderLayer(namespace, 'RGT_arm')
		layers.append(result)
		# result = self.makeRenderLayer(namespace, 'LFT_hand')
		# layers.append(result)
		# result = self.makeRenderLayer(namespace, 'RGT_hand')
		# layers.append(result)
		result = self.makeRenderLayer(namespace, 'head')
		layers.append(result)
		# result = self.makeRenderLayer(namespace, 'LFT_leg')
		# layers.append(result)
		# result = self.makeRenderLayer(namespace, 'RGT_leg')
		# layers.append(result)

		self.exportChar(namespace, rigGrp, layers, camera, frame)

		mc.delete(layers)



	def makeRenderLayer(self, namespace, key) : 
		selObjs = []
		if key in self.renderLayerGrp.keys() : 
			objs = self.renderLayerGrp[key]

			for each in objs : 
				selObj = '%s:%s' % (namespace, each)

				if mc.objExists(selObj) : 
					selObjs.append(selObj)

			if selObjs : 
				result = mc.createRenderLayer(selObjs, name = key, number = 1, noRecurse = True)
				print 'Create render layer %s -> %s' % (key, selObjs)

				return result


	def exportChar(self, namespace, char, layers, camera, frame) : 
		mc.select(char)
		mc.select(layers, add = True)
		mc.select(camera, add = True)
		mc.select('defaultRenderGlobals', add = True)

		mayaExportPath = self.getRenderPath()[0]
		mayaRenderPath = '%s/%s/%s' % (self.getRenderPath()[1], namespace, '%03d' % int(frame))
		expPath = '%s/%s' % (mayaExportPath, namespace)

		if not os.path.exists(expPath) : 
			os.makedirs(expPath)

		if not os.path.exists(mayaRenderPath) : 
			os.makedirs(mayaRenderPath)


		fileName = '%s/%s' % (expPath, '%s_%s.ma' % (namespace, '%03d' % int(frame)))

		mc.file(fileName, force = True, options = "v=0", typ = "mayaAscii", pr = True, es = True)

		self.genBatchFile(frame, camera, mayaRenderPath, fileName)


	def getRenderPath(self) : 
		currScene = mc.file(q = True, sn = True)

		if currScene : 
			sceneEles = currScene.split('/')
			episode = sceneEles[3]
			sequence = sceneEles[4]
			shot = sceneEles[5]
			root = ('/').join((currScene.split('/')[0:3]))
			shotRoot = ('/').join([root, episode, sequence, shot])
			exportPath = ('/').join([shotRoot, 'mayaRender'])
			renderPath = ('/').join([shotRoot, 'psd2D', 'mayaRender'])

			return exportPath, renderPath


	def genBatchFile(self, frame, camera, output, renderFile) : 
		batFile = renderFile.replace('.ma', '.bat')
		output = output.replace('/', '\\')
		renderFile = renderFile.replace('/', '\\')
		cmd = '"C:\\Program Files\\Autodesk\\Maya2012\\bin\\Render.exe" -r file -s %s -e %s -cam %s -rd "%s" "%s"' % (frame, frame, camera, output, renderFile)

		fileUtils.writeFile(batFile, cmd)


	def setRenderSetting(self, ) : 
		imageFormat = 32
		w = 2048
		h = 2048
		mc.setAttr('defaultRenderGlobals.imageFormat', imageFormat)
		mc.setAttr('defaultRenderGlobals.extensionPadding', 3)
		mc.setAttr('defaultResolution.width', w)
		mc.setAttr('defaultResolution.height', h)
		mc.setAttr('defaultRenderGlobals.animation', 1)


	def restoreRender(self, ) : 
		w = 1920	
		h = 1080
		mc.setAttr('defaultResolution.width', w)
		mc.setAttr('defaultResolution.height', h)



	def makeCamera(self, arg = None) : 
		self.setRenderSetting()
		self.currentCamera = mc.lookThru(q = True)

		if self.currentCamera : 

			if not mc.objExists(self.renderCameraName) : 
				self.renderCamera = mc.duplicate(self.currentCamera, n = self.renderCameraName)

			else : 
				self.renderCamera = [self.renderCameraName]

			mc.setAttr('renderCameraShape.panZoomEnabled', 1)
			mc.setAttr('renderCameraShape.renderPanZoom', 1)

			mc.textField('%s_cameraTX' % self.ui, e = True, tx = self.renderCamera[0])
			mc.textField('%s_crrCameraTX' % self.ui, e = True, tx = self.currentCamera)
			mc.lookThru(self.renderCamera[0])

		else : 
			print 'Cannot get current camera'


	def removeCamera(self, arg = None) : 
		mc.lookThru(self.currentCamera)
		if mc.objExists(self.renderCamera[0]) : 
			mc.delete(self.renderCamera[0])



	def switchCamera(self, arg = None) : 
		cam3D = mc.textField('%s_crrCameraTX' % self.ui, q = True, tx = True)
		cam2D = mc.textField('%s_cameraTX' % self.ui, q = True, tx = True)

		if cam3D and cam2D : 
			cam = {cam2D: cam3D, cam3D: cam2D}
			setting = {cam3D: 'self.setRenderSetting()', cam2D: 'self.restoreRender()'}
			currentCam = mc.lookThru(q = True)

			if currentCam : 
				mc.lookThru(cam[currentCam])
				eval(setting[currentCam])





	def readProject(self, arg = None) : 
		path = self.getRenderPath()[0]
		mc.textField('%s_projectTX' % self.ui, e = True, tx = path)


	def listBatFile(self, arg = None) : 
		path = mc.textField('%s_projectTX' % self.ui, q = True, tx = True)
		files = []

		dirs = fileUtils.listFolder(path)

		for each in dirs : 
			batFiles = fileUtils.listFile('%s/%s' % (path, each), 'bat')
			
			for eachBatFile in batFiles : 
				if not eachBatFile in files : 
					files.append(eachBatFile)
					renderPath = '%s/%s' % (self.getRenderPath()[1], each)
					self.fileInfo.update({eachBatFile: {'batFile': '%s/%s/%s' % (path, each, eachBatFile), 'renderPath': renderPath}})


		mc.textScrollList('%s_TSL' % self.ui, e = True, ra = True)

		for each in files : 
			mc.textScrollList('%s_TSL' % self.ui, e = True, append = each)


	def checkCamera(self) : 
		if mc.objExists(self.renderCameraName) : 
			mc.textField('%s_cameraTX' % self.ui, e = True, tx = self.renderCameraName)



	def runBatch(self, arg = None) : 
		sels = mc.textScrollList('%s_TSL' % self.ui, q = True, si = True)
		path = mc.textField('%s_projectTX' % self.ui, q = True, tx = True)

		for eachFile in sels : 
			filePath = self.fileInfo[eachFile]['batFile']

			if os.path.exists(filePath) : 
				# cmd = fileUtils.readFile(filePath)
				cmd = filePath
				cmdRep = subprocess.Popen(cmd,stdout=subprocess.PIPE).communicate()[0]
				print cmd

			else : 
				print 'Path not exists %s' % filePath

		print 'OK'


	def openInExplorer(self, mode, arg = None) : 
		sels = mc.textScrollList('%s_TSL' % self.ui, q = True, si = True)

		if mode == 'output' : 

			for each in sels : 
				checkPath = self.fileInfo[each]['renderPath'].replace('/', '\\')
				subprocess.Popen(r'explorer /select,"%s"' % checkPath)


		if mode == 'bat file' : 
			for each in sels : 
				checkPath = self.fileInfo[each]['batFile'].replace('/', '\\')
				subprocess.Popen(r'explorer /select,"%s"' % checkPath)


	def setUI(self, mode, arg = None) : 
		if mode == 'getCurrentCamera' : 
			camera = mc.lookThru(q = True)
			mc.textField('%s_crrCameraTX' % self.ui, e = True, tx = camera)

		if mode == 'get2DCamera' : 
			mc.textField('%s_cameraTX' % self.ui, e = True, tx = self.renderCameraName)

		if mode == 'getCurrentTime' : 
			currentTime = int(mc.currentTime(q = True))
			mc.textField('%s_frameTX' % self.ui, e = True, tx = currentTime)

import subprocess
import os
import maya.cmds as mc
import maya.mel as mm

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
			
		mc.window(self.ui, t = '2D Tool v.1.2')
		mc.columnLayout(adj = 1,rs = 3)

		mc.text(l = 'Project')
		mc.textField('%s_projectTX' % self.ui)

		mc.text(l = '2D Render Tool')
		

		mc.frameLayout(borderStyle = 'etchedIn', lv = False)
		mc.rowColumnLayout(nc = 4, cw = ([1, 100], [2, 150], [3, 60], [4, 120]), cs = [4, 3])

		mc.text(l = 'Camera Name') 
		mc.textField('%s_newCameraTX' % self.ui, tx = 'renderCamera')
		mc.button(l = 'Get', bgc = [0.9, 0.9, 0.9], c = partial(self.setUI, 'getNewCamera'))

		mc.setParent('..')
		mc.setParent('..')

		mc.button(l = 'Make 2D Camera', bgc = [0.4, 0.9, 0.4], c = partial(self.makeCamera))

		mc.frameLayout(borderStyle = 'etchedIn', lv = False)
		mc.rowColumnLayout(nc = 4, cw = ([1, 100], [2, 150], [3, 60], [4, 120]), cs = [4, 6])

		mc.text(l = 'Current Camera : ', al = 'right')
		mc.textField('%s_crrCameraTX' % self.ui)
		mc.button(l = 'Get', bgc = [0.9, 0.9, 0.9], c = partial(self.setUI, 'getCurrentCamera'))
		mc.optionMenu('%s_crrCameraOM' % self.ui, l='', changeCommand = partial(self.setUI, 'getCurrentCameraOM'))
		self.setMenuItemCamera()

		mc.text(l = '2D Camera : ', al = 'right')
		mc.textField('%s_cameraTX' % self.ui)
		mc.button(l = 'Get (1.)', bgc = [0.9, 0.9, 0.9], c = partial(self.setUI, 'get2DCamera'))
		mc.optionMenu('%s_cameraOM' % self.ui, l = '', changeCommand = partial(self.setUI, 'get2DCameraOM'))
		self.setMenuItemCamera()

		mc.text(l = 'Frame : ', al = 'right')
		mc.textField('%s_frameTX' % self.ui, tx = '1')
		mc.button(l = 'Get (2.)', bgc = [0.9, 0.9, 0.9], c = partial(self.setUI, 'getCurrentTime'))
		mc.checkBox('%s_multiCB' % self.ui, l = 'Multi Frame')

		mc.setParent('..')
		mc.setParent('..')

		mc.frameLayout(borderStyle = 'etchedIn', lv = False)
		mc.rowColumnLayout(nc = 3, cw = ([1, 200], [2, 150], [3, 100]), cs = ([2, 2]))

		mc.button(l = '3D cam <--- Switch ---> 2D cam', h = 30, bgc = [0.8, 0.8, 0.3], c = partial(self.switchCamera))
		mc.button(l = 'Set Key 2D PanZoom', h = 30, bgc = [1, 0.2, 0.2], c = partial(self.setKey))
		mc.button(l = '+ Light', h = 30, bgc = [1, 1, 1], c = partial(self.createLight))

		mc.setParent('..')
		mc.setParent('..')

		mc.frameLayout(borderStyle = 'etchedIn', lv = False)
		mc.columnLayout(adj = True, rs = 4)

		mc.button(l = 'Export to List (3.)', h = 30, bgc = [0.4, 0.6, 0.9], c = partial(self.doCreateRenderLayer))

		mc.setParent('..')
		mc.setParent('..')

		mc.frameLayout(borderStyle = 'etchedIn', lv = False)
		mc.rowColumnLayout(nc = 4, cw = ([1, 100], [2, 100], [3, 100], [4, 160]), cs = ([2, 2]))

		mc.radioCollection('%s_RDB' % self.ui)
		mc.radioButton( '%s_charRDB' % self.ui, label='Character', sl = True)
		mc.radioButton( '%s_propRDB' % self.ui, label='Prop')
		mc.radioButton( '%s_exportAllRDB' % self.ui, label='This scene')
		mc.checkBox('%s_extraCB' % self.ui, l = 'Add Layer', onc = partial(self.setUI, 'onAddLayers'), ofc = partial(self.setUI, 'offAddLayers'), v = True)
		mc.checkBox('%s_deleteCB' % self.ui, l = 'Delete after export') 
		mc.text(l = '')
		mc.text(l = '')
		mc.text(l = '')
		mc.checkBox('%s_namespaceCB' % self.ui, l = 'Skip Namespace') 

		mc.setParent('..')
		mc.setParent('..')

		mc.frameLayout(borderStyle = 'etchedIn', lv = False)
		mc.rowColumnLayout(nc = 2, cw = ([1, 250], [2, 200]))

		mc.columnLayout(adj = True, rs = 4)
		mc.text(l = 'Render List')
		mc.textScrollList('%s_TSL' % self.ui, numberOfRows = 8, allowMultiSelection = True)
		mc.button(l = 'Run Batch', h = 30, bgc = [0.4, 0.9, 0.4], c = partial(self.runBatch))
		mc.button(l = 'Open bat file', bgc = [1, 0.6, 0.2], c = partial(self.openInExplorer, 'bat file'))
		mc.setParent('..')

		mc.columnLayout(adj = True, rs = 4)
		mc.text(l = 'RenderLayer')
		mc.textScrollList('%s_renderLayerTSL' % self.ui, numberOfRows = 8, allowMultiSelection = True, en = True)
		mc.button(l = 'Refresh', c = partial(self.listRenderLayer), bgc = [1, 1, 1], h = 30)
		mc.button(l = 'Open output', bgc = [1, 0.6, 0.2], c = partial(self.openInExplorer, 'output'))
		
		mc.setParent('..')

		mc.setParent('..')
		mc.setParent('..')


		mc.showWindow()
		mc.window(self.ui, e = True, wh = [460, 600])

		self.readProject()
		self.checkCamera()
		self.listBatFile()
		self.listRenderLayer()



	def doCreateRenderLayer(self, arg = None) : 
		# 2D camera
		camera = mc.textField('%s_cameraTX' % self.ui, q = True, tx = True)

		# render frame
		frame = mc.textField('%s_frameTX' % self.ui, q = True, tx = True)
		rigGrp = mc.ls(sl = True)

		# character or prop
		value = mc.radioCollection('%s_RDB' % self.ui, q = True, sl = True)

		frames = self.checkMultiFrame(frame)

		if frames : 

			for eachFrame in frames : 

				if rigGrp and camera and eachFrame : 

					mc.currentTime(eachFrame)
					
					if value == '%s_charRDB' % self.ui : 
						self.createCharRenderLayerCmd(rigGrp[0], camera, eachFrame)
						self.listBatFile()

					if value == '%s_propRDB' % self.ui : 
						self.createPropRenderLayerCmd(rigGrp[0], camera, eachFrame)
						self.listBatFile()
					

				else : 
					if not rigGrp : 
						print 'Select object'

					if not camera : 
						print 'No render camera'

					if not eachFrame : 
						print 'Please set frame'


			print 'Export finished!!'



	def createCharRenderLayerCmd(self, rigGrp, camera, frame) : 

		layers = []

		namespace = mayaTools.getNamespace(rigGrp)
		rigGrp = '%s:Rig_Grp' % (namespace)
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

		mc.setAttr('defaultRenderLayer.renderable', 1)
		self.exportChar(namespace, rigGrp, layers, camera, frame)

		mc.delete(layers)


	def createPropRenderLayerCmd(self, rigGrp, camera, frame) : 
		layers = []
		extraLayers = []

		if mc.checkBox('%s_namespaceCB' % self.ui, q = True, v = True) : 
			namespace = rigGrp

		else :
			namespace = mayaTools.getNamespace(rigGrp)

		# rigGrp = '%s:Rig_Grp' % (namespace)
		key = 'prop'

		

		extraLayers = mc.textScrollList('%s_renderLayerTSL' % self.ui, q = True, si = True)
		baseLayer = layers

		# add extra layer
		if mc.checkBox('%s_extraCB' % self.ui, q = True, v = True) : 
			if extraLayers : 
				layers = layers + extraLayers

			# else : 
			# 	mm.eval('error "Select atlease 1 render layers";')

		# if not, use default layer
		else : 
			result = mc.createRenderLayer(rigGrp, name = key, number = 1, noRecurse = True)
			print 'Create render layer %s -> %s' % (key, rigGrp)
			layers.append(result)

		mc.setAttr('defaultRenderLayer.renderable', 0)
		self.exportChar(namespace, rigGrp, layers, camera, frame)
		mc.setAttr('defaultRenderLayer.renderable', 1)

		if not mc.checkBox('%s_extraCB' % self.ui, q = True, v = True) : 
			mc.delete(baseLayer)

		if mc.checkBox('%s_deleteCB' % self.ui, q = True, v = True) : 
			mc.delete(extraLayers)

		self.listRenderLayer()


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
		if layers : 
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
		mc.setAttr('defaultResolution.deviceAspectRatio', 1)
		mc.setAttr('defaultResolution.pixelAspect', 1)
		mc.setAttr('defaultRenderGlobals.outFormatControl', 0)
		mc.setAttr('defaultRenderGlobals.animation', 1)
		mc.setAttr('defaultRenderGlobals.putFrameBeforeExt', 1)
		mc.setAttr('defaultRenderGlobals.extensionPadding', 4)
		mc.setAttr('defaultRenderGlobals.currentRenderer', 'mentalRay', type = 'string')



	def restoreRender(self, ) : 
		w = 1920	
		h = 1080
		mc.setAttr('defaultResolution.width', w)
		mc.setAttr('defaultResolution.height', h)
		mc.setAttr('defaultRenderGlobals.currentRenderer', 'mayaSoftware', type = 'string')
		mc.setAttr('defaultResolution.pixelAspect', 1)
		mc.setAttr('defaultResolution.deviceAspectRatio', 1.777)



	def makeCamera(self, arg = None) : 
		self.renderCameraName = mc.textField('%s_newCameraTX' % self.ui, q = True, tx = True)
		self.setRenderSetting()
		self.currentCamera = mc.lookThru(q = True)

		if self.currentCamera : 

			if not mc.objExists(self.renderCameraName) : 
				self.renderCamera = mc.duplicate(self.currentCamera, n = self.renderCameraName)

			else : 
				self.renderCamera = [self.renderCameraName]

			cameraShape = mc.listRelatives(self.renderCamera[0], s = True)[0]

			mc.setAttr('%s.panZoomEnabled' % cameraShape, 1)
			mc.setAttr('%s.renderPanZoom' % cameraShape, 1)
			mc.setAttr('%s.displayResolution' % cameraShape, 1)

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

		print cam3D, cam2D

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

		# multi frame
		multi = mc.checkBox('%s_multiCB' % self.ui, q = True, v = True)

		if mode == 'getCurrentCamera' : 
			camera = mc.lookThru(q = True)
			mc.textField('%s_crrCameraTX' % self.ui, e = True, tx = camera)

		if mode == 'get2DCamera' : 
			camera = mc.lookThru(q = True)
			mc.textField('%s_cameraTX' % self.ui, e = True, tx = camera)

		if mode == 'getCurrentTime' : 
			if multi : 
				currentTime = str(int(mc.currentTime(q = True)))
				currentTimes = self.checkMultiFrame()

				if not currentTime in currentTimes : 
					text = (',').join(currentTimes)
					text = (',').join([text, str(currentTime)])
					mc.textField('%s_frameTX' % self.ui, e = True, tx = text)

			else : 
				currentTime = int(mc.currentTime(q = True))
				mc.textField('%s_frameTX' % self.ui, e = True, tx = currentTime)

		if mode == 'getCurrentCameraOM' : 
			camera = mc.optionMenu('%s_crrCameraOM' % self.ui, q = True, v = True)
			mc.textField('%s_crrCameraTX' % self.ui, e = True, tx = camera)

		if mode == 'get2DCameraOM' : 
			camera = mc.optionMenu('%s_cameraOM' % self.ui, q = True, v = True)
			mc.textField('%s_cameraTX' % self.ui, e = True, tx = camera)


		if mode == 'getNewCamera' : 
			sel = mc.ls(sl = True)

			if sel : 
				namespace = mayaTools.getNamespace(sel[0])
				text = '%s_cam' % namespace
				mc.textField('%s_newCameraTX' % self.ui, e = True, tx = text)


		if mode == 'onAddLayers' : 
			mc.textScrollList('%s_renderLayerTSL' % self.ui, e = True, en = True)

		if mode == 'offAddLayers' : 
			mc.textScrollList('%s_renderLayerTSL' % self.ui, e = True, en = False)



	def setMenuItemCamera(self) : 
		cameras = mc.listCameras()
		exclude = ['front', 'side', 'top']

		for each in cameras : 
			if not each in exclude : 
				mc.menuItem(l = each)



	def checkMultiFrame(self, arg = None) : 
		frame = mc.textField('%s_frameTX' % self.ui, q = True, tx = True)
		separator = ','
		frames = []

		if separator in frame : 
			frames = frame.split(separator)

			for each in frames : 
				frame = each.replace(' ', '')

				if frame.isdigit() : 
					if not frame in frames : 
						frames.append(frame)


		else : 
			frames.append(frame)

		return frames


	def listRenderLayer(self, arg = None) : 
		layers = mc.ls(type = 'renderLayer')
		exclusion = 'defaultRenderLayer'

		mc.textScrollList('%s_renderLayerTSL' % self.ui, e = True, ra = True)

		for each in layers : 
			if not exclusion in each : 
				mc.textScrollList('%s_renderLayerTSL' % self.ui, e = True, append = each)


	def setKey(self, arg = None) : 
		camera = mc.textField('%s_cameraTX' % self.ui, q = True, tx = True)
		cameraShape = mc.listRelatives(camera, s = True)[0]

		mc.setKeyframe('%s.pn' % cameraShape)
		mc.setKeyframe('%s.zom' % cameraShape)



	def createLight(self, arg = None) : 
		mm.eval('defaultDirectionalLight(1, 1,1,1, "0", 0,0,0, 0);')
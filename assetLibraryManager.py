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

class renderCamera() : 
	def __init__(self) : 


		self.ui = 'assetLibraryWin'
		self.renderPath = str()


	def mayaUI(self) : 
		
		if mc.window(self.ui, exists = True) : 
			mc.deleteUI(self.ui)
			
		mc.window(self.ui, t = '2D Tool v.1.2')
		mc.columnLayout(adj = 1,rs = 4)

		mc.frameLayout(borderStyle = 'etchedIn', lv = False)
		mc.rowColumnLayout(nc = 3, cw = ([1, 50], [2, 300], [3, 68]), cs = [4, 3])

		mc.text(l = 'Project')
		mc.textField('%s_projectTX' % self.ui)
		mc.button(l = 'Get Path', bgc = [0.2, 0.4, 0.8], c = partial(self.setPath))

		mc.setParent('..')
		mc.setParent('..')

		mc.frameLayout(borderStyle = 'etchedIn', lv = False)
		mc.rowColumnLayout(nc = 2, cw = ([1, 210], [2, 210]), cs = [4, 3])

		mc.button(l = 'Gen Dome', bgc = [0.6, 1, 0.6], c = partial(self.genDome))
		mc.button(l = 'Get Character Template', bgc = [0.4, 0.6, 0.9], c = partial(self.getTemplate))

		mc.text(l = 'Camera')
		mc.text(l = 'Renderable Camera')

		mc.textScrollList('%s1_TSL' % self.ui, numberOfRows = 16, allowMultiSelection = True, sc = partial(self.lookThruCam, 1))
		mc.textScrollList('%s2_TSL' % self.ui, numberOfRows = 16, allowMultiSelection = True, sc = partial(self.lookThruCam, 2))

		mc.setParent('..')
		mc.setParent('..')

		mc.frameLayout(borderStyle = 'etchedIn', lv = False)
		mc.rowColumnLayout(nc = 2, cw = ([1, 210], [2, 210]), cs = [4, 3])

		mc.button(l = 'Make Render --->', bgc = [0.2, 0.8, 0.2], c = partial(self.makeRenderCamera, True))
		mc.button(l = '<--- Make Non Render', bgc = [0.8, 0.2, 0.2], c = partial(self.makeRenderCamera, False))

		mc.setParent('..')
		mc.setParent('..')

		mc.frameLayout(borderStyle = 'etchedIn', lv = False)
		mc.rowColumnLayout(nc = 3, cw = ([1, 200], [2, 60], [3, 160]), cs = [4, 3])

		mc.checkBox('%s_selectCB' % self.ui, l = 'Look Thru cam')
		mc.text(l = 'Set Pose')
		mc.textField('%s_poseTX' % self.ui, tx = 'default')

		mc.setParent('..')
		mc.setParent('..')

		mc.frameLayout(borderStyle = 'etchedIn', lv = False)
		mc.rowColumnLayout(nc = 2, cw = ([1, 210], [2, 210]), cs = [2, 4], rs = [2, 4])

		mc.checkBox('%s_useFrameCB' % self.ui, l = 'Render multiple frame (Character)', v = True)

		mc.rowColumnLayout(nc = 3, cw = ([1, 50], [2, 50], [3, 50]))
		mc.radioCollection('%s_RDB' % self.ui)
		mc.text(l = 'Size')
		mc.radioButton( '%s_1RDB' % self.ui, label='2K', sl = True)
		mc.radioButton( '%s_2RDB' % self.ui, label='4K')
		mc.setParent('..')

		mc.button(l = 'Assign Blackhold', bgc = [0.2, 0.2, 0.2], c = partial(self.assignBlackhole))
		mc.button(l = 'Save Scene', h = 30, c = partial(self.saveScene))

		mc.setParent('..')
		mc.setParent('..')

		mc.button(l = 'Export Batch', h = 30, c = partial(self.exportBatch))
		mc.textScrollList('%s3_TSL' % self.ui, numberOfRows = 6, allowMultiSelection = True)

		mc.frameLayout(borderStyle = 'etchedIn', lv = False)
		mc.rowColumnLayout(nc = 2, cw = ([1, 210], [2, 210]), cs = [2, 4])

		mc.button(l = 'Open bat file', bgc = [1, 1, 1], c = partial(self.openInExplorer, 'bat file'))
		mc.button(l = 'Open output', bgc = [1, 1, 1], c = partial(self.openInExplorer, 'output'))

		mc.setParent('..')
		mc.setParent('..')

		mc.button(l = 'Run Batch', h = 30, c = partial(self.runBatch), bgc = [0.3, 0.5, 0.8])

		mc.showWindow()
		mc.window(self.ui, e = True, wh = [430, 730])

		self.listAllCamera()


	def listAllCamera(self) : 
		cameras = mc.listCameras()

		mc.textScrollList('%s1_TSL' % self.ui, e = True, ra = True)
		mc.textScrollList('%s2_TSL' % self.ui, e = True, ra = True)

		for each in cameras : 
			shape = mc.listRelatives(each, s = True)[0]
			renderable = mc.getAttr('%s.%s' % (shape, 'renderable'))

			if not renderable : 
				mc.textScrollList('%s1_TSL' % self.ui, e = True, append = each)

			else : 
				mc.textScrollList('%s2_TSL' % self.ui, e = True, append = each)


	def makeRenderCamera(self, cameraState, arg = None) : 

		if cameraState : 
			sels = mc.textScrollList('%s1_TSL' % self.ui, q = True, si = True)

		else : 
			sels = mc.textScrollList('%s2_TSL' % self.ui, q = True, si = True)

		if sels : 
			for each in sels : 
				shape = mc.listRelatives(each, s = True)[0]
				mc.setAttr('%s.renderable' % shape, cameraState)

		self.listAllCamera()


	def setRenderSetting(self, namespace, arg = None) : 
		value = mc.radioCollection('%s_RDB' % self.ui, q = True, sl = True)

		if value == '%s_1RDB' % self.ui : 
			w = 2048
			h = 2048

		if value == '%s_2RDB' % self.ui : 
			w = 4096
			h = 4096

		mc.setAttr('defaultRenderGlobals.imageFilePrefix', '<Camera>/<RenderLayer>', type = "string")
		imageFormat = 32
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


	def setPath(self, arg = None) : 
		sel = mc.ls(sl = True)

		if sel : 
			referencePath = mayaTools.getReferencePath(sel[0])

			if '/ref/' in referencePath : 
				rootPath = referencePath.split('/ref/')[0]
				exportPath = '%s/%s/%s/%s' % (rootPath, 'shade', 'maya', 'work')

				mc.textField('%s_projectTX' % self.ui, e = True, tx = exportPath)

				if not os.path.exists(exportPath) : 
					os.makedirs(exportPath)

				pose = mc.textField('%s_poseTX' % self.ui, q = True, tx = True)

				self.renderPath = '%s/%s/%s/%s' % (rootPath, 'images', 'library', pose)


			self.listBatFile()


	def exportBatch(self, arg = None) : 

		frame = mc.currentTime(q = True)
		output = self.renderPath

		useSceneFrame = mc.checkBox('%s_useFrameCB' % self.ui, q = True, v = True)

		namespace = mc.textField('%s_poseTX' % self.ui, q = True, tx = True)

		if not os.path.exists(output) : 
			os.makedirs(output)

		renderFile = mc.file(q = True, sn = True)

		print frame, output, renderFile
		if frame and output and renderFile : 

			self.setRenderSetting(namespace)
			mc.file(save = True)
			self.genBatchFile(frame, output, renderFile, useSceneFrame)

		if not output : 
			print 'No Output found'

		if not renderFile : 
			print 'Save scene first'


		self.listBatFile()



	def genBatchFile(self, frame, output, renderFile, useSceneFrame = False) : 
		batFile = renderFile.replace('.ma', '.bat')
		output = output.replace('/', '\\')
		renderFile = renderFile.replace('/', '\\')

		if useSceneFrame : 
			cmd = '"C:\\Program Files\\Autodesk\\Maya2012\\bin\\Render.exe" -r file -rd "%s" "%s"' % (output, renderFile)

		else : 
			cmd = '"C:\\Program Files\\Autodesk\\Maya2012\\bin\\Render.exe" -r file -s %s -e %s -rd "%s" "%s"' % (frame, frame, output, renderFile)

		fileUtils.writeFile(batFile, cmd)



	def listBatFile(self) : 
		exportPath = mc.textField('%s_projectTX' % self.ui, q = True, tx = True)

		files = fileUtils.listFile(exportPath, 'bat')

		mc.textScrollList('%s3_TSL' % self.ui, e = True, ra = True)

		for each in files : 
			mc.textScrollList('%s3_TSL' % self.ui, e = True, append = each)


	def saveScene(self, arg = None) : 
		exportPath = mc.textField('%s_projectTX' % self.ui, q = True, tx = True)
		fileName = 'sceneSetup_v001.ma'

		mc.file(rename = '%s/%s' % (exportPath, fileName))
		mc.file(save = True)



	def runBatch(self, arg = None) : 
		sels = mc.textScrollList('%s3_TSL' % self.ui, q = True, si = True)
		path = mc.textField('%s_projectTX' % self.ui, q = True, tx = True)

		for eachFile in sels : 
			filePath = '%s/%s' % (path, eachFile)

			if os.path.exists(filePath) : 
				# cmd = fileUtils.readFile(filePath)
				cmd = filePath
				cmdRep = subprocess.Popen(cmd,stdout=subprocess.PIPE).communicate()[0]
				print cmd

			else : 
				print 'Path not exists %s' % filePath

		print 'OK'



	def openInExplorer(self, mode, arg = None) : 
		sels = mc.textScrollList('%s3_TSL' % self.ui, q = True, si = True)
		path = mc.textField('%s_projectTX' % self.ui, q = True, tx = True)

		if mode == 'output' : 

			checkPath = self.renderPath.replace('/', '\\')
			subprocess.Popen(r'explorer /select,"%s"' % checkPath)


		if mode == 'bat file' : 
			if sels : 
				path = '%s/%s' % (path, sels[0])
				checkPath = path.replace('/', '\\')
				subprocess.Popen(r'explorer /select,"%s"' % checkPath)



	def genDome(self, arg = None) : 
		camGen.run()
		self.listAllCamera()


	def getTemplate(self, arg = None) : 
		path = 'P:/Lego_City2D/asset/3D/_global/dome/template.ma'
		mc.file(path, i = True, type = 'mayaAscii', rpr = 'template', pr = True, loadReferenceDepth = 'all')
		self.listAllCamera()



	def lookThruCam(self, panel, arg = None) : 
		if mc.checkBox('%s_selectCB' % self.ui, q = True, v = True) : 

			if panel == 1 : 
				item = mc.textScrollList('%s1_TSL' % self.ui, q = True, si = True)

			if panel == 2 : 
				item = mc.textScrollList('%s2_TSL' % self.ui, q = True, si = True)

			if item : 
				mc.lookThru(item[0])

			mc.camera(item, e = True, displayFilmGate = False, displayResolution = True, overscan = 1.3)


	def assignBlackhole(self, arg = None) : 
		sel = mc.ls(sl = True)
		name = 'blackhole_shd'
		shd = name

		if not mc.objExists(name) : 
			shd = mc.shadingNode('lambert', asShader = True, n = name)

		mc.setAttr('%s.matteOpacityMode' % shd, 0)

		mc.select(sel)
		mc.hyperShade(assign = shd)


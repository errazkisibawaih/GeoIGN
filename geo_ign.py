"""
/***************************************************************************
 GeoIGN
                                 A QGIS plugin
 Geoservice de l'IGN
                              -------------------
        begin                : 2016-05-12
        git sha              : $Format:%H$
        copyright            : (C) 2016 by ENSG
        email                : errazkisibawaih@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt4.QtGui import QAction, QIcon
# Initialize Qt resources from file resources.py
import resources
#Project
import sys
from PyQt4.QtCore import *
from PyQt4.QtNetwork import QHttp, QNetworkProxy
from owslib.wms import WebMapService
from owslib.wmts import WebMapTileService
from PyQt4.QtGui import QInputDialog
import unicodedata
from PyQt4 import QtCore, QtGui
from qgis.core import QgsRasterLayer,QgsMapLayerRegistry,QgsVectorLayer,QgsCoordinateReferenceSystem
from PyQt4.QtGui import QMessageBox
from qgis.utils import iface
# Import the code for the DockWidget
from geo_ign_dockwidget import GeoIGNDockWidget
import os.path
import qgis.core
from PyQt4.QtCore import *
from qgis.core import QgsVectorLayer, QgsField, QgsMapLayerRegistry, QgsFeature, QgsGeometry, QgsPoint, QgsCoordinateReferenceSystem, QgsCoordinateTransform  
import os


class GeoIGN:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GeoIGN_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Geo IGN')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'GeoIGN')
        self.toolbar.setObjectName(u'GeoIGN')

        #print "** INITIALIZING GeoIGN"

        self.pluginIsActive = False
        self.dockwidget = None


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('GeoIGN', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = 'C:/Users/anto/.qgis2/python/plugins/GeoIGN/GeoIGN_icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'GeoIGN'),
            callback=self.run,
            parent=self.iface.mainWindow())
		
		

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING GeoIGN"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD GeoIGN"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Geo IGN'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING GeoIGN"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = GeoIGNDockWidget()
			
			
			
            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            self.dockwidget.show()
        
        
        
        self.dockwidget.zone_mdp_2.insert("Vide en Cas de Default Proxy")
        self.dockwidget.zone_mdp_3.insert("Vide en Cas de Default Proxy")
        self.dockwidget.zone_login.insert("Optionnel")
        self.dockwidget.zone_mdp.insert("Optionnel")
        self.dockwidget.pushButton_3.clicked.connect(self.informations)
        self.dockwidget.pushButton_6.clicked.connect(self.urlfgd)
        self.dockwidget.pushButton_7.clicked.connect(self.geocodedirect)
        self.dockwidget.pushButton_10.clicked.connect(self.urlgd)
        self.dockwidget.pushButton_14.clicked.connect(self.urlgi)
        self.dockwidget.pushButton_15.clicked.connect(self.urlgid)
        self.dockwidget.pushButton_11.clicked.connect(self.geocodeinverse)
        self.dockwidget.pushButton_13.clicked.connect(self.help)
        self.dockwidget.pushButton_12.clicked.connect(self.about)

    """ fonction pour savoir le format du geocodage direct et indirect par fichier """  
    def help(self):
    	QMessageBox.information(None, "Help:", "Un respect de la syntaxe assure le fonctionnement du plugin \n Pour le fichier adresse, il faut avoir chaque adresse sur une ligne et à la fin veiller à ne pas avoir de vide \n Pour le fichier de coordonnees, il faut avoir \n latitude;longitude\nlatitude;longitude") 
    
    """ Information sur le plugin"""
    def about(self):
    	message='This plugin has been developed through a development project of an engineering school called ENSG.\nHe use the geodata services of IGN to make geocoding.\nHe has been developed in python language.\n \n \n Author: ER-RAZKI Sibawaih, DARENGOSSE Leo et VIGNERON Antony (ENSG student) \n In Collaboration with : THAUVIN Xavier (IGN)'
        QMessageBox.information(None, "About:", message) 
    """ Fichier à entrer en parametre pour le geocodage indirect """
    def urlgi(self):
        filename = QtGui.QFileDialog.getOpenFileName(self.dockwidget, 'Open File', '', 'Txt (*.txt)')
    	self.dockwidget.lineEdit_6.setText(filename)
    """ Fichier de sortie du geocodage indirect """	
    def urlgid(self):
    	filename = QtGui.QFileDialog.getExistingDirectory(self.dockwidget, 'Open folder','' )
    	self.dockwidget.lineEdit_7.setText(filename)
    
    def geocodeinverse(self):
    	b=self.dockwidget.checkBox.isChecked() 
    	long=self.dockwidget.lineEdit_3.text()
    	lat=self.dockwidget.lineEdit_2.text()
    	urlfichier=self.dockwidget.lineEdit_6.text()
    	urlsortie=self.dockwidget.lineEdit_7.text()
    	if long and lat :
			long=float(long)
			lat=float(lat)
			self.cles=self.dockwidget.zone_cle.text()
			self.usern=self.dockwidget.zone_login.text()
			self.passw=self.dockwidget.zone_mdp.text()
			res=protocoleinit(self.cles,self.usern,self.passw).geocode_inverse(lat,long)
			point = res[0]  
			latitude = str(res[1])
			longitude = str(res[2])
			numero = str(res[3])
			rue = str(res[4])
			code_postal = str(res[5])
			commune = str(res[6])
			distance=str(res[7])
			#if checkBox_2 is checked do :
			if( b== True) :
				couche_adresse = crea_couche(numero+rue+code_postal+commune,'Point')
				couche_adresse.create_point(point,numero,rue,code_postal,commune,latitude,longitude)
				couche_adresse.aff_couche
        elif urlfichier and urlsortie :
            protocoleinit(self.cles,self.usern,self.passw).geocode_inverse_fichier(urlfichier,urlsortie,b)
        self.dockwidget.lineEdit_2.clear()
        self.dockwidget.lineEdit_3.clear()
        self.dockwidget.lineEdit_6.clear()
        self.dockwidget.lineEdit_7.clear()
		
    def geocodedirect(self):
    	address=self.dockwidget.lineEdit.text()
    	urlfichier=self.dockwidget.lineEdit_4.text()
    	urlsortie=self.dockwidget.lineEdit_5.text()
    	b=self.dockwidget.checkBox_2.isChecked() 
    	if( address ) :
			self.cles=self.dockwidget.zone_cle.text()
			self.usern=self.dockwidget.zone_login.text()
			self.passw=self.dockwidget.zone_mdp.text()
			res=protocoleinit(self.cles,self.usern,self.passw).geocode_address(address)
			point = res[0]  
			latitude = str(res[1])
			longitude = str(res[2])
			numero = str(res[3])
			rue = str(res[4])
			code_postal = str(res[5])
			commune = str(res[6])
			#if checkBox_2 is checked do :
			if( b==True):
				couche_adresse = crea_couche(address,'Point')
				couche_adresse.create_point(point,numero,rue,code_postal,commune,latitude,longitude)
				couche_adresse.aff_couche
        elif urlfichier:
            protocoleinit(self.cles,self.usern,self.passw).geocode_fichier(urlfichier,urlsortie,b)
            print urlsortie
        self.dockwidget.lineEdit.clear()
        self.dockwidget.lineEdit_5.clear()
        self.dockwidget.lineEdit_4.clear()
        
    		
    """ Fichier à entrer en parametre pour le geocodage indirect """  
    def urlfgd(self):
    	filename = QtGui.QFileDialog.getOpenFileName(self.dockwidget, 'Open File', '', 'Txt (*.txt)')
    	self.dockwidget.lineEdit_4.setText(filename)
    	
    """ Fichier en sortie pour le geocodage indirect """
    def urlgd(self):
    	filename = QtGui.QFileDialog.getExistingDirectory(self.dockwidget, 'Open folder','' )
    	self.dockwidget.lineEdit_5.setText(filename)
     
        
    def informations(self):
    	n=self.dockwidget.comboBox_2.clear()
    	"""for i in range(0,n+1):
    		self.dockwidget.comboBox_2.removeItem(i)"""
    	self.cles=self.dockwidget.zone_cle.text()
        self.usern=self.dockwidget.zone_login.text()
        self.passw=self.dockwidget.zone_mdp.text()
        self.typeproxy=self.dockwidget.comboBox.currentText()
        self.hote=self.dockwidget.zone_mdp_2.text()
        self.port=self.dockwidget.zone_mdp_3.text()
        """ Exception au cas ou les champs sont vide 
        on demande a l'utilisateur de remplir les champs """
        if self.cles=="" or self.usern=="" or self.passw=="" or self.typeproxy=="" or self.hote=="" or self.port=="" :
        	QMessageBox.information(None, "Avertissement","Veuillez remplir tous les champs") 
        	return 0
        	
        pinit=protocoleinit(self.cles,self.usern,self.passw)
        pinit.prox(self.typeproxy,self.usern,self.passw,self.hote,self.port)
        """ on recupere un string ou il y'a tout les protocoles disponible"""
        res=pinit.getcapabilities()
        a=res.find("OpenLS (geocodage)")
        """ dans le cas ou on trouve que la cle n'est pas eligible a OpenLS 
        on met un texte dans les champs openls pour ne pas les utiliser """
        if( a!=-1 ) :
        	self.dockwidget.lineEdit_4.insert("Service OpenLS non disponible")
        	self.dockwidget.lineEdit_5.insert("Service OpenLS non disponible")
        	self.dockwidget.lineEdit.insert("Service OpenLS non disponible")
        	self.dockwidget.lineEdit_2.insert("Service OpenLS non disponible")
        	self.dockwidget.lineEdit_3.insert("Service OpenLS non disponible")
        	self.dockwidget.lineEdit_6.insert("Service OpenLS non disponible")
        	self.dockwidget.lineEdit_7.insert("Service OpenLS non disponible")
        else :
        	self.dockwidget.lineEdit_4.clear()
        	self.dockwidget.lineEdit_5.clear()
        	self.dockwidget.lineEdit.clear()
        	self.dockwidget.lineEdit_2.clear()
        	self.dockwidget.lineEdit_3.clear()
        	self.dockwidget.lineEdit_6.clear()
        	self.dockwidget.lineEdit_7.clear()
		""" on ajoute les couches WMS au menu deroulant """
        try:
            lwms=pinit.getnamelayerswmsr()
            i=0
            while ( i<len(lwms) ) :
            	self.dockwidget.comboBox_2.addItem(lwms[i])
            	i=i+1
        except:
            pass
        """ on ajoute les couches inspire au menu deroulant """
        try:
            linspire=pinit.getnamelayersinspirer()
            i=0
            while ( i<len(linspire) ) :
            	self.dockwidget.comboBox_2.addItem(linspire[i])
            	i=i+1
        except:
            pass
        """ on ajoute les couches WMTS mercator au menu deroulant """
        try:
            lwmtsm=pinit.getnamelayerswmtsm()
            i=0
            while ( i<len(lwmtsm) ) :
            	self.dockwidget.comboBox_2.addItem(lwmtsm[i])
            	i=i+1
            
        except:
            pass
        """ on ajoute les couches WMTS Lambert au menu deroulant """
        try:
            lwmtsl=pinit.getnamelayerswmtsl()
            i=0
            while ( i<len(lwmtsl) ) :
        	   self.dockwidget.comboBox_2.addItem(lwmtsl[i])
        	   i=i+1
        except:
            pass
        """ On connecte le bouton ajouter à la fonction qui ajoute les couches"""
        self.dockwidget.pushButton_2.clicked.connect(self.ajoutcouche)
        	
    def ajoutcouche(self):
    	couche=self.dockwidget.comboBox_2.currentText()
    	pinit=protocoleinit(self.cles,self.usern,self.passw)
        pinit.prox(self.typeproxy,self.usern,self.passw,self.hote,self.port)
        
        try :
			lwms=pinit.getnamelayerswmsr()
			i=0
			while ( i<len(lwms) ) :
				if(lwms[i]==couche):
					pinit.showlayerwmsr(couche)
					return 0
				i=i+1
        except :
			pass
		
        try:
			linspire=pinit.getnamelayersinspirer()
			i=0
			while ( i<len(linspire) ) :
				if(linspire[i]==couche) :
					pinit.showlayerinspirer(couche)
					return 0	
				i=i+1
        except :
			pass

        try :
			lwmtsm=pinit.getnamelayerswmtsm()
			i=0
			while ( i<len(lwmtsm) ) :
				if (lwmtsm[i]==couche) :
					pinit.showlayerwmtsm(couche)
					return 0
				i=i+1
        except :
			pass
        
        try :
			lwmtsl=pinit.getnamelayerswmtsl()
			i=0
			while ( i<len(lwmtsl) ) :
				if( lwmtsl[i]==couche) :
					pinit.showlayerwmtsl(couche)
					return 0
				i=i+1
        except : 
			pass
    	     
        
""" Dans cette classe on va avoir tout les types de protocoles 
le code est entierement idependant de la version de Qgis car on construit 
nous meme les requetes pour recuperer les couches.
Pour chaque service on le definie avec un url"""        
class protocoleinit :
	
	def __init__(self,cles,usern,passw):
		self.cles = cles
		self.usern=usern
		self.passw=passw
	""" On va definir la fonction qui va definir le type 
	de proxy et elle va le modifier dans les proporietes de QGis """
	def prox(self,mode,user,password,host,port):
		proxy = QNetworkProxy()
		if mode == "DefaultProxy":
			proxy.setType(QNetworkProxy.DefaultProxy)
		elif mode == "Socks5Proxy":
			proxy.setType(QNetworkProxy.Socks5Proxy)
			proxy.setHostName(host)
			proxy.setPort(int(port))
			proxy.setUser(self.usern)
			proxy.setPassword(self.passw)
			QNetworkProxy.setApplicationProxy(proxy)
		elif mode == "HttpProxy":
			proxy.setType(QNetworkProxy.HttpProxy)
			proxy.setHostName(host)
			proxy.setPort(int(port))
			proxy.setUser(self.usern)
			proxy.setPassword(self.passw)
			QNetworkProxy.setApplicationProxy(proxy)
		elif mode == "HttpCachingProxy":
			proxy.setType(QNetworkProxy.HttpCachingProxy)
			proxy.setHostName(host)
			proxy.setPort(int(port))
			proxy.setUser(self.usern)
			proxy.setPassword(self.passw)
			QNetworkProxy.setApplicationProxy(proxy)
		elif mode == "FtpCachingProxy":
			proxy.setType(QNetworkProxy.FtpCachingProxy)
			proxy.setHostName(host)
			proxy.setPort(int(port))
			proxy.setUser(self.usern)
			proxy.setPassword(self.passw)
			QNetworkProxy.setApplicationProxy(proxy)
	""" Fonction qui permet de recuperer le nom des couches WMS raster
	la version peut changer alors il faut s'assurer lors des prochaines 
	versions de s'assurer de la diponibilite de l'actuel version"""	
	def getnamelayerswmsr(self):
		urls='https://wxs.ign.fr/'
		urle='/geoportail/r/wms'
		url=urls+self.cles+urle
		wms=WebMapService(url, version='1.1.1',username=self.usern,password=self.passw)
		layers=wms.contents.keys()
		return layers  

	"""fonction qui permet d'afficher sur Qgis une couche WMS  raster
	lors de l'ajout on modifie la projection vers la projection de la couche 
	actuel .
	on construit nous meme la requete ce qui rend le plugin idependant de la version de Qgis"""
	def showlayerwmsr(self,layer):
		urls='https://wxs.ign.fr/'
		urle='/geoportail/r/wms'
		url=urls+self.cles+urle
		wms=WebMapService(url,username=self.usern,password=self.passw)
		scr=wms[layer].boundingBox[4]
		QMessageBox.information(None, "Avertissement:", "Votre projet passera en projection "+scr) 
	
		url1='contextualWMSLegend=0&crs=EPSG:2154&dpiMode=7&featureCount=10&format=image/jpeg&layers='
		url2='&password='
		url3='&styles=&url=https://wxs.ign.fr/6mpwghesbxdoe9ybobqzmd59/geoportail/r/wms&username='
		url=url1+layer+url2+self.passw+url3+self.usern
		rlayer = QgsRasterLayer(url,layer, 'wms')
		QgsMapLayerRegistry.instance().addMapLayer(rlayer)
		
		my_crs = QgsCoordinateReferenceSystem(int(scr.split(':')[1]),QgsCoordinateReferenceSystem.EpsgCrsId)
		iface.mapCanvas().mapRenderer().setDestinationCrs(my_crs)
		
		return 0
		
	"""
	On a supprimer les couches vecteurs cqr ils sont vide 
	def getnamelayersv(self):
		urls='https://wxs.ign.fr/'
		urle='/geoportail/v/wms'
		url=urls+self.cles+urle
		wms=WebMapService(url, version='1.1.1',username=self.usern,password=self.passw)
		layers=wms.contents.keys()


		return layers
	"""
	""" On recupere tout les noms des couches insipre """
	def getnamelayersinspirer(self):
		urls='https://wxs.ign.fr/'
		urle='/inspire/r/wms'
		url=urls+self.cles+urle
		usern='qgis_ensg'
		passw='qgis_prov'
		wms=WebMapService(url,username=self.usern,password=self.passw)
		layers=wms.contents.keys()
		return layers
        
	"""
	def getnamelayersv(self):
		#, version='1.3.0'
		urls='https://wxs.ign.fr/'
		urle='/inspire/v/wms'
		url=urls+self.cles+urle
		usern='qgis_ensg'
		passw='qgis_prov'
		wms=WebMapService(url,username=self.usern,password=self.passw)
		layers=wms.contents.keys()

		return layers
	"""		
	""" On affiche tout les noms des couches inspire
	et comme pour le precedentes fonctions on force la projection vers la projection 
	de la nouvelle couche"""
	def showlayerinspirer(self,layer):
		urls='https://wxs.ign.fr/'
		urle='/inspire/r/wms'
		url=urls+self.cles+urle
		wms=WebMapService(url,username=self.usern,password=self.passw)
		scr=wms[layer].boundingBox[4]
		QMessageBox.information(None, "Avertissement:", "Votre projet passera en projection "+scr) 
		
		url1='contextualWMSLegend=0&crs='
		url2='&dpiMode=7&featureCount=10&format=image/jpeg&layers='
		url3='&password='
		url4='&styles=&url=https://wxs.ign.fr/6mpwghesbxdoe9ybobqzmd59/inspire/r/wms&username='
		url=url1+scr+url2+layer+url3+self.passw+url4+self.usern
		rlayer = QgsRasterLayer(url,layer, 'wms')
		QgsMapLayerRegistry.instance().addMapLayer(rlayer)
		## possible values are: prompt, useProject, useGlobal
		
		my_crs = QgsCoordinateReferenceSystem(int(scr.split(':')[1]),QgsCoordinateReferenceSystem.EpsgCrsId)
		iface.mapCanvas().mapRenderer().setDestinationCrs(my_crs)
		
		return 0
		
	""" Fonction permet de recuperer les noms des couches WMTS Mercator"""	
	#Mecator
	def getnamelayerswmtsm(self):
		urls='http://wxs.ign.fr/'
		urle='/geoportail/wmts'
		url=urls+self.cles+urle
		wmts=WebMapTileService(url, version='1.0.0',username=self.usern,password=self.passw)
		layers=wmts.contents.keys()
		return layers
        
	"""Fonction permet de recuperer les noms des couches WMTS Lambert"""	
	#Lambert 93
	def getnamelayerswmtsl(self):
		urls='http://wxs.ign.fr/'
		urle='/proxy-wmts'
		url=urls+self.cles+urle
		wmts=WebMapTileService(url, version='1.0.0',username=self.usern,password=self.passw)
		layers=wmts.contents.keys()
		return layers
	""" Fonction qui permet d'ajouter une couche WMTS Mercator
    la requete de couche est contruite manuellement pour la perinite et indepance du plugin 
    des fonctions , on force le passage à la projection de la nouvelle couche"""
	def showlayerwmtsm(self,layer):
		urls='http://wxs.ign.fr/'
		urle='/geoportail/wmts'
		url=urls+self.cles+urle
		wmts=WebMapTileService(url, version='1.0.0',username=self.usern,password=self.passw)
		format=wmts[layer].formats[0]
	
		url1='contextualWMSLegend=0&crs=EPSG:3857&dpiMode=7&featureCount=10&format='
		url2='&layers='
		url3='&password='
		url4='&styles=normal&tileMatrixSet=PM&url=http://wxs.ign.fr/6mpwghesbxdoe9ybobqzmd59//wmts?SERVICE%3DWMTS%26REQUEST%3DGetCapabilities&username='
		url=url1+format+url2+layer+url3+self.passw+url4+self.usern
		QMessageBox.information(None, "Avertissement:", "Votre projet passera en projection EPSG:3857") 
		rlayer = QgsRasterLayer(url,layer, 'wms')
		QgsMapLayerRegistry.instance().addMapLayer(rlayer)
		
		my_crs = QgsCoordinateReferenceSystem(3857,QgsCoordinateReferenceSystem.EpsgCrsId)
		iface.mapCanvas().mapRenderer().setDestinationCrs(my_crs)
		
		return 0
	""" On construit manuellement la requete d'ajout d'une couche WMTS Lambert
	 , on force le passage à la projection de la nouvelle couche """
	def showlayerwmtsl(self,layer):
		urls='http://wxs.ign.fr/'
		urle='/proxy-wmts'
		url=urls+self.cles+urle
		wmts=WebMapTileService(url, version='1.0.0',username=self.usern,password=self.passw)
		format=wmts[layer].formats[0]
		
		url1='contextualWMSLegend=0&crs=EPSG:2154&dpiMode=7&featureCount=10&format='
		url2='&layers='
		url3='&password='
		url4='&styles=normal&tileMatrixSet=LAMB93&url=https://wxs.ign.fr/6mpwghesbxdoe9ybobqzmd59/proxy-wmts?SERVICE%3DWMTS%26REQUEST%3DGetCapabilities&username='
		
		url=url1+format+url2+layer+url3+self.passw+url4+self.usern
		
		QMessageBox.information(None, "Avertissement:", "Votre projet passera en projection EPSG:2154") 
		
		rlayer = QgsRasterLayer(url,layer, 'wms')
		QgsMapLayerRegistry.instance().addMapLayer(rlayer)
		
		my_crs = QgsCoordinateReferenceSystem(2154,QgsCoordinateReferenceSystem.EpsgCrsId)
		iface.mapCanvas().mapRenderer().setDestinationCrs(my_crs)
		
		return 0      
	""" Fonction qui permet de savoir les protocoles disponibles pour une clé """
	def getcapabilities(self):
		urlswms='https://wxs.ign.fr/'
		urlewms='/inspire/r/wms'
		urlwms=urlswms+self.cles+urlewms
		usern='qgis_ensg'
		passw='qgis_prov'
		urlsinspire='https://wxs.ign.fr/'
		urleinspire='/inspire/r/wms'
		urlinspire=urlsinspire+self.cles+urleinspire
		urlswmtsm='http://wxs.ign.fr/'
		urlewmtsm='/geoportail/wmts'
		urlwmtsm=urlswmtsm+self.cles+urlewmtsm
		urlswmstsl='http://wxs.ign.fr/'
		urlewmtsl='/proxy-wmts'
		urlwmtsl=urlswmstsl+self.cles+urlewmtsl

		stra= ""
		stri=""
		res=protocoleinit(self.cles,self.usern,self.passw).geocode_address("6 Avenue Blaise Pascal Champs sur Marne")
		print res
		try : 
			wms=WebMapService(urlwms,username=self.usern,password=self.passw)
			stra=stra+ "WMS\n"
		except :
			stri=stri+ "WMS\n"
			pass
		try :
			inspire=WebMapService(urlinspire,username=self.usern,password=self.passw)
			stra=stra+ "Inspire\n"
		except :
			stri=stri+ "Inspire\n"
			pass
		try :
			wmtsm=WebMapTileService(urlwmtsm, version='1.0.0',username=self.usern,password=self.passw)
			stra=stra+ "WMTS Mercator\n"
		except :
			stri=stri+ "WMTS Mercator\n"
			pass
		try :
			wmtsl=WebMapTileService(urlwmtsl, version='1.0.0',username=self.usern,password=self.passw)
			stra=stra+"WMTS Lambert\n"
		except :
			stri=stri+ "WMTS Lambert\n"
			pass
		if res!=[]:
			stra= stra + u"OpenLS (geocodage)\n"
		else:
			stri= stri + u"OpenLS (geocodage)\n"
		if(stra== ""):
			QMessageBox.information(None,"Information","Verifiez votre cle et vos informations d'authentification")
		else:
			QMessageBox.information(None,"Information","Connexion reussie! \nVotre cle est elligible a :\n" + stra+ "\nVotre cle n'est pas elligible a :\n" + stri)
		
		return stri
	
	def geocode_address(self,address):
		self.address = address
		import xml
		import urllib,urllib2,httplib
		import base64
		from qgis.utils import iface
		from urllib2 import HTTPBasicAuthHandler, HTTPPasswordMgrWithDefaultRealm, HTTPPasswordMgr, build_opener, install_opener
		
		print 'geocodage en cours ...'
		
		url = "https://wxs.ign.fr/"+self.cles+"/geoportail/ols?"
		
		#requete de recherche par adresse
		xls_request = '<?xml version="1.0" encoding="UTF-8"?>\
        <XLS xmlns:gml="http://www.opengis.net/gml" xmlns="http://www.opengis.net/xls" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\
         version="1.2" xsi:schemaLocation="http://www.opengis.net/xls http://schemas.opengis.net/ols/1.2/olsAll.xsd">\
        <RequestHeader srsName="epsg:4326"/>\
            <Request maximumResponses="1" methodName="GeocodeRequest" requestID="uid42" version="1.2">\
                <GeocodeRequest returnFreeForm="false">\
                    <Address countryCode="StreetAddress">\
                        <freeFormAddress>'+self.address+'</freeFormAddress>\
                    </Address>\
                </GeocodeRequest>\
            </Request>\
        </XLS>'   

		r = urllib2.Request(url, data=xls_request, headers={'Content-Type': 'application/xml'})
		
		#r.add_header('Referer', 'http://localhost')
		#ajout de l'en-tete d'authentification (protocole http basic authentification)
		username = self.usern
		password = self.passw
		base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
		r.add_header("Authorization", "Basic %s" % base64string)
		resultats = []
		try :
			u = urllib2.urlopen(r)
			response = u.read()
			#print response #le fichier xml recu
			xml_response = xml.etree.ElementTree.fromstring(response) #partition du fichier xml
			#root = xml_response.getroot()
			#print "root : ", xml_response
			###On cree un objet qui permet de transformer les coordonnees geographiques fournies dans le systeme de reference de la carte
			proj_WGS84 = QgsCoordinateReferenceSystem(4326, QgsCoordinateReferenceSystem.EpsgCrsId) #car les coordonees geocodees sont en WGS 84
			proj_current = iface.mapCanvas().mapRenderer().destinationCrs() #on recupere l'EPSG du projet courant
			proj_transformer = QgsCoordinateTransform(proj_WGS84, proj_current) # creation de la transformation adequate
			#On recupere la reponse xml du serveur openLS
			geocoded_address = xml_response.findall("*/*/*/*")
			#print "geocoded_address : ", geocoded_address #toutes les adresses geocodees disponibles (Une seule ici puisque maximumResponses="1" dans la requete)
			coords = geocoded_address[0].findall("./{http://www.opengis.net/gml}Point/{http://www.opengis.net/gml}pos")[0].text #recuperation des coordonnees
			latitude = (float(coords.split(' ')[0])) #recuperation de la latitude
			longitude = (float(coords.split(' ')[1])) #recuperation de la longitude
			point = proj_transformer.transform (longitude, latitude) #transformation dans le projet courant
			rue = geocoded_address[0].findall("./{http://www.opengis.net/xls}Address/{http://www.opengis.net/xls}StreetAddress/{http://www.opengis.net/xls}Street")[0].text
			code_postal = geocoded_address[0].findall("./{http://www.opengis.net/xls}Address/{http://www.opengis.net/xls}PostalCode")[0].text
			commune = geocoded_address[0].findall("./{http://www.opengis.net/xls}Address/{http://www.opengis.net/xls}Place")[0].text
			building = (geocoded_address[0].findall("./{http://www.opengis.net/xls}Address/{http://www.opengis.net/xls}StreetAddress/{http://www.opengis.net/xls}Building"))
			for build in building:
				num = build.get('number')
			#On teste l'existence d'un numero dans l'adresse demandee
			try:
				numero = int(num)
			except:
				numero = ""
			resultats.append(point)
			resultats.append(latitude)
			resultats.append(longitude)
			resultats.append(numero)
			resultats.append(rue)
			resultats.append(code_postal)
			resultats.append(commune)
		except :
			print (u"Probleme de geocodage")
		return resultats
	
	def geocode_fichier(self, cheminFichier, cheminEnregistrement,ajout_canevas):
		fichier_adresses = open(cheminFichier, "r")
		ligne = fichier_adresses.readlines()
		fichier_resultats = open(cheminEnregistrement + "/resultats_geo.txt",'w')
		fichier_resultats.write('adresse;latitude;longitude\n')
		fichier_resultats = open(cheminEnregistrement + "/resultats_geo.txt",'a')
		couche_adresse = crea_couche("Adresses",'Point')
		for i in range(len(ligne)):
			res = protocoleinit(self.cles,self.usern, self.passw).geocode_address(ligne[i]) #on determine le geocodage de chacune des adresses demandees
			point = res[0]  
			latitude = str(res[1])
			longitude = str(res[2])
			numero = str(res[3])
			rue = str(res[4])
			code_postal = str(res[5])
			commune = str(res[6])
			couche_adresse.create_point(point,numero,rue,code_postal,commune,latitude,longitude) #ajout du point a la couche et des attibuts        
			#si il n'y a pas de numero ce n'est pas la peine d'ajouter le premier espace
			if numero != "":
				fichier_resultats.write(numero + " " + rue + " " + code_postal + " " + commune +";" + latitude + ";" + longitude + "\n")
			else:
				fichier_resultats.write(rue + " " + code_postal + " " + commune +";" + latitude + ";" + longitude + "\n")
		fichier_adresses.close()
		fichier_resultats.close()
		#si l'utilisateur souhaite ajouter les adresses geocodees a sa carte, on affiche la couche
		if ajout_canevas:
			couche_adresse.aff_couche
	
	
	def geocode_inverse(self,latitude, longitude):
		self.latitude = latitude
		self.longitude = longitude
		import xml
		import urllib,urllib2,httplib
		import base64
		from qgis.utils import iface
		print("Recherche des adresses...")
		url = "https://wxs.ign.fr/"+self.cles+"/geoportail/ols?"
		coordonnees = str(self.latitude) + " " + str(self.longitude)
		#print point
		xls_request = '<?xml version="1.0" encoding="UTF-8"?><XLS version="1.2"\
		 xmlns="http://www.opengis.net/xls" xmlns:gml="http://www.opengis.net/gml" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\
		 xsi:schemaLocation="http://www.opengis.net/xls http://schemas.opengis.net/ols/1.2/olsAll.xsd">\
		 <RequestHeader/>\
		 <Request methodName="ReverseGeocodeRequest" maximumResponses="1" requestID="abc" version="1.2">\
		 <ReverseGeocodeRequest><ReverseGeocodePreference>StreetAddress</ReverseGeocodePreference>\
		 <Position>\
		 <gml:Point>\
		 <gml:pos>'+ coordonnees +'</gml:pos>\
		 </gml:Point></Position>\
		 </ReverseGeocodeRequest>\
		 </Request>\
		 </XLS>'
		r = urllib2.Request(url, data=xls_request, headers={'Content-Type': 'application/xml'})
		#r.add_header('Referer', 'http://localhost')
		#ajout de l'en-tete d'authentification (protocole http basic authentification)
		username = self.usern
		password = self.passw
		base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
		r.add_header("Authorization", "Basic %s" % base64string)
		u = urllib2.urlopen(r)
		response = u.read()
		#print response #le fichier xml recu
		xml_response = xml.etree.ElementTree.fromstring(response)
		#partition du fichier xml
		#root = xml_response.getroot()
		#print "root : ", xml_response
		#print xml_response.attrib
		resultats = []
		try:
			find_address = xml_response.findall("*/*/")
			#print "find_address : ", find_address #toutes les adresses geocodees disponibles (Une seule ici puisque maximumResponses="1" dans la requete)
			coords = find_address[0].findall("./{http://www.opengis.net/gml}Point/{http://www.opengis.net/gml}pos")[0].text #recuperation des coordonnees
			#print(coords)
			latitude = (float(coords.split(' ')[0])) #recuperation de la latitude
			longitude = (float(coords.split(' ')[1])) #recuperation de la longitude
			###On cree un objet qui permet de transformer les coordonnees geographiques fournies dans le systeme de reference de la carte
			proj_WGS84 = QgsCoordinateReferenceSystem(4326, QgsCoordinateReferenceSystem.EpsgCrsId) #car les coordonees geocodees sont en WGS 84
			proj_current = iface.mapCanvas().mapRenderer().destinationCrs() #on recupere l'EPSG du projet courant
			proj_transformer = QgsCoordinateTransform(proj_WGS84, proj_current) # creation de la transformation adequate
			point = proj_transformer.transform (longitude, latitude) #transformation dans le projet courant
			commune = find_address[0].findall("./{http://www.opengis.net/xls}Address/{http://www.opengis.net/xls}Place")[0].text #recuperation des coordonnees
			#print(commune)
			code_postal = find_address[0].findall("./{http://www.opengis.net/xls}Address/{http://www.opengis.net/xls}PostalCode")[0].text
			#print(code_postal)
			rue = find_address[0].findall("{http://www.opengis.net/xls}Address/{http://www.opengis.net/xls}StreetAddress/{http://www.opengis.net/xls}Street")[0].text
			# {http://www.opengis.net/xls}Building {http://www.opengis.net/xls}Street
			#print(rue) 
			building = (find_address[0].findall("{http://www.opengis.net/xls}Address/{http://www.opengis.net/xls}StreetAddress/{http://www.opengis.net/xls}Building"))
			for build in building:
				num = build.get('number')
			#On teste l'existence d'un numero dans l'adresse demandee
			try:
				numero = int(num)
			except:
				numero = ""
			#print(numero)
			precision = find_address[0].findall("{http://www.opengis.net/xls}SearchCentreDistance")
			for prec in precision:
				distance = prec.get('value')
			
			resultats.append(point)
			resultats.append(latitude)
			resultats.append(longitude)
			resultats.append(numero)
			resultats.append(rue)
			resultats.append(code_postal)
			resultats.append(commune)
			resultats.append(distance)   
			
		except:
			print("Nous n'avons pas trouve d'adresse correspondante.")
			
		return resultats
	
	
	def geocode_inverse_fichier(self, cheminFichier, cheminEnregistrement,ajout_canevas):
		fichier_coordonnees = open(cheminFichier, "r")
		ligne = fichier_coordonnees.readlines()
		fichier_resultats = open(cheminEnregistrement + "/resultats_geo_inv.txt",'w')
		fichier_resultats.write('adresse;latitude;longitude;distance\n')
		fichier_resultats = open(cheminEnregistrement + "/resultats_geo_inv.txt",'a')
		couche_adresse = crea_couche("Adresses",'Point')
		for i in range(len(ligne)):
			coords = ligne[i].split(';')
			latitude = (float(coords[0])) #recuperation de la latitude
			longitude = (float(coords[1])) #recuperation de la longitude
			res = protocoleinit(self.cles,self.usern, self.passw).geocode_inverse(latitude,longitude) #on determine le geocodage inverse de chacune des coordonnees demandees
			if res:
				point = res[0]  
				latitude = str(res[1])
				longitude = str(res[2])
				numero = str(res[3])
				rue = str(res[4])
				code_postal = str(res[5])
				commune = str(res[6])
				distance = str(res[7])
				print(commune)
				couche_adresse.create_point(point,numero,rue,code_postal,commune,latitude,longitude) #ajout du point a la couche et des attibuts        
				#si il n'y a pas de numero ce n'est pas la peine d'ajouter le premier espace
				if numero != "":
					fichier_resultats.write(numero + " " + rue + " " + code_postal + " " + commune +";" + latitude + ";" + longitude + ";" + distance + "\n")
				else:
					fichier_resultats.write(rue + " " + code_postal + " " + commune +";" + latitude + ";" + longitude + ";" + distance + "\n")
			else:
				fichier_resultats.write("Erreur : Nous n'avons pas trouve d'adresse correspondante;" + str(latitude) + ";" + str(longitude) + "\n")
		fichier_coordonnees.close()
		fichier_resultats.close()
		#si l'utilisateur souhaite ajouter les adresses geocodees a sa carte, on affiche la couche
		if ajout_canevas:
			couche_adresse.aff_couche
            



"""
Classe permettant l'ajout de couche au canevas
"""

class crea_couche(object):
     
    def __init__(self,nom,type):
        self.nom = nom
        self.type= type
        self.couche =  QgsVectorLayer(self.type, self.nom , "memory") #creation de la couche virtuelle
        self.pr = self.couche.dataProvider()                
        self.couche.startEditing()
        #ajout des attributs
        self.pr.addAttributes( [QgsField("numero", QVariant.String), QgsField("rue", QVariant.String), QgsField("code_postal", QVariant.Double),
                            QgsField("commune", QVariant.String), QgsField("latitude",  QVariant.Double), QgsField("longitude", QVariant.Double)])

    def create_point(self,point,numero,rue,code_postal,commune,latitude,longitude):
        #ajout d'un point
        self.seg = QgsFeature()
        self.seg.setGeometry(QgsGeometry.fromPoint(point)) #renseignement de la geometrie du point (lat,long)
        self.seg.setAttributes([numero,rue,code_postal,commune,latitude, longitude]) #renseignement des attributs
        self.pr.addFeatures([self.seg]) 
        self.couche.commitChanges()
        self.couche.updateExtents()
    @property
    def aff_couche(self):
        #fin de l'edition et affichage de la couche
        QgsMapLayerRegistry.instance().addMapLayers([self.couche])


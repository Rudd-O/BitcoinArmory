# This is a sample plugin file that will be used to create a new tab
# in the Armory main window.  All plugin files (such as this one) will
# be injected with the globals() from ArmoryQt.py, which includes pretty
# much all of Bitcoin & Armory related stuff that you need.  So this
# file can use any utils or objects accessible to functions in ArmoryQt.py.
from PyQt4.Qt import QPushButton, QScrollArea, SIGNAL, QLabel, QLineEdit, \
   QTextEdit
from qtdefines import QRichLabel, makeVertFrame, makeHorizFrame, GETFONT, \
   relaxedSizeNChar, VERTICAL
from ui.WalletFrames import SelectWalletFrame
from armoryengine.BDM import getBDM
from armoryengine.ArmoryOptions import getTestnetFlag

# Class name is required by the plugin framework.
class PluginObject(object):
   tabName = 'PMTA'
   maxVersion = '0.99'

   # NB: As a general rule of thumb, it's wise to not rely on access to anything
   # until the BDM is ready to go and/or Armory has finished loading itself. Any
   # code that must run before both conditions are satisfied (e.g., get info
   # from a wallet) may fail.
   def __init__(self, main):
      self.main = main
      self.wlt = None

      # Set up the GUI.
      headerLabel    = QRichLabel(tr("<b>PMTA-related Functions</b>"""),
                                  doWrap=False)
      addressLabel = QLabel('Choose wallet:')
      self.frmSelectedWlt = SelectWalletFrame(main, main, VERTICAL,
                                              selectWltCallback=self.setWallet)
      self.pksButton      = QPushButton('Save PKS Record')
      self.pmtaButton     = QPushButton('Save PMTA Record')
      self.payReqButton   = QPushButton('Payment Request')
      self.addIDButton    = QPushButton('Save Wallet ID')
      payReqLabel         = QLabel('Payment Request:')
      self.payReqTextArea = QTextEdit()
      self.payReqTextArea.setFont(GETFONT('Fixed', 8))
      w                   = relaxedSizeNChar(self.payReqTextArea, 68)[0]
      h                   = int(12 * 8.2)
      self.payReqTextArea.setMinimumWidth(w)
      self.payReqTextArea.setMinimumHeight(h)
      self.payReqTextArea.setReadOnly(True)
      self.clearButton    = QPushButton('Clear')

      # Qt GUI calls must occur on the main thread. We need to update the frame
      # once the BDM is ready, so that the wallet balance is shown. To do this,
      # we register a signal with the main thread that can be used to call an
      # associated function.
      self.main.connect(self.main, SIGNAL('bdmReadyPMTA'), self.bdmReady)
      self.main.connect(self.main, SIGNAL('wltChangedPKS'), self.wltHasChanged)

      # Action for when the PKS button is pressed.
      def pksAction():
         self.savePKSFile()

      # Action for when the PMTA button is pressed.
      def pmtaAction():
         self.savePMTAFile()

      # Action for when the payment request button is pressed.
      def prAction():
         # TO BE COMPLETED
         self.payReqTextArea.setText("<Payment Request Blob>")

      # Action for when the add wallet ID button is pressed.
      def addIDAction():
         # TO BE COMPLETED
         pass

      # Action for when the clear text button is pressed.
      def clearTextArea():
         self.payReqTextArea.setText('')

      self.main.connect(self.pksButton,    SIGNAL('clicked()'), pksAction)
      self.main.connect(self.pmtaButton,   SIGNAL('clicked()'), pmtaAction)
      self.main.connect(self.payReqButton, SIGNAL('clicked()'), prAction)
      self.main.connect(self.addIDButton,  SIGNAL('clicked()'), addIDAction)
      self.main.connect(self.clearButton,  SIGNAL('clicked()'), clearTextArea)

      # ID stuff
      idLabel = QLabel('Public Wallet ID: ')
      self.inID = QLineEdit()
      self.inID.setFont(GETFONT('Fixed'))
      self.inID.setMinimumWidth(tightSizeNChar(GETFONT('Fixed'), 14)[0])
      self.inID.setAlignment(Qt.AlignLeft)
      idTip = self.main.createToolTipWidget('An ID, in email address form, ' \
                                            'that will be associated with ' \
                                            'this wallet in a DNS record.')

      # Base58 PKS stuff
      pksB58Label = QLabel('PKS (Base 58): ')
      self.pksB58Line = QLineEdit()
      self.pksB58Line.setFont(GETFONT('Fixed'))
      self.pksB58Line.setMinimumWidth(tightSizeNChar(GETFONT('Fixed'), 14)[0])
      self.pksB58Line.setAlignment(Qt.AlignLeft)
      self.pksB58Line.setReadOnly(True)
      pksB58Tip = self.main.createToolTipWidget('The wallet\'s PKS record, ' \
                                                'Base58-encoded.')

      # Create the frame and set the scrollarea widget to the layout.
      # self.tabToDisplay is required by the plugin framework.
      pluginFrame = makeVertFrame([headerLabel,
                                   makeHorizFrame([addressLabel,
                                                   'Stretch']),
                                   makeHorizFrame([self.frmSelectedWlt,
                                                   'Stretch']),
                                   makeHorizFrame([pksB58Label,
                                                   self.pksB58Line,
                                                   pksB58Tip,
                                                   'Stretch']),
                                   makeHorizFrame([idLabel,
                                                   self.inID,
                                                   idTip,
                                                   'Stretch']),
                                   makeHorizFrame([self.pksButton,
                                                   self.pmtaButton,
                                                   self.payReqButton,
                                                   self.addIDButton,
                                                   'Stretch']),
                                   payReqLabel,
                                   makeHorizFrame([self.payReqTextArea,
                                                   'Stretch']),
                                   makeHorizFrame([self.clearButton,
                                                   'Stretch']),
                                   'Stretch'])
      self.tabToDisplay = QScrollArea()
      self.tabToDisplay.setWidgetResizable(True)
      self.tabToDisplay.setWidget(pluginFrame)

      # Register the BDM callback for when the BDM sends signals.
      getBDM().registerCppNotification(self.handleBDMNotification)


   # Call for when we want to save a binary PKS record to a file. By default,
   # all PKS flags will be false.
   # INPUT:  PKS-related flags (bool) - See armoryengine/ConstructedScript.py
   # OUTPUT: None
   # RETURN: Final PKS record (PKSRecord)
   def savePKSFile(self, isStatic = False, useCompr = False, use160 = False,
                   isUser = False, isExt = False, chksumPres = False):
      defName = 'armory_%s.pks' % self.wlt.uniqueIDB58
      filePath = unicode(self.main.getFileSave(defaultFilename = defName))
      myPKS = None

      if len(filePath) > 0:
         pathdir = os.path.dirname(filePath)
         if not os.path.exists(pathdir):
            raise FileExistsError('Path for new PMTA record does not ' \
                                  'exist: %s', pathdir)
         else:
            myPKS = getWltPKS(self.wlt, isStatic, useCompr, use160, isUser,
                              isExt, sbdPubKey65.toBinStr(), chksumPres)
            # Write the PKS record to the file, then return the record.
            with open(filePath, 'wb') as newWltFile:
               newWltFile.write(myPKS.serialize())


   # Function that creates and returns a PublicKeySource (PMTA/DNS) record based
   # on the incoming wallet.
   # INPUT:  The wallet used to generate the PKS record (ABEK_StdWallet)
   #         PKS-related flags (bool) - See armoryengine/ConstructedScript.py
   # OUTPUT: None
   # RETURN: Final PKS record (PKSRecord)
   def getWltPKS(self, inWlt, isStatic = False, useCompr = False,
                 use160 = False, isUser = False, isExt = False,
                 chksumPres = False):
      # Start with the wallet's uncompressed root key.
      sbdPubKey33 = SecureBinaryData(inWlt.sbdPublicKey33)
      sbdPubKey65 = CryptoECDSA().UncompressPoint(sbdPubKey33)

      myPKS = PublicKeySource()
      myPKS.initialize(isStatic, useCompr, use160, isUser, isExt,
                       sbdPubKey65.toBinStr(), chksumPres)
      return myPKS


   # Call for when we want to save a binary PMTA record to a file. The PMTA
   # record will include a PKS record for the currently selected wallet. By
   # default, all PKS flags will be false, except for the flag adding a checksum
   # to the PKS record.
   # INPUT:  PKS-related flags (bool) - See armoryengine/ConstructedScript.py
   # OUTPUT: None
   # RETURN: Final PMTA record (PMTARecord)
   def savePMTAFile(self, isStatic = False, useCompr = False, use160 = False,
                    isUser = False, isExt = False, chksumPres = True):
         defName = 'armory_%s.pmta' % self.wlt.uniqueIDB58
         payNet = PAYNET_BTC
         if getTestnetFlag():
            payNet = PAYNET_TBTC

         filePath = unicode(self.main.getFileSave(defaultFilename = defName))
         if not len(filePath) > 0:
            return
         else:
            # Start with the wallet's uncompressed root key.
            sbdPubKey33 = SecureBinaryData(self.wlt.sbdPublicKey33)
            sbdPubKey65 = CryptoECDSA().UncompressPoint(sbdPubKey33)

            pathdir = os.path.dirname(filePath)
            if not os.path.exists(pathdir):
               raise FileExistsError('Path for new PKS record does not ' \
                                     'exist: %s', pathdir)

            # Write the PMTA record to the file, then return the record.
            myPMTA = PMTARecord()
            with open(filePath, 'wb') as newWltFile:
               myPKS = PublicKeySource()
               myPKS.initialize(isStatic, useCompr, use160, isUser, isExt,
                                sbdPubKey65.toBinStr(), chksumPres)
               myPMTA.initialize(myPKS.serialize(), payNet)
               newWltFile.write(myPMTA.serialize())
            return myPMTA


   # Callback function for when the user selects a wallet. Be careful, as some
   # objects (GUI objects, most likely) aren't acceptable, probably due to the
   # function being called before Armory is ready to be displayed.
   def setWallet(self, wlt):
      self.wlt = wlt

      # Signal doesn't work when first called. Probably due to Armory not being
      # fully loaded just yet. This is acceptable.
      self.main.emit(SIGNAL('wltChangedPKS'))

      # If it exists, set the DNS wallet ID.
#      FIX FIX FIX

      # Get the PKS record and display it. It appears that the BDM calls this
      # function early and chooses a wallet right away. This is good. A race
      # condition with the call from registerCppNotification() doesn't matter
      # in this case, and we don't care which wallet is chosen first.


   # Function called when the "bdmReadyPMTA" signal is emitted. Updates the
   # wallet balance on startup.
   def bdmReady(self):
      # Update wallet balance
      self.frmSelectedWlt.updateOnWalletChange()

      # If it exists, get the DNS wallet ID.
#      FIX FIX FIX

      # Get the PKS record and display it as a Base58-encoded string. Used only
      # for the initial string load.
      if self.wlt is not None:
         wltPKS = binary_to_base58(self.getWltPKS(self.wlt).serialize())
         self.pksB58Line.setText(wltPKS)


   # Function called when the "wltChangedPKS" signal is emitted. Updates the
   # QLineEdit object showing the wallet's Base58-encoded PKS record.
   def wltHasChanged(self):
      if self.wlt is None:
         self.pksB58Line.setText('')
      else:
         wltPKS = binary_to_base58(self.getWltPKS(self.wlt).serialize())
         self.pksB58Line.setText(wltPKS)


   # Place any code here that must be executed when the BDM emits a signal. The
   # only thing we do is emit a signal so that the call updating the GUI can be
   # called by the main thread. (Qt GUI requirement, lest Armory crash due to a
   # non-main thread updating the GUI. This updates wallet-related info.
   def handleBDMNotification(self, action, args):
      if action == FINISH_LOAD_BLOCKCHAIN_ACTION:
         self.main.emit(SIGNAL('bdmReadyPMTA'))


   # Function is required by the plugin framework.
   def getTabToDisplay(self):
      return self.tabToDisplay

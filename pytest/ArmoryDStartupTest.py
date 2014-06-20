import sys
sys.path.append('..')
from pytest.Tiab import *
import json

from armoryd import Armory_Daemon

# runs a Test In a Box (TIAB) bitcoind session. By copying a prebuilt
# testnet with a known state
# Charles's recommendation is that you keep the TIAB somewhere like ~/.armory/tiab.charles
# and export that path in your .bashrc as ARMORY_TIAB_PATH
class ArmoryDSession:
   numInstances=0
   
   # create a Test In a Box, initializing it and filling it with data
   # the data comes from a path in the environment unless tiabdatadir is set
   # tiab_repository is used to name which flavor of box is used if
   # tiabdatadir is not used - It is intended to be used for when we
   # have multiple testnets in a box with different properties
   def __init__(self, tiab):
      self.processes = []
      self.running = False
      self.tiab = tiab
      self.armorydPath = 'armoryd.py' if os.path.exists('armoryd.py') else \
         os.path.join('..', 'armoryd.py')
      self.restart()
      
   
   def __del__(self):
      self.clean()
   
   # exit bitcoind and remove all data
   def clean(self):
      if not self.running:
         return
      ArmoryDSession.numInstances -= 1
      for x in self.processes:
         x.kill()
      for x in self.processes:
         x.wait()
      self.processes = []
      self.running=False
   
   # clean() and then start bitcoind again
   def callArmoryD(self, additionalArgs, waitForOutput=True):
      armoryDArgs = ['python', self.armorydPath,
            '--testnet',
            '--datadir=' + os.path.join(self.tiab.tiabDirectory, 'tiab', 'armory'),
            '--satoshi-datadir=' + os.path.join(self.tiab.tiabDirectory, 'tiab', '1')]
      armoryDArgs.extend(additionalArgs)
      if waitForOutput:
         # If there is output coming back convert it from a string to a dictionary
         return json.loads(subprocess.check_output(armoryDArgs))
      else:
         # If we are not waiting output, e.g. when starting ArmoryD, return the started process.
         startedProcess = subprocess.Popen(armoryDArgs)
         self.processes.append(startedProcess)
         return startedProcess

   def restart(self):
      self.clean()
      if ArmoryDSession.numInstances != 0:
         raise RuntimeError("Cannot have more than one ArmoryD session simultaneously")
      
      try:
         self.callArmoryD([os.path.join(self.tiab.tiabDirectory, 'tiab', 'armory',FIRST_WLT_FILE_NAME)], False)
         ArmoryDSession.numInstances += 1
         # Wait for Armory_Daemon to start running
         while not Armory_Daemon.checkForAlreadyRunning():
            time.sleep(1)

      except:
         self.clean()
         raise
      self.running = True

class ArmoryDStartupTest(TiabTest):      

   def setUp(self):
      self.armoryDSession = ArmoryDSession(self.tiab)
   
   
   def tearDown(self):
      self.armoryDSession.clean()
            
   def testJSONGetinfo(self):
      actualResult = self.armoryDSession.callArmoryD(['getinfo'], True)
      self.assertEqual(actualResult['balance'], FIRST_WLT_BALANCE)
      self.assertEqual(actualResult['bdmstate'], 'BlockchainReady')
      self.assertEqual(actualResult['blocks'], TOP_TIAB_BLOCK)
      self.assertEqual(actualResult['difficulty'], 1.0)
      self.assertEqual(actualResult['testnet'], True)
      
   def testJSONMultipleWallets(self):
      wltDictionary = self.armoryDSession.callArmoryD(['listloadedwallets'])
      self.assertTrue(len(wltDictionary), 3)
      actualResult = self.armoryDSession.callArmoryD(['getwalletinfo'], True)
      self.assertEqual(actualResult, {u'description': u'', u'name': u'Primary Wallet', u'numaddrgen': 22, u'balance': FIRST_WLT_BALANCE, u'highestusedindex': 10, u'keypoolsize': 10})
      setWltResult = self.armoryDSession.callArmoryD(['setactivewallet', SECOND_WLT_NAME])
      self.assertTrue(setWltResult.index(SECOND_WLT_NAME) > 0)
      actualResult2 = self.armoryDSession.callArmoryD(['getwalletinfo'], True)
      self.assertEqual(actualResult2, {u'description': u'', u'name': u'Third Wallet', u'numaddrgen': 15, u'balance': 12.8999, u'highestusedindex': 3, u'keypoolsize': 10})
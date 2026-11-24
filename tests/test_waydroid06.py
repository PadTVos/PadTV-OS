import subprocess,unittest
from unittest.mock import patch
from padtv import android

class WaydroidFallbackTests(unittest.TestCase):
    def test_inventory_does_not_dbus_activate_stopped_runtime(self):
        with patch.object(android.sys,'platform','linux'),patch.object(android.shutil,'which',return_value='/usr/bin/waydroid'),patch.object(android.Path,'is_file',return_value=True),patch.object(android.ConfigParser,'read'),patch.object(android,'run',return_value=subprocess.CompletedProcess([],3,stdout='')) as run:
            state=android.inventory()
            self.assertFalse(state['running']);self.assertFalse(state['known'])
            self.assertEqual(run.call_args.args[0],['systemctl','is-active','--quiet','waydroid-container.service'])
            self.assertEqual(run.call_count,1)

if __name__=='__main__':unittest.main()

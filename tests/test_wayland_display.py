import io
import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
from padtv import wayland_display as display

OUTPUTS = json.dumps([{'name':'HDMI-A-1','enabled':True,'modes':[
    {'width':1920,'height':1080,'refresh':60.0,'current':True},
    {'width':1280,'height':720,'refresh':59.94,'current':False}]}])
REQUEST = {'action':'display-set','output':'HDMI-A-1','mode':'1280x720@59.940Hz'}


class WaylandDisplayTests(unittest.TestCase):
    def test_refresh_rate_is_preserved(self):
        parsed = display.parse_outputs(OUTPUTS)[0]
        self.assertEqual(parsed['current'],'1920x1080@60.000Hz')
        self.assertIn('1280x720@59.940Hz', parsed['modes'])

    def test_timeout_rolls_back_and_does_not_save(self):
        run = Mock(return_value=OUTPUTS)
        with patch.object(display.select,'select',return_value=([],[],[])), patch.object(display,'save') as save:
            display.dispatch(REQUEST, run, Mock())
            save.assert_not_called()
        run.assert_any_call('wlr-randr','--output','HDMI-A-1','--mode','1920x1080@60.000Hz')

    def test_disconnect_of_worker_input_rolls_back(self):
        run = Mock(return_value=OUTPUTS)
        with patch.object(display.select,'select',return_value=([1],[],[])), patch.object(display.sys,'stdin',io.StringIO('')):
            with self.assertRaises(ValueError): display.dispatch(REQUEST,run,Mock())
        run.assert_any_call('wlr-randr','--output','HDMI-A-1','--mode','1920x1080@60.000Hz')

    def test_confirmation_saves_and_restore_uses_available_modes(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(display,'settings_path',return_value=Path(temp)/'display.json'):
            with patch.object(display.select,'select',return_value=([1],[],[])), patch.object(display.sys,'stdin',io.StringIO('{"confirm":true}\n')):
                display.dispatch(REQUEST,Mock(return_value=OUTPUTS),Mock())
            run = Mock(return_value=OUTPUTS)
            display.restore(run)
            run.assert_any_call('wlr-randr','--output','HDMI-A-1','--mode','1280x720@59.940Hz')

    def test_unknown_output_or_mode_never_changes_hardware(self):
        for changed in ({'mode':'$(reboot)'},{'output':'../../other'}):
            run = Mock(return_value=OUTPUTS)
            with self.assertRaises(ValueError): display.dispatch({**REQUEST,**changed},run,Mock())
            self.assertEqual(run.call_count,1)

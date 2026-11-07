from __future__ import annotations
import json
import os
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from model_gateway import Gateway
from security import OutputGuard

class Response:
    def __init__(self,data): self.raw=json.dumps(data).encode()
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,*args):return self.raw

class AdapterTests(unittest.TestCase):
    def test_cloud_key_only_in_header_and_fixed_model(self):
        env={'DAY15_CLOUD_API_KEY':'synthetic_provider_key','DAY15_CLOUD_MODEL':'configured-model'}
        captured=[]
        class Opener:
            def open(self,req,**kwargs):
                captured.append(req)
                return Response({'model':'resolved-model','choices':[{'message':{'content':'safe'},'finish_reason':'stop'}], 'usage':{'prompt_tokens':3,'completion_tokens':1}})
        with patch.dict(os.environ,env,clear=True),patch('urllib.request.build_opener',return_value=Opener()):
            gw=Gateway('cloud',OutputGuard([env['DAY15_CLOUD_API_KEY']]),time.monotonic()+30)
            self.assertEqual(gw.complete('system','user',200,'test'),'safe')
        req=captured[0]
        self.assertEqual(req.get_header('Authorization'),'Bearer synthetic_provider_key')
        self.assertNotIn(b'synthetic_provider_key',req.data)
        self.assertEqual(json.loads(req.data)['model'],'configured-model')
        self.assertEqual(json.loads(req.data)['max_completion_tokens'],200)
        self.assertEqual(gw.calls[0]['returned_model'],'resolved-model')
        self.assertEqual(gw.usage['prompt_tokens'],3)
    def test_model_canary_and_truncated_response_are_rejected(self):
        env={'DAY15_CLOUD_API_KEY':'dummy_cloud_key','DAY15_CLOUD_MODEL':'configured-model'}
        for content,finish in [('hidden_value_abcdefghijklmnopqrst','stop'),('safe','length')]:
            class Opener:
                def open(self,*args,**kwargs):
                    return Response({'choices':[{'message':{'content':content},'finish_reason':finish}]})
            with patch.dict(os.environ,env,clear=True),patch('urllib.request.build_opener',return_value=Opener()):
                gw=Gateway('cloud',OutputGuard(['hidden_value_abcdefghijklmnopqrst']),time.monotonic()+30)
                with self.assertRaises(ValueError):gw.complete('system','user',200,'test')
    def test_cloud_transport_and_profile_fail_closed(self):
        env={'DAY15_CLOUD_API_KEY':'dummy','DAY15_CLOUD_MODEL':'m','DAY15_CLOUD_URL':'http://example.com/v1/chat/completions'}
        with patch.dict(os.environ,env,clear=True):
            with self.assertRaises(ValueError):Gateway('cloud',OutputGuard(),time.monotonic()+30)
            with self.assertRaises(ValueError):Gateway('other',OutputGuard(),time.monotonic()+30)

if __name__=='__main__':unittest.main()

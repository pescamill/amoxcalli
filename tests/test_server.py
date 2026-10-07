import json,socket,subprocess,sys,time,unittest,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ServerTest(unittest.TestCase):
    @unittest.skipUnless((ROOT/'data/prepared/train.jsonl').exists(),'Prepare corpus first')
    def test_local_lookup_and_origin(self):
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        process=subprocess.Popen([sys.executable,'-m','nahuatl_local.serve','--port',str(port)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            url=f'http://127.0.0.1:{port}'
            for _ in range(40):
                try:page=urllib.request.urlopen(url,timeout=1).read().decode();break
                except urllib.error.URLError:time.sleep(.1)
            else:self.fail('Server did not start')
            self.assertIn('Exportar ficha de revisión',page)
            data=json.dumps({'text':'Contemplo una flor','draft':False}).encode()
            result=json.load(urllib.request.urlopen(urllib.request.Request(url+'/query',data=data,headers={'Content-Type':'application/json'})))
            self.assertEqual(result['passages'][0]['nah'],'NIQUITTA IN XOCHITL')
            with self.assertRaises(urllib.error.HTTPError) as err:urllib.request.urlopen(urllib.request.Request(url+'/query',data=data,headers={'Content-Type':'application/json','Origin':'https://example.com'}))
            self.assertEqual(err.exception.code,403)
        finally:process.terminate();process.wait(timeout=5)
if __name__=='__main__':unittest.main()

import unittest
import os,subprocess,tempfile
from pathlib import Path
from scan import scan_content,scan_path,run

class PublicationGateTests(unittest.TestCase):
    def test_secrets(self):
        cases=['gh'+'p_'+'A'*36,'-----BEGIN '+'PRIVATE KEY-----','password = "'+'a-real-value'+'"','https://'+'user:'+'pass@example.com','AK'+'IA'+'A'*16,'sk-'+'A'*40]
        for value in cases:
            with self.subTest(kind=value[:3]):self.assertTrue(scan_content('fixture.py',value.encode()))
    def test_personal_identifiers(self):
        for value in ['C:/Users/'+'private-person/file','person'+'@private.example.net','S-1-5-21-'+'111-222-333-1001']:
            self.assertTrue(scan_content('fixture',value.encode()))
    def test_allowed(self):
        self.assertFalse(scan_content('fixture',b'account_login = 123456789\nC:/Users/EXAMPLE_USER/file'))
    def test_excluded_paths(self):
        for path in ['state/journal.sqlite3','.env.prod','config.demo.json','data/ticks.csv','key.pem']:
            self.assertTrue(scan_path(path))
    def test_large_binary_and_local_blacklist(self):
        self.assertTrue(scan_content('file',b'x'*1048577))
        self.assertTrue(scan_content('file',b'\0binary'))
        self.assertTrue(scan_content('file',b'private-account',['private-account']))

    def test_unreachable_secret_object_blocks_history(self):
        previous=Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            try:
                os.chdir(folder)
                subprocess.run(['git','init','-q'],check=True)
                subprocess.run(['git','hash-object','-w','--stdin'],input=('gh'+'p_'+'B'*36).encode(),capture_output=True,check=True)
                result=run(history=True)
                self.assertEqual(result['status'],'BLOCKED')
                self.assertTrue(any(x['rule']=='github-token' for x in result['findings']))
            finally:os.chdir(previous)

    def test_staged_blob_scanned_instead_of_working_file(self):
        previous=Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            try:
                os.chdir(folder);subprocess.run(['git','init','-q'],check=True)
                Path('file.py').write_text('gh'+'p_'+'C'*36)
                subprocess.run(['git','add','file.py'],check=True)
                Path('file.py').write_text('safe replacement only in working tree')
                self.assertEqual(run(staged=True)['status'],'BLOCKED')
            finally:os.chdir(previous)

if __name__=='__main__':unittest.main()

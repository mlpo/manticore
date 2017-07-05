import StringIO
import unittest
import sys
import shutil
import tempfile
import os
import hashlib
import subprocess
import time

#logging.basicConfig(filename = "test.log",
#                format = "%(asctime)s: %(name)s:%(levelname)s: %(message)s",
#                level = logging.DEBUG)

class IntegrationTest(unittest.TestCase):
    _multiprocess_can_split_ = True
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)
        pass

    def _runWithTimeout(self, procargs, logfile, timeout=1200):

        with open(os.path.join(os.pardir, logfile), "w") as output:
            po = subprocess.Popen(procargs, stdout=output)
            secs_used = 0

            while po.poll() is None and secs_used < timeout:
                time.sleep(1)
                sys.stderr.write("~")
                secs_used += 1

            self.assertEqual(po.returncode, 0)
            self.assertTrue(secs_used < timeout)
            sys.stderr.write("\n")

    def testTimeout(self):
        dirname = os.path.dirname(__file__)
        filename = os.path.abspath(os.path.join(dirname, 'binaries/arguments_linux_amd64'))
        self.assertTrue(filename.startswith(os.getcwd()))
        filename = filename[len(os.getcwd())+1:]
        data = file(filename,'rb').read()
        self.assertEqual(len(data), 767152)
        self.assertEqual(hashlib.md5(data).hexdigest() , '00fb23e47831a1054ca4a74656035472')
        workspace = '%s/workspace'%self.test_dir
        t = time.time()
        with open(os.path.join(os.pardir, '%s/output.log'%self.test_dir), "w") as output:
            po = subprocess.check_call(['python', '-m', 'manticore',
                                '--workspace', workspace,
                                '--timeout', '1',
                                '--procs', '4',
                                filename,
                                '+++++++++'], stdout=output)
            
        self.assertTrue(time.time()-t < 20)

    def test_cli_verbosity(self):
        """
        Tests that default verbosity produces the expected volume of output
        """

        dirname = os.path.dirname(__file__)
        filename = os.path.join(dirname, 'binaries/basic_linux_amd64')
        output = subprocess.check_output(['python', '-m', 'manticore', filename])
        self.assertLessEqual(len(output.splitlines()), 25)

    def testArgumentsAssertions(self):
        dirname = os.path.dirname(__file__)
        filename = os.path.abspath(os.path.join(dirname, 'binaries/arguments_linux_amd64'))
        self.assertTrue(filename.startswith(os.getcwd()))
        filename = filename[len(os.getcwd())+1:]
        SE = os.path.join(dirname, '../main.py')
        data = file(filename,'rb').read()
        self.assertEqual(len(data), 767152)
        self.assertEqual(hashlib.md5(data).hexdigest() , '00fb23e47831a1054ca4a74656035472')
        workspace = '%s/workspace'%self.test_dir
        assertions = '%s/assertions.txt'%self.test_dir
        file(assertions,'w').write('0x0000000000401003 ZF == 1')
        with open(os.path.join(os.pardir, '%s/output.log'%self.test_dir), "w") as output:
            po = subprocess.Popen(['python', '-m', 'manticore',
                                '--workspace', workspace,
                                '--proc', '4',
                                '--assertions', assertions,
                                filename,
                                '+++++++++'], stdout=output)
            po.wait()

        data = file('%s/visited.txt'%workspace,'r').read()
        data = '\n'.join(sorted(set(data.split('\n'))))
        self.assertEqual(hashlib.md5(data).hexdigest() , '6e07108975a1a4fe37207f2ffff7d0a7')


    def testDecree(self):
        dirname = os.path.dirname(__file__)
        filename = os.path.abspath(os.path.join(dirname, 'binaries/cadet_decree_x86'))
        self.assertTrue(filename.startswith(os.getcwd()))
        filename = filename[len(os.getcwd())+1:]
        SE = os.path.join(dirname, '../main.py')
        data = file(filename,'rb').read()
        self.assertEqual(len(data), 1828)
        self.assertEqual(hashlib.md5(data).hexdigest() , '8955a29d51c1edd39b0e53794ebcf464')
        workspace = '%s/workspace'%self.test_dir
        self._runWithTimeout(['python', '-m', 'manticore',
                    '--workspace', workspace,
                    '--timeout', '20',
                    '--proc', '4',
                    '--policy', 'uncovered',
                    filename], '%s/output.log'%self.test_dir)

        data = file('%s/visited.txt'%workspace,'r').read()
        visited = len(set(data.split('\n')))
        self.assertTrue(visited > 100 )


if __name__ == '__main__':
    unittest.main()


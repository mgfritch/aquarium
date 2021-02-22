import pytest
from pathlib import Path
from pyfakefs.fake_filesystem_unittest import TestCase

from gravel.controllers.orch.ceph import Mgr, Mon

CEPH_CONF_FILE = '/etc/ceph/ceph.conf'
CEPH_CONF_CONTENT = '''
# minimal ceph.conf for 049e7b49-0c86-4373-85a4-cb9d50c374a7
[global]
        fsid = 049e7b49-0c86-4373-85a4-cb9d50c374a7
        mon_host = [v2:192.168.1.1:40919/0,v1:192.168.1.1:40920/0] [v2:192.168.1.1:40921/0,v1:192.168.1.1:40922/0] [v2:192.168.1.1:40923/0,v1:192.168.1.1:40924/0]
'''  # noqa:E501


class TestCeph(TestCase):

    def setUp(self):
        self.setUpPyfakefs()
        self.write_ceph_conf()

    def write_ceph_conf(self,
                        conf_file: str = CEPH_CONF_FILE,
                        content: str = CEPH_CONF_CONTENT):

        Path(conf_file).parent.mkdir(0o700, parents=True, exist_ok=True)
        with open(conf_file, 'w') as f:
            f.write(content)

    def test_ceph_conf(self):
        # default location
        Mgr()
        Mon()

        # custom location
        conf_file = '/foo/bar/baz.conf'
        self.write_ceph_conf(conf_file=conf_file)
        Mgr(conf_file=conf_file)
        Mon(conf_file=conf_file)

        # invalid location
        conf_file = "missing.conf"
        with pytest.raises(FileNotFoundError, match=conf_file):
            Mgr(conf_file=conf_file)
            Mon(conf_file=conf_file)

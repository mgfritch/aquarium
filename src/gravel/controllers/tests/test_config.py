from datetime import datetime
from pathlib import Path
from pyfakefs.fake_filesystem_unittest import TestCase

from gravel.controllers.config \
    import Config, DeploymentStage


class TestConfig(TestCase):

    def setUp(self):
        self.setUpPyfakefs()

    def test_config_version(self):
        config = Config()
        assert config.config.version == 2

    def test_deployment_state(self):
        ds = Config().deployment_state
        assert ds.stage == DeploymentStage.none
        assert ds.last_modified < datetime.now()

    def test_config_options(self):
        opts = Config().options
        assert opts.inventory_probe_interval == 60
        assert opts.storage_probe_interval == 30.0

    def test_config_path(self):
        config = Config()
        assert config.confpath == Path('/etc/aquarium/config.json')
        assert config.options.service_state_path == Path('/etc/aquarium/storage.json')

        config = Config(path='foo')
        assert config.confpath == Path('foo/config.json')
        assert config.options.service_state_path == Path('foo/storage.json')

    def test_existing_config(self):
        ss_path = '/foo/bar/baz/bang'
        conf = '''
{
 "version": 2,
 "name": "",
 "deployment_state": {
   "last_modified": "2021-02-17T16:57:07.071579",
   "stage": "bootstrapped"
 },
 "options": {
   "inventory_probe_interval": 60,
   "storage_probe_interval": 30.0,
   "service_state_path": "%s"
 }
}
''' % (ss_path)
        with open('config.json', 'w') as f:
            f.write(conf)

        config = Config(path='/')
        assert config.options.service_state_path == Path(ss_path)

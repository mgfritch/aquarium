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
        assert config.options.service_state_path == '/etc/aquarium/storage.json'

        config = Config(path='foo')
        assert config.confpath == Path('foo/config.json')
        assert config.options.service_state_path == 'foo/storage.json'

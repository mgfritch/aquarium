# project aquarium's backend
# Copyright (C) 2021 SUSE, LLC.

from json.decoder import JSONDecodeError
from gravel.controllers.orch.models \
    import CephDFModel, CephOSDMapModel, CephOSDPoolEntryModel
import rados
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, Optional


class CephError(Exception):
    pass


class CephNotConnectedError(CephError):
    pass


class CephCommandError(CephError):
    pass


class Ceph(ABC):

    cluster: Optional[rados.Rados] = None

    def __init__(self, confpath: str = "/etc/ceph/ceph.conf"):

        path = Path(confpath)
        if not path.exists():
            raise FileNotFoundError(confpath)

        self.cluster = rados.Rados(conffile=confpath)
        if not self.cluster:
            raise CephError("error creating cluster handle")

        # apparently we can't rely on argument "timeout" because it's not really
        # supported by the C API, and thus the python bindings simply expose it
        # until some day when it's supposed to be dropped.
        # This is mighty annoying because we can, technically, get stuck here
        # forever.
        try:
            self.cluster.connect()
        except Exception as e:
            raise CephError(e) from e

        try:
            self.cluster.require_state("connected")
        except rados.RadosStateError as e:
            raise CephError(e) from e

        self._is_connected = True

    def __del__(self):
        if self.cluster:
            self.cluster.shutdown()
            self._is_connected = False

    def is_connected(self):
        return self._is_connected

    def assert_is_ready(self):
        if not self.cluster or not self.is_connected():
            raise CephNotConnectedError()

    @property
    def fsid(self) -> str:
        self.assert_is_ready()
        try:
            return self.cluster.get_fsid()
        except Exception as e:
            raise CephError(e)

    def _cmd(self, func: Callable[[str, bytes], Any],
             cmd: Dict[str, Any]
             ) -> Any:
        self.assert_is_ready()
        try:
            cmdstr: str = json.dumps(cmd)
            rc, out, outstr = func(cmdstr, b"")
            res: Dict[str, Any] = {}
            if rc != 0:
                raise CephCommandError(outstr)
            if out:
                try:
                    res = json.loads(out)
                except JSONDecodeError:  # maybe free-form?
                    res = {"result": outstr}
            elif outstr:  # assume 'outstr' always as free-form text
                res = {"result": outstr}
            return res
        except Exception as e:
            raise CephCommandError(e) from e

    @abstractmethod
    def call(self, cmd: Dict[str, Any]) -> Any:
        raise NotImplementedError("method 'call' has not been implemented")


class Mgr(Ceph):

    def __init__(self):
        super().__init__()

    def call(self, cmd: Dict[str, Any]) -> Any:
        return self._cmd(self.cluster.mgr_command, cmd)


class Mon(Ceph):

    def __init__(self):
        super().__init__()

    def call(self, cmd: Dict[str, Any]) -> Any:
        return self._cmd(self.cluster.mon_command, cmd)

    @property
    def status(self) -> Dict[str, Any]:
        cmd: Dict[str, Any] = {
            "prefix": "status",
            "format": "json"
        }
        result: Dict[str, Any] = self.mon(cmd)  # propagate exception
        return result

    def df(self) -> CephDFModel:
        cmd: Dict[str, str] = {
            "prefix": "df",
            "format": "json"
        }
        result: Dict[str, Any] = self.mon(cmd)
        return CephDFModel.parse_obj(result)

    def get_osdmap(self) -> CephOSDMapModel:
        cmd: Dict[str, str] = {
            "prefix": "osd dump",
            "format": "json"
        }
        result: Dict[str, Any] = self.mon(cmd)
        return CephOSDMapModel.parse_obj(result)

    def get_pools(self) -> List[CephOSDPoolEntryModel]:
        osdmap = self.get_osdmap()
        return osdmap.pools

    def set_pool_size(self, name: str, size: int) -> None:
        cmd: Dict[str, str] = {
            "prefix": "osd pool set",
            "pool": name,
            "var": "size",
            "val": str(size)
        }
        self.mon(cmd)


if __name__ == "__main__":
    mgr = Mgr()
    print(f"fsid: {mgr.fsid}")
    mon = Mon()
    print(f"fsid: {mon.fsid}")
    print(f"status: {mon.status}")

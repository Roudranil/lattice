import warnings

warnings.simplefilter("ignore")

from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from deepagents.backends.protocol import BackendFactory
from fs.tempfs import TempFS
from langchain.tools import ToolRuntime


class CustomBackend:
    def __init__(self):
        self.memories_fs = TempFS("memories")
        self.artifacts_fs = TempFS("artifacts")

    def __call__(self, rt: ToolRuntime) -> BackendFactory:
        return CompositeBackend(
            default=StateBackend(rt),
            routes={
                "/notes/": StateBackend(rt),
                "/memories/": FilesystemBackend(
                    root_dir=self.memories_fs.getsyspath("/"), virtual_mode=True
                ),
                "/artifacts/": FilesystemBackend(
                    root_dir=self.artifacts_fs.getsyspath("/"), virtual_mode=True
                ),
            },
        )

    def close(self):
        for fs in (self.memories_fs, self.artifacts_fs):
            try:
                if not fs.isclosed():
                    fs.close()
            except Exception:
                pass

from abc import ABC, abstractmethod
from logging import Logger


class GitScriptDownloaderBase(ABC):

    def __init__(self, logger: Logger):
        self.logger = logger

    @abstractmethod
    def download_repo(self, url: str, token: str, branch: str = "") -> str:
        """
        method should do the following:
        1.make request
        2. download repo
        3. prepare working dir, add repo contents to working dir
        4. return full path of working dir as string
        """
        pass


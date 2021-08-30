
from discord.ext import commands


class Paginator(commands.Paginator):

    def __init__(self, seperator = "\n", prefix='```', suffix='```', max_size=2000):
        super().__init__(prefix, suffix, max_size)
        self.seperator = seperator
        self._current_page = []

    def add_section(self, section='', *, empty=False):
        if len(section) > self.max_size - len(self.prefix) - 2:
            raise RuntimeError('Section exceeds maximum page size %s' % (self.max_size - len(self.prefix) - 2))

        if self._count + len(section) + len(self.seperator) > self.max_size:
            self.close_page()

        self._count += len(section) + len(self.seperator)
        self._current_page.append(section)

        if empty:
            self._current_page.append('')
            self._count += len(self.seperator)

    def close_page(self):
        self._pages.append(self.prefix + "\n" + self.seperator.join(self._current_page) + "\n" + self.suffix)
        self._current_page = []
        self._count = len(self.prefix) + len(self.seperator)

    @property
    def pages(self):
        if len(self._current_page) > 0:
            self.close_page()
        return self._pages


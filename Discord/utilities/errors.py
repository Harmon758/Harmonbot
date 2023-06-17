
from discord.ext.commands.errors import CheckFailure


class NotGuildOwner(CheckFailure):
    """Not Guild Owner"""

class VoiceNotConnected(CheckFailure):
    """Voice Not Connected"""

class PermittedVoiceNotConnected(VoiceNotConnected):
    """Permitted, but Voice Not Connected"""

class NotPermittedVoiceNotConnected(VoiceNotConnected):
    """Voice Not Connected, and Not Permitted"""

class NotPermitted(CheckFailure):
    """Not Permitted"""

class AudioError(CheckFailure):
    """Audio Error"""


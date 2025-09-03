from .start import register_start
from .help import register_help
from .cl import register_cl
from .addwl import register_addwl
from .subwl import register_subwl
from .addsl import register_addsl
from .subsl import register_subsl
from .setwl import register_setwl
from .setsl import register_setsl
from .scr import register_scr
from .ccr import register_ccr


def register_all_commands(application):
    """
    Register all bot commands into the Application.
    """
    register_start(application)
    register_help(application)
    register_cl(application)
    register_addwl(application)
    register_subwl(application)
    register_addsl(application)
    register_subsl(application)
    register_setwl(application)
    register_setsl(application)
    register_scr(application)
    register_ccr(application)

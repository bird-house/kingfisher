from .wps_say_hello import SayHello
from .wps_COP_search import COP_searchProcess
# from .wps_COP_fetch import EO_COP_fetchProcess
# from .wps_COP_indices import EO_COP_indicesProcess


processes = [
    SayHello(),
    COP_searchProcess(),
    # COP_fetchProcess(),
    # COP_indicesProcess(),
]

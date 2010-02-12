"""
 Unit tests for models.
"""

import sys
sys.path.append('../bin')
from models import LocalMusic



lm = LocalMusic()
lm.add_dir("/home/daniel/media/music")
lm.add_dir("/win_fs/D/music")

print "Dirs:"
print lm.get_dir_list()
print "Cache: "
print lm.get_album_cache()

# -*- mode: python -*-

PROJ_HOME='/home/daniel/media/code/MediaMover'
a = Analysis([
	os.path.join(HOMEPATH,'support/_mountzlib.py'), 
	os.path.join(HOMEPATH,'support/useUnicode.py'), 
	PROJ_HOME + '/bin/mover.py', 
	PROJ_HOME + '/bin/models.py', 
	PROJ_HOME + '/bin/view.py'],
             pathex=['/home/daniel/media/software/pyinstaller'],
			 hookspath=['PROJ_HOME' + '/pyinstaller'])
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build/pyi.linux2/mover', 'mover'),
          debug=False,
          strip=True,
          upx=True,
          console=1 )
coll = COLLECT( exe,
               a.binaries,
               a.zipfiles,
               a.datas + [('README', PROJ_HOME + '/README', None)],
               strip=True,
               upx=True,
               name=os.path.join(PROJ_HOME, 'dist'))

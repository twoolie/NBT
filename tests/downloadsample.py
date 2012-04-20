#!/usr/bin/env python
# encoding: utf-8
"""
Download a Minecraft sample world from GitHub and verify the SHA256 checksum.
"""

import sys
import os
try:
	import urllib.request as urllib	  # Python 3
except ImportError:
	import urllib2 as urllib   # Python 2
import logging
import tarfile
import hashlib

URL = "https://github.com/downloads/twoolie/NBT/Sample_World.tar.gz"
"""URL to retrieve"""
checksums = {
	'Sample World/': None, 
	'Sample World/data': None, 
	'Sample World/level.dat': 'f252cf8b938fa1e41c9335ea1bdc70fca73ac5c63c2cf2db4b2ddc4cb2fa4d91', 
	'Sample World/level.dat_mcr': '933238e89a9f7f94c72f236da0d81d44d966c7a1544490e51e682ab42ccc50ff', 
	'Sample World/level.dat_old': 'c4b5a5c355d4f85c369604ca27ee349dba41adc4712a43a6f8c8399fe44071e7', 
	'Sample World/region': None, 
	'Sample World/region/r.-1.0.mca': '6e8ec8698e2e68ca3ee2090da72e4f24c85f9db3f36191e5e33ebc8cafb209f2', 
	'Sample World/region/r.-1.0.mcr': '3a9ccafc6f64b98c0424814f44f1d0d3429cbb33448ff97e2e84ca649bfa16ae', 
	'Sample World/region/r.-1.1.mca': 'c5f6fb5c72ca534d0f73662f2199dca977d2de1521b4823f73384aa6826c4b74', 
	'Sample World/region/r.-1.1.mcr': '8e8b545b412a6a2bb519aee0259a63e6a918cd25a49538451e752e3bf90d4cf1', 
	'Sample World/region/r.0.0.mca': 'd86e51c2adf35f82492e974f75fe83e9e5db56a267a3fe76150dc42f0aeb07c7', 
	'Sample World/region/r.0.0.mcr': 'a8e7fea4e40a70e0d70dea7ebb1328c7623ed01b77d8aff34d01e530fbdad9d5', 
	'Sample World/region/r.0.1.mca': '8a03d910c7fd185ae5efb1409c592e4a9688dfab1fbd31f8c736461157a7675d', 
	'Sample World/region/r.0.1.mcr': '08fcd50748d4633a3b1d52e1b323c7dd9c4299a28ec095d0261fd195d3c9a537', 
	'Sample World/session.lock': 'd05da686dd04cd2ad1f660ddaa7645abc9fd9af396357a5b3256b437af0d7dba', 
}
"""SHA256 checksums for each file in the tar file.
Directories MUST also be included, with None as the checksum"""


def download(url, destination):
	"""
	Download the file from the specified URL, and extract the contents.
	
	May raise an IOError (or one of it's subclasses) upon error, either
	in reading from the URL of writing to file.
	"""
	logger = logging.getLogger("nbt.tests.downloadsample")
	localfile = None
	remotefile = None
	try:
		request = urllib.Request(url)
		remotefile = urllib.urlopen(request)
		localfile = open(destination, 'wb')
		logger.info("Downloading %s" % url)
		chunksize = 524288 # 0.5 MiB
		size = 0
		while True:
			data = remotefile.read(chunksize)
			if not data: break
			localfile.write(data)
			size += len(data)
			logging.info("Downloaded %0.1f MiByte..." % (float(size)/1048576))
	except (urllib.HTTPError) as e:
		logger.error('Download %s failed: HTTP Error %d: %s\n' % (url, e.code, e.reason))
		raise
	except (urllib.URLError) as e:
		# e.reason may be a socket.error. If so, print e.reason.strerror.
		logger.error('Download %s failed: %s\n' % \
				(url, e.reason.strerror if hasattr(e.reason, "strerror") else e.reason))
		raise
	except IOError as e:
		logger.error('Download to %s failed: %s' % \
				(e.filename, e.strerror if hasattr(e, "strerror") else e))
		raise
	finally:
		try:
			remotefile.close()
			localfile.close()
		except (IOError, AttributeError):
			pass
	logging.info("Download complete")

def extract(filename, workdir, filelist):
	"""
	Extract contents of a tar file in workdir. The tar file may be compressed 
	using gzip or bzip2.
	
	For security, only files listed in filelist are extracted.
	Extraneous files will be logged as warning.
	"""
	logger = logging.getLogger("nbt.tests.downloadsample")
	logger.info("Extracting")
	def filefilter(members):
		for tarinfo in members:
			name = tarinfo.name.replace("/", "\\") if "nt" in os.name else tarinfo.name
			if name in filelist:
				logger.info("Extract %s" % tarinfo.name)
				yield tarinfo
			else:
				logger.warning("Skip %s" % tarinfo.name)
	# r:* means any compression (gzip or bz2 are supported)
	files = tarfile.open(filename, 'r:*')
	files.extractall(workdir, filefilter(files.getmembers()))
	files.close()


def verify(dir, checksums):
	"""
	Given a folder, verify if all given files are present and their SHA256 
	checksum is correct. Any files not explicitly listed are deleted.
	
	checksums is a dict of file => checksum, with file a file relative to dir.
	
	Returns a boolean indicating that all checksums are correct, and all files 
	are present.
	
	Any warnings and errors are printer to logger.
	Errors or exceptions result in a return value of False.
	"""
	logger = logging.getLogger("nbt.tests.downloadsample")
	logger.info("Verifying")
	success = True
	for relpath in checksums.keys():
		try:
			check = checksums[relpath]
			if check == None: continue  # Skip folders
			fullpath = os.path.join(dir, relpath)
			localfile = open(fullpath, 'rb')
			h = hashlib.sha256()
			chunksize = 524288 # 0.5 MiB
			while True:
				data = localfile.read(chunksize)
				if not data: break
				h.update(data)
			calc = h.hexdigest()
			if calc != check:
				logger.error("Checksum failed %s: %s found, %s expected" % (relpath, calc, check))
				success = False
		except IOError as e:
			logger.error('Checksum verificiation of %s failed: %s' % \
					(e.filename, e.strerror if hasattr(e, "strerror") else e))
			return False
	return success


def install(url, workdir, checksums):
	"""
	Download and extract a sample world, used for testing.
	The download file and sample world are stored in workdir.
	
	Verifies the checksum of all files. Files without a checksum are not
	extracted.
	"""
	# the paths in checksum are relative, and UNIX-based. Normalise them to 
	# support Windows; and create the following three derivates:
	# - nchecksums: as checksum, but with normalised paths (required for Windows)
	# - dirs: list of full native path of dirs -- to check if folder exists
	# - filepaths: list of relative native path -- to filter extraction
	nchecksums = dict([(os.path.normpath(path), checksums[path]) for path in checksums.keys()])
	filepaths = nchecksums.keys()
	dirs = sorted(os.path.join(workdir, file) for file in filepaths if nchecksums[file] == None)
	
	# only extract files if none of the directories exist (do not overwrite anything)
	if not any(map(os.path.exists, dirs)):
		try:
			file = os.path.join(basedir, os.path.basename(url))
			if not os.path.exists(file):
				download(url=URL, destination=file)
			extract(filename=file, workdir=workdir, filelist=filepaths)
		except IOError:
			raise
			return False
	if not verify(dir=workdir, checksums=nchecksums):
		return False
	else:
		return False


if __name__ == '__main__':
	logger = logging.getLogger("nbt.tests.downloadsample")
	if len(logger.handlers) == 0:
		# Logging is not yet configured. Configure it.
		logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)-8s %(message)s')
	basedir = os.path.dirname(__file__)
	success = install(URL, basedir, checksums)
	sys.exit(0 if success else 1)

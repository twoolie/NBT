#!/usr/bin/env python
# encoding: utf-8
"""
Download a Minecraft sample world from GitHub and verify the SHA256 checksum.
"""

import sys
import os
try:
    import urllib.request as urllib   # Python 3
except ImportError:
    import urllib2 as urllib   # Python 2
import logging
import subprocess
import tarfile
import hashlib

import glob
import tempfile
import shutil


URL = "https://github.com/downloads/twoolie/NBT/Sample_World.tar.gz"
"""URL to retrieve"""
workdir = os.path.dirname(__file__)
"""Directory for download and extracting the sample files"""
worlddir = os.path.join(workdir, 'Sample World')
"""Destination folder for the sample world."""
checksums = {
    'Sample World': None, 
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
Directories MUST also be included (without trailing slash), with None as the checksum"""


def download(url, destination):
    """
    Download the file from the specified URL, and extract the contents.
    
    Uses urllib2.
    
    WARNING: urllib2 does not verify the certificate for Python 
    earlier than 2.7.9 or 3.4.2 (!). Verify the checksums before using 
    the downloaded files.

    Warning: Before Python 2.7.9, urllib2 can't download over HTTPS, since 
    it effectively only supports SSLv3, which is nowadays deprecated by websites.
    In these cases, the following SSLError is raised:
    error:14077410:SSL routines:SSL23_GET_SERVER_HELLO:sslv3 alert handshake failure
    
    May raise an IOError or SSLError.
    """
    logger = logging.getLogger("nbt.tests.downloadsample")
    localfile = None
    remotefile = None
    try:
        logger.info("Downloading %s" % url)
        request = urllib.Request(url)
        remotefile = urllib.urlopen(request)
        localfile = open(destination, 'wb')
        chunksize = 524288 # 0.5 MiB
        size = 0
        while True:
            data = remotefile.read(chunksize)
            if not data: break
            localfile.write(data)
            size += len(data)
            logging.info("Downloaded %0.1f MiByte..." % (float(size)/1048576))
    finally:
        try:
            localfile.close()
        except (IOError, AttributeError):
            pass
    logging.info("Download complete")

def download_with_external_tool(url, destination):
    """
    Download the file from the specified URL, and extract the contents.
    
    Uses the external curl program.
    wget fails if it is compiled with older version of OpenSSL. Hence we use curl.
    
    May raise an OSError (or one of it's subclasses).
    """
    logger = logging.getLogger("nbt.tests.downloadsample")
    logger.info("Downloading %s (with curl)" % url)
    # command = ['wget', '-O', destination, url]
    command = ['curl', '-o', destination, '-L', '-#', url]
    # Open a subprocess, wait till it is done, and get the STDOUT result
    exitcode = subprocess.call(command)
    if exitcode != 0:
        raise OSError("%s returned exit code %d" % (" ".join(command), exitcode))



def extract(filename, workdir, filelist):
    """
    Extract contents of a tar file in workdir. The tar file may be compressed 
    using gzip or bzip2.
    
    For security, only files listed in filelist are extracted.
    Extraneous files will be logged as warning.
    """
    logger = logging.getLogger("nbt.tests.downloadsample")
    logger.info("Extracting %s" % filename)
    def filefilter(members):
        for tarinfo in members:
            if tarinfo.name in filelist:
                logger.info("Extract %s" % tarinfo.name)
                yield tarinfo
            else:
                logger.warning("Skip %s" % tarinfo.name)
    # r:* means any compression (gzip or bz2 are supported)
    files = tarfile.open(filename, 'r:*')
    files.extractall(workdir, filefilter(files.getmembers()))
    files.close()


def verify(checksums):
    """
    Verify if all given files are present and their SHA256 
    checksum is correct. Any files not explicitly listed are deleted.
    
    checksums is a dict of file => checksum, with file a file relative to dir.
    
    Returns a boolean indicating that all checksums are correct, and all files 
    are present.
    
    Any warnings and errors are printer to logger.
    Errors or exceptions result in a return value of False.
    """
    logger = logging.getLogger("nbt.tests.downloadsample")
    success = True
    for path in checksums.keys():
        try:
            check = checksums[path]
            if check == None: continue  # Skip folders
            localfile = open(path, 'rb')
            h = hashlib.sha256()
            chunksize = 524288 # 0.5 MiB
            while True:
                data = localfile.read(chunksize)
                if not data: break
                h.update(data)
            localfile.close()
            calc = h.hexdigest()
            if calc != check:
                logger.error("Checksum failed %s: %s found, %s expected" % (path, calc, check))
                success = False
        except IOError as e:
            if e.errno == 2:
                logger.error('Checksum verificiation failed: file %s not found' % e.filename)
            else:
                logger.error('Checksum verificiation of %s failed: errno %d: %s' % \
                        (e.filename, e.errno, e.strerror))
            return False
    logger.info("Checksum of %d files verified" % len(checksums))
    return success


def install(url=URL, workdir=workdir, checksums=checksums):
    """
    Download and extract a sample world, used for testing.
    The download file and sample world are stored in workdir.
    
    Verifies the checksum of all files. Files without a checksum are not
    extracted.
    """
    # the paths in checksum are relative to the working dir, and UNIX-based. 
    # Normalise them to support Windows; and create the following three derivates:
    # - posixpaths: list of relative posix paths -- to filter tar extraction
    # - nchecksums: as checksum, but with normalised absolute paths
    # - files: list of normalised absolute path of files (non-directories)
    logger = logging.getLogger("nbt.tests.downloadsample")
    posixpaths = checksums.keys()
    nchecksums = dict([(os.path.join(workdir, os.path.normpath(path)), checksums[path]) \
            for path in posixpaths if checksums[path] != None])
    files = nchecksums.keys()
    tar_file = os.path.join(workdir, os.path.basename(url))
    
    if not any(map(os.path.exists, files)):
        # none of the destination files exist. We can safely download/extract without overwriting.
        if not os.path.exists(tar_file):
            has_ssl_error = False
            try:
                download(url=URL, destination=tar_file)
            except urllib.URLError as e:
                # e.reason may be a socket.error. If so, print e.reason.strerror.
                logger.error('Download %s failed: %s' % \
                        (url, e.reason.strerror if hasattr(e.reason, "strerror") else e.reason))
                has_ssl_error = "sslv3" in ("%s" % e)
            except urllib.HTTPError as e:
                # urllib.HTTPError.reason does not have a reason in Python 2.6 (perhaps neither in 2.7).
                logger.error('Download %s failed: HTTP Error %d: %s' % (url, e.code, \
                        e.reason if hasattr(e, "reason") else e))
                return False
            except Exception as e:
                logger.error('Download %s failed: %s' % (url, e))
                return False
            if has_ssl_error:
                try:
                    download_with_external_tool(url=URL, destination=tar_file)
                except Exception as e:
                    logger.error('Download %s failed: %s' % (url, e))
                    return False
        try:
            extract(filename=tar_file, workdir=workdir, filelist=posixpaths)
        except tarfile.TarError as e:
            logger.error('Extract %s failed: %s' % (tar_file, e.message))
            return False
        except Exception as e:
            logger.error('Extract %s failed: %s' % (tar_file, e))
            return False
    return verify(checksums=nchecksums)



def _mkdir(dstdir, subdir):
    """Helper function: create folder /dstdir/subdir"""
    os.mkdir(os.path.join(dstdir, os.path.normpath(subdir)))
def _copyglob(srcdir, destdir, pattern):
    """Helper function: copies files from /srcdir/pattern to /destdir/pattern.
    pattern is a glob pattern."""
    for fullpath in glob.glob(os.path.join(srcdir, os.path.normpath(pattern))):
        relpath = os.path.relpath(fullpath, srcdir)
        shutil.copy2(fullpath, os.path.join(destdir, relpath))
def _copyrename(srcdir, destdir, src, dest):
    """Helper function: copy file from /srcdir/src to /destdir/dest."""
    shutil.copy2(os.path.join(srcdir, os.path.normpath(src)), \
                os.path.join(destdir, os.path.normpath(dest)))

def temp_mcregion_world(worldfolder=worlddir):
    """Create a McRegion worldfolder in a temporary directory, based on the 
    files in the given mixed worldfolder. Returns the temporary directory path."""
    logger = logging.getLogger("nbt.tests.downloadsample")
    tmpfolder = tempfile.mkdtemp(prefix="nbtmcregion")
    logger.info("Create temporary McRegion world folder at %s" % tmpfolder)
    _mkdir(tmpfolder, 'region')
    _copyglob(worldfolder, tmpfolder, "region/*.mcr")
    _copyrename(worldfolder, tmpfolder, "level.dat_mcr", "level.dat")
    return tmpfolder
def temp_anvil_world(worldfolder=worlddir):
    """Create a Anvil worldfolder in a temporary directory, based on the 
    files in the given mixed worldfolder. Returns the temporary directory path."""
    logger = logging.getLogger("nbt.tests.downloadsample")
    tmpfolder = tempfile.mkdtemp(prefix="nbtanvil")
    logger.info("Create temporary Anvil world folder at %s" % tmpfolder)
    _mkdir(tmpfolder, 'region')
    _copyglob(worldfolder, tmpfolder, "region/*.mca")
    _copyrename(worldfolder, tmpfolder, "level.dat", "level.dat")
    return tmpfolder
def cleanup_temp_world(tmpfolder):
    """Remove a temporary directory"""
    logger = logging.getLogger("nbt.tests.downloadsample")
    logger.info("Remove temporary world folder at %s" % tmpfolder)
    shutil.rmtree(tmpfolder, ignore_errors=True)

if __name__ == '__main__':
    logger = logging.getLogger("nbt.tests.downloadsample")
    if len(logger.handlers) == 0:
        # Logging is not yet configured. Configure it.
        logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)-8s %(message)s')
    success = install()
    sys.exit(0 if success else 1)

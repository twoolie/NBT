import os

import pytest

from nbt.world import WorldFolder

from .sample_server import make_world
from .sample_server import world_dir as sample_world_dir


@pytest.fixture(scope='session', autouse=True)
def world_dir():
    make_world()
    yield sample_world_dir


def test_we_have_a_world_dir(world_dir):
    assert os.path.isdir(world_dir)
    assert os.path.exists(os.path.join(world_dir, 'level.dat'))


@pytest.mark.xfail(reason="NBT is not (yet) compatible with Minecraft 1.20.2")
def test_read_no_smoke(world_dir):
    """We dont crash when reading a world"""
    world = WorldFolder(world_dir)
    assert world.get_boundingbox()
    assert world.chunk_count()
    for chunk in world.iter_chunks():
        assert chunk

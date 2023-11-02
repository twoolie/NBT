import os

import pytest

from nbt.world import WorldFolder

from .sample_server import get_world_dir, versions


@pytest.fixture(
    scope='session',
    autouse=True,
    params=versions.keys(),
)
def world_dir(request):
    yield get_world_dir(version=request.param)


def test_we_have_a_world_dir(world_dir):
    assert os.path.isdir(world_dir)
    assert os.path.exists(os.path.join(world_dir, 'level.dat'))


def test_read_no_smoke(world_dir):
    """We dont crash when reading a world"""
    world = WorldFolder(world_dir)
    assert world.get_boundingbox()
    assert world.chunk_count()

    chunk = next(world.iter_chunks())
    assert chunk.get_max_height()

    block = chunk.get_block(0, 0, 0)
    assert block

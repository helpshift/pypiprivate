import pypiprivate.publish as pp

try:
    import mock
except ImportError:
    from unittest import mock

from pkg_resources import packaging
import pytest


Version = packaging.version.Version


def test__filter_pkg_dists():
    dists = ['abc-0.1.0-py2-none-any.whl',
             'abc-0.1.0.tar.gz',
             'abc-0.0.1.tar.gz',
             'abc-0.1.0b1.tar.gz']
    filtered = list(pp._filter_pkg_dists(dists, 'abc', Version('0.1.0')))
    assert ['abc-0.1.0-py2-none-any.whl', 'abc-0.1.0.tar.gz'] == filtered

    filtered = list(pp._filter_pkg_dists(dists, 'abc', Version('0.1.0-beta1')))
    assert ['abc-0.1.0b1.tar.gz'] == filtered


def test_find_pkg_dists():
    project_path = '/tmp/abc'
    with mock.patch('os.listdir') as mock_fn:
        mock_fn.return_value = ['abc-0.1.0-py2-none-any.whl',
                                'abc-0.1.0.tar.gz',
                                'FooBar-3.2.0.tar.gz',
                                'Bat_baz-1.8.4-py2-none-any.whl']
        result = list(pp.find_pkg_dists(project_path, 'dist', 'abc', '0.1.0'))
        expected = [{'pkg': 'abc',
                     'normalized_name': 'abc',
                     'artifact': 'abc-0.1.0-py2-none-any.whl',
                     'path': '/tmp/abc/dist/abc-0.1.0-py2-none-any.whl'},
                    {'pkg': 'abc',
                     'normalized_name': 'abc',
                     'artifact': 'abc-0.1.0.tar.gz',
                     'path': '/tmp/abc/dist/abc-0.1.0.tar.gz'}]
        assert expected == result

        result = list(pp.find_pkg_dists(project_path, 'dist', 'FooBar', '3.2.0'))
        expected = [{'pkg': 'FooBar',
                     'normalized_name': 'foobar',
                     'artifact': 'FooBar-3.2.0.tar.gz',
                     'path': '/tmp/abc/dist/FooBar-3.2.0.tar.gz'}]
        assert expected == result

        result = list(pp.find_pkg_dists(project_path, 'dist', 'Bat_baz', '1.8.4'))
        expected = [{'pkg': 'Bat_baz',
                     'normalized_name': 'batbaz',
                     'artifact': 'Bat_baz-1.8.4.tar.gz',
                     'path': '/tmp/abc/dist/Bat_baz-1.8.4.tar.gz'}]

        mock_fn.assert_called_with('/tmp/abc/dist')


def test_upload_dist():
    dist = {'pkg': 'abc',
            'normalized_name': 'abc',
            'artifact': 'abc-0.1.0.tar.gz',
            'path': '/tmp/abc/dist/abc-0.1.0.tar.gz'}
    storage = mock.MagicMock()
    storage.join_path.return_value = 'abc/abc-0.1.0.tar.gz'
    pp.upload_dist(storage, dist)
    storage.put_file.assert_called_once_with('/tmp/abc/dist/abc-0.1.0.tar.gz',
                                             'abc/abc-0.1.0.tar.gz',
                                             sync=True)


def test_publish_package():
    storage = 'dummy-storage'

    d1 = {'pkg': 'abc',
          'normalized_name': 'abc',
          'artifact': 'abc-0.1.0-py2-none-any.whl',
          'path': '/tmp/abc/dist/abc-0.1.0-py2-none-any.whl'}
    d2 = {'pkg': 'abc',
          'normalized_name': 'abc',
          'artifact': 'abc-0.1.0.tar.gz',
          'path': '/tmp/abc/dist/abc-0.1.0.tar.gz'}
    pkg_dists = [d1, d2]

    pp.find_pkg_dists = mock.Mock()
    pp.find_pkg_dists.return_value = pkg_dists

    # When no dists are already published
    pp.is_dist_published = mock.Mock()
    pp.is_dist_published.return_value = False
    pp.upload_dist = mock.Mock()
    pp.update_pkg_index = mock.Mock()
    pp.update_root_index = mock.Mock()

    pp.publish_package('abc', '0.1.0', storage, '.', 'dist')

    pp.find_pkg_dists.assert_called_once_with('.', 'dist', 'abc', Version('0.1.0'))
    assert pp.upload_dist.call_count == 2
    assert pp.upload_dist.call_args_list[0][0] == (storage, d1)
    assert pp.upload_dist.call_args_list[1][0] == (storage, d2)
    pp.update_pkg_index.assert_called_once_with(storage, 'abc')
    pp.update_root_index.assert_called_once_with(storage)

    # When some dists are already published
    pp.find_pkg_dists = mock.Mock()
    pp.find_pkg_dists.return_value = pkg_dists

    def mock_is_dist_published(storage, dist):
        if dist == d1:
            return True
        elif dist == d2:
            return False

    pp.is_dist_published = mock.Mock()
    pp.is_dist_published.side_effect = mock_is_dist_published
    pp.upload_dist = mock.Mock()
    pp.update_pkg_index = mock.Mock()
    pp.update_root_index = mock.Mock()

    pp.publish_package('abc', '0.1.0', storage, '.', 'dist')

    pp.find_pkg_dists.assert_called_once_with('.', 'dist', 'abc', Version('0.1.0'))
    assert pp.upload_dist.call_count == 1
    assert pp.upload_dist.call_args_list[0][0] == (storage, d2)
    pp.update_pkg_index.assert_called_once_with(storage, 'abc')
    pp.update_root_index.assert_called_once_with(storage)

    # When all dists are already published
    pp.find_pkg_dists = mock.Mock()
    pp.find_pkg_dists.return_value = pkg_dists
    pp.is_dist_published = mock.Mock()
    pp.is_dist_published.return_value = True
    pp.upload_dist = mock.Mock()
    pp.update_pkg_index = mock.Mock()
    pp.update_root_index = mock.Mock()

    pp.publish_package('abc', '0.1.0', storage, '.', 'dist')

    pp.find_pkg_dists.assert_called_once_with('.', 'dist', 'abc', Version('0.1.0'))
    assert pp.upload_dist.call_count == 0
    assert pp.update_pkg_index.call_count == 0
    assert pp.update_root_index.call_count == 0

    # When no dists are found
    pp.find_pkg_dists = mock.Mock()
    pp.find_pkg_dists.return_value = []
    with pytest.raises(pp.DistNotFound):
        pp.publish_package('abc', '0.1.0', storage, '.', 'dist')

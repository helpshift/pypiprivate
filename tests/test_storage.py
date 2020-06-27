import pypiprivate.storage as ps


try:
    import mock
except ImportError:
    from unittest import mock


def test_AWSS3Storage__from_config_1():
    sc = {'bucket': 'mybucket',
          'prefix': 'simple'}
    env = {'PP_S3_ACCESS_KEY': 'access',
           'PP_S3_SECRET_KEY': 'secret'}
    config = mock.Mock(storage_config=sc, env=env)
    with mock.patch('pypiprivate.storage.boto3.Session') as m:
        s = ps.AWSS3Storage.from_config(config)
        assert s.endpoint is None
        assert s.region is None
        assert s.acl == 'private'

        # Assertions on calls made to Session object
        assert len(m.mock_calls) == 3
        c1, c2, c3 = m.mock_calls
        exp_c1 = mock.call(aws_access_key_id='access',
                           aws_secret_access_key='secret',
                           aws_session_token=None)
        exp_c2 = mock.call().resource('s3')
        exp_c3 = mock.call().resource().Bucket('mybucket')
        assert c1 == exp_c1
        assert c2 == exp_c2
        assert c3 == exp_c3


def test_AWSS3Storage__from_config_2():
    sc = {'bucket': 'mybucket',
          'prefix': 'simple',
          'acl': 'public'}
    env = {'PP_S3_ACCESS_KEY': 'access',
           'PP_S3_SECRET_KEY': 'secret',
           'PP_S3_SESSION_TOKEN': 'session'}
    config = mock.Mock(storage_config=sc, env=env)
    with mock.patch('pypiprivate.storage.boto3.Session') as m:
        s = ps.AWSS3Storage.from_config(config)
        assert s.endpoint is None
        assert s.region is None
        assert s.acl == 'public'

        # Assertions on calls made to Session object
        assert len(m.mock_calls) == 3
        c1, c2, c3 = m.mock_calls
        exp_c1 = mock.call(aws_access_key_id='access',
                           aws_secret_access_key='secret',
                           aws_session_token='session')
        exp_c2 = mock.call().resource('s3')
        exp_c3 = mock.call().resource().Bucket('mybucket')
        assert c1 == exp_c1
        assert c2 == exp_c2
        assert c3 == exp_c3


def test_AWSS3Storage__from_config_3():
    sc = {'bucket': 'mybucket',
          'prefix': 'simple',
          'endpoint': 'https://s3.us-west-2.amazonaws.com',
          'region': 'us-west-2'}
    env = {'PP_S3_ACCESS_KEY': 'access',
           'PP_S3_SECRET_KEY': 'secret',
           'PP_S3_SESSION_TOKEN': 'session'}
    config = mock.Mock(storage_config=sc, env=env)
    with mock.patch('pypiprivate.storage.boto3.Session') as m:
        s = ps.AWSS3Storage.from_config(config)
        assert s.endpoint == 'https://s3.us-west-2.amazonaws.com'
        assert s.region == 'us-west-2'
        assert s.acl == 'private'

        # Assertions on calls made to Session object
        assert len(m.mock_calls) == 3
        c1, c2, c3 = m.mock_calls
        exp_c1 = mock.call(aws_access_key_id='access',
                           aws_secret_access_key='secret',
                           aws_session_token='session')
        exp_c2 = mock.call().resource('s3',
                                      endpoint_url='https://s3.us-west-2.amazonaws.com',
                                      region_name='us-west-2')
        exp_c3 = mock.call().resource().Bucket('mybucket')
        assert c1 == exp_c1
        assert c2 == exp_c2
        assert c3 == exp_c3


def test_AWSS3Storage__from_config_4():
    sc = {'bucket': 'mybucket',
          'prefix': 'simple',
          'endpoint': 'https://s3.us-west-2.amazonaws.com',
          'region': 'us-west-2'}
    env = {}
    config = mock.Mock(storage_config=sc, env=env)
    with mock.patch('pypiprivate.storage.boto3.Session') as m:
        s = ps.AWSS3Storage.from_config(config)
        assert s.endpoint == 'https://s3.us-west-2.amazonaws.com'
        assert s.region == 'us-west-2'
        assert s.acl == 'private'

        # Assertions on calls made to Session object
        assert len(m.mock_calls) == 3
        c1, c2, c3 = m.mock_calls
        exp_c1 = mock.call()
        exp_c2 = mock.call().resource('s3',
                                      endpoint_url='https://s3.us-west-2.amazonaws.com',
                                      region_name='us-west-2')
        exp_c3 = mock.call().resource().Bucket('mybucket')
        assert c1 == exp_c1
        assert c2 == exp_c2
        assert c3 == exp_c3

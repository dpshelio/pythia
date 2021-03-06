from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pythia.seo.sunspotter import Sunspotter
from sunpy.util import SunpyUserWarning

path = Path.cwd() / "data/all_clear"


@pytest.fixture
def properties_columns():
    return ['#id', 'filename', 'zooniverse_id', 'angle', 'area', 'areafrac',
            'areathesh', 'bipolesep', 'c1flr24hr', 'id_filename', 'flux',
            'fluxfrac', 'hale', 'hcpos_x', 'hcpos_y', 'm1flr12hr', 'm5flr12hr',
            'n_nar', 'noaa', 'pxpos_x', 'pxpos_y', 'sszn', 'zurich']


@pytest.fixture
def properties(properties_columns):
    # Properties corresponding to `obs_date` '2000-01-01 12:47:02' and `#id` 1
    data = [[1, '530be1183ae74079c300000d.jpg', 'ASZ000090y', 37.8021,
             34400.0, 0.12, 2890.0, 3.72, 0, 1, 2.18e+22, 0.01, 'beta', 452.26991,
             443.92976, 0, 0, 1, 8809, 229.19343999999998, 166.877, 1, 'bxo']]

    return pd.DataFrame(data=data, columns=properties_columns)


@pytest.fixture
def timesfits_columns():
    return ['#id', 'filename', 'obs_date']


@pytest.fixture
def classifications_columns():
    return ['#id', 'zooniverse_class', 'user_id', 'image_id_0', 'image_id_1',
            'image0_more_complex_image1', 'used_inverted', 'bin', 'date_created',
            'date_started', 'date_finished']


@pytest.fixture
def sunspotter(properties_columns, timesfits_columns, classifications_columns):
    return Sunspotter(timesfits=path / "lookup_timesfits.csv",
                      properties=path / "lookup_properties.csv",
                      classifications=path / "classifications.csv",
                      delimiter=';',
                      timesfits_columns=timesfits_columns,
                      properties_columns=properties_columns,
                      classifications_columns=classifications_columns)


@pytest.fixture
def obsdate():
    # `obs_date` corresponding to `#id` 1
    return '2000-01-01 12:47:02'


def test_sunspotter_no_parameters():
    timesfits = pd.read_csv(path / "lookup_timesfits.csv", delimiter=';')
    properties = pd.read_csv(path / "lookup_properties.csv", delimiter=';')

    # get all columns is by default True for both Timesfits and Properties.
    sunspotter = Sunspotter()

    # To get obs_date back a column of dtype `str`
    sunspotter.timesfits.reset_index(inplace=True)
    sunspotter.timesfits.obs_date = sunspotter.timesfits.obs_date.dt.strftime('%Y-%m-%d %H:%M:%S')

    # To get #id back a column of dtype int
    sunspotter.properties.reset_index(inplace=True)

    # Sorting columns as the order of Columns shouldn't matter
    assert sunspotter.timesfits.sort_index(axis=1).equals(timesfits.sort_index(axis=1))
    assert sunspotter.properties.sort_index(axis=1).equals(properties.sort_index(axis=1))


def test_sunspotter_base_object(properties_columns, timesfits_columns):

    sunspotter = Sunspotter(timesfits=path / "lookup_timesfits.csv",
                            properties=path / "lookup_properties.csv",
                            timesfits_columns=timesfits_columns,
                            properties_columns=properties_columns)

    assert set(sunspotter.properties_columns) == set(properties_columns)
    assert set(sunspotter.timesfits_columns) == set(timesfits_columns)


def test_sunspotter_with_classifications(classifications_columns):

    sunspotter = Sunspotter(timesfits=path / "lookup_timesfits.csv",
                            properties=path / "lookup_properties.csv")

    assert sunspotter.classifications_columns is None
    assert sunspotter.classifications is None

    with pytest.raises(SunpyUserWarning):
        # Because Classifications Columns aren't specified.
        Sunspotter(timesfits=path / "lookup_timesfits.csv",
                   properties=path / "lookup_properties.csv",
                   classifications=path / "classifications.csv")

    assert sunspotter.classifications_columns is None
    assert sunspotter.classifications is None

    sunspotter = Sunspotter(timesfits=path / "lookup_timesfits.csv",
                            properties=path / "lookup_properties.csv",
                            classifications=path / "classifications.csv",
                            classifications_columns=classifications_columns)

    assert set(sunspotter.classifications_columns) == set(classifications_columns)


def test_sunspotter_incorrect_delimiter():

    with pytest.raises(SunpyUserWarning):
        Sunspotter(timesfits=path / "lookup_timesfits.csv",
                   properties=path / "lookup_properties.csv",
                   delimiter=',')


def test_sunspotter_properties_columns():

    with pytest.raises(SunpyUserWarning):
        Sunspotter(timesfits=path / "lookup_timesfits.csv",
                   properties=path / "lookup_properties.csv",
                   properties_columns=["This shouldn't be present"],
                   delimiter=';')


def test_sunspotter_classifications_columns():

    with pytest.raises(SunpyUserWarning):
        Sunspotter(timesfits=path / "lookup_timesfits.csv",
                   properties=path / "lookup_properties.csv",
                   classifications=path / "classifications.csv",
                   classifications_columns=["This shouldn't be present"],
                   delimiter=';')


def test_sunspotter_timesfits_columns():

    with pytest.raises(SunpyUserWarning):
        Sunspotter(timesfits=path / "lookup_timesfits.csv",
                   properties=path / "lookup_properties.csv",
                   timesfits_columns=["This shouldn't be present"],
                   delimiter=';')


def test_get_timesfits_id(sunspotter, obsdate):
    assert sunspotter.get_timesfits_id(obsdate) == 1


def test_get_all_ids_for_observation(sunspotter, obsdate):

    assert all(sunspotter.get_all_ids_for_observation(obsdate) == np.array([1, 2, 3, 4, 5]))


def test_get_properties(sunspotter, properties):
    properties.set_index("#id", inplace=True)
    assert sunspotter.get_properties(1).equals(properties.iloc[0])


def test_get_properties_from_obsdate(sunspotter, obsdate, properties):
    properties.set_index("#id", inplace=True)
    assert sunspotter.get_properties_from_obsdate(obsdate).equals(properties.iloc[0])


def test_number_of_observations(sunspotter, obsdate):
    assert sunspotter.number_of_observations(obsdate) == 5


@pytest.mark.parametrize("obsdate,closest_date",
                         [('2000-01-02 00:49:02', '2000-01-02 12:51:02'),
                          ('2000-01-02 00:49:01', '2000-01-01 12:47:02'),
                          ('1999-01-01 00:00:00', '2000-01-01 12:47:02'),
                          ('2100-01-01 00:00:00', '2005-12-31 12:48:02')])
def test_get_nearest_observation(sunspotter, obsdate, closest_date):
    with pytest.warns(SunpyUserWarning):
        assert sunspotter.get_nearest_observation(obsdate) == closest_date


def test_get_all_observations_ids_in_range(sunspotter):
    start = '2000-01-02 12:51:02'
    end = '2000-01-03 12:51:02'
    assert all(sunspotter.get_all_observations_ids_in_range(start, end) == np.array([6, 7, 8, 9, 10, 11, 12, 13]))


@pytest.mark.parametrize("start,end,filenames",
                        [('2000-01-02 12:51:02', '2000-01-03 12:51:02',
                         np.array(['20000102_1251_mdiB_1_8810.fits', '20000102_1251_mdiB_1_8813.fits',
                                   '20000102_1251_mdiB_1_8814.fits', '20000102_1251_mdiB_1_8815.fits',
                                   '20000103_1251_mdiB_1_8810.fits', '20000103_1251_mdiB_1_8813.fits',
                                   '20000103_1251_mdiB_1_8814.fits', '20000103_1251_mdiB_1_8815.fits'], dtype=object)),
                         ('2000-01-02 12:51:02', '2000-01-02 12:51:02',
                         np.array(['20000102_1251_mdiB_1_8810.fits', '20000102_1251_mdiB_1_8813.fits',
                                   '20000102_1251_mdiB_1_8814.fits', '20000102_1251_mdiB_1_8815.fits'], dtype=object))])
def test_get_fits_filenames_from_range(sunspotter, start, end, filenames):
    assert all(sunspotter.get_fits_filenames_from_range(start, end).values == filenames)


@pytest.mark.parametrize("start,end,obslist",
                        [('2000-01-01 12:47:02', '2000-01-15 12:47:02',
                         pd.DatetimeIndex(['2000-01-01 12:47:02', '2000-01-02 12:51:02',
                                           '2000-01-03 12:51:02', '2000-01-04 12:51:02',
                                           '2000-01-05 12:51:02', '2000-01-06 12:51:02',
                                           '2000-01-11 12:51:02', '2000-01-12 12:51:02',
                                           '2000-01-13 12:51:02', '2000-01-14 12:47:02',
                                           '2000-01-15 12:47:02'],
                                           dtype='datetime64[ns]', name='obs_date', freq=None))])
def test_get_available_obsdatetime_range(sunspotter, start, end, obslist):
    assert all(sunspotter.get_available_obsdatetime_range(start, end) == obslist)
